import sqlite3
from tabulate import tabulate
import httpx
import time
from constants import LEETCODE_CLIENT_URL

def create_table(db_file, table_name="users"):
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()

        query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            username TEXT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            total_solved INTEGER,
            points INTEGER,
            easy_solved INTEGER DEFAULT 0,
            medium_solved INTEGER DEFAULT 0,
            hard_solved INTEGER DEFAULT 0
        );
        """
        cursor.execute(query)
        print(f"{table_name} table is ready")

def add_user(db_file, username, first_name, last_name, total_solved=0, points=0, easy_solved=0, medium_solved=0, hard_solved=0, 
             baseline_easy=0, baseline_medium=0, baseline_hard=0, table_name="users"):
    
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()

        if table_name == "users":
            query = f"""
            INSERT INTO {table_name} (username, first_name, last_name, total_solved, points, easy_solved, medium_solved, hard_solved)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (username, first_name, last_name, total_solved, points, easy_solved, medium_solved, hard_solved))
        elif table_name == "weekly_stats":
            query = f"""
            INSERT INTO {table_name} (username, first_name, last_name, total_solved, points, easy_solved, medium_solved, hard_solved, baseline_easy, baseline_medium, baseline_hard)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (username, first_name, last_name, total_solved, points, easy_solved, medium_solved, hard_solved, baseline_easy, baseline_medium, baseline_hard))
        else:
            print(f"Invalid table name: {table_name}")

def update_user(db_file, old_username, new_username, new_first_name, new_last_name, table_name="users"):
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        query = f"""
            UPDATE {table_name}
            SET
                username = ?,
                first_name = ?,
                last_name = ?
            WHERE username = ?
        """
        cursor.execute(query, (new_username, new_first_name, new_last_name, old_username))

def get_all_users(db_file, table_name="users"):
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        query = f"SELECT * FROM {table_name}"
        cursor.execute(query)
        output = cursor.fetchall()
        if output:
            print(f"Displaying all registered users for {table_name}")
            return output
        print("No users found in the database.")
        return None

def get_top_users(db_file, table_name="users"):
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        assert table_name in ["users", "weekly_stats"], f"Invalid table: {table_name}"
        
        query = f"""
            SELECT username, first_name, last_name, total_solved, points, easy_solved, medium_solved, hard_solved
            FROM {table_name}
            ORDER BY points DESC
        """
        cursor.execute(query)
        users = cursor.fetchall()

        if not users:
            print("No users found in the database.")
            return []

        # Create a list of dictionaries for the result
        result = [
            {
                "username": user[0],
                "first_name": user[1],    
                "last_name": user[2],     
                "total_solved": user[3],  
                "points": user[4],        
                "easy_solved": user[5],   
                "medium_solved": user[6], 
                "hard_solved": user[7]
            }
            for user in users
        ]
        return result

def check_if_user_exists(db_file, username, table_name="users"):
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        query = f"SELECT COUNT(1) FROM {table_name} WHERE username=? LIMIT 1"
        cursor.execute(query, (username,))
        existing_user = cursor.fetchone()
        return bool(existing_user and existing_user[0] == 1)

def get_first_place(db_file, table_name="users"):
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        query = f"SELECT * FROM {table_name} ORDER BY points DESC LIMIT 1"
        cursor.execute(query)
        column_names = [description[0] for description in cursor.description]
        data = cursor.fetchall()

        print("Showing the top user")
        if data:
            print(tabulate(data, headers=column_names, tablefmt="grid"))
        else:
            print("No users added")
        
        return data

def delete_user(db_file, username, table_name="users"):
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        query = f"DELETE FROM {table_name} WHERE username=?"
        cursor.execute(query, (username,))
        print(f"{username} has been deleted")

async def fetch_user_stats(username):
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(f"{LEETCODE_CLIENT_URL}/{username}")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch stats for user {username}: {response.text}")
            return None

async def update_all_users_stats(db_file, table_name="users"):
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        query = f"SELECT username FROM {table_name}"
        cursor.execute(query)
        users = cursor.fetchall()
        for user in users:
            username = user[0]
            updated_stats = await fetch_user_stats(username)

            if updated_stats:
                total_solved = updated_stats.get("EASY", 0) + updated_stats.get("MEDIUM", 0) + updated_stats.get("HARD", 0)
                points = (updated_stats.get("EASY", 0) * 1) + (updated_stats.get("MEDIUM", 0) * 3) + (updated_stats.get("HARD", 0) * 5)
                easy_solved = updated_stats.get("EASY", 0)
                medium_solved = updated_stats.get("MEDIUM", 0)
                hard_solved = updated_stats.get("HARD", 0)

                update_user(db_file, username, total_solved, points, easy_solved, medium_solved, hard_solved)
                time.sleep(5)

def reset_all_users(db_file, table_name="users"):
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        query = f"""
            UPDATE {table_name}
            SET easy_solved = 0, medium_solved = 0, hard_solved = 0, total_solved = 0, points = 0
        """
        cursor.execute(query)
        print(f"{table_name} has been reset to 0 while keeping baseline data.")

def update_weekly_db(db_file):
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        query = "SELECT username, baseline_easy, baseline_medium, baseline_hard FROM weekly_stats"
        cursor.execute(query)
        weekly_users = cursor.fetchall()

        for user in weekly_users:
            username, baseline_easy, baseline_medium, baseline_hard = user

            # Get latest lifetime stats from `users` table
            query = "SELECT easy_solved, medium_solved, hard_solved FROM users WHERE username = ?"
            cursor.execute(query, (username,))
            lifetime_stats = cursor.fetchone()

            if not lifetime_stats:
                print(f"Skipping {username}, no lifetime stats found.")
                continue

            easy_lifetime, medium_lifetime, hard_lifetime = lifetime_stats

            # Calculate weekly progress (lifetime - baseline)
            easy_progress = max(0, easy_lifetime - baseline_easy)
            medium_progress = max(0, medium_lifetime - baseline_medium)
            hard_progress = max(0, hard_lifetime - baseline_hard)

            # Compute total solved and points
            total_solved = easy_progress + medium_progress + hard_progress
            points = (easy_progress * 1) + (medium_progress * 3) + (hard_progress * 5)

            # Update weekly_stats with new progress
            query = """
                UPDATE weekly_stats 
                SET easy_solved = ?, medium_solved = ?, hard_solved = ?, total_solved = ?, points = ?
                WHERE username = ?
            """
            cursor.execute(query, (easy_progress, medium_progress, hard_progress, total_solved, points, username))

def reset_weekly_db(db_file):
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        query = "DELETE FROM weekly_stats"
        cursor.execute(query)  # Clear weekly stats table

        query = """
            INSERT INTO weekly_stats (username, first_name, last_name, total_solved, points, easy_solved, medium_solved, hard_solved, baseline_easy, baseline_medium, baseline_hard)
            SELECT username, first_name, last_name, 0, 0, 0, 0, 0, easy_solved, medium_solved, hard_solved FROM users
        """
        cursor.execute(query)
