"""
売買のユースケース
"""
from datetime import date
from typing import Optional, Tuple

from domain.models import Portfolio
from domain.exp import calc_profit_bonus_exp
from domain.trading import execute_buy, execute_sell, calculate_portfolio_value
from infra.db import DatabaseRepository


class TradingService:
    """売買を管理するサービス"""

    def __init__(self, db_repo: DatabaseRepository):
        self.db_repo = db_repo

    def buy_stock(
        self,
        portfolio: Portfolio,
        current_price: float,
        current_date: date
    ) -> Tuple[Portfolio, int, float, bool]:
        """
        株を購入する

        Args:
            portfolio: 現在のポートフォリオ
            current_price: 現在の株価
            current_date: 現在の日付

        Returns:
            Tuple[Portfolio, int, float, bool]: (新しいポートフォリオ, 購入株数, 購入コスト, 成功フラグ)
        """
        new_portfolio, shares, cost = execute_buy(portfolio, current_price, current_date)
        success = shares > 0
        return new_portfolio, shares, cost, success

    def sell_stock(
        self,
        portfolio: Portfolio,
        current_price: float
    ) -> Tuple[Portfolio, int, float, float, Optional[dict]]:
        """
        株を売却する

        Args:
            portfolio: 現在のポートフォリオ
            current_price: 現在の株価

        Returns:
            Tuple[Portfolio, int, float, float, Optional[dict]]:
            (新しいポートフォリオ, 売却株数, 売却代金, 利益, レベルアップ結果)
        """
        new_portfolio, sold_shares, proceeds, profit = execute_sell(portfolio, current_price)

        # 利益が出た場合のみ経験値を加算
        exp_bonus = calc_profit_bonus_exp(profit, rate=0.001)  # 0.1%

        level_up_result = None
        if exp_bonus > 0:
            level_up_result = self.db_repo.update_exp(exp_bonus)

        # prev_total_valueを更新
        new_portfolio.prev_total_value = calculate_portfolio_value(new_portfolio, current_price)

        return new_portfolio, sold_shares, proceeds, profit, level_up_result
