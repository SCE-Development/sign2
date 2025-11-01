import datetime
import logging
import sys
import uvicorn
import threading
import zoneinfo
import subprocess
from gtts import gTTS
import os
import time
import tempfile

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
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
wav_generation_lock = threading.Lock()
last_wav_generation_time = None

app = FastAPI()
arguments = args.get_args()

with open(arguments.config, "r") as stream:
    try:
        data = yaml.safe_load(stream)
        API_KEY = data.get("api_key", "NOTHING_REALLY")
        POLLING_INTERVAL = data.get("leetcode_polling_interval", 300)
        PORT = data.get("port", 8000)
        SQLITE_FILE_NAME = data.get("sqlite3_file_name", "users.db")
        TIME_ZONE = data.get("local_timezone", "UTC")
        POINTS = data.get("points", {})
    except Exception:
        logger.exception("unable to open yaml file / file is missing data, exiting")
        sys.exit(1)

metrics_handler = MetricsHandler.instance()

@app.get("/")
def get_leaderboard():
    try:
        leaderboard_data = leaderboard()
        MetricsHandler.sign_last_updated.set(time.time())
        MetricsHandler.sign_update_error.set(0)
        return leaderboard_data
    except Exception as e:
        MetricsHandler.sign_update_error.set(1)
        logger.exception(f"Error fetching leaderboard: {str(e)}")
        return {"error": str(e), "status_code": 500}


@app.post("/user/add")
async def add_user(request: Request):
    try:
        data = await request.json()
        username = data.get("username", "")
        first_name = data.get("firstName", "unknown")
        last_name = data.get("lastName", "unknown")
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


@app.get("/phone")
async def get_phone_script():
    global last_wav_generation_time
    
    wav_path = os.path.join('/app/tmp', 'leetcode_latest.wav')
    current_time = datetime.datetime.now().timestamp()

    if os.path.exists(wav_path) and last_wav_generation_time is not None and current_time - last_wav_generation_time < 1800:
        MetricsHandler.wav_last_sent.set(time.time())
        return FileResponse(wav_path, media_type="audio/wav", filename='leetcode_latest.wav')

    with wav_generation_lock:
        if last_wav_generation_time is None or current_time - last_wav_generation_time > 1800:
            logger.info("Regenerating phone script audio file on demand")
            my_big_dumb_generation_life() 

    MetricsHandler.wav_last_sent.set(time.time())
    return FileResponse(wav_path, media_type="audio/wav", filename='leetcode_latest.wav')


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


def leaderboard():
    """Fetch the leaderboard data from the SQLite database."""
    tz = zoneinfo.ZoneInfo(TIME_ZONE)
    now_local = datetime.datetime.now(tz)

    # Set start of month to 1st of the month 12am
    start_of_month_local = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start_of_month_utc = start_of_month_local.astimezone(datetime.timezone.utc)
    now_utc = now_local.astimezone(datetime.timezone.utc)

    # Format dates to match SQLite's string format
    start_date_str = start_of_month_utc.strftime("%Y-%m-%d %H:%M:%S")
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
    leaderboard_data = sorted(users, key=lambda u: u["points"], reverse=True)
    return {
        "leaderboard": leaderboard_data,
        "month": now_local.month - 1
    }


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


def create_asterisk_encoded_wav(mp3_path, wav_path):
    """Convert mp3 file to wav format with compression settings and cleanup."""
    # Convert mp3 to wav using ffmpeg with compression settings
    subprocess.run([
        'ffmpeg', '-i', mp3_path,
        '-ar', '8000',          # Sample rate: 8kHz 
        '-ac', '1',             # Mono audio
        '-acodec', 'pcm_s16le', # PCM 16-bit little-endian codec
        '-y',                   # Overwrite output file
        wav_path
    ], check=True, stdout=subprocess.DEVNULL)
    
    os.remove(mp3_path)


def generate_ai_audio(output_dir, time_str, num_participants, month, top_10):
    """Generate a simple AI-only audio file when pre-recorded files are missing."""
    global last_wav_generation_time
    logger.info("Defaulting to AI voice for entire script")
    script = f"As of {time_str}, our LeetCode Leaderboard has {num_participants} participants. The top 10 for the month of {month} is as follows: {top_10}. If you wish to participate in the leaderboard, please visit sce dot sjsu dot edu"
    mp3_path = os.path.join(output_dir, f'{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.mp3')
    tts = gTTS(text=script, lang='en', slow=False)
    tts.save(mp3_path)
    
    wav_path = os.path.join(output_dir, 'leetcode_latest.wav')
    create_asterisk_encoded_wav(mp3_path, wav_path)

    last_wav_generation_time = datetime.datetime.now().timestamp()
    MetricsHandler.wav_last_generated.set(last_wav_generation_time)
    logger.info(f"Phone script WAV file generated successfully at {datetime.datetime.fromtimestamp(last_wav_generation_time)}")


def my_big_dumb_generation_life():
    """Generate the phone script WAV file from the current leaderboard data."""
    global last_wav_generation_time

    try:
        fetch_leaderboard = leaderboard()
        leaderboard_data = fetch_leaderboard['leaderboard']
        num_participants = str(len(leaderboard_data))
        tz = zoneinfo.ZoneInfo("America/Los_Angeles")
        now_local = datetime.datetime.now(tz)
        month = now_local.strftime("%B")
        now = datetime.datetime.now(tz)
        time_str = now.strftime("%I:%M %p %Z").lstrip("0")
        top_10 = ""    
        for i, entry in enumerate(leaderboard_data):
            if i > 9:
                break
            points = entry['points']
            top_10 += f"\n{entry['username']} has {points} {'point' if points == 1 else 'points'}."
        
    except Exception:
        logger.exception("Unexpected error generating phone script")
        return

    OUTPUT_DIR = '/app/tmp'
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    ben = ['as_of.mp3', 'our_lc_leaderboard.mp3', 'top_10_for_month.mp3', 'is_as_follows.mp3', 'visit_our_website.mp3']
    not_ben_filenames = ['time', 'num_participants', 'month', 'top_10']
    not_ben = [time_str, num_participants, month, top_10]
    full_order = []

    for i, file in enumerate(ben):
        full_path = os.path.join(OUTPUT_DIR, file)
        if not os.path.exists(full_path):
            generate_ai_audio(OUTPUT_DIR, time_str, num_participants, month, top_10)
            return

        full_order.append(full_path)
        if i == len(not_ben):
            break
        mp3 = os.path.join(OUTPUT_DIR, not_ben_filenames[i] + '.mp3')
        tts = gTTS(text=not_ben[i], lang='en', slow=False)
        logger.info(f"File {not_ben_filenames[i]} found, using AI voice")
        tts.save(mp3)
        full_order.append(mp3)
        logger.info(f"{full_order}")

    # Concatenate all audio files together
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        for path in full_order:
            f.write(f"file '{os.path.abspath(path)}'\n")
        list_file = f.name

    mp3_path = os.path.join(OUTPUT_DIR, f'{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.mp3')

    cmd = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", list_file,
        "-c", "copy",
        mp3_path
    ]

    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
    logger.info('we pieced ben together with the ai')

    wav_path = os.path.join(OUTPUT_DIR, 'leetcode_latest.wav')
    create_asterisk_encoded_wav(mp3_path, wav_path, full_order, ben, OUTPUT_DIR)
    # Clean up temporary generated files if provided
    ben_full_paths = [os.path.join(OUTPUT_DIR, f) for f in ben]
    for file in full_order:
        if file not in ben_full_paths:
            os.remove(file)

    # Update the timestamp
    last_wav_generation_time = datetime.datetime.now().timestamp()
    MetricsHandler.wav_last_generated.set(last_wav_generation_time)
    logger.info(f"Phone script WAV file generated successfully at {datetime.datetime.fromtimestamp(last_wav_generation_time)}")


@app.on_event("shutdown")
def shutdown_event():
    logger.info("you should stop the leetcode thread NOW")
    leetcode_stop_event.set()

if __name__ == "server":
    # Initialize metrics on container startup
    MetricsHandler.wav_last_generated.set(time.time())
    MetricsHandler.wav_last_sent.set(time.time())
    MetricsHandler.sign_last_updated.set(time.time())
    threading.Thread(target=poll_leetcode).start()

if __name__ == "__main__":
    sqlite_helpers.maybe_create_table(SQLITE_FILE_NAME)
    logger.info(f"Starting server, listening on port {PORT}")
    uvicorn.run("server:app", host="0.0.0.0", port=PORT, reload=True)
