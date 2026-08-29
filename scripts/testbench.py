import zmq, json, time, threading

ctx = zmq.Context()

# 1. CAN Publisher (bindet den IPC-Pfad)
pub = ctx.socket(zmq.PUB)
pub.bind("ipc:///run/rnse_control/can_stream.ipc")

# 2. Draw Receiver (PULL socket simuliert den dis_draw daemon)
draw_sub = ctx.socket(zmq.PULL)
draw_sub.bind("ipc:///run/rnse_control/dis_draw.ipc")

def draw_listener():
    screen = {1: "", 2: "", 3: "", 4: "", 5: ""}
    while True:
        try:
            msg = draw_sub.recv_json()
            cmd = msg.get("command")
            if cmd == "draw_text":
                y = msg.get("y", 0)
                line_idx = (y // 10) + 1
                screen[line_idx] = msg.get("text", "")
            elif cmd == "clear":
                screen = {1: "", 2: "", 3: "", 4: "", 5: ""}
            elif cmd == "commit":
                print("\n" + "="*25 + " FIS DISPLAY " + "="*25)
                for i in range(1, 6):
                    val = screen.get(i, "")
                    print(f"Zeile {i}: {val}")
                print("="*63 + "\nLenkrad-Aktion > ", end="", flush=True)
        except Exception:
            pass

threading.Thread(target=draw_listener, daemon=True).start()
time.sleep(0.5)

print("\n=== FIS TESTBENCH AKTIV (B8.5 Lenkrad 0x5C3) ===")
print("Tasten: [w] Scroll Up | [s] Scroll Down | [e] Enter Klick | [b] Enter Long-Press (Back) | [q] Beenden\n")

def send_can(payload_hex):
    msg = json.dumps({"data_hex": payload_hex})
    pub.send_multipart([b"CAN_0x5C3", msg.encode()])

while True:
    cmd = input("Lenkrad-Aktion > ").strip().lower()
    if cmd == "w":
        send_can("0000020000000000")
    elif cmd == "s":
        send_can("0000030000000000")
    elif cmd == "e":
        send_can("0000060000000000")
        time.sleep(0.08)
        send_can("0000000000000000")
    elif cmd == "b":
        send_can("0000060000000000")
        time.sleep(0.8)
        send_can("0000000000000000")
    elif cmd == "q":
        break
