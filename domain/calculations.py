"""
純粋な計算ロジック（副作用なし）
"""
import pandas as pd
from typing import Tuple, Optional


def calculate_price_change(display_data: pd.DataFrame) -> Tuple[float, float]:
    """
    前日比を計算する（純粋関数）

    Args:
        display_data: 表示データ（DataFrame）

    Returns:
        Tuple[float, float]: (変化額, 変化率%)
    """
    if len(display_data) <= 1:
        return 0.0, 0.0

    current_price = display_data.loc[display_data.index[-1], 'Close']
    prev_price = display_data.loc[display_data.index[-2], 'Close']
    change = current_price - prev_price
    change_pct = (change / prev_price) * 100

    return change, change_pct


def prepare_display_data(
    data: pd.DataFrame,
    current_date,
    start_date,
    context_days: int = 60
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    表示用データとSMA計算用データを準備する（純粋関数）

    Args:
        data: 全データ（DataFrame）
        current_date: 現在の日付
        start_date: 開始日
        context_days: コンテキスト表示日数（デフォルト: 60日）

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: (表示用データ, SMA計算用データ)
    """
    from datetime import timedelta

    context_start_date = start_date - timedelta(days=context_days)
    display_data = data[
        (data.index.date >= context_start_date) &
        (data.index.date <= current_date)
    ]
    sma_calc_data = data[data.index.date <= current_date]

    return display_data, sma_calc_data


def calculate_sma_for_display(
    sma_calc_data: pd.DataFrame,
    display_data: pd.DataFrame
) -> Tuple[pd.Series, pd.Series]:
    """
    SMAを計算し、表示期間に合わせてフィルタリングする（純粋関数）

    Args:
        sma_calc_data: SMA計算用データ（全期間）
        display_data: 表示用データ

    Returns:
        Tuple[pd.Series, pd.Series]: (SMA25, SMA75) - 表示期間にフィルタリング済み
    """
    sma_25_full = sma_calc_data['Close'].rolling(window=25, min_periods=25).mean()
    sma_75_full = sma_calc_data['Close'].rolling(window=75, min_periods=75).mean()

    sma_25 = sma_25_full[sma_25_full.index.isin(display_data.index)]
    sma_75 = sma_75_full[sma_75_full.index.isin(display_data.index)]

    return sma_25, sma_75
