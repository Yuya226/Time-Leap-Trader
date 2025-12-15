"""
レベルアップ時のUI処理（Streamlit依存）
"""
import streamlit as st
from typing import Dict, Optional


def handle_level_up_ui(result: Optional[Dict]) -> None:
    """
    レベルアップ時のUI処理を実行する（Streamlit依存）

    Args:
        result: check_level_up()またはupdate_exp()の戻り値（level_up, level, old_levelを含む）

    Returns:
        None（副作用としてst.session_stateを更新）
    """
    if not result or not result.get('level_up'):
        return

    # レベルアップ通知フラグをセット
    if "ui_state" in st.session_state:
        st.session_state.ui_state["needs_levelup_toast"] = True
    else:
        st.session_state.needs_levelup_toast = True

    new_level = result['level']
    old_level = result['old_level']

    # レベルごとの処理をdictで管理
    level_handlers = {
        2: {
            'toast_message': "🎊 レベルアップしてローソク足が解放されました！",
            'condition': lambda: not st.session_state.get("level_up_toast_shown", False),
            'action': lambda: setattr(st.session_state, 'level_up_toast_shown', True)
        },
        3: {
            'toast_message': "⏰ 時空圧縮スキル発動！チャートの土日が削除されました",
            'condition': lambda: True,
            'action': lambda: None
        },
        4: {
            'toast_message': f"🎉 レベルアップ！ レベル {old_level} → レベル {new_level}",
            'condition': lambda: True,
            'action': lambda: setattr(st.session_state, 'sma_25_enabled', True)
        },
        5: {
            'toast_message': f"🎉 レベルアップ！ レベル {old_level} → レベル {new_level}",
            'condition': lambda: True,
            'action': lambda: setattr(st.session_state, 'sma_75_enabled', True)
        }
    }

    # 現在のレベルに対応する処理を実行
    if new_level in level_handlers:
        handler = level_handlers[new_level]
        # 条件をチェック
        if handler['condition']():
            # アクションを実行
            handler['action']()
            # トーストメッセージを設定
            if "ui_state" in st.session_state:
                st.session_state.ui_state["levelup_toast_message"] = handler['toast_message']
            else:
                st.session_state.levelup_toast_message = handler['toast_message']
    else:
        # デフォルトのメッセージ
        default_message = f"🎉 レベルアップ！ レベル {old_level} → レベル {new_level}"
        if "ui_state" in st.session_state:
            st.session_state.ui_state["levelup_toast_message"] = default_message
        else:
            st.session_state.levelup_toast_message = default_message
