import datetime
import sys
import uvicorn
import threading
import zoneinfo

from fastapi import FastAPI, HTTPException, Request
import yaml

from modules import args
from modules import leetcode_helpers
from modules import sqlite_helpers
from modules.logger import logger


leetcode_stop_event = threading.Event()
clear_db_stop_event = threading.Event()

app = FastAPI()
arguments = args.get_args()

with open(arguments.config, "r") as stream:
    try:
        data = yaml.safe_load(stream)
        API_KEY = data.get("api_key", "NOTHING_REALLY")
        POLLING_INTERVAL = data.get("leetcode_polling_interval", "300")
        PORT = data.get("port", 8000)
        SQLITE_FILE_NAME = data.get("sqlite3_file_name", "users.db")
        TIME_ZONE = data.get("local_timezone", "UTC")
        POINTS = data.get("points", {})
        LEADERBOARD_INTERVAL = data.get("leaderboard_interval", "604800")  # Default to one week
    except Exception:
        logger.exception("unable to open yaml file / file is missing data, exiting")
        sys.exit(1)


@app.get("/")
def leaderboard():
    try:
        tz = zoneinfo.ZoneInfo(TIME_ZONE)
        now_local = datetime.datetime.now(tz)
        # Set start of week to Sunday 12am
        days_since_sunday = now_local.weekday() + 1 if now_local.weekday() < 6 else 0
        start_of_week_local = now_local - datetime.timedelta(days=days_since_sunday)
        start_of_week_local = start_of_week_local.replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        start_of_week_utc = start_of_week_local.astimezone(datetime.timezone.utc)
        now_utc = now_local.astimezone(datetime.timezone.utc)

        # Format dates to match SQLite's string format
        start_date_str = start_of_week_utc.strftime("%Y-%m-%d %H:%M:%S")
        end_date_str = now_utc.strftime("%Y-%m-%d %H:%M:%S")

        users = sqlite_helpers.get_users_as_leaderboard(
            SQLITE_FILE_NAME, start_date=start_date_str, end_date=end_date_str
        )
        for user in users:
            user["points"] = (
                user["easy"] * POINTS["easy"]
                + user["medium"] * POINTS["medium"]
                + user["hard"] * POINTS["hard"]
            )
        users_sorted = sorted(users, key=lambda u: u["points"], reverse=True)
        return users_sorted
    except Exception as e:
        logger.exception(f"Error fetching leaderboard: {str(e)}")
        return {"error": str(e), "status_code": 500}


@app.post("/user/add")
async def add_user(request: Request):
    try:
        data = await request.json()
        username = data.get("username", "")
        if not username:
            raise HTTPException(status_code=400, detail="Username must be populated")
        if sqlite_helpers.check_if_user_exists(SQLITE_FILE_NAME, username):
            raise HTTPException(status_code=400, detail="User already exists")
        sqlite_helpers.add_user(SQLITE_FILE_NAME, username)
        return {"detail": f"{username} added successfully"}
    except HTTPException as e:
        logger.exception(f"Error adding user: {str(e)}")
        return {"error": str(e), "status_code": e.status_code}
    except Exception as e:
        logger.exception(f"Error adding user: {str(e)}")
        return {"error": str(e), "status_code": 500}


@app.post("/user/remove")
async def remove_user(request: Request):
    try:
        data = await request.json()
        username = data.get("username", "")
        if not sqlite_helpers.check_if_user_exists(SQLITE_FILE_NAME, username):
            raise HTTPException(status_code=404, detail="User not found")
        sqlite_helpers.delete_user(SQLITE_FILE_NAME, username)
        return {"detail": f"{username} removed successfully"}
    except HTTPException as e:
        logger.exception(f"Error removing user: {str(e)}")
        return {"error": str(e), "status_code": e.status_code}
    except Exception as e:
        logger.exception(f"Error removing user: {str(e)}")
        return {"error": str(e), "status_code": 500}


@app.get("/debug")
def debug():
    # dump all contents of the tables sorted by created_at for both tables
    leetcode_snapshots = sqlite_helpers.get_all_leetcode_snapshots(SQLITE_FILE_NAME)
    users = sqlite_helpers.get_all_users(SQLITE_FILE_NAME)
    return {"leetcode_snapshots": leetcode_snapshots, "users": users}


def poll_leetcode():
    while not leetcode_stop_event.is_set():
        logger.info("Polling LeetCode now...")
        try:
            all_users = sqlite_helpers.get_all_users(SQLITE_FILE_NAME)
            for user in all_users:
                snapshot = leetcode_helpers.get_leetcode_problems_solved(user)
                sqlite_helpers.store_snapshot(
                    SQLITE_FILE_NAME,
                    snapshot.user,
                    snapshot.easy,
                    snapshot.medium,
                    snapshot.hard,
                )
        except Exception as e:
            logger.exception(f"Error polling LeetCode: {str(e)}")

        # Sleep but wake up if leetcode_stop_event is set
        leetcode_stop_event.wait(POLLING_INTERVAL)


def clear_leetcode_snapshots():
    while not clear_db_stop_event.is_set():
        try:
            today = datetime.datetime.today()
            if today.weekday() == 5 and today.hour == 23 and today.minute == 55: # reset every Saturday at 11:55pm -> gives time before the tracking starts

                start_date = today - datetime.timedelta(days=6) # saturday is 6 days after sunday
                end_date = today
                
                start_date_str = start_date.strftime("%m/%d/%Y")
                end_date_str = end_date.strftime("%m/%d/%Y")
                
                logger.info(f"Processing week from {start_date_str} to {end_date_str}")
                sqlite_helpers.find_weekly_winners(SQLITE_FILE_NAME, start_date_str, end_date_str)

                logger.info(f"Clearing LeetCode snapshots for the week from {start_date_str} to {end_date_str}")
                sqlite_helpers.reset_leetcode_snapshots(SQLITE_FILE_NAME)
        except Exception as e:
            logger.exception(f"Error clearing LeetCode snapshots: {str(e)}")

        clear_db_stop_event.wait(POLLING_INTERVAL) # very frequent checks for a once a week thing, but we can fix later


@app.on_event("shutdown")
def shutdown_event():
    logger.info("you should stop the leetcode thread NOW")
    leetcode_stop_event.set()
    clear_db_stop_event.set()

if __name__ == "server":
    threading.Thread(target=poll_leetcode).start()
    threading.Thread(target=clear_leetcode_snapshots).start()

if __name__ == "__main__":
    sqlite_helpers.maybe_create_table(SQLITE_FILE_NAME)
    logger.info(f"Starting server, listening on port {PORT}")
    uvicorn.run("server:app", host="0.0.0.0", port=PORT, reload=True)
