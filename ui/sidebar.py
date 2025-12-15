"""
サイドバーUI描画（Streamlit依存）
"""
import streamlit as st
from datetime import date, timedelta
from typing import Dict, Optional
import pandas as pd


def render_control_sidebar(
    current_date: date,
    start_date: date,
    end_date: date,
    display_data: pd.DataFrame,
    data: pd.DataFrame
) -> Optional[str]:
    """
    コントロールサイドバーを描画

    Args:
        current_date: 現在の日付
        start_date: 開始日
        end_date: 終了日
        display_data: 表示データ
        data: 全データ

    Returns:
        Optional[str]: 押されたボタンの種類（"prev", "reset", "next", None）
    """
    st.sidebar.title("コントロール")
    st.sidebar.caption("ボタンを押すたびに、日足データが1日ずつ進んでいきます。")

    col1, col2, col3 = st.sidebar.columns(3)

    with col1:
        if st.button("◀ 前の日", disabled=(current_date <= start_date)):
            return "prev"

    with col2:
        if st.button("リセット"):
            return "reset"

    with col3:
        if st.button("次の日 ▶", disabled=(current_date >= end_date)):
            return "next"

    return None


def render_date_info_sidebar(
    current_date: date,
    start_date: date,
    end_date: date,
    display_data: pd.DataFrame
):
    """日付情報をサイドバーに表示"""
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**現在の日付:** {current_date.strftime('%Y年%m月%d日')}")
    st.sidebar.markdown(f"**表示日数:** {len(display_data)}日")
    st.sidebar.markdown(f"**開始日:** {start_date.strftime('%Y年%m月%d日')}")
    st.sidebar.markdown(f"**終了日:** {end_date.strftime('%Y年%m月%d日')}")

    # 進捗バー
    progress = (current_date - start_date).days / (end_date - start_date).days
    st.sidebar.progress(progress)


def render_trading_sidebar(
    current_price: float,
    current_date: date,
    shares: int
) -> Optional[str]:
    """
    取引サイドバーを描画

    Args:
        current_price: 現在の株価
        current_date: 現在の日付
        shares: 保有株数

    Returns:
        Optional[str]: 押されたボタンの種類（"buy", "sell", None）
    """
    st.sidebar.markdown("---")
    st.sidebar.title("取引")

    col_buy, col_sell = st.sidebar.columns(2)

    with col_buy:
        if st.button("買い", type="primary", use_container_width=True):
            return "buy"

    with col_sell:
        if st.button("売り", type="secondary", use_container_width=True, disabled=(shares == 0)):
            return "sell"

    return None


def render_equipment_sidebar(player_level: int, sma_25_enabled: bool, sma_75_enabled: bool) -> Dict[str, bool]:
    """
    装備設定サイドバーを描画

    Args:
        player_level: プレイヤーのレベル
        sma_25_enabled: SMA25の現在の状態
        sma_75_enabled: SMA75の現在の状態

    Returns:
        dict: {'sma_25_enabled': bool, 'sma_75_enabled': bool}
    """
    st.sidebar.markdown("---")
    with st.sidebar.expander("🛠 装備（インジケーター）", expanded=True):
        new_sma_25_enabled = sma_25_enabled
        new_sma_75_enabled = sma_75_enabled

        # 移動平均線 (25日) のチェックボックス
        if player_level < 4:
            st.checkbox("🔒 移動平均線 (25日) - Lv.4で解放", value=False, disabled=True)
        else:
            new_sma_25_enabled = st.checkbox("📈 移動平均線 (25日)", value=sma_25_enabled)

        # 移動平均線 (75日) のチェックボックス
        if player_level < 5:
            st.checkbox("🔒 移動平均線 (75日) - Lv.5で解放", value=False, disabled=True)
        else:
            new_sma_75_enabled = st.checkbox("📈 移動平均線 (75日)", value=sma_75_enabled)

    return {
        'sma_25_enabled': new_sma_25_enabled,
        'sma_75_enabled': new_sma_75_enabled
    }


def render_skip_buttons_sidebar(current_date: date, end_date: date) -> Optional[int]:
    """
    スキップボタンをサイドバーに描画

    Args:
        current_date: 現在の日付
        end_date: 終了日

    Returns:
        Optional[int]: 進める日数（7 or 30）、またはNone
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown("**時間操作**")
    skip_col1, skip_col2 = st.sidebar.columns(2)

    with skip_col1:
        if st.button("1週間 (+7日)", disabled=(current_date >= end_date), use_container_width=True):
            return 7

    with skip_col2:
        if st.button("1ヶ月 (+30日)", disabled=(current_date >= end_date), use_container_width=True):
            return 30

    return None


def render_debug_sidebar() -> bool:
    """
    デバッグボタンをサイドバーに描画

    Returns:
        bool: 強制レベルアップボタンが押されたかどうか
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown("**🔧 デバッグ**")
    if st.sidebar.button("強制レベルアップ (+100EXP)", use_container_width=True):
        return True
    return False
