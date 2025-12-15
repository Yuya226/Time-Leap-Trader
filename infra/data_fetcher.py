"""
外部データ取得（yfinance）
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Tuple, Optional


class StockDataFetcher:
    """株価データ取得クラス"""

    @staticmethod
    def fetch_data(
        ticker: str,
        year: int,
        days_before_start: int = 220
    ) -> Tuple[Optional[pd.DataFrame], Optional[datetime.date], Optional[datetime.date]]:
        """
        株価データを取得する

        Args:
            ticker: ティッカーシンボル（例: "7203.T"）
            year: 取得する年
            days_before_start: 開始日の何日前から取得するか（デフォルト: 220日 = 150営業日）

        Returns:
            Tuple[DataFrame, start_date, end_date]: (データ, 開始日, 終了日)
        """
        try:
            # 開始日の指定日数前からデータを取得
            game_start = datetime(year, 1, 1)
            data_start = game_start - timedelta(days=days_before_start)
            end = datetime(year, 12, 31)

            data = yf.download(ticker, start=data_start, end=end)

            # MultiIndexの場合は最初の銘柄を取得
            if isinstance(data.columns, pd.MultiIndex):
                data = data.xs(ticker, axis=1, level=1)

            if data.empty:
                return None, None, None

            # ゲームの開始日を決定
            game_start_date = game_start.date()
            available_dates = pd.Index(data.index.date)

            if game_start_date in available_dates:
                start_date = game_start_date
            else:
                # 開始日が営業日でない場合、最も近い営業日を探す
                future_dates = available_dates[available_dates >= game_start_date]
                if len(future_dates) > 0:
                    start_date = future_dates[0]
                else:
                    start_date = available_dates[0]

            end_date = data.index[-1].date()

            return data, start_date, end_date

        except Exception as e:
            print(f"データ取得エラー: {e}")
            return None, None, None
