# READ ALL BEFORE RUNNING ANYTHING !

## FIND THE TMUX SECTION FIRST, IT HAS ALL THE COMMANDS TO RUN THE PROGRAM
## ATTEMPT TO ATTACH TO SESSION FIRST WITH: tmux attach -t ledsign
## KILL SESSION WITH: tmux kill-session -t ledsign
## Detach from session with: Ctrl+b, d
## Navigate between windows with: Ctrl+b, arrow keys

# LeetCode Leaderboard LED Sign

This project is a **LeetCode Leaderboard** displayed on an **RGB LED matrix**, running on a **Raspberry Pi**. It integrates with **LeetCode's GraphQL API**, fetches user stats, and displays them dynamically. The backend is built using **FastAPI** and **SQLite**, while the frontend includes a React-based dashboard.

---

## 📂 Project Structure

### 🟢 LED Matrix Library
- Inside the `leetcode_leaderboard` folder, there are multiple **LED matrix libraries** sourced from GitHub.
- These libraries help display data on the **RGB LED matrix**.
- text-example.cc is what actually displays the leaderboard on the LED matrix, it has been modified to work for our use case.
- The original text-example.cc can be found [here](https://github.com/hzeller/rpi-rgb-led-matrix/blob/master/utils/text-example.cc).
- We brought the font and the make file from the original repository and modified it to work for our use case.

### 🔥 Core Backend Files (Python)
The core logic for fetching, processing, and displaying the leaderboard is inside the `core` folder.

#### 1️⃣ `leetcode_client.py`
- Handles **GraphQL queries** to fetch LeetCode user data.
- Contains a **FastAPI server** to make querying easier.

#### 2️⃣ `main.py`
- The **main backend file** that runs the **FastAPI** server.
- **Key Endpoints:**
  - `/leaderboard`: **Essential** endpoint for:
    - **Fetching** leaderboard data.
    - **Parsing** data for the LED matrix.
    - **Fetching new stats** for the database tables.
  - `/register`: Adds new users.
  - `/delete_user`: Removes users.
- **Weekly Reset Logic:** 
  - Resets **baseline stats** every week for accurate tracking.
  - Implements **repeat-every logic** to refresh stats periodically.

#### 3️⃣ `sqlite_helper.py`
- Handles **all interactions** with the SQLite database.
- **Database Tables:**
  - **`users` table** (lifetime stats)
    - `username`, `first_name`, `last_name`, `total_solved`, `points`, `easy_solved`, `medium_solved`, `hard_solved`
  - **`weekly_stats` table** (weekly stats with baselines)
    - Same columns as `users`, plus:
      - `baseline_easy`
      - `baseline_medium`
      - `baseline_hard`
- Methods **default to `users`**, but override behavior via parameters.

#### 4️⃣ `user_schema.py`
- Defines the **user object schema** for structured data handling.

#### 5️⃣ `constants.py`
- Contains **host and port settings** for easy **development vs. deployment** changes.

---

## 🖥️ Frontend (LED Matrix Web Interface)
Located in the `led_matrix_se` folder.

### 🟡 React Dashboard
- The **dashboard** is a single page (`Dashboard.jsx`) with three key components:
  - **Admin List**
  - **LED Set**
  - **Register User**
- The **dashboard is imported into `App.jsx`** for display.

### 🟡 LED Sign Emulator
- **Iframe-based emulator** for previewing the leaderboard without an actual LED matrix.
- Uses the **RGB matrix browser emulator** to replicate the display.

---

## ⚡ Running the Project

### 🛠️ Prerequisites
Ensure your system meets the requirements by using a **virtual environment**.

A virtual environment called **`leetcode-led`** is already set up.  
To activate it, navigate to the `leetcode_leaderboard` directory and run:

```bash
source leetcode-led/bin/activate
```
Then, install dependencies:

```bash
pip install -r requirements.txt
```

## 🚀 Start the LED Sign Server
Run the following command inside home/pi:
```bash
./start_led.sh
```

This will start the LeetCode Leaderboard client, the main server, the led sign, and the website frontend.

Since this is using tmux, you can detach from the session by pressing `Ctrl+b` and then `d`.
To reattach to the session, run the following command:
```bash
tmux attach -t ledsign
```
To kill the session, run the following command in any of the terminal windows:
```bash
tmux kill-session -t ledsign
``` 
to navigate terminal windows, use `Ctrl+b` and then `arrow keys`.

If one doesnt want to run you can also run the following commands separately:

```bash
cd ~/leetcode-leaderboard && source leetcode-led/bin/activate && cd core_files && python3 leetcode_client.py
```
```bash
cd ~/leetcode-leaderboard && source leetcode-led/bin/activate && cd core_files && python3 main.py
```
```bash
cd ~/leetcode-leaderboard && source leetcode-led/bin/activate && cd RGBMatrixEmulator/samples && python3 leaderboard.py --led-rows=128 --led-cols=64 --led-chain=2
```
```bash
cd ~/leetcode-leaderboard/led-matrix-sce/src && npm run dev
```
```bash
sudo ./text-example --led-rows=64 --led-cols=64 --led-chain=4 --led-gpio-mapping=adafruit-hat --led-slowdown-gpio=4 --led-pixel-mapper="U-mapper"
```

Author - Oliver Majano
Contact - olivermajano01@gmail.com

## Samples
### This is to display the general meeting flyer
sudo ./utils/led-image-viewer --led-rows=64 --led-cols=64 --led-chain=4 --led-gpio-mapping=adafruit-hat --led-slowdown-gpio=4 --led-pixel-mapper="U-mapper" flyer.png
### This is to display sce logo
sudo ./utils/led-image-viewer --led-rows=64 --led-cols=64 --led-chain=4 --led-gpio-mapping=adafruit-hat --led-no-hardware-pulse --led-slowdown-gpio=4 --led-pixel-mapper="U-mapper" Nathan-led-scaled.png



convert sce_logo_2.png -resize 128x128! sce_logo_display.png


ffmpeg -i video_1.mp4 -vf "fps=24,scale=128:128" frames/frame_%04d.ppmcd