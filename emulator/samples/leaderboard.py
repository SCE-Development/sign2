#!/usr/bin/env python
import requests
import json
import time
from samplebase import SampleBase
import os
# Set the emulator to bind to the Raspberry Pi's IP address
from RGBMatrixEmulator import graphics
MAIN_URL='http://backend:8000/'

months_mapping = {
    0: "January",
    1: "February",
    2: "March",
    3: "April",
    4: "May",
    5: "June",
    6: "July",
    7: "August",
    8: "September",
    9: "October",
    10: "November",
    11: "December"
}

class LeaderboardDisplay(SampleBase):
    def __init__(self, *args, **kwargs):
        super(LeaderboardDisplay, self).__init__(*args, **kwargs)
        
        # Display configuration
        self.DISPLAY_WIDTH = 64
        self.DISPLAY_HEIGHT = 64
        
        # Text positioning
        self.TITLE_Y = 6
        self.SUBTITLE_Y = 16
        self.ENTRIES_START_Y = 26
        self.ENTRY_SPACING = 8
        self.LEFT_MARGIN = 2

        # Max entries to display
        self.MAX_ENTRIES = 10

    def fetch_leaderboard(self):
        """Fetch leaderboard data from API."""
        try:
            response = requests.get(MAIN_URL)
            data = response.json()  # Expecting a list of dicts
            leaderboard = data.get("leaderboard", [])
            month = data.get("month", -1)
            # Extract just username + points for each entry
            leaderboard = [
                {
                    "username": entry.get("username", "unknown"),
                    "points": entry.get("points", 0)
                }
                for entry in leaderboard
            ]
            return {"leaderboard": leaderboard, "month": month}
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
                offset_canvas.Clear()

                # 1) Title line
                graphics.DrawText(
                    offset_canvas, font,
                    self.LEFT_MARGIN, self.TITLE_Y,
                    yellow, " LeetCode Leaderboard"
                )

                # 2) Header line: "Username    Points"
                graphics.DrawText(
                    offset_canvas, font,
                    self.LEFT_MARGIN, self.SUBTITLE_Y,
                    white, "Username        Points"
                )

                # 3) Loop over top 5 entries
                y_pos = self.ENTRIES_START_Y
                try:
                    leaderboard_data = self.fetch_leaderboard()
                    leaderboard = leaderboard_data['leaderboard']
                    month = leaderboard_data['month']
                    for i, entry in enumerate(leaderboard, start=1):
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

                    if month in months_mapping:
                        graphics.DrawText(
                            offset_canvas, font,
                            self.LEFT_MARGIN, y_pos,
                            white, f"Month: {months_mapping[month]}"
                        )

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
