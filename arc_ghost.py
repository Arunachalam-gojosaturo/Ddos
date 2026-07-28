#!/usr/bin/env python3
"""
ARC-GHOST: Isolated Process Network Shield
-------------------------------------------
Personal-use hacker-aesthetic GUI application for Linux.
Isolates ONLY Firefox's internet access while keeping your system WiFi 100% connected.
3 seconds after starting isolation, triggers a 1-time page refresh on Firefox.

Usage:
    python3 arc_ghost.py
"""
import sys
import signal
import tkinter as tk

from src.network_isolator import ensure_sudo_cached, restore_target
from src.ui import ArcGhostUI


def main():
    # 1. Request single sudo password prompt in terminal before opening GUI window
    ensure_sudo_cached()

    # 2. Cleanup signal handlers for emergency exit / Ctrl+C
    def cleanup_signal(sig, frame):
        print("\n[ARC-GHOST] Signal received. Restoring network rules...")
        try:
            restore_target()
        except Exception as e:
            print(f"[ARC-GHOST] Cleanup error: {e}")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup_signal)
    signal.signal(signal.SIGTERM, cleanup_signal)

    # 3. Initialize GUI Window
    root = tk.Tk()
    app = ArcGhostUI(root)

    # Clean cleanup on window close
    def on_window_close():
        print("[ARC-GHOST] Closing application & cleaning rules...")
        try:
            restore_target()
        except Exception:
            pass
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_window_close)
    root.mainloop()


if __name__ == "__main__":
    main()
