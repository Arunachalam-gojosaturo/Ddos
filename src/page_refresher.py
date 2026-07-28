import time
import shutil
import subprocess
import threading


def send_firefox_refresh_event():
    """
    Send a single F5 refresh event specifically targeting Firefox.
    Tries Hyprland (hyprctl), X11 (xdotool), Wayland (wtype), or ydotool.
    """
    refreshed = False
    details = ""

    # 1. Hyprland Wayland Compositor (Hyde / Hyprland)
    if shutil.which("hyprctl"):
        try:
            # Focus Firefox window and dispatch F5 / Ctrl+R shortcut
            subprocess.run(
                ["hyprctl", "dispatch", "focuswindow", "class:firefox"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            time.sleep(0.2)
            subprocess.run(
                ["hyprctl", "dispatch", "sendshortcut", ",F5,class:firefox"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            refreshed = True
            details = "hyprctl shortcut (F5)"
        except Exception as e:
            details = f"hyprctl error: {e}"

    # 2. X11 Window Manager via xdotool
    if not refreshed and shutil.which("xdotool"):
        try:
            search_res = subprocess.run(
                ["xdotool", "search", "--class", "firefox"],
                capture_output=True, text=True
            )
            windows = search_res.stdout.strip().split()
            if windows:
                win_id = windows[0]
                subprocess.run(["xdotool", "key", "--window", win_id, "F5"], check=True)
                refreshed = True
                details = f"xdotool key F5 (window {win_id})"
            else:
                # Global F5 fallback
                subprocess.run(["xdotool", "key", "F5"], check=True)
                refreshed = True
                details = "xdotool global key F5"
        except Exception as e:
            details = f"xdotool error: {e}"

    # 3. Generic Wayland via wtype
    if not refreshed and shutil.which("wtype"):
        try:
            subprocess.run(["wtype", "-k", "F5"], check=True)
            refreshed = True
            details = "wtype key F5"
        except Exception as e:
            details = f"wtype error: {e}"

    # 4. Input device level via ydotool
    if not refreshed and shutil.which("ydotool"):
        try:
            subprocess.run(["ydotool", "key", "63:1", "63:0"], check=True)
            refreshed = True
            details = "ydotool key F5"
        except Exception as e:
            details = f"ydotool error: {e}"

    return refreshed, details


def schedule_one_time_refresh(delay_sec=3.0, log_callback=None):
    """
    Schedule a 1-time page refresh 3 seconds after Firefox internet isolation starts.
    """
    def _worker():
        if log_callback:
            log_callback(f"> Timer set: 1-time page refresh in {delay_sec:g}s...")
        
        time.sleep(delay_sec)
        
        if log_callback:
            log_callback(f"> [{delay_sec:g}s reached] Triggering Firefox page refresh...")
        
        success, details = send_firefox_refresh_event()
        
        if log_callback:
            if success:
                log_callback(f"> Firefox page refreshed via {details}")
                log_callback("> Status: Internet blocked -> Load failed (Expected)")
            else:
                log_callback("> Notice: Manual refresh recommended (No auto-key tool responded)")

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
