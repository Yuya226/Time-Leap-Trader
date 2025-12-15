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
    display_business_days: int = 60
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    表示用データとSMA計算用データを準備する（純粋関数）
    スライディングウィンドウ方式で、最新から指定営業日数分のデータを表示する

    Args:
        data: 全データ（DataFrame）
        current_date: 現在のトレード日
        start_date: ゲームの開始日（参考用、未使用）
        display_business_days: 表示したい営業日数（デフォルト: 60日）
                             最新から数えてこの日数分のデータを表示

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: (表示用データ, SMA計算用データ)
    """
    # ステップ1: 現在のトレード日までのデータ全体を取得
    available_data = data[data.index.date <= current_date]

    if len(available_data) == 0:
        return pd.DataFrame(), pd.DataFrame()

    # ステップ2: 最新から数えて display_business_days 分のデータを切り出す
    if len(available_data) <= display_business_days:
        # データが指定日数より少ない場合は全て表示
        display_data = available_data
    else:
        # 最新から display_business_days 分だけを取得（スライディングウィンドウ）
        # インデックスは時系列順なので、最後の display_business_days 行を取得
        display_data = available_data.iloc[-display_business_days:]

    # ステップ3: SMA計算用データ（現在の日付までの全データ）
    # SMA計算には過去のデータも必要なので、全期間のデータを返す
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


