"""
Streamlitアプリ - メインファイル（処理の流れのみ）
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# 新しいレイヤー構造をインポート
from infra.db import init_db, get_player_stats, update_exp, DatabaseRepository
from infra.data_fetcher import StockDataFetcher
from domain.models import Portfolio
from domain.exp import calc_exp_gain, calc_profit_bonus_exp
from domain.trading import calculate_portfolio_value, execute_buy, execute_sell
from domain.calculations import calculate_price_change, prepare_display_data
from ui.sidebar import (
    render_control_sidebar,
    render_display_period_selector,
    render_date_info_sidebar,
    render_trading_sidebar,
    render_equipment_sidebar,
    render_skip_buttons_sidebar,
    render_debug_sidebar
)
from ui.hud import render_hud, render_metrics
from ui.chart_display import render_chart
from ui.level_up_handler import handle_level_up_ui

# ページ設定
st.set_page_config(layout="wide", page_title="株価チャート - 日足アニメーション")

# ============================================================================
# セッションステートの初期化
# ============================================================================
def init_session_state():
    """セッションステートを論理的なグループごとに初期化する"""
    # game_state: ゲーム進行に関する状態
    if "game_state" not in st.session_state:
        st.session_state.game_state = {
            "current_date": None,
            "start_date": None,
            "end_date": None,
            "stock_data": None
        }

    # portfolio_state: ポートフォリオに関する状態
    if "portfolio_state" not in st.session_state:
        st.session_state.portfolio_state = {
            "cash": 1000000,
            "shares": 0,
            "buy_dates": [],
            "prev_total_value": 1000000
        }

    # player_state: プレイヤーに関する状態
    if "player_state" not in st.session_state:
        st.session_state.player_state = {
            "initial_capital": 1000000
        }

    # ui_state: UI表示に関する状態
    if "ui_state" not in st.session_state:
        st.session_state.ui_state = {
            "level_up_toast_shown": False,
            "needs_levelup_toast": False,
            "levelup_toast_message": "",
            "sma_25_enabled": False,
            "sma_75_enabled": False
        }

    _sync_session_state()

def _sync_session_state():
    """グループ化されたstateと既存の変数名を同期する（後方互換性のため）"""
    # game_state の同期
    if "current_date" not in st.session_state:
        st.session_state.current_date = st.session_state.game_state.get("current_date")
    else:
        st.session_state.game_state["current_date"] = st.session_state.current_date

    if "stock_data" not in st.session_state:
        st.session_state.stock_data = st.session_state.game_state.get("stock_data")
    else:
        st.session_state.game_state["stock_data"] = st.session_state.stock_data

    if "start_date" not in st.session_state:
        st.session_state.start_date = st.session_state.game_state.get("start_date")
    else:
        st.session_state.game_state["start_date"] = st.session_state.start_date

    if "end_date" not in st.session_state:
        st.session_state.end_date = st.session_state.game_state.get("end_date")
    else:
        st.session_state.game_state["end_date"] = st.session_state.end_date

    # portfolio_state の同期
    if "cash" not in st.session_state:
        st.session_state.cash = st.session_state.portfolio_state.get("cash")
    else:
        st.session_state.portfolio_state["cash"] = st.session_state.cash

    if "shares" not in st.session_state:
        st.session_state.shares = st.session_state.portfolio_state.get("shares")
    else:
        st.session_state.portfolio_state["shares"] = st.session_state.shares

    if "buy_dates" not in st.session_state:
        st.session_state.buy_dates = st.session_state.portfolio_state.get("buy_dates")
    else:
        st.session_state.portfolio_state["buy_dates"] = st.session_state.buy_dates

    if "prev_total_value" not in st.session_state:
        st.session_state.prev_total_value = st.session_state.portfolio_state.get("prev_total_value")
    else:
        st.session_state.portfolio_state["prev_total_value"] = st.session_state.prev_total_value

    # player_state の同期
    if "initial_capital" not in st.session_state:
        st.session_state.initial_capital = st.session_state.player_state.get("initial_capital")
    else:
        st.session_state.player_state["initial_capital"] = st.session_state.initial_capital

    # ui_state の同期
    if "level_up_toast_shown" not in st.session_state:
        st.session_state.level_up_toast_shown = st.session_state.ui_state.get("level_up_toast_shown")
    else:
        st.session_state.ui_state["level_up_toast_shown"] = st.session_state.level_up_toast_shown

    if "needs_levelup_toast" not in st.session_state:
        st.session_state.needs_levelup_toast = st.session_state.ui_state.get("needs_levelup_toast")
    else:
        st.session_state.ui_state["needs_levelup_toast"] = st.session_state.needs_levelup_toast

    if "levelup_toast_message" not in st.session_state:
        st.session_state.levelup_toast_message = st.session_state.ui_state.get("levelup_toast_message")
    else:
        st.session_state.ui_state["levelup_toast_message"] = st.session_state.levelup_toast_message

    if "sma_25_enabled" not in st.session_state:
        st.session_state.sma_25_enabled = st.session_state.ui_state.get("sma_25_enabled")
    else:
        st.session_state.ui_state["sma_25_enabled"] = st.session_state.sma_25_enabled

    if "sma_75_enabled" not in st.session_state:
        st.session_state.sma_75_enabled = st.session_state.ui_state.get("sma_75_enabled")
    else:
        st.session_state.ui_state["sma_75_enabled"] = st.session_state.sma_75_enabled

# セッションステートの初期化
init_session_state()

# ============================================================================
# データベース接続
# ============================================================================
if "db_conn" not in st.session_state:
    st.session_state.db_conn = init_db()

# ============================================================================
# データ取得（キャッシュ化）
# ============================================================================
@st.cache_data
def fetch_stock_data(ticker: str, year: int, days_before_start: int = 220):
    """
    株価データを取得する（キャッシュ化）

    Args:
        ticker: ティッカーシンボル
        year: 取得する年
        days_before_start: 開始日の何日前から取得するか

    Returns:
        Tuple[DataFrame, start_date, end_date]: (データ, 開始日, 終了日)
    """
    data_fetcher = StockDataFetcher()
    return data_fetcher.fetch_data(ticker, year, days_before_start=days_before_start)

ticker = "7203.T"
year = 2024

if st.session_state.stock_data is None:
    with st.spinner("データを取得中..."):
        data, start_date, end_date = fetch_stock_data(ticker, year, days_before_start=220)

        if data is not None:
            st.session_state.stock_data = data
            st.session_state.start_date = start_date
            st.session_state.end_date = end_date
            st.session_state.current_date = start_date
            st.session_state.game_state["stock_data"] = data
            st.session_state.game_state["start_date"] = start_date
            st.session_state.game_state["end_date"] = end_date
            st.session_state.game_state["current_date"] = start_date
        else:
            st.error("データの取得に失敗しました。")

# ============================================================================
# メイン処理
# ============================================================================
if st.session_state.stock_data is not None and st.session_state.current_date is not None:
    data = st.session_state.stock_data
    current_date = st.session_state.current_date
    start_date = st.session_state.start_date
    end_date = st.session_state.end_date

    # ========================================================================
    # サイドバー: 表示期間選択
    # ========================================================================
    display_business_days = render_display_period_selector()

    # 表示データの準備（純粋関数）
    display_data, sma_calc_data = prepare_display_data(data, current_date, start_date, display_business_days=display_business_days)

    # ========================================================================
    # サイドバー: コントロール
    # ========================================================================
    control_action = render_control_sidebar(current_date, start_date, end_date, display_data, data)

    if control_action == "prev":
        if current_date > start_date:
            prev_data = data[data.index.date < current_date]
            if not prev_data.empty:
                st.session_state.current_date = prev_data.index[-1].date()
                st.session_state.game_state["current_date"] = st.session_state.current_date
                st.rerun()

    elif control_action == "reset":
        st.session_state.current_date = start_date
        st.session_state.cash = 1000000
        st.session_state.shares = 0
        st.session_state.buy_dates = []
        st.session_state.prev_total_value = 1000000
        st.session_state.level_up_toast_shown = False
        st.session_state.needs_levelup_toast = False
        st.session_state.levelup_toast_message = ""
        st.session_state.portfolio_state = {
            "cash": 1000000,
            "shares": 0,
            "buy_dates": [],
            "prev_total_value": 1000000
        }
        st.session_state.ui_state["level_up_toast_shown"] = False
        st.session_state.ui_state["needs_levelup_toast"] = False
        st.session_state.ui_state["levelup_toast_message"] = ""
        db_repo = DatabaseRepository()
        db_repo.reset_player_stats()
        st.rerun()

    elif control_action == "next":
        if current_date < end_date:
            next_data = data[data.index.date > current_date]
            if not next_data.empty:
                current_price_before = display_data.loc[display_data.index[-1], 'Close'] if not display_data.empty else 0
                current_total_before = st.session_state.cash + (st.session_state.shares * current_price_before)

                st.session_state.current_date = next_data.index[0].date()
                st.session_state.game_state["current_date"] = st.session_state.current_date

                new_display_data = data[data.index.date <= st.session_state.current_date]
                new_current_price = new_display_data.loc[new_display_data.index[-1], 'Close'] if not new_display_data.empty else 0
                new_total_value = st.session_state.cash + (st.session_state.shares * new_current_price)

                exp_to_add = calc_exp_gain(st.session_state.prev_total_value, new_total_value, rate=0.0001)
                if exp_to_add > 0:
                    result = update_exp(st.session_state.db_conn, exp_to_add)
                    if result and result['level_up']:
                        st.success(f"🎉 レベルアップ！ レベル {result['old_level']} → レベル {result['level']} になりました！")
                        handle_level_up_ui(result)

                st.session_state.prev_total_value = new_total_value
                st.session_state.portfolio_state["prev_total_value"] = new_total_value
                st.rerun()

    # ========================================================================
    # 日付を進める共通関数
    # ========================================================================
    def advance_date(days_to_advance):
        """指定した日数分、営業日を進める"""
        if current_date >= end_date:
            return

        future_data = data[data.index.date > current_date]
        if future_data.empty:
            return

        available_dates = list(future_data.index.date)
        if len(available_dates) >= days_to_advance:
            new_date = available_dates[days_to_advance - 1]
        else:
            new_date = end_date

        current_price_before = display_data.loc[display_data.index[-1], 'Close'] if not display_data.empty else 0
        current_total_before = st.session_state.cash + (st.session_state.shares * current_price_before)

        st.session_state.current_date = new_date
        st.session_state.game_state["current_date"] = new_date

        new_display_data = data[data.index.date <= st.session_state.current_date]
        new_current_price = new_display_data.loc[new_display_data.index[-1], 'Close'] if not new_display_data.empty else 0
        new_total_value = st.session_state.cash + (st.session_state.shares * new_current_price)

        exp_to_add = calc_exp_gain(st.session_state.prev_total_value, new_total_value, rate=0.0001)
        if exp_to_add > 0:
            result = update_exp(st.session_state.db_conn, exp_to_add)
            if result and result['level_up']:
                st.success(f"🎉 レベルアップ！ レベル {result['old_level']} → レベル {result['level']} になりました！")
                handle_level_up_ui(result)

        st.session_state.prev_total_value = new_total_value
        st.session_state.portfolio_state["prev_total_value"] = new_total_value
        st.rerun()

    # ========================================================================
    # サイドバー: スキップボタン
    # ========================================================================
    skip_days = render_skip_buttons_sidebar(current_date, end_date)
    if skip_days:
        advance_date(skip_days)

    # ========================================================================
    # サイドバー: デバッグ
    # ========================================================================
    if render_debug_sidebar():
        result = update_exp(st.session_state.db_conn, 100)
        if result and result['level_up']:
            st.success(f"🎉 レベルアップ！ レベル {result['old_level']} → レベル {result['level']} になりました！")
            handle_level_up_ui(result)
        else:
            player_stats = get_player_stats(st.session_state.db_conn)
            st.sidebar.info(f"経験値 +100 獲得！ (現在のレベル: {player_stats['level']})")
        st.rerun()

    # ========================================================================
    # サイドバー: 日付情報
    # ========================================================================
    render_date_info_sidebar(current_date, start_date, end_date, display_data)

    # ========================================================================
    # サイドバー: 取引
    # ========================================================================
    if not display_data.empty:
        current_price = display_data.loc[display_data.index[-1], 'Close']
        trading_action = render_trading_sidebar(current_price, current_date, st.session_state.shares)

        if trading_action == "buy":
            portfolio = Portfolio(
                cash=st.session_state.cash,
                shares=st.session_state.shares,
                buy_dates=st.session_state.buy_dates,
                prev_total_value=st.session_state.prev_total_value
            )
            new_portfolio, shares, cost, success = execute_buy(portfolio, current_price, current_date)

            if success:
                st.session_state.cash = new_portfolio.cash
                st.session_state.shares = new_portfolio.shares
                st.session_state.buy_dates = new_portfolio.buy_dates
                st.session_state.portfolio_state = new_portfolio.to_dict()
                st.sidebar.success(f"{shares:,}株を¥{current_price:,.0f}で購入しました！")
            else:
                st.sidebar.warning("現金が不足しています。")
            st.rerun()

        elif trading_action == "sell":
            portfolio = Portfolio(
                cash=st.session_state.cash,
                shares=st.session_state.shares,
                buy_dates=st.session_state.buy_dates,
                prev_total_value=st.session_state.prev_total_value
            )
            new_portfolio, sold_shares, proceeds, profit = execute_sell(portfolio, current_price)

            total_value_after = new_portfolio.cash
            exp_bonus = calc_profit_bonus_exp(profit, rate=0.001)
            if exp_bonus > 0:
                result = update_exp(st.session_state.db_conn, exp_bonus)
                if result and result['level_up']:
                    st.success(f"🎉 レベルアップ！ レベル {result['old_level']} → レベル {result['level']} になりました！")
                    handle_level_up_ui(result)
                st.sidebar.info(f"利確ボーナス: +{exp_bonus}経験値獲得！")

            st.session_state.cash = new_portfolio.cash
            st.session_state.shares = new_portfolio.shares
            st.session_state.prev_total_value = total_value_after
            st.session_state.portfolio_state = new_portfolio.to_dict()
            st.sidebar.success(f"{sold_shares:,}株を¥{current_price:,.0f}で売却しました！")
            st.rerun()

    # ========================================================================
    # サイドバー: 装備設定
    # ========================================================================
    player_stats = get_player_stats(st.session_state.db_conn)
    equipment_state = render_equipment_sidebar(
        player_stats['level'],
        st.session_state.get("sma_25_enabled", False),
        st.session_state.get("sma_75_enabled", False)
    )
    st.session_state.sma_25_enabled = equipment_state['sma_25_enabled']
    st.session_state.sma_75_enabled = equipment_state['sma_75_enabled']
    st.session_state.ui_state["sma_25_enabled"] = equipment_state['sma_25_enabled']
    st.session_state.ui_state["sma_75_enabled"] = equipment_state['sma_75_enabled']

    # ========================================================================
    # メイン表示エリア
    # ========================================================================
    if not display_data.empty:
        current_price = display_data.loc[display_data.index[-1], 'Close']
        total_value = calculate_portfolio_value(
            Portfolio(
                cash=st.session_state.cash,
                shares=st.session_state.shares,
                buy_dates=st.session_state.buy_dates,
                prev_total_value=st.session_state.prev_total_value
            ),
            current_price
        )
        profit_loss = total_value - st.session_state.initial_capital
        profit_loss_pct = (profit_loss / st.session_state.initial_capital) * 100

        # HUD表示
        render_hud(
            player_stats=player_stats,
            total_value=total_value,
            cash=st.session_state.cash,
            shares=st.session_state.shares,
            profit_loss=profit_loss,
            profit_loss_pct=profit_loss_pct,
            current_date=current_date,
            display_data_count=len(display_data),
            total_data_count=len(data)
        )

        # メトリクス表示
        latest_data = display_data.iloc[-1]
        change, change_pct = calculate_price_change(display_data)
        render_metrics(
            current_price=latest_data.loc['Close'],
            change=change,
            change_pct=change_pct,
            high=latest_data.loc['High'],
            low=latest_data.loc['Low']
        )

        # チャート表示
        render_chart(
            display_data=display_data,
            buy_dates=st.session_state.buy_dates,
            sma_25_enabled=st.session_state.sma_25_enabled,
            sma_75_enabled=st.session_state.sma_75_enabled,
            sma_calc_data=sma_calc_data,
            player_level=player_stats['level'],
            current_date=current_date,
            year=year,
            ticker=ticker
        )
    else:
        st.warning("表示するデータがありません。")
else:
    st.info("データを取得中です。しばらくお待ちください...")

# ========================================================================
# レベルアップ通知（画面描画の最後に表示）
# ========================================================================
if st.session_state.needs_levelup_toast and st.session_state.levelup_toast_message:
    st.toast(st.session_state.levelup_toast_message, icon="🆙")
    st.session_state.needs_levelup_toast = False
    st.session_state.levelup_toast_message = ""
    st.session_state.ui_state["needs_levelup_toast"] = False
    st.session_state.ui_state["levelup_toast_message"] = ""
