import sqlite3
from tabulate import tabulate
from fastapi import HTTPException
import httpx
import time
import constants
import traceback
from constants import LEETCODE_CLIENT_URL

def create_table(db_file, table_name='users'):
    con = sqlite3.connect(db_file)
    cursor_obj = con.cursor()

    query_table = f"""
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
    cursor_obj.execute(query_table)
    print(f"{table_name} table is ready")
    con.close()

def add_user(db_file, username, first_name, last_name, total_solved=0, points=0, easy_solved=0, medium_solved=0, hard_solved=0, 
             baseline_easy=0, baseline_medium=0, baseline_hard=0, table_name='users'):
    con = sqlite3.connect(db_file)
    cursor_obj = con.cursor()

    if table_name == "users":
        query = f"""
        INSERT INTO {table_name} (username, first_name, last_name, total_solved, points, easy_solved, medium_solved, hard_solved)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor_obj.execute(query, (username, first_name, last_name, total_solved, points, easy_solved, medium_solved, hard_solved))

    elif table_name == "weekly_stats":
        query = f"""
        INSERT INTO {table_name} (username, first_name, last_name, total_solved, points, easy_solved, medium_solved, hard_solved, baseline_easy, baseline_medium, baseline_hard)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor_obj.execute(query, (username, first_name, last_name, total_solved, points, easy_solved, medium_solved, hard_solved, baseline_easy, baseline_medium, baseline_hard))

    else:
        print(f"Invalid table name: {table_name}")
        con.close()
        return

    con.commit()
    con.close()


def update_user(db_file, username, total_solved, points, easy_solved=0, medium_solved=0, hard_solved=0, table_name='users'):
    try:
        db = sqlite3.connect(db_file)
        cursor = db.cursor()
        query = f"""
        UPDATE {table_name}
        SET total_solved = ?, points = ?, easy_solved = ?, medium_solved = ?, hard_solved = ?
        WHERE username = ?
        """
        cursor.execute(query, (total_solved, points, easy_solved, medium_solved, hard_solved, username))
        db.commit()
    except Exception as e:
        print(f"Error updating user: {e}")
    finally:
        db.close()

def display_all_user(db_file, table_name='users'):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM {table_name}')
    output = cursor.fetchall()
    column_names = [description[0] for description in cursor.description]

    conn.close()
    if output:
        print(f"Displaying all registered users for {table_name}")
        return tabulate(output, headers=column_names, tablefmt="grid")
    else:
        return "No users found in the database."

def get_top_users(db_file, table_name='users'):
    try:
        # Connect to the SQLite database
        db = sqlite3.connect(db_file)
        cursor = db.cursor()
        assert table_name in ["users", "weekly_stats"], f"Invalid table: {table_name}"
        # SQL query to fetch all users sorted by points in descending order
        query = f"""
        SELECT username, first_name, last_name, total_solved, points, easy_solved, medium_solved, hard_solved
        FROM {table_name}
        ORDER BY points DESC
        """
        cursor.execute(query)
        users = cursor.fetchall()

        # Check if the database returned any users
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

        # Print the top users in a tabular format
        db.close()
    finally:
        return result

def check_user_exists(db_file, username, table_name='users'):
    conn = sqlite3.connect(db_file)
    curr = conn.cursor()
    query_table = f"SELECT COUNT(1) FROM {table_name} WHERE username=? LIMIT 1"

    curr.execute(query_table, (username,))
    existing_user = curr.fetchone()

    conn.close()
    
    if existing_user and existing_user[0] == 1:
        return True
    else:
        return False

def get_first_place(db_file, table_name='users'):
    conn = sqlite3.connect(db_file)
    curr = conn.cursor()
    query_table = f"SELECT * FROM {table_name} ORDER BY points DESC LIMIT 1"

    curr.execute(query_table)
    column_names = [description[0] for description in curr.description]
    data = curr.fetchall()

    print("Showing the top user")
    if data:
        print(tabulate(data, headers=column_names, tablefmt="grid"))
    else:
        print("No users added")
    
    conn.close()
    return data

async def delete_user(db_file, username , table_name='users'):
    conn = sqlite3.connect(db_file)
    curr = conn.cursor()
    query_table = f'DELETE FROM {table_name} WHERE username=?'
    curr.execute(query_table, (username,))
    print(f'{username} has been deleted')
    conn.commit()
    conn.close()

async def fetch_user_stats(username):
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(f"{LEETCODE_CLIENT_URL}/{username}")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch stats for user {username}: {response.text}")
            return None

async def update_all_users_stats(db_file, table_name='users'):
    try:
        db = sqlite3.connect(db_file)
        cursor = db.cursor()
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
    except Exception as e:
        print(f"Error updating all users' stats: {e}")
        traceback.print_exc()  # Print full traceback for debugging
    finally:
        db.close()

def reset_all_users(db_file, table_name='users'):
    try:
        db = sqlite3.connect(db_file)
        cursor = db.cursor()
        query = f'''
            UPDATE {table_name}
            SET easy_solved = 0, medium_solved = 0, hard_solved = 0, total_solved = 0, points = 0
        '''
        cursor.execute(query)
        db.commit()
        db.close()
        print(f"{table_name} has been reset to 0 while keeping baseline data.")
    except sqlite3.Error as e:
        print(f'Database reset error: {e}')
        raise


def update_user(db_file, username, total_solved=0, points=0, easy_solved=0, medium_solved=0, hard_solved=0, 
                table_name='users'):
    try:
        db = sqlite3.connect(db_file)
        cursor = db.cursor()
        query = f'''
            UPDATE {table_name} 
            SET total_solved = ?, points = ?, easy_solved = ?, medium_solved = ?, hard_solved = ?
            WHERE username = ?
        '''
        cursor.execute(query, (total_solved, points, easy_solved, medium_solved, hard_solved, username))
        db.commit()
        db.close()
    except sqlite3.Error as e:
        logger.error(f'User modification error: {e}')
        raise