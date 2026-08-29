#!/usr/bin/env python3
import time
import os
import sys
import can

CAN_CHANNEL = 'can0'
CAN_BITRATE = 100000

# 0x359 Byte 0, Bit 1 (Maske 0x02) signalisiert den aktiven Rückwärtsgang
REVERSE_CAN_ID = 0x359
REVERSE_BITMASK = 0x02

# Hysterese: Sekunden, die nach dem Gang-Rausnehmen gewartet wird, bevor AA zurückkehrt
HYSTERESIS_SECONDS = 2.0

def set_video_output(enable: bool):
    """
    Kappt bzw. reaktiviert das Videosignal/Sync.
    vcgencmd display_power steuert den Display-Controller / HDMI / TV-DAC direkt an.
    """
    state = 1 if enable else 0
    os.system(f"vcgencmd display_power {state} > /dev/null 2>&1")

def main():
    try:
        bus = can.interface.Bus(channel=CAN_CHANNEL, bustype='socketcan')
    except Exception as e:
        print(f"[OPS-Switcher] Fehler beim Initialisieren von {CAN_CHANNEL}: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"[OPS-Switcher] Aktiv auf {CAN_CHANNEL}. Überwache ID {hex(REVERSE_CAN_ID)}...")
    
    reverse_active = False
    disengage_timestamp = None

    while True:
        # Kurzer Timeout, damit die Zeitschleife auch ohne neue CAN-Frames weiterläuft
        msg = bus.recv(timeout=0.1)

        if msg is not None and msg.arbitration_id == REVERSE_CAN_ID:
            if len(msg.data) > 0:
                is_reverse = bool(msg.data[0] & REVERSE_BITMASK)

                if is_reverse:
                    disengage_timestamp = None
                    if not reverse_active:
                        print("[OPS-Switcher] Rückwärtsgang erkannt -> Video AUS (RNS-E OPS aktiv)")
                        set_video_output(False)
                        reverse_active = True
                else:
                    if reverse_active and disengage_timestamp is None:
                        disengage_timestamp = time.time()

        # Hysterese-Prüfung zum Reaktivieren des Android Auto Bildes
        if reverse_active and disengage_timestamp is not None:
            if (time.time() - disengage_timestamp) >= HYSTERESIS_SECONDS:
                print("[OPS-Switcher] Rückwärtsgang inaktiv (Timeout vorbei) -> Video AN (Android Auto)")
                set_video_output(True)
                reverse_active = False
                disengage_timestamp = None

if __name__ == '__main__':
    main()
