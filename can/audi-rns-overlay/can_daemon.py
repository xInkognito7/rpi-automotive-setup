#!/usr/bin/env python3
import math
import logging
import threading
import os
import gi

# Display-Umgebungsvariablen
os.environ["DISPLAY"] = ":0"
os.environ["WAYLAND_DISPLAY"] = "wayland-0"
os.environ["XDG_RUNTIME_DIR"] = "/run/user/1000"

gi.require_version("Gst", "1.0")
gi.require_version("GstVideo", "1.0")
from gi.repository import Gst, GLib
import cairo
import can

CAN_INTERFACE = "can0"  # Am Schreibtisch "vcan0", im Auto "can0"
USE_DUMMY_VIDEO = False   # True = Testbild/Hintergrundbild, False = /dev/video0
BG_IMAGE_PATH = "/home/pi/audi-rns-overlay/camera_bg.jpg"
CAR_PNG_PATH = "/home/pi/audi-rns-overlay/car_top.png"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class AudiMmiOverlay:
    def __init__(self):
        Gst.init(None)
        self.steering_angle = 0.0
        # 8 Sensoren: [Front LA, Front ML, Front MR, Front RA, Heck LA, Heck ML, Heck MR, Heck RA]
        # Distanz 0.0 (Frei) bis 1.0 (Kritischer Nahbereich)
        self.pdc_distances = [0.0] * 8
        self.pipeline = None
        self.is_running = False
        self.loop = None
        self.thread = None

        self.car_surface = None
        if os.path.exists(CAR_PNG_PATH):
            try:
                self.car_surface = cairo.ImageSurface.create_from_png(CAR_PNG_PATH)
                logging.info(f"Fahrzeuggrafik geladen: {CAR_PNG_PATH}")
            except Exception as e:
                logging.error(f"Fehler beim Laden von {CAR_PNG_PATH}: {e}")

    def draw_pdc_zone(self, context, car_cx, car_cy, is_rear=False):
        """Zeichnet nahtlos anliegende PDC-Flaechen mit OEM-Stufenkontur"""
        y_center = car_cy + (50.0 if is_rear else -50.0)
        r_in = 41.0

        if is_rear:
            ang_splits = [math.radians(a) for a in [160.0, 125.0, 90.0, 55.0, 20.0]]
            offset_idx = 4
            r_out_list = [65.0, 82.0, 82.0, 65.0]
        else:
            ang_splits = [math.radians(a) for a in [200.0, 235.0, 270.0, 305.0, 340.0]]
            offset_idx = 0
            r_out_list = [65.0, 82.0, 82.0, 65.0]

        # 1. Segmente zeichnen
        for i in range(4):
            r_out = r_out_list[i]
            a1 = ang_splits[i]
            a2 = ang_splits[i + 1]

            grad = cairo.RadialGradient(car_cx, y_center, r_in, car_cx, y_center, r_out)
            grad.add_color_stop_rgba(0.0, 0.28, 0.30, 0.33, 0.65)
            grad.add_color_stop_rgba(0.70, 0.16, 0.18, 0.20, 0.55)
            grad.add_color_stop_rgba(1.0, 0.04, 0.04, 0.05, 0.72)

            context.new_path()
            if is_rear:
                context.arc(car_cx, y_center, r_out, a2, a1)
                context.arc_negative(car_cx, y_center, r_in, a1, a2)
            else:
                context.arc(car_cx, y_center, r_out, a1, a2)
                context.arc_negative(car_cx, y_center, r_in, a2, a1)
            context.close_path()
            context.set_source(grad)
            context.fill_preserve()

            context.set_line_width(1.1)
            context.set_source_rgba(0.06, 0.07, 0.08, 0.85)
            context.stroke()

        # 2. Trennlinien
        context.set_line_width(1.5)
        context.set_source_rgba(0.04, 0.04, 0.05, 0.95)
        for i in range(1, 4):
            a = ang_splits[i]
            r_out_step = min(r_out_list[i-1], r_out_list[i])
            context.move_to(car_cx + r_in * math.cos(a), y_center + r_in * math.sin(a))
            context.line_to(car_cx + r_out_step * math.cos(a), y_center + r_out_step * math.sin(a))
            context.stroke()

        # 3. Aktive Distanzbalken
        context.set_line_width(6.0)
        context.set_line_cap(cairo.LINE_CAP_BUTT)

        for i in range(4):
            dist = self.pdc_distances[offset_idx + i]
            if dist > 0.05:
                r_out = r_out_list[i]
                r_dist = r_out - dist * (r_out - r_in - 3.0)

                if dist >= 0.75:
                    context.set_source_rgba(0.96, 0.15, 0.15, 0.98) # Rot
                else:
                    context.set_source_rgba(0.98, 0.98, 1.0, 0.98) # Kaltweiss

                context.new_path()
                if is_rear:
                    context.arc(car_cx, y_center, r_dist, ang_splits[i+1], ang_splits[i])
                else:
                    context.arc(car_cx, y_center, r_dist, ang_splits[i], ang_splits[i+1])
                context.stroke()

    def draw_overlay(self, overlay, context, timestamp, duration):
        w = 800.0
        h = 480.0

        # --- 1. OPS Fahrzeugdarstellung & PDC ---
        car_cx = 100.0
        car_cy = 236.0
        target_w = 88.0

        self.draw_pdc_zone(context, car_cx, car_cy, is_rear=False)
        self.draw_pdc_zone(context, car_cx, car_cy, is_rear=True)

        if self.car_surface:
            context.save()
            img_w = self.car_surface.get_width()
            img_h = self.car_surface.get_height()
            scale_factor = target_w / float(img_w)
            
            draw_x = car_cx - (target_w / 2.0)
            draw_y = car_cy - ((img_h * scale_factor) / 2.0)

            context.translate(draw_x, draw_y)
            context.scale(scale_factor, scale_factor)
            context.set_source_surface(self.car_surface, 0, 0)
            context.paint_with_alpha(0.70)
            context.restore()

        # --- 2. Statischer Bereich ---
        y_bottom = h * 0.81
        y_top = h * 0.28
        
        base_half_w = w * 0.335
        top_half_w = w * 0.110
        center_x = w * 0.50

        t_splits = [0.0, 0.28, 0.52, 0.73, 0.88, 1.0]
        alpha_levels = [0.58, 0.35, 0.14, 0.0, 0.0]

        def get_static_points(t):
            y = y_bottom - t * (y_bottom - y_top)
            cur_half_w = base_half_w - t * (base_half_w - top_half_w)
            return (center_x - cur_half_w, y), (center_x + cur_half_w, y)

        for s in range(5):
            if alpha_levels[s] > 0.0:
                p1_l, p1_r = get_static_points(t_splits[s])
                p2_l, p2_r = get_static_points(t_splits[s+1])

                context.new_path()
                context.move_to(p1_l[0], p1_l[1])
                context.line_to(p2_l[0], p2_l[1])
                context.line_to(p2_r[0], p2_r[1])
                context.line_to(p1_r[0], p1_r[1])
                context.close_path()

                context.set_source_rgba(0.06, 0.36, 0.98, alpha_levels[s])
                context.fill()

        context.set_line_width(3.2)
        context.set_source_rgba(0.15, 0.46, 1.0, 0.95)

        p_start_l, p_start_r = get_static_points(0.0)
        p_end_l, p_end_r = get_static_points(1.0)

        context.move_to(p_start_l[0], p_start_l[1])
        context.line_to(p_end_l[0], p_end_l[1])
        context.stroke()

        context.move_to(p_start_r[0], p_start_r[1])
        context.line_to(p_end_r[0], p_end_r[1])
        context.stroke()

        tick_len = 10.0
        for tf in t_splits[1:]:
            (lx, ly), (rx, ry) = get_static_points(tf)
            context.move_to(lx, ly)
            context.line_to(lx + tick_len, ly)
            context.stroke()

            context.move_to(rx, ry)
            context.line_to(rx - tick_len, ry)
            context.stroke()

        context.set_line_width(2.0)
        context.set_source_rgba(0.95, 0.15, 0.15, 0.90)
        context.move_to(p_start_l[0], p_start_l[1])
        context.line_to(p_start_r[0], p_start_r[1])
        context.stroke()

        # --- 3. Dynamische Fuehrungsschienen ---
        steer_factor = self.steering_angle / 540.0
        max_bend = w * 0.46
        base_shift = steer_factor * (w * 0.055)

        num_segments = 70
        dyn_left = []
        dyn_right = []

        t_min = -0.09
        t_max = 1.0

        for i in range(num_segments + 1):
            t = t_min + (i / float(num_segments)) * (t_max - t_min)
            y = y_bottom - t * (y_bottom - y_top)
            cur_half_w = base_half_w - t * (base_half_w - top_half_w)
            
            t_eff = max(0.0, t)
            bend_offset = base_shift + (steer_factor * max_bend * (0.65 * (t_eff ** 2.2) + 0.35 * t_eff))
            width_adj = 1.0 - (abs(steer_factor) * 0.12 * t_eff)
            dyn_cx = center_x + bend_offset

            dyn_left.append((dyn_cx - cur_half_w * width_adj, y))
            dyn_right.append((dyn_cx + cur_half_w * width_adj, y))

        context.set_line_width(5.5)
        context.set_line_cap(cairo.LINE_CAP_ROUND)
        context.set_line_join(cairo.LINE_JOIN_ROUND)
        context.set_source_rgba(1.0, 0.56, 0.04, 0.98)

        context.move_to(dyn_left[0][0], dyn_left[0][1])
        for p in dyn_left[1:]:
            context.line_to(p[0], p[1])
        context.stroke()

        context.move_to(dyn_right[0][0], dyn_right[0][1])
        for p in dyn_right[1:]:
            context.line_to(p[0], p[1])
        context.stroke()

        # --- 4. Bottom Bar ---
        bar_height = 46.0
        context.set_source_rgba(0.0, 0.0, 0.0, 1.0)
        context.rectangle(0.0, h - bar_height, w, bar_height)
        context.fill()

        context.set_line_width(1.5)
        context.set_source_rgba(1.0, 1.0, 1.0, 0.18)
        context.move_to(0.0, h - bar_height)
        context.line_to(w, h - bar_height)
        context.stroke()

        # --- 5. Warnhinweis ---
        warn_text = "Fahrweg kontrollieren!"
        context.select_font_face("Roboto", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        context.set_font_size(17.0)
        text_extents = context.text_extents(warn_text)

        tri_w = 23.0
        tri_h = 20.0
        gap = 11.0
        total_w = tri_w + gap + text_extents.width
        start_x = (w - total_w) / 2.0
        center_y = h - (bar_height / 2.0)

        tri_top_x = start_x + (tri_w / 2.0)
        tri_top_y = center_y - (tri_h / 2.0) + 1.0
        tri_bot_y = center_y + (tri_h / 2.0) + 1.0

        context.move_to(tri_top_x, tri_top_y)
        context.line_to(start_x + tri_w, tri_bot_y)
        context.line_to(start_x, tri_bot_y)
        context.close_path()
        context.set_source_rgba(1.0, 1.0, 1.0, 1.0)
        context.fill_preserve()

        context.set_line_width(2.2)
        context.set_line_join(cairo.LINE_JOIN_ROUND)
        context.set_source_rgba(0.95, 0.15, 0.15, 1.0)
        context.stroke()

        context.select_font_face("monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        context.set_font_size(13.0)
        excl_extents = context.text_extents("!")
        
        centroid_y = (tri_top_y + 2.0 * tri_bot_y) / 3.0
        excl_x = tri_top_x - excl_extents.x_bearing - (excl_extents.width / 2.0)
        excl_y = centroid_y - excl_extents.y_bearing - (excl_extents.height / 2.0) - 0.5

        context.set_source_rgba(0.0, 0.0, 0.0, 1.0)
        context.move_to(excl_x, excl_y)
        context.show_text("!")

        context.select_font_face("Roboto", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        context.set_font_size(17.0)
        context.set_source_rgba(0.95, 0.22, 0.22, 1.0)
        context.move_to(start_x + tri_w + gap, center_y - text_extents.y_bearing - (text_extents.height / 2.0))
        context.show_text(warn_text)

    def start(self):
        if self.is_running:
            return
        self.is_running = True

        if USE_DUMMY_VIDEO:
            if os.path.exists(BG_IMAGE_PATH):
                src = f"filesrc location={BG_IMAGE_PATH} ! jpegdec ! imagefreeze ! videoconvert ! videoscale ! video/x-raw,width=800,height=480,framerate=30/1"
            else:
                src = "videotestsrc pattern=smpte ! video/x-raw,width=800,height=480,framerate=30/1"
        else:
            src = (
                "v4l2src device=/dev/video0 ! "
                "videoconvert ! "
                "deinterlace mode=auto method=linear ! "
                "videocrop top=20 bottom=20 left=2 right=2 ! "
                "videoscale add-borders=false ! "
                "video/x-raw,width=800,height=480,pixel-aspect-ratio=1/1 ! "
                "videoconvert"
            )

        pipe_desc = f"{src} ! cairooverlay name=overlay ! videoconvert ! waylandsink fullscreen=true sync=false"

        try:
            self.pipeline = Gst.parse_launch(pipe_desc)
        except Exception:
            pipe_desc = f"{src} ! cairooverlay name=overlay ! videoconvert ! autovideosink sync=false"
            self.pipeline = Gst.parse_launch(pipe_desc)

        cairo_elem = self.pipeline.get_by_name("overlay")
        cairo_elem.connect("draw", self.draw_overlay)

        self.pipeline.set_state(Gst.State.PLAYING)
        logging.info("Kamera gestartet.")

        self.loop = GLib.MainLoop()
        self.thread = threading.Thread(target=self.loop.run)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        if not self.is_running:
            return
        self.is_running = False
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline = None
        if self.loop:
            self.loop.quit()
        logging.info("Kamera gestoppt.")

def convert_kline_cm_to_dist(raw_cm):
    """
    Konvertiert die Messwerte des 8E0-919-283 Steuergeraets (in cm) in 0.0..1.0
    0xFF / 0xFE = Kein Hindernis
    200 cm (Fernbereich) bis <= 30 cm (Dauerton / kritischer Nahbereich)
    """
    if raw_cm in [0xFF, 0xFE, 0x00]:
        return 0.0
    dist = 1.0 - ((raw_cm - 30.0) / (200.0 - 30.0))
    return min(1.0, max(0.05, dist))

def can_listener(overlay):
    try:
        bus = can.interface.Bus(channel=CAN_INTERFACE, bustype="socketcan")
        logging.info(f"CAN verbunden mit {CAN_INTERFACE}")
    except Exception as e:
        logging.error(f"CAN-Fehler: {e}")
        return

    current_gear = 0
    while True:
        msg = bus.recv(0.5)
        if not msg:
            continue

        # 1. Rueckwaertsgang (ID 0x351, Byte 0 = 'R' = 0x52 oder 0x02)
        if msg.arbitration_id == 0x351 and len(msg.data) >= 1:
            is_rev = (msg.data[0] == 0x52) or (msg.data[0] == 0x02) or (msg.data[0] == ord('R'))
            if is_rev and current_gear != 1:
                current_gear = 1
                overlay.start()
            elif not is_rev and current_gear != 0:
                current_gear = 0
                overlay.stop()

        # 2. Lenkwinkel (Antriebs-CAN 0x0C0)
        elif msg.arbitration_id == 0x0C0 and len(msg.data) >= 3:
            raw_angle = (msg.data[2] << 8) | msg.data[1]
            if raw_angle & 0x8000:
                raw_angle -= 0x10000
            overlay.steering_angle = raw_angle * 0.04375

        # 3. OPS Sensordaten vom Arduino (ID 0x6DA)
        elif msg.arbitration_id == 0x6DA and len(msg.data) >= 6:
            cmd = msg.data[1]
            if cmd == 0x92: # Front
                for i in range(4):
                    overlay.pdc_distances[i] = convert_kline_cm_to_dist(msg.data[2 + i])
            elif cmd == 0x93: # Heck
                for i in range(4):
                    overlay.pdc_distances[4 + i] = convert_kline_cm_to_dist(msg.data[2 + i])

if __name__ == "__main__":
    overlay = AudiMmiOverlay()
    listener_thread = threading.Thread(target=can_listener, args=(overlay,), daemon=True)
    listener_thread.start()

    try:
        while True:
            threading.Event().wait(1.0)
    except KeyboardInterrupt:
        overlay.stop()
