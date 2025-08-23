import datetime
import sys
import uvicorn
import threading
import time
import zoneinfo

from fastapi import FastAPI, HTTPException, Request
import yaml

from modules import args
from modules import leetcode_helpers
from modules import sqlite_helpers
from modules.logger import logger


stop_event = threading.Event()
app = FastAPI()
arguments = args.get_args()

with open(arguments.config, "r") as stream:
    try:
        data = yaml.safe_load(stream)
        API_KEY = data.get("api_key", "NOTHING_REALLY")
        POLLING_INTERVAL = data.get("leetcode_polling_interval", "5m")
        PORT = data.get("port", 8000)
        SQLITE_FILE_NAME = data.get("sqlite3_file_name", "users.db")
        TIME_ZONE = data.get("local_timezone", "UTC")
        POINTS = data.get("points", {})
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
        now = datetime.datetime.now(tz)
        users = sqlite_helpers.get_users_as_leaderboard(
            SQLITE_FILE_NAME, start_date=start_of_week_utc, end_date=now
        )
        for user in users:
            user["points"] = (
                user["easy"] * POINTS["easy"]
                + user["medium"] * POINTS["medium"]
                + user["hard"] * POINTS["hard"]
            )
        return users
    except Exception as e:
        logger.exception(f"Error fetching leaderboard: {str(e)}")
        return {"error": str(e)}


@app.post("/user/add")
async def add_user(request: Request):
    try:
        data = await request.json()
        username = data.get("username")
        if sqlite_helpers.check_if_user_exists(SQLITE_FILE_NAME, username):
            raise HTTPException(status_code=400, detail="User already exists")
        sqlite_helpers.add_user(SQLITE_FILE_NAME, username)
        return {"detail": "User added successfully"}
    except Exception as e:
        logger.exception(f"Error adding user: {str(e)}")
        return {"error": str(e)}


@app.post("/user/remove")
async def remove_user(request: Request):
    try:
        data = await request.json()
        username = data.get("username")
        if not sqlite_helpers.check_if_user_exists(SQLITE_FILE_NAME, username):
            raise HTTPException(status_code=404, detail="User not found")
        sqlite_helpers.delete_user(SQLITE_FILE_NAME, username)
        return {"detail": "User removed successfully"}
    except Exception as e:
        logger.exception(f"Error removing user: {str(e)}")
        return {"error": str(e)}


@app.get("/clear_tables")
def clear_all_tables():
    sqlite_helpers.clear_tables(SQLITE_FILE_NAME)
    return {"detail": "All tables cleared"}


@app.get("/debug")
def debug():
    # dump all contents of the tables sorted by created_at for both tables
    leetcode_snapshots = sqlite_helpers.get_all_leetcode_snapshots(SQLITE_FILE_NAME)
    users = sqlite_helpers.get_all_users(SQLITE_FILE_NAME)
    return {"leetcode_snapshots": leetcode_snapshots, "users": users}


def poll_leetcode():
    while not stop_event.is_set():
        try:
            all_users = sqlite_helpers.get_all_users(SQLITE_FILE_NAME)
            for user in all_users:
                result = leetcode_helpers.get_leetcode_problems_solved(user)
                for snapshot in result:
                    sqlite_helpers.store_snapshot(
                        SQLITE_FILE_NAME,
                        snapshot.user,
                        snapshot.easy,
                        snapshot.medium,
                        snapshot.hard,
                    )
        except Exception as e:
            logger.exception(f"Error polling LeetCode: {str(e)}")

        # Sleep but wake up if stop_event is set
        stop_event.wait(30)


@app.on_event("shutdown")
def shutdown_event():
    logger.info("you should stop the leetcode thread NOW")
    stop_event.set()


# we need a function that every 30 seconds (hardcoded for now) polls leetcode
# use leetcode_helpers, iterate over the return value, then pass the dataclass into sqlite helpers
# call store_snapshot
# make a thread like
# https://github.com/SCE-Development/sce-tv/blob/b154d52730114d6a27a59b582da06241e7516055/server.py#L656

if __name__ == "server":
    threading.Thread(target=poll_leetcode).start()

if __name__ == "__main__":
    sqlite_helpers.maybe_create_table(SQLITE_FILE_NAME)
    logger.info(f"Starting server, listening on port {PORT}")
    uvicorn.run("server:app", host="0.0.0.0", port=PORT, reload=True)
