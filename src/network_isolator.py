import os
import sys
import time
import subprocess
from src.config import GROUP_NAME, CGROUP_NAME, COMMENT, TARGET_PROC


def ensure_sudo_cached():
    """Prompt for sudo password once in terminal before GUI launches."""
    print("[ARC-GHOST] Requesting privileges (one-time sudo authorization)...")
    res = subprocess.run(["sudo", "-v"])
    if res.returncode != 0:
        print("[ARC-GHOST] Sudo authorization failed. Exiting.")
        sys.exit(1)


def sudo_run(args, **kwargs):
    """Run command with sudo prefix cleanly without leaking error noise."""
    check_arg = kwargs.pop("check", False)
    has_custom_std = "stdout" in kwargs or "stderr" in kwargs
    capture = kwargs.get("capture_output", False) or not has_custom_std

    cmd = ["sudo", "-n"] + args
    if capture:
        res = subprocess.run(cmd, capture_output=True, text=True)
    else:
        res = subprocess.run(cmd, **kwargs)

    # If sudo -n failed because auth was required
    if res.returncode != 0 and capture and any(msg in (res.stderr or "").lower() for msg in ["password is required", "a password is required", "terminal is required"]):
        subprocess.run(["sudo", "-v"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if capture:
            res = subprocess.run(["sudo"] + args, capture_output=True, text=True)
        else:
            res = subprocess.run(["sudo"] + args, **kwargs)

    if check_arg and res.returncode != 0:
        raise subprocess.CalledProcessError(res.returncode, args, output=getattr(res, "stdout", None), stderr=getattr(res, "stderr", None))

    return res


def get_real_user():
    """Get non-root username."""
    user = os.environ.get("USER") or os.environ.get("SUDO_USER")
    if not user or user == "root":
        try:
            import getpass
            user = getpass.getuser()
        except Exception:
            user = "arunachalam"
    return user if user != "root" else "arunachalam"


def setup_group():
    """Create Linux GID group for target process isolation."""
    check = subprocess.run(["getent", "group", GROUP_NAME], stdout=subprocess.DEVNULL)
    if check.returncode != 0:
        sudo_run(["groupadd", GROUP_NAME], check=True)


def get_running_pids():
    """Get list of ALL active Firefox process PIDs."""
    user = get_real_user()
    try:
        res = subprocess.run(["pgrep", "-u", user, "-f", TARGET_PROC], capture_output=True, text=True)
        if res.returncode == 0:
            return [p.strip() for p in res.stdout.strip().split() if p.strip()]
    except Exception:
        pass
    return []


def rule_exists():
    """Check if iptables/ip6tables DROP rules are active."""
    cgroup_check = sudo_run(
        [
            "iptables", "-C", "OUTPUT",
            "-m", "cgroup", "--path", CGROUP_NAME,
            "-m", "comment", "--comment", COMMENT,
            "-j", "DROP"
        ]
    )
    return cgroup_check.returncode == 0


def setup_cgroup():
    """Create cgroup v2 directory for live PID isolation."""
    cgroup_path = f"/sys/fs/cgroup/{CGROUP_NAME}"
    sudo_run(["mkdir", "-p", cgroup_path])


def get_cgroup_pids():
    """Get set of PIDs currently inside cgroup v2."""
    cgroup_procs = f"/sys/fs/cgroup/{CGROUP_NAME}/cgroup.procs"
    res = sudo_run(["cat", cgroup_procs])
    if res.returncode == 0 and res.stdout:
        return set(p.strip() for p in res.stdout.strip().split() if p.strip())
    return set()


def attach_pids_to_cgroup(pids):
    """Move running Firefox PIDs into cgroup v2 without restarting or closing Firefox."""
    if not pids:
        return 0
    setup_cgroup()
    count = 0
    cgroup_procs = f"/sys/fs/cgroup/{CGROUP_NAME}/cgroup.procs"
    for pid in pids:
        res = sudo_run(["sh", "-c", f"echo {pid} > {cgroup_procs}"])
        if res.returncode == 0:
            count += 1
    return count


def attach_new_pids():
    """
    Real-time auto detect: find any running Firefox PIDs NOT yet in cgroup v2
    and attach them immediately. Returns list of newly attached PIDs.
    """
    all_pids = get_running_pids()
    if not all_pids:
        return []
    
    current_cgroup_pids = get_cgroup_pids()
    new_pids = [p for p in all_pids if p not in current_cgroup_pids]
    
    if new_pids:
        attach_pids_to_cgroup(new_pids)
        kill_active_firefox_sockets(new_pids)
        
    return new_pids


def kill_active_firefox_sockets(pids):
    """Kill active IPv4 and IPv6 TCP/UDP sockets owned by Firefox PIDs cleanly."""
    if not pids:
        return
    pid_strs = [f"pid={p}" for p in pids]
    try:
        res = subprocess.run(["ss", "-H", "-t", "-u", "-p"], capture_output=True, text=True)
        if res.returncode == 0:
            ports = set()
            for line in res.stdout.splitlines():
                if any(p_str in line for p_str in pid_strs):
                    parts = line.split()
                    if len(parts) >= 4:
                        local_addr = parts[3]
                        if ":" in local_addr:
                            port = local_addr.rsplit(":", 1)[1]
                            if port.isdigit():
                                ports.add(port)
            for port in ports:
                sudo_run(["ss", "-K", "sport", "=", port], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def isolate_target():
    """
    Block Firefox network traffic IMMEDIATELY without restarting or opening new Firefox windows!
    1. Refresh sudo timestamp.
    2. Attach all currently running Firefox PIDs to cgroup v2 '/sys/fs/cgroup/arcghost'.
    3. Add IPv4 AND IPv6 top-priority DROP rules (-I OUTPUT 1) for both cgroup and GID.
    4. Flush active IPv4 & IPv6 TCP/UDP sockets for Firefox PIDs.
    """
    # Refresh sudo credential before applying firewall rules
    subprocess.run(["sudo", "-v"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    setup_group()
    setup_cgroup()
    pids = get_running_pids()
    attached_count = attach_pids_to_cgroup(pids)

    # 1. Apply IPv4 cgroup DROP rule (-I OUTPUT 1)
    if not sudo_run(
        [
            "iptables", "-C", "OUTPUT",
            "-m", "cgroup", "--path", CGROUP_NAME,
            "-m", "comment", "--comment", COMMENT,
            "-j", "DROP"
        ]
    ).returncode == 0:
        sudo_run(
            [
                "iptables", "-I", "OUTPUT", "1",
                "-m", "cgroup", "--path", CGROUP_NAME,
                "-m", "comment", "--comment", COMMENT,
                "-j", "DROP"
            ]
        )

    # 2. Apply IPv6 cgroup DROP rule (-I OUTPUT 1)
    if not sudo_run(
        [
            "ip6tables", "-C", "OUTPUT",
            "-m", "cgroup", "--path", CGROUP_NAME,
            "-m", "comment", "--comment", COMMENT,
            "-j", "DROP"
        ]
    ).returncode == 0:
        sudo_run(
            [
                "ip6tables", "-I", "OUTPUT", "1",
                "-m", "cgroup", "--path", CGROUP_NAME,
                "-m", "comment", "--comment", COMMENT,
                "-j", "DROP"
            ]
        )

    # 3. Apply IPv4 GID DROP rule as fallback (-I OUTPUT 1)
    if not sudo_run(
        [
            "iptables", "-C", "OUTPUT",
            "-m", "owner", "--gid-owner", GROUP_NAME,
            "-m", "comment", "--comment", COMMENT,
            "-j", "DROP"
        ]
    ).returncode == 0:
        sudo_run(
            [
                "iptables", "-I", "OUTPUT", "1",
                "-m", "owner", "--gid-owner", GROUP_NAME,
                "-m", "comment", "--comment", COMMENT,
                "-j", "DROP"
            ]
        )

    # 4. Apply IPv6 GID DROP rule as fallback (-I OUTPUT 1)
    if not sudo_run(
        [
            "ip6tables", "-C", "OUTPUT",
            "-m", "owner", "--gid-owner", GROUP_NAME,
            "-m", "comment", "--comment", COMMENT,
            "-j", "DROP"
        ]
    ).returncode == 0:
        sudo_run(
            [
                "ip6tables", "-I", "OUTPUT", "1",
                "-m", "owner", "--gid-owner", GROUP_NAME,
                "-m", "comment", "--comment", COMMENT,
                "-j", "DROP"
            ]
        )

    # 5. Flush existing IPv4 & IPv6 sockets
    if pids:
        kill_active_firefox_sockets(pids)

    return pids, attached_count


def restore_target():
    """Remove IPv4 and IPv6 cgroup and GID iptables DROP rules cleanly."""
    subprocess.run(["sudo", "-v"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Delete IPv4 cgroup rule
    while sudo_run(
        [
            "iptables", "-C", "OUTPUT",
            "-m", "cgroup", "--path", CGROUP_NAME,
            "-m", "comment", "--comment", COMMENT,
            "-j", "DROP"
        ]
    ).returncode == 0:
        sudo_run(
            [
                "iptables", "-D", "OUTPUT",
                "-m", "cgroup", "--path", CGROUP_NAME,
                "-m", "comment", "--comment", COMMENT,
                "-j", "DROP"
            ]
        )

    # Delete IPv6 cgroup rule
    while sudo_run(
        [
            "ip6tables", "-C", "OUTPUT",
            "-m", "cgroup", "--path", CGROUP_NAME,
            "-m", "comment", "--comment", COMMENT,
            "-j", "DROP"
        ]
    ).returncode == 0:
        sudo_run(
            [
                "ip6tables", "-D", "OUTPUT",
                "-m", "cgroup", "--path", CGROUP_NAME,
                "-m", "comment", "--comment", COMMENT,
                "-j", "DROP"
            ]
        )

    # Delete IPv4 GID rule
    while sudo_run(
        [
            "iptables", "-C", "OUTPUT",
            "-m", "owner", "--gid-owner", GROUP_NAME,
            "-m", "comment", "--comment", COMMENT,
            "-j", "DROP"
        ]
    ).returncode == 0:
        sudo_run(
            [
                "iptables", "-D", "OUTPUT",
                "-m", "owner", "--gid-owner", GROUP_NAME,
                "-m", "comment", "--comment", COMMENT,
                "-j", "DROP"
            ]
        )

    # Delete IPv6 GID rule
    while sudo_run(
        [
            "ip6tables", "-C", "OUTPUT",
            "-m", "owner", "--gid-owner", GROUP_NAME,
            "-m", "comment", "--comment", COMMENT,
            "-j", "DROP"
        ]
    ).returncode == 0:
        sudo_run(
            [
                "ip6tables", "-D", "OUTPUT",
                "-m", "owner", "--gid-owner", GROUP_NAME,
                "-m", "comment", "--comment", COMMENT,
                "-j", "DROP"
            ]
        )

