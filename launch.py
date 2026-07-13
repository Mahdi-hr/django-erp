"""
ERP Launcher - Terminal Application
Run: python launch.py
"""
import os
import sys
import subprocess
import time
from pathlib import Path

APP_NAME = "ERP تولید — کارخانه تجهیزات فلزی"
VERSION = "1.0.0"
PORT = 8000

# Find project directory - works for both EXE and script
if getattr(sys, 'frozen', False):
    PROJECT_DIR = Path(sys.executable).parent.absolute()
else:
    PROJECT_DIR = Path(__file__).parent.absolute()


class C:
    RESET='\033[0m'; BOLD='\033[1m'; DIM='\033[2m'
    RED='\033[91m'; GREEN='\033[92m'; YELLOW='\033[93m'
    BLUE='\033[94m'; CYAN='\033[96m'; WHITE='\033[97m'


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def get_python():
    """Get the correct python executable."""
    if os.name == 'nt':
        p = PROJECT_DIR / 'venv' / 'Scripts' / 'python.exe'
    else:
        p = PROJECT_DIR / 'venv' / 'bin' / 'python'
    return str(p) if p.exists() else sys.executable


def get_waitress():
    """Get waitress-serve executable."""
    if os.name == 'nt':
        ws = PROJECT_DIR / 'venv' / 'Scripts' / 'waitress-serve.exe'
    else:
        ws = PROJECT_DIR / 'venv' / 'bin' / 'waitress-serve'
    return str(ws) if ws.exists() else 'waitress-serve'


def print_banner():
    clear()
    print(f"""
{C.RED}{C.BOLD}{'='*60}
     {C.WHITE}{APP_NAME}{C.RED}
     نسخه {VERSION}
{'='*60}{C.RESET}""")


def print_menu():
    print(f"""
{C.CYAN}  ┌────────────────────────────────────┐
  │         {C.WHITE}منوی اصلی{C.CYAN}                  │
  ├────────────────────────────────────┤
  │  {C.GREEN}1{C.CYAN}  ▶  اجرای سرور{C.WHITE}              │
  │  {C.GREEN}2{C.CYAN}  🌐  باز کردن مرورگر{C.WHITE}         │
  │  {C.GREEN}3{C.CYAN}  📦  نصب / آپدیت وابستگی‌ها{C.WHITE}  │
  │  {C.GREEN}4{C.CYAN}  🔧  ایجاد کاربر ادمین{C.WHITE}       │
  │  {C.GREEN}5{C.CYAN}  📊  بررسی وضعیت{C.WHITE}             │
  │  {C.GREEN}0{C.CYAN}  🚪  خروج{C.WHITE}                    │
  └────────────────────────────────────┘{C.RESET}
""")


def status(label, ok=True):
    icon = f"{C.GREEN}✓" if ok else f"{C.RED}✗"
    print(f"    {icon}{C.RESET}  {label}")


def check_system():
    print(f"\n{C.CYAN}  ── وضعیت سیستم ──{C.RESET}\n")
    # Python
    v = sys.version.split()[0]
    status(f"Python {v}", int(v.split('.')[0]) >= 3 and int(v.split('.')[1]) >= 10)
    # Venv
    venv_exists = (PROJECT_DIR / 'venv').exists()
    status("محیط مجازی", venv_exists)
    # Django
    if venv_exists:
        try:
            r = subprocess.run([get_python(), '-c', 'import django; print(django.get_version())'],
                             capture_output=True, text=True, timeout=10, cwd=str(PROJECT_DIR))
            status(f"Django {r.stdout.strip()}", r.returncode == 0)
        except:
            status("Django", False)
    else:
        status("Django", False)
    # DB
    db = PROJECT_DIR / 'db.sqlite3'
    status(f"دیتابیس ({db.stat().st_size//1024}KB)" if db.exists() else "دیتابیس", db.exists())
    # Waitress
    try:
        r = subprocess.run([get_python(), '-m', 'waitress', '--help'], capture_output=True, timeout=5)
        status("Waitress", r.returncode == 0)
    except:
        status("Waitress", False)
    print()


def install_deps():
    print(f"\n{C.YELLOW}  📦 در حال نصب...{C.RESET}\n")
    py = get_python()
    # Create venv if needed
    if not (PROJECT_DIR / 'venv').exists():
        print(f"    {C.CYAN}►{C.RESET} ایجاد محیط مجازی...")
        subprocess.run([sys.executable, '-m', 'venv', 'venv'], cwd=str(PROJECT_DIR), timeout=120)
        py = get_python()
    # Install
    print(f"    {C.CYAN}►{C.RESET} نصب پکیج‌ها...")
    r = subprocess.run([py, '-m', 'pip', 'install', '-r', 'requirements.txt', '-q'],
                      capture_output=True, text=True, timeout=300, cwd=str(PROJECT_DIR))
    if r.returncode == 0:
        print(f"    {C.GREEN}✓{C.RESET} پکیج‌ها نصب شد")
    else:
        print(f"    {C.RED}✗{C.RESET} خطا: {r.stderr[:200]}")
    # Migrate
    print(f"    {C.CYAN}►{C.RESET} مایگریشن...")
    r = subprocess.run([py, 'manage.py', 'migrate', '--run-syncdb'], capture_output=True, timeout=60, cwd=str(PROJECT_DIR))
    print(f"    {C.GREEN}✓{C.RESET} مایگریشن انجام شد" if r.returncode == 0 else f"    {C.RED}✗{C.RESET} خطا")
    print(f"\n{C.GREEN}  ✓ نصب کامل شد!{C.RESET}\n")


def create_admin():
    print(f"\n{C.YELLOW}  🔧 ایجاد ادمین...{C.RESET}\n")
    subprocess.run([get_python(), 'manage.py', 'createsuperuser'], cwd=str(PROJECT_DIR))


def start_server():
    py = get_python()
    print(f"\n{C.YELLOW}  🚀 راه‌اندازی سرور...{C.RESET}\n")
    subprocess.run([py, 'manage.py', 'migrate', '--run-syncdb'], capture_output=True, timeout=60, cwd=str(PROJECT_DIR))
    print(f"    {C.GREEN}✓{C.RESET} مایگریشن انجام شد")

    # Install waitress if needed
    subprocess.run([py, '-m', 'pip', 'install', 'waitress', '-q'], capture_output=True, timeout=60)

    print(f"\n{C.GREEN}  ═══════════════════════════════════════{C.RESET}")
    print(f"{C.GREEN}  🌐 سرور در حال اجراست!{C.RESET}")
    print(f"{C.WHITE}  آدرس: http://127.0.0.1:{PORT}{C.RESET}")
    print(f"{C.WHITE}  توقف: Ctrl+C{C.RESET}")
    print(f"{C.GREEN}  ═══════════════════════════════════════{C.RESET}\n")

    try:
        subprocess.run([py, '-m', 'waitress',
                        f'--host=0.0.0.0', f'--port={PORT}',
                        f'--threads={os.cpu_count() or 4}',
                        'erp_project.wsgi:application'],
                       cwd=str(PROJECT_DIR))
    except KeyboardInterrupt:
        print(f"\n{C.YELLOW}  ⏹️  سرور متوقف شد{C.RESET}\n")


def open_browser():
    import webbrowser
    webbrowser.open(f"http://127.0.0.1:{PORT}")
    print(f"\n    {C.GREEN}✓{C.RESET} مرورگر باز شد\n")


def main():
    while True:
        print_banner()
        print_menu()
        ch = input(f"  {C.CYAN}→{C.WHITE} انتخاب [0-5]: {C.RESET}").strip()
        if ch == '1': start_server(); input(f"\n  {C.DIM}Enter...{C.RESET}")
        elif ch == '2': open_browser(); input(f"  {C.DIM}Enter...{C.RESET}")
        elif ch == '3': install_deps(); input(f"  {C.DIM}Enter...{C.RESET}")
        elif ch == '4': create_admin(); input(f"\n  {C.DIM}Enter...{C.RESET}")
        elif ch == '5': check_system(); input(f"  {C.DIM}Enter...{C.RESET}")
        elif ch == '0': print(f"\n  {C.GREEN}👋 خروج{C.RESET}\n"); sys.exit(0)
        else: print(f"\n  {C.RED}✗ نامعتبر{C.RESET}"); time.sleep(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n  {C.YELLOW}👋{C.RESET}\n"); sys.exit(0)
