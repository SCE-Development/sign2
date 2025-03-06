from fastapi import FastAPI,HTTPException,Security,Depends,File,UploadFile  
from userSchemas import Users
import sqlite3
import pytz
import os
from secureApi import get_api_key
import ssl
import certifi
import aiohttp
from sqllite_helper import create_table,add_user,get_top_users,display_all_user,check_user_exists,get_first_place,update_all_users_stats, delete_user, update_user, reset_all_users
ssl_context = ssl.create_default_context(cafile=certifi.where())
import uvicorn
from fastapi_utils.tasks import repeat_every
import asyncio
from datetime import datetime
import logging  # Add at top
from tabulate import tabulate
from core_file import get_api_key
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import constants
import subprocess
from pathlib import Path

HOST = constants.MAIN_HOST
PORT = constants.MAIN_PORT
LEETURL=constants.LEETCODE_CLIENT_URL

app=FastAPI()

leetCodeUrl=f"{LEETURL}"



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   
    allow_credentials=True,
    allow_methods=["*"],   
    allow_headers=["*"],  
)

# Set up logging
logging.basicConfig(
    filename='server.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def get_db_file():
    return 'leetcode.db'



@app.post('/register') ## Before /register/{username}
async def register_user(user: Users, api_key: str = Security(get_api_key)): # I'm testing the security for the api username:str
    first_name=user.first_name
    last_name=user.last_name
    username=user.username
    api_key=Security(get_api_key)

    url=f"{leetCodeUrl}/{username}"

    try:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context))as session:
            async with session.get(f'{url}') as response:

                print(f'Got response')
                if(response.status == 200):

                    data=await response.json()
                    easy_solved=data['EASY']
                    medium_solved=data['MEDIUM']
                    hard_solved=data["HARD"]
                  
                    #Assigned the user equal to the different fields 
                    user.easy_solved=easy_solved
                    user.medium_solved=medium_solved
                    user.hard_solved=hard_solved
    
                else:
                    raise HTTPException(status_code=response.status,detail="Couldn't get the correct url")
               
    except Exception as e:
        logging.error(f"Error in register_user: {e}")  # Log the error
        raise HTTPException(detail=f"This is what is occurring in the program: {e}")
    db_file=get_db_file() 
                   
    exisiting_user=check_user_exists(db_file, user.username)
    print("Registering user")

    if(not exisiting_user):
        add_user(db_file,user.username,user.first_name,user.last_name,user.total_solved,user.points,user.easy_solved,user.medium_solved,user.hard_solved)
        add_user(db_file, user.username, user.first_name, user.last_name, 0, 0, 0, 0, 0,  # Weekly progress starts at 0
         user.easy_solved, user.medium_solved, user.hard_solved,  # Use `users` values as baseline
         table_name="weekly_stats")
                    #Not already in the db
    else:
        #Returns error to frontend if user already exists
        raise HTTPException(status_code=400, detail="User already exists")
    return{
        'message':'user registered',
        'userInfo':{
            'username':user.username,
            'first_name':user.first_name,
            'last_name':user.last_name,
            'total_solved':user.total_solved,
            'points':user.points
        }
    }

@app.get('/leaderboard')
def get_users():
    try:
        db_file = get_db_file()
        leaderboard_data = get_top_users(db_file, table_name="weekly_stats")
        return leaderboard_data
    except Exception as e:
        logging.error(f"Error in get_users: {e}")  # Log the error
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.post("/deleteUser")
async def delete_user_endpoint(user: Users):
    db_file = 'leetcode.db'
    username = user.username
    if not check_user_exists(db_file, username):
        raise HTTPException(status_code=404, detail="User not found")

    try:
        # Delete the user from the database
        await delete_user(db_file, username)
        await delete_user(db_file, username, table_name="weekly_stats")
    except Exception as e:
        logging.error(f"Error in delete_user_endpoint: {e}")  # Log the error
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")
    
    return {"message": f"User '{username}' has been deleted successfully."}

@app.post("/uploadImage")
async def upload_image(file: UploadFile = File(...), api_key: str = Security(get_api_key)):
    # Create directories if they don't exist
    os.makedirs("../rpi-rgb-led-matrix/user-images", exist_ok=True)
    os.makedirs("../rpi-rgb-led-matrix/user-vids", exist_ok=True)

    # Get file content
    content = await file.read()
    file_name = file.filename
    file_extension = Path(file_name).suffix.lower()

    # Define image and video extensions
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp'}
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.gif'}

    try:
        # Kill the current process with Ctrl+C and Enter
        subprocess.run([
            "tmux", "send-keys", "-t", "ledsign:0.4", "C-c"
        ], check=True)
        subprocess.run([
            "tmux", "send-keys", "-t", "ledsign:0.4", "Enter"
        ], check=True)
        await asyncio.sleep(0.5)  # Give it time to kill the process

        if file_extension in image_extensions:
            # Process image
            image_path = f"../rpi-rgb-led-matrix/user-images/{file_name}"
            with open(image_path, "wb") as f:
                f.write(content)

            subprocess.run([
                "convert",
                image_path,
                "-resize", "128x128!",
                f"../rpi-rgb-led-matrix/user-images/resized-{file_name}"
            ], check=True)

            # Send cd command and display command
            subprocess.run([
                "tmux", "send-keys", "-t", "ledsign:0.4", 
                "cd ~/leetcode-leaderboard/rpi-rgb-led-matrix", "Enter"
            ], check=True)
            await asyncio.sleep(0.2)

            display_command = (
                f"sudo ./utils/led-image-viewer --led-rows=64 --led-cols=64 "
                f"--led-chain=4 --led-gpio-mapping=adafruit-hat --led-slowdown-gpio=4 "
                f"--led-pixel-mapper=U-mapper ./user-images/resized-{file_name}"
            )
            
            subprocess.run([
                "tmux", "send-keys", "-t", "ledsign:0.4", display_command, "Enter"
            ], check=True)

            return {"message": "Image processed and displayed successfully"}

        elif file_extension in video_extensions:
            # Handle video processing similarly
            video_path = f"../rpi-rgb-led-matrix/user-vids/{file_name}"
            frames_dir = f"../rpi-rgb-led-matrix/{Path(file_name).stem}-frames"
            
            # Check if frames already exist
            if not os.path.exists(frames_dir) or not os.listdir(frames_dir):
                with open(video_path, "wb") as f:
                    f.write(content)

                os.makedirs(frames_dir, exist_ok=True)

                subprocess.run([
                    "ffmpeg",
                    "-i", video_path,
                    "-vf", "fps=24,scale=128:128",
                    f"{frames_dir}/frame_%04d.ppm"
                ], check=True)

            # Send cd command with literal keystrokes
            subprocess.run([
                "tmux", "send-keys", "-l", "-t", "ledsign:0.4", 
                "cd ~/leetcode-leaderboard/rpi-rgb-led-matrix"
            ], check=True)
            subprocess.run([
                "tmux", "send-keys", "-t", "ledsign:0.4", "Enter"
            ], check=True)
            await asyncio.sleep(1)

            # Send the video display command with literal keystrokes
            video_command = (
                f"sudo ./utils/led-image-viewer --led-rows=64 --led-cols=64 "
                f"--led-chain=4 --led-gpio-mapping=adafruit-hat --led-slowdown-gpio=4 "
                f"--led-pixel-mapper=U-mapper -f -D50 {frames_dir}/frame_*.ppm"
            )
            
            subprocess.run([
                "tmux", "send-keys", "-l", "-t", "ledsign:0.4", video_command
            ], check=True)
            subprocess.run([
                "tmux", "send-keys", "-t", "ledsign:0.4", "Enter"
            ], check=True)

            return {"message": "Video processed and displayed successfully"}

        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

    except subprocess.CalledProcessError as e:
        logging.error(f"Subprocess error in upload_image: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    except Exception as e:
        logging.error(f"Error in upload_image: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

def is_within_active_hours():
    """Returns True if the current time is between 9 AM - 9 PM."""
    now = datetime.now().hour
    return 10 <= now < 20

@app.on_event("startup")
@repeat_every(seconds=1800) #Runs every 30 minutes
async def update_stats_periodically() -> None:
    try:
        db_file = get_db_file()
        await update_all_users_stats(db_file)
    except Exception as e:
        logging.error(f"Error updating stats: {e}")  # Log the error
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error updating stats: {e}")

@app.on_event("startup")
@repeat_every(seconds=300)  # Runs every 300 seconds
async def update_weekly_db():
    """ Tracks weekly progress dynamically """
    try:
        db_file = get_db_file()
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # 🚀 Fetch all users from weekly_stats
        cursor.execute("SELECT username, baseline_easy, baseline_medium, baseline_hard FROM weekly_stats")
        weekly_users = cursor.fetchall()

        for user in weekly_users:
            username, baseline_easy, baseline_medium, baseline_hard = user

            #Get latest lifetime stats from `users` table
            cursor.execute("SELECT easy_solved, medium_solved, hard_solved FROM users WHERE username = ?", (username,))
            lifetime_stats = cursor.fetchone()

            if not lifetime_stats:
                print(f"Skipping {username}, no lifetime stats found.")
                continue

            easy_lifetime, medium_lifetime, hard_lifetime = lifetime_stats

            #Calculate weekly progress (lifetime - baseline)
            easy_progress = max(0, easy_lifetime - baseline_easy)
            medium_progress = max(0, medium_lifetime - baseline_medium)
            hard_progress = max(0, hard_lifetime - baseline_hard)

            #Compute total solved and points
            total_solved = easy_progress + medium_progress + hard_progress
            points = (easy_progress * 1) + (medium_progress * 3) + (hard_progress * 5)

            #Update weekly_stats with new progress
            cursor.execute("""
                UPDATE weekly_stats 
                SET easy_solved = ?, medium_solved = ?, hard_solved = ?, total_solved = ?, points = ?
                WHERE username = ?
            """, (easy_progress, medium_progress, hard_progress, total_solved, points, username))

        conn.commit()
        conn.close()
        #print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Updated weekly progress!")

    except Exception as e:
        logging.error(f"Error updating weekly stats: {e}")  # Log the error
        print(f"Error updating weekly stats: {e}")




@app.on_event("startup")
@repeat_every(seconds=60)  # Runs every 60 seconds and checks if it is Monday to reset weekly stats
async def reset_weekly_db():
    """ Resets weekly stats every Monday between 9:00 am - 9:05 am """
    try:
        tz = pytz.timezone('America/Los_Angeles')
        now = datetime.now(tz)
        if now.weekday() == 0 and 9 <= now.hour < 10 and 0 <= now.minute < 5:
            db_file = get_db_file()
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()

            # 🚀 Reset weekly progress but store new baseline from `users`
            cursor.execute("DELETE FROM weekly_stats")  # Clear weekly stats table
            cursor.execute("""
                INSERT INTO weekly_stats (username, first_name, last_name, total_solved, points, easy_solved, medium_solved, hard_solved, baseline_easy, baseline_medium, baseline_hard)
                SELECT username, first_name, last_name, 0, 0, 0, 0, 0, easy_solved, medium_solved, hard_solved FROM users
            """)

            conn.commit()
            conn.close()
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Weekly stats reset! Baseline stored.")
    except Exception as e:
        logging.error(f"Error resetting weekly database: {e}")  # Log the error
        print(f"Error resetting weekly database: {e}")

 

if __name__ == "__main__":
    print(f"main.py running on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT, log_level="error", use_colors=False)