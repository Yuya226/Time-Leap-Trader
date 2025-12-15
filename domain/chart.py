"""
チャート生成ロジック（Plotly、Streamlit非依存）
"""
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
from typing import List, Optional


def create_candlestick_chart(
    display_data: pd.DataFrame,
    buy_dates: List[date],
    sma_25_enabled: bool = False,
    sma_75_enabled: bool = False,
    sma_25_data: Optional[pd.Series] = None,
    sma_75_data: Optional[pd.Series] = None,
    player_level: int = 1,
    current_date: date = None,
    year: int = 2024,
    ticker: str = "7203.T"
) -> go.Figure:
    """
    チャートを生成する（純粋関数、Streamlit非依存）

    Args:
        display_data: 表示するデータ（DataFrame）
        buy_dates: 買いを実行した日付のリスト
        sma_25_data: SMA25のデータ（Series）
        sma_75_data: SMA75のデータ（Series）
        player_level: プレイヤーのレベル
        current_date: 現在の日付
        year: 年
        ticker: ティッカーシンボル

    Returns:
        go.Figure: PlotlyのFigureオブジェクト
    """
    # レベルに応じてチャートタイプを切り替え
    if player_level == 1:
        # Lv.1: 折れ線グラフ
        fig = go.Figure(data=[go.Scatter(
            x=display_data.index,
            y=display_data.loc[:, 'Close'],
            mode='lines',
            name='終値',
            line=dict(color='#3399FF', width=2),
        )])
    else:
        # Lv.2以上: ローソク足チャート
        fig = go.Figure(data=[go.Candlestick(
            x=display_data.index,
            open=display_data.loc[:, 'Open'],
            high=display_data.loc[:, 'High'],
            low=display_data.loc[:, 'Low'],
            close=display_data.loc[:, 'Close']
        )])

    # 買いを実行した日付に三角形マーカーを追加
    if buy_dates:
        buy_markers_data = display_data[
            pd.Index(display_data.index.date).isin(buy_dates)
        ]

        if not buy_markers_data.empty:
            # マーカーの位置を調整
            if player_level == 1:
                marker_y = buy_markers_data.loc[:, 'Close'] * 0.995
            else:
                marker_y = buy_markers_data.loc[:, 'Low'] * 0.995

            fig.add_trace(go.Scatter(
                x=buy_markers_data.index,
                y=marker_y,
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

    # 移動平均線の追加
    if sma_25_enabled and sma_25_data is not None and player_level >= 4:
        sma_25_clean = sma_25_data.dropna()
        if len(sma_25_clean) > 0:
            fig.add_trace(go.Scatter(
                x=sma_25_clean.index,
                y=sma_25_clean.values,
                mode='lines',
                name='SMA (25)',
                line=dict(color='#FF9900', width=2),
                hovertemplate='<b>SMA (25)</b><br>日付: %{x}<br>価格: ¥%{y:,.0f}<extra></extra>'
            ))

    if sma_75_enabled and sma_75_data is not None and player_level >= 5:
        sma_75_clean = sma_75_data.dropna()
        if len(sma_75_clean) > 0:
            fig.add_trace(go.Scatter(
                x=sma_75_clean.index,
                y=sma_75_clean.values,
                mode='lines',
                name='SMA (75)',
                line=dict(color='#A55EEA', width=2),
                hovertemplate='<b>SMA (75)</b><br>日付: %{x}<br>価格: ¥%{y:,.0f}<extra></extra>'
            ))

    # X軸の範囲を設定（現在のトレード日より5日分未来まで余白を作る）
    xaxis_max = current_date + timedelta(days=5) if current_date else display_data.index[-1]

    # チャートタイトルの設定
    chart_title = f"トヨタ自動車 (7203.T) - {year}年"
    if player_level >= 3:
        chart_title += " ⚡️ Market Time Vision (土日削除中)"

    # X軸の設定
    xaxis_config = dict(
        range=[display_data.index[0], xaxis_max]
    )

    # Lv.3以上の場合、データが存在しない日付（土日・祝日）を全て削除
    if player_level >= 3:
        dt_all = pd.date_range(start=display_data.index[0], end=display_data.index[-1], freq='D')
        dt_breaks = dt_all.difference(display_data.index).strftime("%Y-%m-%d").tolist()
        if len(dt_breaks) > 0:
            xaxis_config['rangebreaks'] = [
                dict(values=dt_breaks)
            ]

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        height=500,
        title=chart_title,
        xaxis_title="日付",
        yaxis_title="株価 (円)",
        showlegend=True,
        margin=dict(l=50, r=50, t=50, b=50),
        xaxis=xaxis_config
    )

    return fig


def calculate_sma(
    data: pd.DataFrame,
    window_25: int = 25,
    window_75: int = 75
) -> tuple[pd.Series, pd.Series]:
    """
    移動平均線を計算する（純粋関数）

    Args:
        data: 株価データ（DataFrame）
        window_25: SMA25のウィンドウサイズ
        window_75: SMA75のウィンドウサイズ

    Returns:
        Tuple[pd.Series, pd.Series]: (SMA25, SMA75)
    """
    sma_25 = data['Close'].rolling(window=window_25, min_periods=window_25).mean()
    sma_75 = data['Close'].rolling(window=window_75, min_periods=window_75).mean()
    return sma_25, sma_75
