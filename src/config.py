import os

# --- UI Layout & Dimensions ---
WIDTH = 520
HEIGHT = 900

# --- Color Palette (Cyberpunk / Terminal Matrix Aesthetic) ---
BG = "#020503"            # Deep matrix obsidian background
PANEL_BG = "#061208"      # Dark green panel surface
GREEN = "#00ff66"         # Neon matrix green accent
GLOW_GREEN = "#39ff14"    # High intensity neon green
DARK_GREEN = "#003312"    # Subtle frame green
RED = "#ff0055"           # Alert neon red
AMBER = "#ffb700"         # Warning amber
CYAN = "#00e5ff"          # Cyber cyan highlight
DIM = "#204427"           # Muted text green/gray
TEXT_FG = "#d0ffd6"       # Terminal text color

# --- Fonts ---
FONT_FAMILY = "JetBrains Mono"
FONT_FALLBACKS = ["Consolas", "Monospace", "Courier"]

# --- Network & Target Settings ---
GROUP_NAME = "arcghost"
CGROUP_NAME = "arcghost"
COMMENT = "arcghost-rule"
TARGET_PROC = "firefox"
REFRESH_DELAY_SEC = 3.0   # Wait 3 seconds after attack trigger before reloading Firefox

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
IMAGE_CANDIDATES = [
    os.path.join(ASSETS_DIR, "robot.png"),
    os.path.join(ASSETS_DIR, "robot.jpg"),
    os.path.join(ASSETS_DIR, "robot.jpeg"),
    os.path.join(BASE_DIR, "robot.png"),
    os.path.join(BASE_DIR, "robot.jpg"),
    os.path.join(BASE_DIR, "robot.jpeg"),
]
