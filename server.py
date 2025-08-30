import datetime
import logging
import sys
import uvicorn
import threading
import zoneinfo
import time

from fastapi import FastAPI, HTTPException, Request, Response
import yaml
import prometheus_client

from modules import args
from modules import leetcode_helpers
from modules import sqlite_helpers
from modules.logger import logger
from modules.metrics import MetricsHandler


logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)


leetcode_stop_event = threading.Event()

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
    except Exception:
        logger.exception("unable to open yaml file / file is missing data, exiting")
        sys.exit(1)

metrics_handler = MetricsHandler.instance()

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
                user["easy"] * POINTS.get("easy", 1)
                + user["medium"] * POINTS.get("medium", 3)
                + user["hard"] * POINTS.get("hard", 5)
            )
        users_sorted = sorted(users, key=lambda u: u["points"], reverse=True)
        MetricsHandler.sign_last_updated.set(int(time.time()))
        MetricsHandler.sign_update_error.set(0)
        return users_sorted
    except Exception as e:
        MetricsHandler.sign_update_error.set(1)
        logger.exception(f"Error fetching leaderboard: {str(e)}")
        return {"error": str(e), "status_code": 500}


@app.post("/user/add")
async def add_user(request: Request):
    try:
        data = await request.json()
        username = data.get("username", "")
        first_name = data.get("first_name", "unknown")
        last_name = data.get("last_name", "unknown")
        if not username:
            raise HTTPException(status_code=400, detail="Username must be populated")
        if sqlite_helpers.check_if_user_exists(SQLITE_FILE_NAME, username):
            raise HTTPException(status_code=400, detail="User already exists")
        sqlite_helpers.add_user(SQLITE_FILE_NAME, username, first_name, last_name)
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
 

@app.get("/getAllUsers")
async def get_all_users():
    try:
        users = sqlite_helpers.get_all_users(SQLITE_FILE_NAME)
        return {"users": users}
    except Exception as e:
        logger.exception(f"Error fetching all users: {str(e)}")
        return {"error": str(e), "status_code": 500}


@app.get("/debug")
def debug():
    # dump all contents of the tables sorted by created_at for both tables
    leetcode_snapshots = sqlite_helpers.get_all_leetcode_snapshots(SQLITE_FILE_NAME)
    users = sqlite_helpers.get_all_users(SQLITE_FILE_NAME)
    weekly_baselines = sqlite_helpers.get_all_weekly_baselines(SQLITE_FILE_NAME)
    return {"leetcode_snapshots": leetcode_snapshots, "users": users, "weekly_baselines": weekly_baselines}


@app.middleware("http")
async def track_response_codes(request: Request, call_next):
    response = await call_next(request)
    MetricsHandler.endpoint_hits.labels(request.url.path, response.status_code).inc()
    return response


@app.get("/metrics")
def get_metrics():
    return Response(
        media_type="text/plain",
        content=prometheus_client.generate_latest()
    )


def poll_leetcode():
    while not leetcode_stop_event.is_set():
        try:
            all_users = sqlite_helpers.get_all_users(SQLITE_FILE_NAME)
            for user in all_users:
                username = user["username"]
                snapshot = leetcode_helpers.get_leetcode_problems_solved(username)
                if snapshot is None:
                    continue
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


@app.on_event("shutdown")
def shutdown_event():
    logger.info("you should stop the leetcode thread NOW")
    leetcode_stop_event.set()

if __name__ == "server":
    threading.Thread(target=poll_leetcode).start()

if __name__ == "__main__":
    sqlite_helpers.maybe_create_table(SQLITE_FILE_NAME)
    logger.info(f"Starting server, listening on port {PORT}")
    uvicorn.run("server:app", host="0.0.0.0", port=PORT, reload=True)
