import yaml
from fastapi import FastAPI, HTTPException
from modules.args import get_args
import logging
import sys
import uvicorn
from modules.sqlite_helpers import add_user, delete_user, get_leaderboard, check_if_user_exists
from modules.leetcode_helpers 

app = FastAPI()
args = get_args()

with open(args.config, "r") as stream:
    try:
        data = yaml.safe_load(stream)
        API_KEY = data.get("api_key", "NOTHING_REALLY")
        POLLING_INTERVAL = data.get("leetcode_polling_interval", "5m")
        PORT = data.get("port", 8000)
        SQLITE_TABLE_NAME = data.get("sqlite3_table_name", "users")
    except Exception:
        logging.exception("unable to open yaml file / file is missing data, exiting")
        sys.exit(1)

@app.get("/")
def leaderboard():
    users = get_leaderboard(SQLITE_TABLE_NAME)
    return {"leaderboard": users}

@app.post("/user/add")
def add_user(username: str):
    if check_if_user_exists(SQLITE_TABLE_NAME, username):
        raise HTTPException(status_code=400, detail="User already exists")
    add_user(SQLITE_TABLE_NAME, username)
    return {"detail": "User added successfully"}

@app.post("/user/remove")
def remove_user(username: str):
    if not check_if_user_exists(SQLITE_TABLE_NAME, username):
        raise HTTPException(status_code=404, detail="User not found")
    delete_user(SQLITE_TABLE_NAME, username)
    return {"detail": "User removed successfully"}

if __name__ == '__main__':
    logging.info(f"Starting server, listening on port {PORT}")
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)