"""
HUD（ヘッドアップディスプレイ）UI描画（Streamlit依存）
"""
import streamlit as st
from datetime import date
from typing import Dict


def render_hud(
    player_stats: Dict[str, int],
    total_value: float,
    cash: float,
    shares: int,
    profit_loss: float,
    profit_loss_pct: float,
    current_date: date,
    display_data_count: int,
    total_data_count: int
):
    """
    HUD（プレイヤーステータス・資産情報）を描画

    Args:
        player_stats: プレイヤーステータス {'level': int, 'exp': int}
        total_value: 総資産
        cash: 現金
        shares: 保有株数
        profit_loss: 評価損益
        profit_loss_pct: 評価損益率
        current_date: 現在の日付
        display_data_count: 表示データ数
        total_data_count: 全データ数
    """
    required_exp = player_stats['level'] * 50
    exp_progress = (player_stats['exp'] / required_exp) * 100 if required_exp > 0 else 0

    hud_col1, hud_col2, hud_col3, hud_col4 = st.columns(4)

    with hud_col1:
        level_col, exp_col = st.columns(2)
        with level_col:
            st.metric("🎮 レベル", f"Lv.{player_stats['level']}")
        with exp_col:
            remaining_exp = required_exp - player_stats['exp']
            progress_text = f"進捗: {exp_progress:.1f}%" if remaining_exp > 0 else "MAX"
            st.metric("経験値", f"{player_stats['exp']} / {required_exp}", delta=progress_text)
        st.progress(exp_progress / 100)

    with hud_col2:
        st.metric("💰 総資産", f"¥{total_value:,.0f}")
        st.caption(f"現金: ¥{cash:,.0f}")
        if shares > 0:
            st.caption(f"保有株: {shares:,}株")

    with hud_col3:
        profit_sign = "+" if profit_loss >= 0 else ""
        st.metric(
            "📊 評価損益",
            f"¥{profit_loss:+,.0f}",
            delta=f"{profit_sign}{profit_loss_pct:.2f}%"
        )

    with hud_col4:
        st.metric("📅 現在の日付", current_date.strftime('%Y年%m月%d日'))
        st.caption(f"進捗: {display_data_count}日 / {total_data_count}日")


def render_metrics(
    current_price: float,
    change: float,
    change_pct: float,
    high: float,
    low: float
):
    """
    メトリクス（終値・前日比・高値・安値）を描画

    Args:
        current_price: 現在の終値
        change: 前日比（金額）
        change_pct: 前日比（%）
        high: 高値
        low: 安値
    """
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("終値", f"¥{current_price:,.0f}")
    with col2:
        st.metric("前日比", f"¥{change:+,.0f}", f"{change_pct:+.2f}%")
    with col3:
        st.metric("高値", f"¥{high:,.0f}")
    with col4:
        st.metric("安値", f"¥{low:,.0f}")

