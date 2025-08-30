import sqlite3

from modules.logger import logger


def maybe_create_table(sqlite_file: str) -> bool:
    """
    Creates the tables if they don't exist.
    """
    with sqlite3.connect(sqlite_file) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                    CREATE TABLE IF NOT EXISTS leetcode_snapshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        user_slug TEXT NOT NULL,
                        easy INTEGER DEFAULT 0,
                        medium INTEGER DEFAULT 0,
                        hard INTEGER DEFAULT 0,
                        UNIQUE (user_slug, easy, medium, hard)
                    );
                """
            )
            cursor.execute(
                """
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_slug TEXT NOT NULL UNIQUE,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
                """
            )
            cursor.execute(
                """
                    CREATE TABLE IF NOT EXISTS weekly_baselines (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_slug TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        easy INTEGER DEFAULT 0,
                        medium INTEGER DEFAULT 0,
                        hard INTEGER DEFAULT 0
                    );
                """
            )
            cursor.execute(
                """
                    CREATE TRIGGER IF NOT EXISTS first_weekly_snapshot
                    AFTER INSERT ON leetcode_snapshots
                    BEGIN
                        INSERT INTO weekly_baselines (user_slug, easy, medium, hard, created_at)
                        SELECT NEW.user_slug, NEW.easy, NEW.medium, NEW.hard, NEW.created_at
                        WHERE NOT EXISTS (
                            SELECT 1
                            FROM leetcode_snapshots
                            WHERE user_slug = NEW.user_slug
                            AND strftime('%W', created_at, 'localtime') = strftime('%W', NEW.created_at, 'localtime')
                            AND created_at < NEW.created_at
                            AND CAST(strftime('%w', created_at, 'localtime') AS INTEGER) >= 0
                        );
                    END;
                """
            )
            cursor.execute(
                """
                    CREATE INDEX IF NOT EXISTS idx_user_created_at 
                    ON leetcode_snapshots(user_slug, created_at);
                """
            )
            return True
        except Exception:
            logger.exception("Unable to create sqlite tables")
            return False


def get_users_as_leaderboard(
    sqlite_file: str, start_date: str, end_date: str
) -> list[dict]:
    """
    Returns the difference in easy/medium/hard between start_date and now
    for each user in the users table.
    """
    query = """
    WITH latest_weekly_snapshot_per_user AS (
        SELECT user_slug,
               easy AS easy_start,
               medium AS medium_start,
               hard AS hard_start
        FROM weekly_baselines wb
        WHERE created_at = (
            SELECT MAX(created_at)
            FROM weekly_baselines wb2
            WHERE wb2.user_slug = wb.user_slug
            AND created_at <= :end_date
        )
    ),
    end_snap AS (
        SELECT user_slug,
               easy AS easy,
               medium AS medium,
               hard AS hard
        FROM leetcode_snapshots s1
        WHERE created_at = (
            SELECT MAX(created_at)
            FROM leetcode_snapshots s2
            WHERE s2.user_slug = s1.user_slug
            AND created_at <= :end_date
        )
    )
    SELECT u.user_slug,
           COALESCE(e.easy, 0) - COALESCE(s.easy_start, 0) AS easy_diff,
           COALESCE(e.medium, 0) - COALESCE(s.medium_start, 0) AS medium_diff,
           COALESCE(e.hard, 0) - COALESCE(s.hard_start, 0) AS hard_diff
    FROM users u
    LEFT JOIN latest_weekly_snapshot_per_user s ON u.user_slug = s.user_slug
    LEFT JOIN end_snap e ON u.user_slug = e.user_slug;
    """

    with sqlite3.connect(sqlite_file) as conn:
        conn.row_factory = sqlite3.Row  # allows dict-like access
        cursor = conn.cursor()
        cursor.execute(query, {"start_date": start_date, "end_date": end_date})
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append(
                {
                    "user": row["user_slug"],
                    "easy": row["easy_diff"],
                    "medium": row["medium_diff"],
                    "hard": row["hard_diff"],
                }
            )
        return result


def store_snapshot(
    sqlite_file: str, username: str, easy: int = 0, medium: int = 0, hard: int = 0
) -> None:
    """
    Store a LeetCode snapshot in the database.
    """
    try:
        with sqlite3.connect(sqlite_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                    INSERT INTO leetcode_snapshots (user_slug, easy, medium, hard)
                    VALUES (?, ?, ?, ?)
                """,
                (username, easy, medium, hard),
            )
    except sqlite3.IntegrityError:
        return
    except Exception:
        logger.exception(f"Unable to store snapshot for user {username}")
        return


def add_user(sqlite_file: str, username: str, first_name: str, last_name: str) -> None:
    """
    Add a new user to the database.
    """
    try:
        with sqlite3.connect(sqlite_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                    INSERT INTO users (user_slug, first_name, last_name)
                    VALUES (?, ?, ?)
                """,
                (username, first_name, last_name),
            )
    except sqlite3.IntegrityError:
        return
    except Exception:
        logger.info(f"Unable to save {username} in users table")
        return


def delete_user(sqlite_file: str, username: str) -> None:
    """
    Delete a user from the database.
    """
    with sqlite3.connect(sqlite_file) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
                DELETE FROM users
                WHERE user_slug = ?
            """,
            (username,),
        )


def get_all_users(sqlite_file: str):
    """
    Get all users from the database.
    """
    with sqlite3.connect(sqlite_file) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
                SELECT user_slug, first_name, last_name
                FROM users
            """
        )
        rows = cursor.fetchall()
        return [
            {
                "username": row[0],
                "firstName": row[1],
                "lastName": row[2],
            }
            for row in rows
        ]

def check_if_user_exists(sqlite_file: str, username: str):
    """
    Check if a user exists in the database.
    """
    with sqlite3.connect(sqlite_file) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
                SELECT COUNT(1) FROM users
                WHERE user_slug = ?
            """,
            (username,),
        )
        count = cursor.fetchone()[0]
        return count > 0


def clear_tables(sqlite_file: str):
    """
    Clear all tables in the database.
    """
    with sqlite3.connect(sqlite_file) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
                DELETE FROM leetcode_snapshots
            """,
        )
        cursor.execute(
            """
                DELETE FROM users
            """,
        )


def get_all_leetcode_snapshots(sqlite_file: str):
    """
    Get all LeetCode snapshots from the database.
    """
    with sqlite3.connect(sqlite_file) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
                SELECT user_slug, easy, medium, hard, created_at
                FROM leetcode_snapshots
                ORDER BY created_at DESC
            """
        )
        rows = cursor.fetchall()
        return [
            {
                "user": row[0],
                "easy": row[1],
                "medium": row[2],
                "hard": row[3],
                "created_at": row[4],
            }
            for row in rows
        ]


def get_all_weekly_baselines(sqlite_file: str):
    """
    Get all weekly baselines from the database.
    """
    with sqlite3.connect(sqlite_file) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
                SELECT user_slug, easy, medium, hard, created_at
                FROM weekly_baselines
                ORDER BY created_at DESC
            """
        )
        rows = cursor.fetchall()
        return [
            {
                "user": row[0],
                "easy": row[1],
                "medium": row[2],
                "hard": row[3],
                "created_at": row[4],
            }
            for row in rows
        ]
