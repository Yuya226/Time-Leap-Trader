"""
チャート表示UI（Streamlit依存）
"""
import streamlit as st
import pandas as pd
from datetime import date
from typing import List, Optional
from domain.chart import create_candlestick_chart
from domain.calculations import calculate_sma_for_display


def render_chart(
    display_data: pd.DataFrame,
    buy_dates: List[date],
    sma_25_enabled: bool,
    sma_75_enabled: bool,
    sma_calc_data: pd.DataFrame,
    player_level: int,
    current_date: date,
    year: int,
    ticker: str
):
    """
    チャートを描画

    Args:
        display_data: 表示データ
        buy_dates: 買いを実行した日付のリスト
        sma_25_enabled: SMA25が有効かどうか
        sma_75_enabled: SMA75が有効かどうか
        sma_calc_data: SMA計算用データ
        player_level: プレイヤーのレベル
        current_date: 現在の日付
        year: 年
        ticker: ティッカーシンボル
    """
    st.markdown(f"#### {ticker} - {current_date.strftime('%Y年%m月%d日')} までのチャート")

    # SMA計算
    sma_25, sma_75 = calculate_sma_for_display(sma_calc_data, display_data)

    # チャート生成
    fig = create_candlestick_chart(
        display_data=display_data,
        buy_dates=buy_dates,
        sma_25_enabled=sma_25_enabled,
        sma_75_enabled=sma_75_enabled,
        sma_25_data=sma_25 if sma_25_enabled else None,
        sma_75_data=sma_75 if sma_75_enabled else None,
        player_level=player_level,
        current_date=current_date,
        year=year,
        ticker=ticker
    )

    st.plotly_chart(fig, use_container_width=True)

    # データテーブル（オプション）
    with st.expander("表示中のデータを確認", expanded=False):
        st.dataframe(display_data.loc[:, ['Open', 'High', 'Low', 'Close', 'Volume']].tail(10), use_container_width=True)
