import os
import time
import random
import math
import subprocess
import threading
import tkinter as tk
from src.config import (
    WIDTH, HEIGHT, BG, PANEL_BG, GREEN, GLOW_GREEN, DARK_GREEN,
    RED, AMBER, CYAN, DIM, TEXT_FG, FONT_FAMILY, REFRESH_DELAY_SEC
)
from src.image_loader import prepare_and_load_image
from src.network_isolator import isolate_target, restore_target, get_running_pids, attach_new_pids
from src.page_refresher import schedule_one_time_refresh


class ArcGhostUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ARC-GHOST :: Authorized Security Assessment Suite")
        self.root.geometry(f"{WIDTH}x{HEIGHT}")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.state = "standby"  # "standby", "attacking", "active", "stopping"
        self.anim_tick = 0
        self.packet_count = 0
        self.simulated_bandwidth = 0.0
        self.reticle_angle = 0.0
        self.logo_img = None
        self.scanner_x = 0
        self.particles = []
        self.auto_detect_active = False
        self.auto_detect_thread = None

        self.canvas = tk.Canvas(
            root, width=WIDTH, height=HEIGHT, bg=BG, highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        self.build_ui()
        self.start_animations()
        self.keep_sudo_alive()

    # --- UI Layout Assembly ---
    def build_ui(self):
        # 1. CRT Scanlines
        for y in range(0, HEIGHT, 4):
            self.canvas.create_line(0, y, WIDTH, y, fill="#040b05", width=1)

        # 2. Outer Cyber Shield Frame
        self.outer_frame = self.canvas.create_rectangle(
            6, 6, WIDTH - 6, HEIGHT - 6, outline=DARK_GREEN, width=2
        )

        # 3. Header Title
        self.header_title = self.canvas.create_text(
            WIDTH // 2, 36, text="A R C - G H O S T",
            fill=GLOW_GREEN, font=(FONT_FAMILY, 24, "bold")
        )
        self.canvas.create_text(
            WIDTH // 2, 62, text="AUTHORIZED SECURITY ASSESSMENT SUITE",
            fill=RED, font=(FONT_FAMILY, 8, "bold")
        )
        self.canvas.create_line(30, 78, WIDTH - 30, 78, fill=GREEN, width=2)

        # 4. Target Avatar HUD Panel
        self.draw_cyber_panel(25, 88, WIDTH - 25, 335, "ATTACK VECTOR / AVATAR HUD")
        self.logo_img = prepare_and_load_image(max_w=WIDTH - 80, max_h=205)
        self.cx, self.cy = WIDTH // 2, 210

        if self.logo_img is not None:
            self.user_img_id = self.canvas.create_image(self.cx, self.cy, image=self.logo_img)
            w_half = self.logo_img.width() // 2 + 6
            h_half = self.logo_img.height() // 2 + 6
            self.avatar_frame = self.canvas.create_rectangle(
                self.cx - w_half, self.cy - h_half, self.cx + w_half, self.cy + h_half,
                outline=DARK_GREEN, width=2
            )
        else:
            self.canvas.create_polygon(
                self.cx - 60, self.cy + 40, self.cx + 60, self.cy + 40, self.cx + 40, self.cy - 70, self.cx, self.cy - 85, self.cx - 40, self.cy - 70,
                fill=PANEL_BG, outline=GREEN, width=2, smooth=True
            )
            self.canvas.create_text(
                self.cx, self.cy, text="[ ROBOT AVATAR READY ]", fill=DIM, font=(FONT_FAMILY, 9)
            )

        # Equalizer / Frequency Bar Visualizer
        self.eq_bars = []
        eq_y = 300
        for b in range(26):
            bx = 42 + b * 17
            bar_id = self.canvas.create_line(bx, eq_y, bx, eq_y - 5, fill=GREEN, width=3)
            self.eq_bars.append(bar_id)

        # Telemetry Info Bar
        self.canvas.create_rectangle(35, 308, WIDTH - 35, 328, fill="#031006", outline=DARK_GREEN)
        self.telemetry_text = self.canvas.create_text(
            WIDTH // 2, 318,
            text="TARGET: Firefox  |  FLOOD RATE: 0 Pkts/s  |  STATUS: Standby",
            fill=GREEN, font=(FONT_FAMILY, 8, "bold")
        )

        # 5. DDoS Attack Status Panel
        self.draw_cyber_panel(25, 345, WIDTH - 25, 465, "ATTACK CONTROL & STATUS")
        self.status_title = self.canvas.create_text(
            WIDTH // 2, 385, text="SYSTEM STANDBY", fill=GLOW_GREEN, font=(FONT_FAMILY, 21, "bold")
        )
        self.status_sub = self.canvas.create_text(
            WIDTH // 2, 422, text="Firefox traffic normal  •  WiFi online", fill=TEXT_FG, font=(FONT_FAMILY, 9)
        )
        self.vector_text = self.canvas.create_text(
            WIDTH // 2, 442, text="VECTORS: SYN Flood | UDP Storm | HTTP Header Burst", fill=DIM, font=(FONT_FAMILY, 8)
        )

        # 6. Terminal Session Log
        self.draw_cyber_panel(25, 475, WIDTH - 25, 700, "ATTACK LOG TERMINAL")
        self.term_frame = tk.Frame(self.root, bg="#010602", highlightbackground=DARK_GREEN, highlightthickness=1)
        self.term_frame.place(x=38, y=498, width=WIDTH - 76, height=192)

        self.terminal = tk.Text(
            self.term_frame, bg="#010602", fg=GLOW_GREEN, font=(FONT_FAMILY, 9),
            wrap="word", state="disabled", relief="flat", padx=8, pady=6
        )
        self.terminal.pack(fill="both", expand=True)

        # 7. Main Action Button
        btn_y = 725
        self.btn_bg = self.canvas.create_rectangle(
            WIDTH // 2 - 165, btn_y, WIDTH // 2 + 165, btn_y + 60,
            fill="#021406", outline=GLOW_GREEN, width=3
        )
        self.btn_scanner = self.canvas.create_line(
            WIDTH // 2 - 160, btn_y + 30, WIDTH // 2 - 140, btn_y + 30, fill=CYAN, width=3
        )
        self.btn_text = self.canvas.create_text(
            WIDTH // 2, btn_y + 30, text="LAUNCH DDoS ATTACK",
            fill=GLOW_GREEN, font=(FONT_FAMILY, 15, "bold")
        )

        for item in (self.btn_bg, self.btn_text):
            self.canvas.tag_bind(item, "<Button-1>", lambda e: self.on_action_click())
            self.canvas.tag_bind(item, "<Enter>", lambda e: self.on_hover(True))
            self.canvas.tag_bind(item, "<Leave>", lambda e: self.on_hover(False))

        # 8. Footer
        self.canvas.create_text(
            WIDTH // 2, 815, text="cgroup v2 + GID Top-Priority Filter  •  WiFi Preserved",
            fill=DIM, font=(FONT_FAMILY, 8)
        )
        self.draw_corner_brackets()

        self.log("> ARC-GHOST DDoS Attack Engine v2.3")
        self.log("> System initialized & ready.")

    # --- Cyberpunk Decorative Brackets ---
    def draw_cyber_panel(self, x1, y1, x2, y2, label):
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=PANEL_BG, outline="#071b0b", width=1)
        b_len = 12
        for cx, cy in [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]:
            xd = 1 if cx == x1 else -1
            yd = 1 if cy == y1 else -1
            self.canvas.create_line(cx, cy, cx + b_len * xd, cy, fill=GREEN, width=2)
            self.canvas.create_line(cx, cy, cx, cy + b_len * yd, fill=GREEN, width=2)

        lx = x1 + 16
        w = 8 * len(label) + 14
        self.canvas.create_rectangle(lx - 4, y1 - 8, lx + w, y1 + 8, fill=BG, outline="")
        self.canvas.create_text(lx + w / 2 - 4, y1, text=label, fill=AMBER, font=(FONT_FAMILY, 8, "bold"))

    def draw_corner_brackets(self):
        m, sz = 12, 22
        for cx, cy in [(m, m), (WIDTH - m, m), (m, HEIGHT - m), (WIDTH - m, HEIGHT - m)]:
            xd = 1 if cx < WIDTH // 2 else -1
            yd = 1 if cy < HEIGHT // 2 else -1
            self.canvas.create_line(cx, cy, cx + sz * xd, cy, fill=DARK_GREEN, width=1)
            self.canvas.create_line(cx, cy, cx, cy + sz * yd, fill=DARK_GREEN, width=1)

    # --- Hacker Animations Engine ---
    def start_animations(self):
        self.cols = WIDTH // 12
        self.drops = [random.randint(-25, 0) for _ in range(self.cols)]
        self.drop_ids = [[] for _ in range(self.cols)]
        self.animate_loop()

    def animate_loop(self):
        self.anim_tick += 1

        # 1. Matrix Digital Rain
        for i in range(0, self.cols, 2):
            if random.random() > 0.35:
                x = i * 12 + 6
                y = self.drops[i] * 14
                char = random.choice("0123456789ABCDEFGHJKMNPQRSTVWXYZ$%#@")
                color = RED if self.state == "active" and random.random() > 0.6 else random.choice([GREEN, CYAN, "#00aa44", "#004411"])
                tid = self.canvas.create_text(x, y, text=char, fill=color, font=(FONT_FAMILY, 9))
                self.canvas.tag_lower(tid)
                self.drop_ids[i].append(tid)

                if len(self.drop_ids[i]) > 7:
                    self.canvas.delete(self.drop_ids[i].pop(0))

                self.drops[i] += 1
                if self.drops[i] * 14 > HEIGHT and random.random() > 0.92:
                    self.drops[i] = random.randint(-15, 0)

        # 2. Equalizer / Frequency Bar Animation
        eq_y = 300
        for idx, bar in enumerate(self.eq_bars):
            if self.state == "active":
                h = random.randint(5, 26)
                color = RED if idx % 2 == 0 else AMBER
            elif self.state == "attacking" or self.state == "stopping":
                h = random.randint(10, 28)
                color = CYAN
            else:
                h = int(6 + 8 * math.sin(self.anim_tick * 0.2 + idx * 0.4))
                color = GREEN
            bx = 42 + idx * 17
            self.canvas.coords(bar, bx, eq_y, bx, eq_y - h)
            self.canvas.itemconfig(bar, fill=color)

        # 3. Dynamic DDoS Packet Flood Animation Particles
        if self.state == "active":
            if random.random() > 0.3:
                px = random.randint(40, WIDTH - 40)
                py = random.randint(110, 260)
                pid = self.canvas.create_oval(px - 2, py - 2, px + 2, py + 2, fill=RED, outline=AMBER)
                self.particles.append((pid, py, random.randint(4, 9)))

            new_particles = []
            for pid, py, speed in self.particles:
                py += speed
                if py < 340:
                    self.canvas.coords(pid, self.canvas.coords(pid)[0], py - 2, self.canvas.coords(pid)[2], py + 2)
                    new_particles.append((pid, py, speed))
                else:
                    self.canvas.delete(pid)
            self.particles = new_particles

            # Update Telemetry Counts
            self.packet_count += random.randint(15000, 50000)
            self.simulated_bandwidth = round(random.uniform(2.10, 4.80), 2)
            self.canvas.itemconfig(
                self.telemetry_text,
                text=f"TARGET: Firefox  |  FLOOD: {self.packet_count:,} Pkts/s  |  BW: {self.simulated_bandwidth} Gbps  |  ATTACK: ACTIVE"
            )

        # 4. Laser Scanner Effect on Action Button
        btn_x1 = WIDTH // 2 - 160
        btn_x2 = WIDTH // 2 + 160
        self.scanner_x = btn_x1 + ((self.anim_tick * 9) % (btn_x2 - btn_x1))
        btn_y = 755
        self.canvas.coords(self.btn_scanner, self.scanner_x, btn_y, self.scanner_x + 24, btn_y)
        scan_color = RED if self.state == "active" else (CYAN if self.state != "standby" else GLOW_GREEN)
        self.canvas.itemconfig(self.btn_scanner, fill=scan_color)

        # 5. Cyber Shield Pulse Border in Active Attack state
        if self.state == "active":
            pulse_val = (math.sin(self.anim_tick * 0.35) + 1.0) / 2.0
            border_color = RED if pulse_val > 0.4 else "#990033"
            self.canvas.itemconfig(self.outer_frame, outline=border_color, width=2)
            self.canvas.itemconfig(self.btn_bg, outline=RED)
        else:
            self.canvas.itemconfig(self.outer_frame, outline=DARK_GREEN, width=2)

        self.root.after(70, self.animate_loop)

    def on_hover(self, on):
        color = RED if self.state == "active" else GLOW_GREEN
        self.canvas.itemconfig(self.btn_bg, outline=color, width=4 if on else 3)

    def log(self, msg):
        self.terminal.config(state="normal")
        self.terminal.insert("end", msg + "\n")
        self.terminal.see("end")
        self.terminal.config(state="disabled")

    # --- Action Execution ---
    def on_action_click(self):
        if self.state == "standby":
            self.state = "attacking"
            self.canvas.itemconfig(self.btn_text, text="LAUNCHING ATTACK...")
            self.canvas.itemconfig(self.status_title, text="LAUNCHING DDoS...", fill=AMBER)
            self.canvas.itemconfig(self.status_sub, text="Initializing SYN/UDP packet flood...")

            def _isolate_task():
                pids, count = isolate_target()
                self.root.after(0, lambda: self.on_attack_complete(pids, count))

            self.play_log_sequence(
                [
                    "> Launching DDoS Attack against target...",
                    "> Target: Firefox process (cgroup v2 & GID top priority)",
                    "> Vector 1: TCP SYN Flood",
                    "> Vector 2: UDP Datagram Burst",
                    "> Vector 3: HTTP Request Storm",
                    "> SYSTEM WIFI: UNTOUCHED (100% Connected)",
                    "> TARGET FIREFOX NETWORK: BLOCKED & SEVERED",
                ],
                on_done=lambda: threading.Thread(target=_isolate_task, daemon=True).start()
            )

        elif self.state == "active":
            self.state = "stopping"
            self.canvas.itemconfig(self.btn_text, text="ENDING ATTACK...")
            self.canvas.itemconfig(self.status_title, text="ENDING DDoS...", fill=GLOW_GREEN)
            self.canvas.itemconfig(self.status_sub, text="Terminating packet flood...")

            def _restore_task():
                restore_target()
                self.root.after(0, self.on_restore_complete)

            self.play_log_sequence(
                [
                    "> Ceasing DDoS Attack...",
                    "> Removing top-priority iptables drop rules...",
                    "> Restoring network throughput to Firefox...",
                    "> TARGET STATUS: ONLINE",
                ],
                on_done=lambda: threading.Thread(target=_restore_task, daemon=True).start()
            )

    def play_log_sequence(self, lines, on_done, i=0):
        if i < len(lines):
            self.log(lines[i])
            self.root.after(220 + random.randint(0, 80), lambda: self.play_log_sequence(lines, on_done, i + 1))
        else:
            on_done()

    def on_attack_complete(self, pids, count):
        self.state = "active"
        self.canvas.itemconfig(self.status_title, text="[ DDoS ATTACK ACTIVE ]", fill=RED)
        if pids:
            self.canvas.itemconfig(self.status_sub, text=f"Flooding {count} active Firefox PIDs  •  Auto-Detect Active")
            self.log(f"> [ATTACK ACTIVE] Attached to {count} Firefox processes.")
            self.log(f"> PIDs: {', '.join(pids[:4])}{'...' if len(pids) > 4 else ''}")
        else:
            self.canvas.itemconfig(self.status_sub, text="DDoS Attack Active  •  Auto-Detect Active")

        self.canvas.itemconfig(self.btn_bg, outline=RED, fill="#200208")
        self.canvas.itemconfig(self.btn_text, fill=RED, text="END ATTACK")

        # Start 3-second delay page refresh on Firefox
        schedule_one_time_refresh(delay_sec=REFRESH_DELAY_SEC, log_callback=self.log)

        # Start Real-Time Auto-Detect scanner
        self.log("> [AUTO-DETECT] Real-time watcher enabled (0.5s process scanner active).")
        self.start_auto_detect()

    def start_auto_detect(self):
        self.auto_detect_active = True

        def _auto_detect_loop():
            while self.auto_detect_active and self.state == "active":
                try:
                    new_pids = attach_new_pids()
                    if new_pids:
                        pid_str = ", ".join(new_pids[:3]) + ("..." if len(new_pids) > 3 else "")
                        self.root.after(
                            0,
                            lambda p=pid_str: (
                                self.log(f"> [AUTO-DETECT] Captured new Firefox instance (PID: {p}) -> Isolated!"),
                                self.update_active_status()
                            )
                        )
                except Exception:
                    pass
                time.sleep(0.5)

        self.auto_detect_thread = threading.Thread(target=_auto_detect_loop, daemon=True)
        self.auto_detect_thread.start()

    def update_active_status(self):
        pids = get_running_pids()
        count = len(pids)
        if count > 0:
            self.canvas.itemconfig(self.status_sub, text=f"Flooding {count} active Firefox PIDs  •  Auto-Detect Active")
        else:
            self.canvas.itemconfig(self.status_sub, text="DDoS Attack Active  •  Waiting for Firefox launch...")

    def on_restore_complete(self):
        self.auto_detect_active = False
        self.state = "standby"
        self.packet_count = 0
        self.canvas.itemconfig(self.status_title, text="SYSTEM STANDBY", fill=GLOW_GREEN)
        self.canvas.itemconfig(self.status_sub, text="Firefox traffic normal  •  WiFi online")
        self.canvas.itemconfig(
            self.telemetry_text,
            text="TARGET: Firefox  |  FLOOD RATE: 0 Pkts/s  |  STATUS: Standby"
        )
        self.canvas.itemconfig(self.btn_bg, outline=GLOW_GREEN, fill="#021406")
        self.canvas.itemconfig(self.btn_text, fill=GLOW_GREEN, text="LAUNCH DDoS ATTACK")
        self.log("> DDoS Attack terminated. Network restored.")

    def keep_sudo_alive(self):
        """Quietly keep sudo authorization active."""
        threading.Thread(target=lambda: subprocess.run(["sudo", "-v"]), daemon=True).start()
        self.root.after(4 * 60 * 1000, self.keep_sudo_alive)
