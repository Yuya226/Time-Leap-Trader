"""
売買ロジック（純粋関数）
"""
from typing import Tuple
from datetime import date
from .models import Portfolio


def calculate_portfolio_value(portfolio: Portfolio, current_price: float) -> float:
    """
    ポートフォリオの総資産を計算する（純粋関数）

    Args:
        portfolio: ポートフォリオ
        current_price: 現在の株価

    Returns:
        float: 総資産（現金 + 保有株の評価額）
    """
    return portfolio.cash + (portfolio.shares * current_price)


def execute_buy(portfolio: Portfolio, current_price: float, current_date: date) -> Tuple[Portfolio, int, float, bool]:
    """
    買い注文を実行する（純粋関数）

    Args:
        portfolio: 現在のポートフォリオ
        current_price: 現在の株価
        current_date: 現在の日付

    Returns:
        Tuple[Portfolio, int, float, bool]: (新しいポートフォリオ, 購入株数, 購入コスト, 成功フラグ)
    """
    # 可能な限り購入（1株単位）
    max_shares = int(portfolio.cash / current_price)

    if max_shares <= 0:
        return portfolio, 0, 0.0, False

    cost = max_shares * current_price
    new_cash = portfolio.cash - cost
    new_shares = portfolio.shares + max_shares
    new_buy_dates = portfolio.buy_dates.copy()

    # 買いを実行した日付を記録
    if current_date not in new_buy_dates:
        new_buy_dates.append(current_date)

    new_portfolio = Portfolio(
        cash=new_cash,
        shares=new_shares,
        buy_dates=new_buy_dates,
        prev_total_value=portfolio.prev_total_value
    )

    return new_portfolio, max_shares, cost, True


def execute_sell(portfolio: Portfolio, current_price: float) -> Tuple[Portfolio, int, float, float]:
    """
    売り注文を実行する（純粋関数）

    Args:
        portfolio: 現在のポートフォリオ
        current_price: 現在の株価

    Returns:
        Tuple[Portfolio, int, float, float]: (新しいポートフォリオ, 売却株数, 売却代金, 利益)
    """
    if portfolio.shares <= 0:
        return portfolio, 0, 0.0, 0.0

    proceeds = portfolio.shares * current_price
    sold_shares = portfolio.shares

    # 総資産の変化を計算（利益計算用）
    total_value_before = portfolio.cash + (portfolio.shares * current_price)

    new_cash = portfolio.cash + proceeds
    new_portfolio = Portfolio(
        cash=new_cash,
        shares=0,
        buy_dates=portfolio.buy_dates.copy(),
        prev_total_value=portfolio.prev_total_value
    )

    total_value_after = new_cash
    profit = total_value_after - portfolio.prev_total_value

    return new_portfolio, sold_shares, proceeds, profit
