#!/bin/bash

tmux new-session -d -s ledmatrix

tmux send-keys -t ledmatrix "docker compose -f docker-compose.yml up --build" C-m

tmux split-window -h -t ledmatrix

tmux send-keys -t ledmatrix "sleep 10 && sudo ./text-example --led-rows=64 --led-cols=64 --led-chain=4 --led-gpio-mapping=adafruit-hat --led-slowdown-gpio=4 --led-pixel-mapper=U-mapper --led-slowdown-us=10" C-m

tmux attach -t ledmatrix
