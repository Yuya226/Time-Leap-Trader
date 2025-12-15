"""
リファクタリング後のapp.pyの例（段階的移行用）

既存のapp.pyから新しいレイヤー構造を使うように書き換えた例を示します。
完全に書き換えるのではなく、主要な部分を新しい構造に置き換えます。
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# 新しいレイヤー構造をインポート
from infra.db import DatabaseRepository
from infra.data_fetcher import StockDataFetcher
from application.game_service import GameService
from application.trading_service import TradingService
from domain.models import GameState, Portfolio, PlayerState
from domain.chart import create_candlestick_chart, calculate_sma
from domain.trading import calculate_portfolio_value
from ui.level_up_handler import handle_level_up_ui

# ページ設定
st.set_page_config(layout="wide", page_title="株価チャート - 日足アニメーション")

# ============================================================================
# セッションステートの初期化（既存の関数を使用）
# ============================================================================
# 既存のinit_session_state()関数をそのまま使用
# （段階的移行のため、既存の関数を維持）

# ============================================================================
# インフラ層の初期化
# ============================================================================
if "db_repo" not in st.session_state:
    st.session_state.db_repo = DatabaseRepository()

if "data_fetcher" not in st.session_state:
    st.session_state.data_fetcher = StockDataFetcher()

# ============================================================================
# アプリケーション層の初期化
# ============================================================================
if "game_service" not in st.session_state:
    st.session_state.game_service = GameService(st.session_state.db_repo)

if "trading_service" not in st.session_state:
    st.session_state.trading_service = TradingService(st.session_state.db_repo)

# ============================================================================
# データ取得（新しい構造を使用）
# ============================================================================
ticker = "7203.T"
year = 2024

# 既存のgame_stateから復元
if "game_state" in st.session_state and st.session_state.game_state.get("stock_data") is None:
    with st.spinner("データを取得中..."):
        data, start_date, end_date = st.session_state.data_fetcher.fetch_data(ticker, year)

        if data is not None:
            game_state = GameState(
                current_date=start_date,
                start_date=start_date,
                end_date=end_date,
                stock_data=data
            )
            st.session_state.game_state = game_state.to_dict()
            st.session_state.start_date = start_date
            st.session_state.end_date = end_date
            st.session_state.current_date = start_date
            st.session_state.stock_data = data

# ============================================================================
# メイン処理（新しい構造を使用）
# ============================================================================
if "game_state" in st.session_state and st.session_state.game_state.get("stock_data") is not None:
    # 状態をドメインモデルに復元
    game_state = GameState.from_dict(st.session_state.game_state)
    portfolio = Portfolio.from_dict(st.session_state.portfolio_state)
    player_state = PlayerState.from_dict(st.session_state.player_state)

    data = game_state.stock_data
    current_date = game_state.current_date

    # 表示用データの準備
    context_start_date = game_state.start_date - timedelta(days=60)
    display_data = data[
        (data.index.date >= context_start_date) &
        (data.index.date <= current_date)
    ]

    # SMA計算用データ
    sma_calc_data = data[data.index.date <= current_date]

    # ========================================================================
    # サイドバー: コントロール（既存のUIを維持）
    # ========================================================================
    st.sidebar.title("コントロール")
    st.sidebar.caption("ボタンを押すたびに、日足データが1日ずつ進んでいきます。")

    col1, col2, col3 = st.sidebar.columns(3)

    with col1:
        if st.button("◀ 前の日", disabled=(current_date <= game_state.start_date)):
            if current_date > game_state.start_date:
                prev_data = data[data.index.date < current_date]
                if not prev_data.empty:
                    new_date = prev_data.index[-1].date()
                    game_state.current_date = new_date
                    st.session_state.game_state = game_state.to_dict()
                    st.session_state.current_date = new_date
                    st.rerun()

    with col2:
        if st.button("リセット"):
            # 新しいサービス層を使用
            new_game_state, new_portfolio, new_player_state = st.session_state.game_service.reset_game(game_state)
            st.session_state.game_state = new_game_state.to_dict()
            st.session_state.portfolio_state = new_portfolio.to_dict()
            st.session_state.player_state = new_player_state.to_dict()
            # 既存の変数も更新（後方互換性）
            st.session_state.current_date = new_game_state.current_date
            st.session_state.cash = new_portfolio.cash
            st.session_state.shares = new_portfolio.shares
            st.session_state.buy_dates = new_portfolio.buy_dates
            st.session_state.prev_total_value = new_portfolio.prev_total_value
            st.session_state.level_up_toast_shown = False
            st.session_state.needs_levelup_toast = False
            st.session_state.levelup_toast_message = ""
            st.rerun()

    with col3:
        if st.button("次の日 ▶", disabled=(current_date >= game_state.end_date)):
            if current_date < game_state.end_date:
                # 新しいサービス層を使用
                new_game_state, new_portfolio, level_up_result = st.session_state.game_service.advance_date(
                    game_state, portfolio, days=1
                )

                # 状態を更新
                st.session_state.game_state = new_game_state.to_dict()
                st.session_state.portfolio_state = new_portfolio.to_dict()
                # 既存の変数も更新（後方互換性）
                st.session_state.current_date = new_game_state.current_date
                st.session_state.prev_total_value = new_portfolio.prev_total_value

                # レベルアップ処理
                if level_up_result and level_up_result['level_up']:
                    st.success(f"🎉 レベルアップ！ レベル {level_up_result['old_level']} → レベル {level_up_result['level']} になりました！")
                    handle_level_up_ui(level_up_result)

                st.rerun()

    # ========================================================================
    # サイドバー: 取引（新しいサービス層を使用）
    # ========================================================================
    st.sidebar.markdown("---")
    st.sidebar.title("取引")

    col_buy, col_sell = st.sidebar.columns(2)

    with col_buy:
        if st.button("買い", type="primary", use_container_width=True):
            if not display_data.empty:
                current_price = display_data.loc[display_data.index[-1], 'Close']
                # 新しいサービス層を使用
                new_portfolio, shares, cost, success = st.session_state.trading_service.buy_stock(
                    portfolio, current_price, current_date
                )

                if success:
                    st.session_state.portfolio_state = new_portfolio.to_dict()
                    st.session_state.cash = new_portfolio.cash
                    st.session_state.shares = new_portfolio.shares
                    st.session_state.buy_dates = new_portfolio.buy_dates
                    st.sidebar.success(f"{shares:,}株を¥{current_price:,.0f}で購入しました！")
                else:
                    st.sidebar.warning("現金が不足しています。")
                st.rerun()

    with col_sell:
        if st.button("売り", type="secondary", use_container_width=True, disabled=(portfolio.shares == 0)):
            if portfolio.shares > 0 and not display_data.empty:
                current_price = display_data.loc[display_data.index[-1], 'Close']
                # 新しいサービス層を使用
                new_portfolio, sold_shares, proceeds, profit, level_up_result = st.session_state.trading_service.sell_stock(
                    portfolio, current_price
                )

                st.session_state.portfolio_state = new_portfolio.to_dict()
                st.session_state.cash = new_portfolio.cash
                st.session_state.shares = new_portfolio.shares
                st.session_state.prev_total_value = new_portfolio.prev_total_value

                # レベルアップ処理
                if level_up_result and level_up_result['level_up']:
                    st.success(f"🎉 レベルアップ！ レベル {level_up_result['old_level']} → レベル {level_up_result['level']} になりました！")
                    handle_level_up_ui(level_up_result)

                st.sidebar.success(f"{sold_shares:,}株を¥{current_price:,.0f}で売却しました！")
                if profit > 0:
                    exp_bonus = int(profit * 0.001)
                    st.sidebar.info(f"利確ボーナス: +{exp_bonus}経験値獲得！")
                st.rerun()

    # ========================================================================
    # メイン表示エリア（新しいチャート生成関数を使用）
    # ========================================================================
    if not display_data.empty:
        # プレイヤーステータス取得
        player_stats = st.session_state.db_repo.get_player_stats()
        player_level = player_stats['level']

        # ポートフォリオ情報
        current_price = display_data.loc[display_data.index[-1], 'Close']
        total_value = calculate_portfolio_value(portfolio, current_price)
        profit_loss = total_value - player_state.initial_capital
        profit_loss_pct = (profit_loss / player_state.initial_capital) * 100

        # HUD表示（既存のUIを維持）
        # ... (既存のHUDコード)

        # チャート生成（新しい関数を使用）
        sma_25_full, sma_75_full = calculate_sma(sma_calc_data)
        sma_25 = sma_25_full[sma_25_full.index.isin(display_data.index)]
        sma_75 = sma_75_full[sma_75_full.index.isin(display_data.index)]

        # UI状態からSMA設定を取得
        sma_25_enabled = st.session_state.get("sma_25_enabled", False)
        sma_75_enabled = st.session_state.get("sma_75_enabled", False)

        fig = create_candlestick_chart(
            display_data=display_data,
            buy_dates=portfolio.buy_dates,
            sma_25_data=sma_25 if sma_25_enabled else None,
            sma_75_data=sma_75 if sma_75_enabled else None,
            player_level=player_level,
            current_date=current_date,
            year=year,
            ticker=ticker
        )

        st.plotly_chart(fig, use_container_width=True)

        # レベルアップ通知（既存の処理を維持）
        if st.session_state.get("needs_levelup_toast") and st.session_state.get("levelup_toast_message"):
            st.toast(st.session_state.levelup_toast_message, icon="🆙")
            st.session_state.needs_levelup_toast = False
            st.session_state.levelup_toast_message = ""

else:
    st.info("データを取得中です。しばらくお待ちください...")
