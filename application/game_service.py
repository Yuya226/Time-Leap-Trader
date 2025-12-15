"""
ゲーム進行のユースケース
"""
from datetime import date, timedelta
from typing import Optional, Tuple
import pandas as pd

from domain.models import GameState, Portfolio, PlayerState
from domain.exp import calc_exp_gain, check_level_up
from domain.trading import calculate_portfolio_value
from infra.db import DatabaseRepository


class GameService:
    """ゲーム進行を管理するサービス"""

    def __init__(self, db_repo: DatabaseRepository):
        self.db_repo = db_repo

    def advance_date(
        self,
        game_state: GameState,
        portfolio: Portfolio,
        days: int = 1
    ) -> Tuple[GameState, Portfolio, Optional[dict]]:
        """
        日付を進める

        Args:
            game_state: 現在のゲーム状態
            portfolio: 現在のポートフォリオ
            days: 進める日数（営業日）

        Returns:
            Tuple[GameState, Portfolio, Optional[dict]]: (新しいゲーム状態, 新しいポートフォリオ, レベルアップ結果)
        """
        if game_state.stock_data is None or game_state.current_date is None:
            return game_state, portfolio, None

        # 現在の日付より後のデータを取得
        future_data = game_state.stock_data[
            game_state.stock_data.index.date > game_state.current_date
        ]

        if future_data.empty:
            return game_state, portfolio, None

        # 営業日を指定日数分進める
        available_dates = list(future_data.index.date)
        if len(available_dates) >= days:
            new_date = available_dates[days - 1]
        else:
            new_date = game_state.end_date

        # 新しい日付での総資産を計算
        new_display_data = game_state.stock_data[
            game_state.stock_data.index.date <= new_date
        ]
        new_current_price = new_display_data.loc[new_display_data.index[-1], 'Close'] if not new_display_data.empty else 0
        new_total_value = calculate_portfolio_value(portfolio, new_current_price)

        # 経験値を計算・加算
        exp_to_add = calc_exp_gain(
            portfolio.prev_total_value,
            new_total_value,
            rate=0.0001  # 0.01%
        )

        level_up_result = None
        if exp_to_add > 0:
            level_up_result = self.db_repo.update_exp(exp_to_add)

        # 状態を更新
        new_game_state = GameState(
            current_date=new_date,
            start_date=game_state.start_date,
            end_date=game_state.end_date,
            stock_data=game_state.stock_data
        )

        new_portfolio = Portfolio(
            cash=portfolio.cash,
            shares=portfolio.shares,
            buy_dates=portfolio.buy_dates.copy(),
            prev_total_value=new_total_value
        )

        return new_game_state, new_portfolio, level_up_result

    def reset_game(
        self,
        game_state: GameState
    ) -> Tuple[GameState, Portfolio, PlayerState]:
        """
        ゲームをリセットする

        Args:
            game_state: 現在のゲーム状態

        Returns:
            Tuple[GameState, Portfolio, PlayerState]: リセット後の状態
        """
        new_game_state = GameState(
            current_date=game_state.start_date,
            start_date=game_state.start_date,
            end_date=game_state.end_date,
            stock_data=game_state.stock_data
        )

        new_portfolio = Portfolio(
            cash=1000000,
            shares=0,
            buy_dates=[],
            prev_total_value=1000000
        )

        new_player_state = PlayerState(
            initial_capital=1000000
        )

        # データベースもリセット
        self.db_repo.reset_player_stats()

        return new_game_state, new_portfolio, new_player_state
