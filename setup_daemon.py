"""
Simple Todo — 通知服务开机自启管理
跨平台：Windows (启动文件夹) / macOS (LaunchAgent) / Linux (手动)
"""
import os
import sys
import platform
import subprocess
import argparse
import textwrap
from pathlib import Path

PLIST_LABEL = "com.simple-todo.notifier"

# Windows 启动文件夹快捷方式名称
_STARTUP_VBS = "SimpleTodo Notifier.vbs"


def get_project_root():
    """返回项目根目录（当前脚本所在目录）"""
    return Path(__file__).resolve().parent


def get_python_path():
    """返回 Python 解释器路径，Windows 下优先使用 pythonw（无控制台窗口）"""
    exe = sys.executable
    if platform.system() == "Windows":
        pw = Path(exe).with_name("pythonw.exe")
        if pw.exists():
            return str(pw)
    return exe


def get_notifier_path():
    """返回 server/notifier.py 的绝对路径"""
    return str(get_project_root() / "server" / "notifier.py")


# ── Windows ──────────────────────────────────────────────

def _startup_dir():
    """Windows 启动文件夹路径"""
    return os.path.join(
        os.environ["APPDATA"],
        "Microsoft", "Windows", "Start Menu", "Programs", "Startup",
    )


def _startup_shortcut():
    return os.path.join(_startup_dir(), _STARTUP_VBS)


def install_windows():
    """创建 VBS 脚本到启动文件夹，用 pythonw 静默启动通知服务"""
    vbs = _startup_shortcut()
    pythonw = get_python_path()
    notifier = get_notifier_path()
    # VBS 脚本：无窗口运行通知服务
    content = (
        f'CreateObject("WScript.Shell").Run '
        f'"{pythonw} ""{notifier}""", 0, False'
    )
    os.makedirs(_startup_dir(), exist_ok=True)
    with open(vbs, "w") as f:
        f.write(content)
    print(f"[OK] 开机自启已安装 (登录时自动启动)")
    print(f"     位置: {vbs}")


def uninstall_windows():
    """从启动文件夹删除 VBS 脚本"""
    vbs = _startup_shortcut()
    try:
        os.remove(vbs)
        print(f"[OK] 开机自启已卸载")
    except FileNotFoundError:
        print(f"[FAIL] 未找到自启文件，可能已卸载")


def status_windows():
    """检查启动文件夹是否存在自启文件"""
    vbs = _startup_shortcut()
    if os.path.exists(vbs):
        print("[INFO] 开机自启已安装")
    else:
        print("[INFO] 开机自启未安装")


# ── macOS ────────────────────────────────────────────────

def _plist_path():
    return os.path.expanduser(
        f"~/Library/LaunchAgents/{PLIST_LABEL}.plist"
    )


def _plist_content():
    return textwrap.dedent(f"""\
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
     "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
    <dict>
        <key>Label</key>
        <string>{PLIST_LABEL}</string>
        <key>ProgramArguments</key>
        <array>
            <string>/usr/bin/python3</string>
            <string>{get_notifier_path()}</string>
        </array>
        <key>RunAtLoad</key>
        <true/>
        <key>KeepAlive</key>
        <false/>
        <key>StandardOutPath</key>
        <string>/tmp/simple-todo-notifier.log</string>
        <key>StandardErrorPath</key>
        <string>/tmp/simple-todo-notifier.log</string>
    </dict>
    </plist>""")


def install_macos():
    plist = _plist_path()
    os.makedirs(os.path.dirname(plist), exist_ok=True)
    with open(plist, "w") as f:
        f.write(_plist_content())
    subprocess.run(["launchctl", "load", plist], capture_output=True)
    print(f"[OK] 开机自启已安装 (登录时自动启动)")
    print(f"     plist: {plist}")


def uninstall_macos():
    plist = _plist_path()
    subprocess.run(
        ["launchctl", "unload", plist],
        capture_output=True,
    )
    try:
        os.remove(plist)
    except FileNotFoundError:
        pass
    print(f"[OK] 开机自启已卸载")


def status_macos():
    result = subprocess.run(
        ["launchctl", "list", PLIST_LABEL],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("[INFO] 通知服务状态:")
        print(result.stdout.strip())
    else:
        print("[INFO] 通知服务未运行")


# ── Main ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Simple Todo 通知服务 — 开机自启管理"
    )
    parser.add_argument(
        "action", choices=["install", "uninstall", "status"],
        help="install=安装开机自启 | uninstall=卸载 | status=查看状态",
    )
    args = parser.parse_args()

    system = platform.system()
    if system == "Windows":
        dispatch = {
            "install": install_windows,
            "uninstall": uninstall_windows,
            "status": status_windows,
        }
    elif system == "Darwin":
        dispatch = {
            "install": install_macos,
            "uninstall": uninstall_macos,
            "status": status_macos,
        }
    else:
        print(f"当前平台 ({system}) 暂不支持自动配置。")
        print("请自行配置 systemd user service 或 cron 定时任务。")
        print(f"示例: python3 {get_notifier_path()}")
        sys.exit(1)

    dispatch[args.action]()


if __name__ == "__main__":
    main()
