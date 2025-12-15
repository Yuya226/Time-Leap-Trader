"""
データベース操作（SQLite）
"""
import sqlite3
from typing import Optional, Dict
from domain.exp import check_level_up


class DatabaseRepository:
    """データベースリポジトリ（SQLite操作を抽象化）"""

    def __init__(self, db_path: str = "trading_game.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """データベースとテーブルを初期化"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # 経験値とレベルのテーブルを作成
        c.execute('''
            CREATE TABLE IF NOT EXISTS player_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level INTEGER DEFAULT 1,
                exp INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 初期データが存在しない場合は作成
        c.execute('SELECT COUNT(*) FROM player_stats')
        if c.fetchone()[0] == 0:
            c.execute('INSERT INTO player_stats (level, exp) VALUES (1, 0)')

        conn.commit()
        conn.close()

    def get_connection(self) -> sqlite3.Connection:
        """データベース接続を取得"""
        return sqlite3.connect(self.db_path)

    def get_player_stats(self) -> Dict[str, int]:
        """プレイヤーの経験値とレベルを取得"""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('SELECT level, exp FROM player_stats ORDER BY id DESC LIMIT 1')
        result = c.fetchone()
        conn.close()

        if result:
            return {'level': result[0], 'exp': result[1]}
        return {'level': 1, 'exp': 0}

    def update_exp(self, exp_to_add: int) -> Optional[Dict]:
        """
        経験値を追加し、レベルアップ判定を行う

        Args:
            exp_to_add: 追加する経験値

        Returns:
            dict: check_level_up()の戻り値、またはNone
        """
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('SELECT level, exp FROM player_stats ORDER BY id DESC LIMIT 1')
        result = c.fetchone()

        if result:
            current_level = result[0]
            current_exp = result[1]

            # 純粋関数でレベルアップ判定
            level_up_result = check_level_up(current_level, current_exp, exp_to_add)

            # データベースを更新
            self._update_exp_in_db(conn, level_up_result['level'], level_up_result['exp'])

            conn.close()
            return level_up_result
        conn.close()
        return None

    def _update_exp_in_db(self, conn: sqlite3.Connection, level: int, exp: int):
        """データベースにレベルと経験値を更新する"""
        c = conn.cursor()
        c.execute('''
            UPDATE player_stats
            SET level = ?, exp = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = (SELECT id FROM player_stats ORDER BY id DESC LIMIT 1)
        ''', (level, exp))
        conn.commit()

    def reset_player_stats(self):
        """プレイヤーステータスをリセット"""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''
            UPDATE player_stats
            SET level = 1, exp = 0, updated_at = CURRENT_TIMESTAMP
            WHERE id = (SELECT id FROM player_stats ORDER BY id DESC LIMIT 1)
        ''')
        conn.commit()
        conn.close()


# ============================================================================
# 既存の関数インターフェース（後方互換性のため）
# ============================================================================

def init_db(db_path: str = "trading_game.db") -> sqlite3.Connection:
    """
    データベースとテーブルを初期化（既存のインターフェース維持）

    Args:
        db_path: データベースファイルパス

    Returns:
        sqlite3.Connection: データベース接続
    """
    repo = DatabaseRepository(db_path)
    return repo.get_connection()


def get_player_stats(conn: sqlite3.Connection) -> Dict[str, int]:
    """
    プレイヤーの経験値とレベルを取得（既存のインターフェース維持）

    Args:
        conn: SQLite接続オブジェクト

    Returns:
        dict: {'level': int, 'exp': int}
    """
    c = conn.cursor()
    c.execute('SELECT level, exp FROM player_stats ORDER BY id DESC LIMIT 1')
    result = c.fetchone()
    if result:
        return {'level': result[0], 'exp': result[1]}
    return {'level': 1, 'exp': 0}


def update_exp_in_db(conn: sqlite3.Connection, level: int, exp: int):
    """
    データベースにレベルと経験値を更新する（既存のインターフェース維持）

    Args:
        conn: SQLite接続オブジェクト
        level: 更新するレベル
        exp: 更新する経験値
    """
    c = conn.cursor()
    c.execute('''
        UPDATE player_stats
        SET level = ?, exp = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = (SELECT id FROM player_stats ORDER BY id DESC LIMIT 1)
    ''', (level, exp))
    conn.commit()


def update_exp(conn: sqlite3.Connection, exp_to_add: int) -> Optional[Dict]:
    """
    経験値を追加し、レベルアップ判定を行う（既存のインターフェース維持）

    Args:
        conn: SQLite接続オブジェクト
        exp_to_add: 追加する経験値

    Returns:
        dict: check_level_up()の戻り値、またはNone
    """
    from domain.exp import check_level_up

    c = conn.cursor()
    c.execute('SELECT level, exp FROM player_stats ORDER BY id DESC LIMIT 1')
    result = c.fetchone()

    if result:
        current_level = result[0]
        current_exp = result[1]

        # 純粋関数でレベルアップ判定
        level_up_result = check_level_up(current_level, current_exp, exp_to_add)

        # データベースを更新
        update_exp_in_db(conn, level_up_result['level'], level_up_result['exp'])

        return level_up_result
    return None
