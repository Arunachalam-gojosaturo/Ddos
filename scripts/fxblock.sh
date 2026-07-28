#!/usr/bin/env bash
#
# fxblock.sh — Headless CLI tool to block ONLY Firefox's internet access on Linux.
# Does NOT touch your global network config (WiFi, NetworkManager, resolv.conf, etc).
# Does NOT close or restart your open Firefox tabs!
#

set -euo pipefail

GROUP_NAME="fxblock"
CGROUP_NAME="arcghost"
COMMENT="fxblock-rule"
REAL_USER="${SUDO_USER:-$USER}"
REAL_HOME=$(eval echo "~$REAL_USER")

require_root() {
    if [[ $EUID -ne 0 ]]; then
        echo "[!] Run with sudo: sudo -E $0"
        exit 1
    fi
}

setup_cgroup_and_rules() {
    echo "[+] Setting up cgroup v2 and iptables rules..."
    mkdir -p "/sys/fs/cgroup/$CGROUP_NAME" 2>/dev/null || true

    # Attach running Firefox PIDs to cgroup v2
    PIDS=$(pgrep -u "$REAL_USER" firefox || true)
    if [[ -n "$PIDS" ]]; then
        echo "[+] Attaching running Firefox PIDs to cgroup (No restart needed)..."
        for PID in $PIDS; do
            echo "$PID" > "/sys/fs/cgroup/$CGROUP_NAME/cgroup.procs" 2>/dev/null || true
        done
        echo "[+] Attached PIDs: $PIDS"
    fi

    # Apply iptables cgroup & GID rules
    iptables -A OUTPUT -m cgroup --path "$CGROUP_NAME" -m comment --comment "$COMMENT" -j DROP 2>/dev/null || true
    iptables -A OUTPUT -m owner --gid-owner "$GROUP_NAME" -m comment --comment "$COMMENT" -j DROP 2>/dev/null || true

    echo "[+] System WiFi remains 100% connected. Firefox isolated."
}

restore_network() {
    echo "[+] Restoring network rules..."
    while iptables -C OUTPUT -m cgroup --path "$CGROUP_NAME" -m comment --comment "$COMMENT" -j DROP 2>/dev/null; do
        iptables -D OUTPUT -m cgroup --path "$CGROUP_NAME" -m comment --comment "$COMMENT" -j DROP
    done
    while iptables -C OUTPUT -m owner --gid-owner "$GROUP_NAME" -m comment --comment "$COMMENT" -j DROP 2>/dev/null; do
        iptables -D OUTPUT -m owner --gid-owner "$GROUP_NAME" -m comment --comment "$COMMENT" -j DROP
    done
    echo "[+] Cleaned up. Firefox network access restored."
}

trigger_3s_refresh() {
    echo "[+] Waiting 3 seconds before 1-time Firefox page refresh..."
    sleep 3
    echo "[+] [3s reached] Triggering 1-time page refresh on Firefox..."

    if command -v hyprctl >/dev/null; then
        hyprctl dispatch focuswindow "class:firefox" >/dev/null 2>&1 || true
        hyprctl dispatch sendshortcut ",F5,class:firefox" >/dev/null 2>&1 || true
        echo "[+] Sent F5 refresh via hyprctl."
    elif command -v xdotool >/dev/null; then
        WIN=$(xdotool search --class "firefox" | head -n1 || true)
        if [[ -n "$WIN" ]]; then
            xdotool key --window "$WIN" F5
        else
            xdotool key F5
        fi
        echo "[+] Sent F5 refresh via xdotool."
    elif command -v wtype >/dev/null; then
        wtype -k F5
        echo "[+] Sent F5 refresh via wtype."
    else
        echo "[!] No shortcut tool (hyprctl/xdotool/wtype) found. Refresh manually."
    fi
}

cleanup() {
    echo
    echo "[!] Stopping fxblock..."
    restore_network
    exit 0
}

trap cleanup SIGINT SIGTERM

require_root
setup_cgroup_and_rules
trigger_3s_refresh

echo "[+] Isolation active. Open tabs preserved. Press Ctrl+C to stop and restore."
while true; do sleep 3600; done
