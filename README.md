# nixietube-clock
Clock control software with mpd support for the raspberrypi nixietube board from cathode creations.

nixietube-clock was written to control the RaspberryPi nixie tube from cathode creations, on a raspberrypi.

It could easily be modified to provide the functionalty to some other display, by replacing nixieString() with a 
function that displays on a different output device.

I've used the mpd integration with mopidy, but it should work with any mpd server local or remote.

## Features
- Displays time
- Periodically scrolls in Date Display
- If MPD server is playing music displays songs number and percent complete
- Displays volume setting if MPD changes volume

## Setup
1. Install dependencies
    - Python
    - python-mpd (if mpd integration desired)
    - RPi.GPIO 
2. Customize configuration
    - $EDITOR nixietube-clock.py
    - $EDITOR nixietube-clock.service
3. Copy script to install path
    - sudo cp nixietube-clock.py /usr/local/bin/
    - sudo chmod a+x /usr/local/bin/nixietube-clock.py
4. Copy systemd service file into system config
    - sudo cp nixietube-clock.service /etc/systemd/system/multi-user.target.wants
5. Have systemd load and start service
    - sudo systemctl daemon-reload
    - sudo systemctl start nixietube-clock.service

## ToDo
- [ ] Add requirements.txt file [https://pip.readthedocs.io/en/1.1/requirements.html]
- [ ] Do not update display if nothing changed
- [ ] Replace regular interval sleeps with calculated sleep until next expected display update
- [ ] Consider prebuffering display on wake-up then calculate afterward.
- [ ] Add command line arguments to control configurable parameters i.e. mpdhostname, port
- [ ] Add Weather reports
- [x] Add display to stdout, if requested or RPi.GPIO unavailable
- [ ] Come up with better song playback display
- [ ] When playback detected, periodically show time
- [ ] Remove old nixietube board demo options

