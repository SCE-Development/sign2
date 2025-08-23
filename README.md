## game plan
### cc binary that displays leaderboard
```sh
sudo ./text-example \
    --led-rows=64 \
    --led-cols=64 \
    --led-chain=4 \
    --led-gpio-mapping=adafruit-hat \
    --led-slowdown-gpio=4 \
    --led-pixel-mapper="U-mapper" \
    --led-slowdown-us=10
```
