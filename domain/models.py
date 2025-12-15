"""
ドメインモデル: ゲームの状態を表すクラス
"""
from dataclasses import dataclass
from datetime import date
from typing import List, Optional
import pandas as pd


@dataclass
class GameState:
    """ゲーム進行に関する状態"""
    current_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    stock_data: Optional[pd.DataFrame] = None

    def to_dict(self) -> dict:
        """辞書形式に変換（session_state保存用）"""
        return {
            "current_date": self.current_date,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "stock_data": self.stock_data
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'GameState':
        """辞書から復元"""
        return cls(
            current_date=data.get("current_date"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            stock_data=data.get("stock_data")
        )


@dataclass
class Portfolio:
    """ポートフォリオに関する状態"""
    cash: int = 1000000  # 初期資金100万円
    shares: int = 0  # 初期保有株数0
    buy_dates: List[date] = None  # 買いを実行した日付のリスト
    prev_total_value: int = 1000000  # 前日の総資産（経験値計算用）

    def __post_init__(self):
        if self.buy_dates is None:
            self.buy_dates = []

    def to_dict(self) -> dict:
        """辞書形式に変換（session_state保存用）"""
        return {
            "cash": self.cash,
            "shares": self.shares,
            "buy_dates": [d.isoformat() if isinstance(d, date) else d for d in self.buy_dates],
            "prev_total_value": self.prev_total_value
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Portfolio':
        """辞書から復元"""
        buy_dates = data.get("buy_dates", [])
        # 文字列の場合はdateに変換
        if buy_dates and isinstance(buy_dates[0], str):
            from datetime import datetime
            buy_dates = [datetime.fromisoformat(d).date() if isinstance(d, str) else d for d in buy_dates]
        return cls(
            cash=data.get("cash", 1000000),
            shares=data.get("shares", 0),
            buy_dates=buy_dates,
            prev_total_value=data.get("prev_total_value", 1000000)
        )


@dataclass
class PlayerState:
    """プレイヤーに関する状態"""
    initial_capital: int = 1000000  # 初期資産（評価損益計算用）

    def to_dict(self) -> dict:
        """辞書形式に変換（session_state保存用）"""
        return {
            "initial_capital": self.initial_capital
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PlayerState':
        """辞書から復元"""
        return cls(
            initial_capital=data.get("initial_capital", 1000000)
        )
