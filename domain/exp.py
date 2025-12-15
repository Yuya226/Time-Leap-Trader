"""
経験値・レベルアップ計算ロジック（純粋関数）
"""
from typing import Dict


def calc_exp_gain(before_value: float, after_value: float, rate: float = 0.0001) -> int:
    """
    総資産の変化から経験値を計算する（純粋関数）

    Args:
        before_value: 変化前の総資産
        after_value: 変化後の総資産
        rate: 経験値計算レート（デフォルト: 0.0001 = 0.01%）

    Returns:
        int: 獲得経験値（増加がない場合は0）
    """
    if after_value <= before_value:
        return 0
    increase_amount = after_value - before_value
    return int(increase_amount * rate)


def calc_profit_bonus_exp(profit: float, rate: float = 0.001) -> int:
    """
    利確ボーナス経験値を計算する（純粋関数）

    Args:
        profit: 利益額
        rate: 経験値計算レート（デフォルト: 0.001 = 0.1%）

    Returns:
        int: 獲得経験値（利益がない場合は0）
    """
    if profit <= 0:
        return 0
    return int(profit * rate)


def check_level_up(level: int, exp: int, exp_to_add: int) -> Dict:
    """
    レベルアップ判定を行う（純粋関数、SQLiteに依存しない）

    Args:
        level: 現在のレベル
        exp: 現在の経験値
        exp_to_add: 追加する経験値

    Returns:
        dict: {
            'level': 新しいレベル,
            'exp': 新しい経験値（レベルアップ後の残り）,
            'level_up': レベルアップしたかどうか,
            'old_level': 元のレベル
        }
    """
    new_exp = exp + exp_to_add
    current_level = level

    # レベルアップ判定（線形: レベル * 50で序盤を早く）
    required_exp = current_level * 50
    new_level = current_level

    level_up = False
    while new_exp >= required_exp:
        new_exp -= required_exp
        new_level += 1
        required_exp = new_level * 50
        level_up = True

    return {
        'level': new_level,
        'exp': new_exp,
        'level_up': level_up,
        'old_level': current_level
    }
