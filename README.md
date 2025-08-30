# SCE LED Matrix

The SCE LED Matrix is an SCE intern project for Winter 2024. The matrix consists of four interconnected LED panels, controlled by a Raspberry Pi.  
This repository contains code and resources for controlling and managing the SCE LED Matrix Display. The below is a description of the layout of this repository.

## Building Sign Binary
```sh
# from the project folder, clone rpi-rgb-led-matrix into cc
git clone https://github.com/hzeller/rpi-rgb-led-matrix.git ./cc/rpi-rgb-led-matrix

# go into the new repo located in cc
cd ./cc/rpi-rgb-led-matrix

# compile everything
make all

# go back into cc
cd ..

# compile sign binary
make all
```

Now to run the binary, from the project's root
```
sudo nohup ./cc/text-example \
    --led-rows=64 \
    --led-cols=64 \
    --led-chain=4 \
    --led-gpio-mapping=adafruit-hat \
    --led-slowdown-gpio=4 \
    --led-pixel-mapper=U-mapper \
    --led-slowdown-us=10 &
```

## How To Run The Server From the Raspberry Pi
1. To run the backend and the emulator: `docker compose -f docker-compose.yml up --build`. 

## How LeetCode Leaderboard Stats Are Calculated
Our leaderboard pulls metrics directly from LeetCode's GraphQL API, querying for all registered users' easy, medium, and hard problems solved. In the server, a thread performs this API call once every polling period, which can be set by the configuration script. After every poll, the users' stats are stored as a snapshot in an SQLite database, with weekly stats being calculated by the difference between the latest snapshot and the earliest snapshot from this week. While these values can be changed, the default point values are 1 point for an easy problem, 3 points for a medium, and 5 points for a hard.