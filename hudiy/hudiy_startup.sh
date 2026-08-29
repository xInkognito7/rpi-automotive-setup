#!/bin/bash

EC_SINK="echo_cancel_sink"
EC_SOURCE="echo_cancel_source"
EQ_SINK="hudiy_equalizer_sink"

sink_exists() { pactl list short sinks 2>/dev/null | awk '{print $2}' | grep -Fxq "$1"; }
until pactl info >/dev/null 2>&1; do sleep 0.1; done

# Gives PipeWire and WirePlumber additional time to detect all audio devices
sleep 1

sink_exists "$EQ_SINK" || pactl load-module module-ladspa-sink sink_name="$EQ_SINK" master="$EC_SINK" plugin=hudiy_equalizer label=hudiy_equalizer control=0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
sink_exists "$EC_SINK" || pactl load-module module-echo-cancel aec_method=webrtc aec_args=\"voice_detection=false\" source_name="$EC_SOURCE" sink_name="$EC_SINK"

pactl set-default-sink "$EQ_SINK"
pactl set-default-source "$EC_SOURCE"

$HOME/.hudiy/share/hudiy &
