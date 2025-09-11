#!/usr/bin/env python
import requests
import json
import time
from samplebase import SampleBase
import os
# Set the emulator to bind to the Raspberry Pi's IP address
from RGBMatrixEmulator import graphics
MAIN_URL='http://backend:8000/'

class LeaderboardDisplay(SampleBase):
    def __init__(self, *args, **kwargs):
        super(LeaderboardDisplay, self).__init__(*args, **kwargs)
        
        # Display configuration
        self.DISPLAY_WIDTH = 64
        self.DISPLAY_HEIGHT = 64
        
        # Text positioning
        self.TITLE_Y = 6
        self.SUBTITLE_Y = 16
        self.HEADER_Y = 26
        self.ENTRIES_START_Y = 36
        self.ENTRY_SPACING = 8
        self.LEFT_MARGIN = 2

        # Max entries to display
        self.MAX_ENTRIES = 10
        
        # Switching configuration
        self.SWITCH_INTERVAL = 300  # 5 minutes in seconds
        self.last_switch_time = time.time()
        self.current_view = "weekly"  # Start with weekly view

    def switch_view_if_needed(self):
        """Switch between weekly and monthly views every 5 minutes."""
        current_time = time.time()
        if current_time - self.last_switch_time >= self.SWITCH_INTERVAL:
            if self.current_view == "weekly":
                self.current_view = "monthly"
            else:
                self.current_view = "weekly"
            self.last_switch_time = current_time
            print(f"Switched to {self.current_view} view")

    def fetch_leaderboard(self):
        """Fetch leaderboard data from API."""
        try:
            # Determine endpoint based on current view
            if self.current_view == "weekly":
                endpoint = f"{MAIN_URL}weekly"
            else:
                endpoint = f"{MAIN_URL}monthly"
                
            response = requests.get(endpoint)
            data = response.json()  # Expecting a list of dicts
            print(f"Fetched {self.current_view} data:", data)
            # Extract just username + points for each entry
            return [
                {
                    "username": entry.get("user", "unknown"),
                    "points": entry.get("points", 0)
                }
                for entry in data
            ]
        except Exception as e:
            print(f"Error fetching leaderboard: {e}")
            return self.get_sample_data()

    def get_sample_data(self):
        """Fallback data if API fails."""
        return [
            {"username": "User1", "points": 100},
            {"username": "User2", "points": 80},
            {"username": "User3", "points": 60},
            {"username": "User4", "points": 40},
            {"username": "User5", "points": 20}
        ]

    def run(self):
        offset_canvas = self.matrix.CreateFrameCanvas()
        font = graphics.Font()
        # Load a 5x7 or 6x10 font, etc., as you prefer
        font.LoadFont("./fonts/5x7.bdf")
        white = graphics.Color(255, 255, 255)
        yellow = graphics.Color(255,191,0)
        red = graphics.Color(255,0,0)
        blue = graphics.Color(126, 147, 255)

        try:
            while True:
                # Check if we need to switch views
                self.switch_view_if_needed()
                
                offset_canvas.Clear()

                # 1) Title line
                graphics.DrawText(
                    offset_canvas, font,
                    self.LEFT_MARGIN, self.TITLE_Y,
                    yellow, " LeetCode Leaderboard"
                )

                # 2) Subtitle showing current view type
                subtitle_text = f"     {self.current_view.title()} Stats"
                graphics.DrawText(
                    offset_canvas, font,
                    self.LEFT_MARGIN, self.SUBTITLE_Y,
                    blue, subtitle_text
                )

                # 3) Header line: "Username    Points"
                graphics.DrawText(
                    offset_canvas, font,
                    self.LEFT_MARGIN, self.HEADER_Y,
                    white, "Username       Points"
                )

                # 3) Loop over top 10 entries
                y_pos = self.ENTRIES_START_Y
                try:
                    leaderboard_data = self.fetch_leaderboard()
                    for i, entry in enumerate(leaderboard_data, start=1):
                        if i > self.MAX_ENTRIES:
                            break

                        username = entry["username"][:10]  # Limit username to 10 characters
                        points   = entry["points"]

                        # Determine color based on rank
                        if i == 1:
                            color = yellow  # First place
                        elif i == 2:
                            color = red     # Second place
                        elif i == 3:
                            color = blue    # Third place
                        else:
                            color = white   # Everyone else

                        # Format: "1. steeevin88   864"
                        text = f"{i}. {username:<13} {points:>4}"  # Adjust formatting for right alignment
                        if i < 10:
                            text = " " + text # super scuffed way to space it right
                        graphics.DrawText(
                            offset_canvas, font,
                            self.LEFT_MARGIN, y_pos,
                            color, text
                        )
                        y_pos += self.ENTRY_SPACING

                except Exception as e:
                    print(f"Error processing leaderboard: {e}")
                    graphics.DrawText(
                        offset_canvas, font,
                        self.LEFT_MARGIN, y_pos,
                        white, "ERROR"
                    )

                # Swap buffers, sleep 60s
                offset_canvas = self.matrix.SwapOnVSync(offset_canvas)
                time.sleep(60)

        except KeyboardInterrupt:
            return


if __name__ == "__main__":
    leaderboard_display = LeaderboardDisplay()
    if not leaderboard_display.process():
        leaderboard_display.print_help()
