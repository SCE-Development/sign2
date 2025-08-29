
# SCE LED Matrix

The SCE LED Matrix is an SCE intern project for Winter 2024. The matrix consists of four interconnected LED panels, controlled by a Raspberry Pi.  
This repository contains code and resources for controlling and managing the SCE LED Matrix Display. The below is a description of the layout of this repository.


## How To Run The Project From the Raspberry Pi
1. To run the backend and the emulator: `docker compose up --build`. 
2. To run the LED sign: `./start_led.sh`.


## How LeetCode Leaderboard Stats Are Calculated
Our leaderboard pulls metrics directly from LeetCode's GraphQL API, querying for all registered users' easy, medium, and hard problems solved. In the server, a thread performs this API call once every polling period, which can be set by the configuration script. After every poll, the users' stats are stored as a snapshot in an SQLite database, with weekly stats being calculated by the difference between the latest snapshot and the earliest snapshot from this week. While these values can be changed, the default point values are 1 point for an easy problem, 3 points for a medium, and 5 points for a hard.
