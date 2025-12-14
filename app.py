import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3

# ページ設定
st.set_page_config(layout="wide", page_title="株価チャート - 日足アニメーション")

# セッションステートの初期化
if "current_date" not in st.session_state:
    st.session_state.current_date = None
if "stock_data" not in st.session_state:
    st.session_state.stock_data = None
if "start_date" not in st.session_state:
    st.session_state.start_date = None
if "end_date" not in st.session_state:
    st.session_state.end_date = None
if "cash" not in st.session_state:
    st.session_state.cash = 1000000  # 初期資金100万円
if "shares" not in st.session_state:
    st.session_state.shares = 0  # 初期保有株数0
if "buy_dates" not in st.session_state:
    st.session_state.buy_dates = []  # 買いを実行した日付のリスト
if "initial_capital" not in st.session_state:
    st.session_state.initial_capital = 1000000  # 初期資産（評価損益計算用）
if "prev_total_value" not in st.session_state:
    st.session_state.prev_total_value = 1000000  # 前日の総資産（経験値計算用）

# SQLiteデータベースの初期化
def init_db():
    """データベースとテーブルを初期化"""
    db_path = "trading_game.db"
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # 経験値とレベルのテーブルを作成
    c.execute('''
        CREATE TABLE IF NOT EXISTS player_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level INTEGER DEFAULT 1,
            exp INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 初期データが存在しない場合は作成
    c.execute('SELECT COUNT(*) FROM player_stats')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO player_stats (level, exp) VALUES (1, 0)')

    conn.commit()
    return conn

def get_player_stats(conn):
    """プレイヤーの経験値とレベルを取得"""
    c = conn.cursor()
    c.execute('SELECT level, exp FROM player_stats ORDER BY id DESC LIMIT 1')
    result = c.fetchone()
    if result:
        return {'level': result[0], 'exp': result[1]}
    return {'level': 1, 'exp': 0}

def update_exp(conn, exp_to_add):
    """経験値を追加し、レベルアップ判定を行う"""
    c = conn.cursor()
    c.execute('SELECT level, exp FROM player_stats ORDER BY id DESC LIMIT 1')
    result = c.fetchone()

    if result:
        current_level = result[0]
        current_exp = result[1]
        new_exp = current_exp + exp_to_add

        # レベルアップ判定（線形: レベル * 50で序盤を早く）
        required_exp = current_level * 50
        new_level = current_level

        level_up = False
        while new_exp >= required_exp:
            new_exp -= required_exp
            new_level += 1
            required_exp = new_level * 50
            level_up = True

        # データベースを更新
        c.execute('''
            UPDATE player_stats
            SET level = ?, exp = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = (SELECT id FROM player_stats ORDER BY id DESC LIMIT 1)
        ''', (new_level, new_exp))

        conn.commit()

        return {'level': new_level, 'exp': new_exp, 'level_up': level_up, 'old_level': current_level}
    return None

# データベース接続
if "db_conn" not in st.session_state:
    st.session_state.db_conn = init_db()

# データ取得
ticker = "7203.T"  # トヨタ
year = 2020

if st.session_state.stock_data is None:
    with st.spinner("データを取得中..."):
        try:
            # 2020年のデータを取得
            start = datetime(year, 1, 1)
            end = datetime(year, 12, 31)

            data = yf.download(ticker, start=start, end=end)

            # MultiIndexの場合は最初の銘柄を取得
            if isinstance(data.columns, pd.MultiIndex):
                data = data.xs(ticker, axis=1, level=1)

            if not data.empty:
                st.session_state.stock_data = data
                st.session_state.start_date = data.index[0].date()
                st.session_state.end_date = data.index[-1].date()
                st.session_state.current_date = st.session_state.start_date
            else:
                st.error("データの取得に失敗しました。")
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

# データが取得できている場合
if st.session_state.stock_data is not None and st.session_state.current_date is not None:
    data = st.session_state.stock_data

    # 現在の日付までのデータを抽出
    current_date = st.session_state.current_date
    display_data = data[data.index.date <= current_date]

    # サイドバーにコントロール
    st.sidebar.title("コントロール")
    st.sidebar.caption("ボタンを押すたびに、日足データが1日ずつ進んでいきます。")

    col1, col2, col3 = st.sidebar.columns(3)

    with col1:
        if st.button("◀ 前の日", disabled=(current_date <= st.session_state.start_date)):
            if current_date > st.session_state.start_date:
                # 前の営業日を探す
                prev_data = data[data.index.date < current_date]
                if not prev_data.empty:
                    st.session_state.current_date = prev_data.index[-1].date()
                    st.rerun()

    with col2:
        if st.button("リセット"):
            st.session_state.current_date = st.session_state.start_date
            st.session_state.cash = 1000000
            st.session_state.shares = 0
            st.session_state.buy_dates = []
            st.session_state.prev_total_value = 1000000
            # データベースもリセット
            c = st.session_state.db_conn.cursor()
            c.execute('UPDATE player_stats SET level = 1, exp = 0, updated_at = CURRENT_TIMESTAMP WHERE id = (SELECT id FROM player_stats ORDER BY id DESC LIMIT 1)')
            st.session_state.db_conn.commit()
            st.rerun()

    with col3:
        if st.button("次の日 ▶", disabled=(current_date >= st.session_state.end_date)):
            if current_date < st.session_state.end_date:
                # 次の営業日を探す
                next_data = data[data.index.date > current_date]
                if not next_data.empty:
                    # 条件A: 前日より総資産が増えている場合のみ経験値を加算
                    current_price_before = display_data.loc[display_data.index[-1], 'Close'] if not display_data.empty else 0
                    current_total_before = st.session_state.cash + (st.session_state.shares * current_price_before)

                    # 日付を進める
                    st.session_state.current_date = next_data.index[0].date()

                    # 新しい日付での総資産を計算
                    new_display_data = data[data.index.date <= st.session_state.current_date]
                    new_current_price = new_display_data.loc[new_display_data.index[-1], 'Close'] if not new_display_data.empty else 0
                    new_total_value = st.session_state.cash + (st.session_state.shares * new_current_price)

                    # 総資産が増えている場合のみ経験値を加算（増加額の0.01%）
                    if new_total_value > st.session_state.prev_total_value:
                        increase_amount = new_total_value - st.session_state.prev_total_value
                        exp_to_add = int(increase_amount * 0.0001)  # 0.01% = 0.0001
                        if exp_to_add > 0:
                            result = update_exp(st.session_state.db_conn, exp_to_add)
                            if result and result['level_up']:
                                st.success(f"🎉 レベルアップ！ レベル {result['old_level']} → レベル {result['level']} になりました！")

                    # 前日の総資産を更新
                    st.session_state.prev_total_value = new_total_value
                    st.rerun()

    # 日付表示
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**現在の日付:** {current_date.strftime('%Y年%m月%d日')}")
    st.sidebar.markdown(f"**表示日数:** {len(display_data)}日")
    st.sidebar.markdown(f"**開始日:** {st.session_state.start_date.strftime('%Y年%m月%d日')}")
    st.sidebar.markdown(f"**終了日:** {st.session_state.end_date.strftime('%Y年%m月%d日')}")

    # 進捗バー
    progress = (current_date - st.session_state.start_date).days / (st.session_state.end_date - st.session_state.start_date).days
    st.sidebar.progress(progress)

    # 取引セクション
    st.sidebar.markdown("---")
    st.sidebar.title("取引")

    # 買い・売りボタン
    col_buy, col_sell = st.sidebar.columns(2)

    with col_buy:
        if st.button("買い", type="primary", use_container_width=True):
            if not display_data.empty:
                current_price = display_data.loc[display_data.index[-1], 'Close']
                # 可能な限り購入（1株単位）
                max_shares = int(st.session_state.cash / current_price)
                if max_shares > 0:
                    cost = max_shares * current_price
                    st.session_state.cash -= cost
                    st.session_state.shares += max_shares
                    # 買いを実行した日付を記録
                    if current_date not in st.session_state.buy_dates:
                        st.session_state.buy_dates.append(current_date)
                    st.sidebar.success(f"{max_shares:,}株を¥{current_price:,.0f}で購入しました！")
                else:
                    st.sidebar.warning("現金が不足しています。")
                st.rerun()

    with col_sell:
        if st.button("売り", type="secondary", use_container_width=True, disabled=(st.session_state.shares == 0)):
            if st.session_state.shares > 0 and not display_data.empty:
                current_price = display_data.loc[display_data.index[-1], 'Close']
                proceeds = st.session_state.shares * current_price

                # 条件B: 利益が出た場合、その利益額の0.1%をボーナス経験値として加算
                # 買い時の総コストを計算（簡易版: 現在の現金と保有株から逆算）
                # より正確には、買い時の価格を記録する必要があるが、簡易的に総資産の変化で判定
                total_value_before = st.session_state.cash + (st.session_state.shares * current_price)

                st.session_state.cash += proceeds
                sold_shares = st.session_state.shares
                st.session_state.shares = 0

                total_value_after = st.session_state.cash
                profit = total_value_after - st.session_state.prev_total_value

                # 利益が出た場合のみ経験値を加算
                if profit > 0:
                    exp_bonus = int(profit * 0.001)  # 0.1% = 0.001
                    if exp_bonus > 0:
                        result = update_exp(st.session_state.db_conn, exp_bonus)
                        if result and result['level_up']:
                            st.success(f"🎉 レベルアップ！ レベル {result['old_level']} → レベル {result['level']} になりました！")
                        st.sidebar.info(f"利確ボーナス: +{exp_bonus}経験値獲得！")

                st.session_state.prev_total_value = total_value_after
                st.sidebar.success(f"{sold_shares:,}株を¥{current_price:,.0f}で売却しました！")
                st.rerun()

    # メイン表示エリア
    if not display_data.empty:
        # HUD: プレイヤーステータスと資産情報をメイン画面の最上部に表示
        current_price = display_data.loc[display_data.index[-1], 'Close'] if not display_data.empty else 0
        total_value = st.session_state.cash + (st.session_state.shares * current_price)
        profit_loss = total_value - st.session_state.initial_capital
        profit_loss_pct = (profit_loss / st.session_state.initial_capital) * 100

        # プレイヤーステータスを取得
        player_stats = get_player_stats(st.session_state.db_conn)
        required_exp = player_stats['level'] * 50  # 線形: レベル * 50
        exp_progress = (player_stats['exp'] / required_exp) * 100 if required_exp > 0 else 0

        # HUDレイアウト（横一列）- st.metricを使用
        hud_col1, hud_col2, hud_col3, hud_col4 = st.columns(4)

        with hud_col1:

            # レベルと経験値を横並びに配置
            level_col, exp_col = st.columns(2)
            with level_col:
                st.metric("🎮 レベル", f"Lv.{player_stats['level']}")
            with exp_col:
                remaining_exp = required_exp - player_stats['exp']
                progress_text = f"進捗: {exp_progress:.1f}%" if remaining_exp > 0 else "MAX"
                st.metric("経験値", f"{player_stats['exp']} / {required_exp}", delta=progress_text)
            # 経験値バーを先に表示
            st.progress(exp_progress / 100)

        with hud_col2:
            # 総資産表示
            st.metric("💰 総資産", f"¥{total_value:,.0f}")
            # 現金と保有株の詳細
            st.caption(f"現金: ¥{st.session_state.cash:,.0f}")
            if st.session_state.shares > 0:
                st.caption(f"保有株: {st.session_state.shares:,}株")

        with hud_col3:
            # 評価損益表示
            profit_sign = "+" if profit_loss >= 0 else ""
            st.metric(
                "📊 評価損益",
                f"¥{profit_loss:+,.0f}",
                delta=f"{profit_sign}{profit_loss_pct:.2f}%"
            )

        with hud_col4:
            # 日付情報
            st.metric("📅 現在の日付", current_date.strftime('%Y年%m月%d日'))
            st.caption(f"進捗: {len(display_data)}日 / {len(data)}日")

        # 現在の日付の情報
        latest_data = display_data.iloc[-1]
        current_price = latest_data.loc['Close']

        # 前日比の計算
        if len(display_data) > 1:
            prev_price = display_data.loc[display_data.index[-2], 'Close']
            change = current_price - prev_price
            change_pct = (change / prev_price) * 100
        else:
            change = 0
            change_pct = 0

        # メトリクス表示
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("終値", f"¥{current_price:,.0f}")
        with col2:
            st.metric("前日比", f"¥{change:+,.0f}", f"{change_pct:+.2f}%")
        with col3:
            st.metric("高値", f"¥{latest_data.loc['High']:,.0f}")
        with col4:
            st.metric("安値", f"¥{latest_data.loc['Low']:,.0f}")

        # チャート表示
        st.markdown(f"#### {ticker} - {current_date.strftime('%Y年%m月%d日')} までのチャート")

        fig = go.Figure(data=[go.Candlestick(
            x=display_data.index,
            open=display_data.loc[:, 'Open'],
            high=display_data.loc[:, 'High'],
            low=display_data.loc[:, 'Low'],
            close=display_data.loc[:, 'Close']
        )])

        # 買いを実行した日付に三角形マーカーを追加
        if st.session_state.buy_dates:
            # 現在表示している日付までの買いエントリーポイントを抽出
            buy_markers_data = display_data[
                pd.Index(display_data.index.date).isin(st.session_state.buy_dates)
            ]

            if not buy_markers_data.empty:
                fig.add_trace(go.Scatter(
                    x=buy_markers_data.index,
                    y=buy_markers_data.loc[:, 'Low'] * 0.995,  # ローソク足の少し下に表示
                    mode='markers',
                    marker=dict(
                        symbol='triangle-up',
                        size=15,
                        color='green',
                        line=dict(color='darkgreen', width=2)
                    ),
                    name='買いエントリー',
                    hovertemplate='<b>買いエントリー</b><br>日付: %{x}<br>価格: ¥%{y:,.0f}<extra></extra>'
                ))

        fig.update_layout(
            xaxis_rangeslider_visible=False,
            height=500,
            title=f"トヨタ自動車 (7203.T) - {year}年",
            xaxis_title="日付",
            yaxis_title="株価 (円)",
            showlegend=True,
            margin=dict(l=50, r=50, t=50, b=50)
        )

        st.plotly_chart(fig, use_container_width=True)

        # データテーブル（オプション）
        with st.expander("表示中のデータを確認", expanded=False):
            st.dataframe(display_data.loc[:, ['Open', 'High', 'Low', 'Close', 'Volume']].tail(10), use_container_width=True)
    else:
        st.warning("表示するデータがありません。")
else:
    st.info("データを取得中です。しばらくお待ちください...")

