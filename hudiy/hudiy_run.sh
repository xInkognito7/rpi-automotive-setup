#!/bin/bash
export WAYLAND_DISPLAY=wayland-0
export XDG_RUNTIME_DIR=/run/user/1000
export LD_LIBRARY_PATH=/home/pi/.hudiy/share:$LD_LIBRARY_PATH
export QT_QPA_PLATFORM=wayland

cd /home/pi/.hudiy/share
./hudiy_startup.sh
