"""
ERP Launcher - GUI Application
Professional launcher for the ERP system.
Build: pyinstaller --onefile --windowed --icon=icon.ico launcher.py
"""
import os
import sys
import subprocess
import threading
import json
from pathlib import Path

# Try to import tkinter
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext
except ImportError:
    print("Python tkinter not found. Use launcher_terminal.py instead.")
    sys.exit(1)


class ERPLauncher:
    """Main launcher application."""

    APP_NAME = "ERP تولید — کارخانه تجهیزات فلزی"
    VERSION = "1.0.0"
    PORT = 8000

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(self.APP_NAME)
        self.root.geometry("700x550")
        self.root.resizable(False, False)
        self.root.configure(bg="#1a1a2e")

        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - 350
        y = (self.root.winfo_screenheight() // 2) - 275
        self.root.geometry(f"700x550+{x}+{y}")

        self.project_dir = Path(__file__).parent.absolute()
        self.server_process = None
        self.is_running = False

        self.setup_styles()
        self.create_widgets()
        self.check_status()

    def setup_styles(self):
        """Configure tkinter styles."""
        self.colors = {
            'bg': '#1a1a2e',
            'card': '#16213e',
            'accent': '#6366f1',
            'accent_light': '#818cf8',
            'success': '#10b981',
            'danger': '#ef4444',
            'warning': '#f59e0b',
            'text': '#e8edf5',
            'text_muted': '#64748b',
            'border': '#2a3a52',
        }

        style = ttk.Style()
        style.theme_use('clam')

        style.configure('TFrame', background=self.colors['bg'])
        style.configure('Card.TFrame', background=self.colors['card'])
        style.configure('TLabel', background=self.colors['bg'], foreground=self.colors['text'], font=('Segoe UI', 10))
        style.configure('Title.TLabel', background=self.colors['bg'], foreground=self.colors['text'], font=('Segoe UI', 18, 'bold'))
        style.configure('Subtitle.TLabel', background=self.colors['bg'], foreground=self.colors['text_muted'], font=('Segoe UI', 9))
        style.configure('Card.TLabel', background=self.colors['card'], foreground=self.colors['text'], font=('Segoe UI', 10))
        style.configure('CardTitle.TLabel', background=self.colors['card'], foreground=self.colors['accent'], font=('Segoe UI', 11, 'bold'))
        style.configure('Status.TLabel', background=self.colors['card'], foreground=self.colors['success'], font=('Segoe UI', 9, 'bold'))

        style.configure('Accent.TButton', background=self.colors['accent'], foreground='white', font=('Segoe UI', 10, 'bold'), padding=(20, 10))
        style.map('Accent.TButton', background=[('active', self.colors['accent_light'])])

        style.configure('Success.TButton', background=self.colors['success'], foreground='white', font=('Segoe UI', 10, 'bold'), padding=(20, 10))
        style.map('Success.TButton', background=[('active', '#059669')])

        style.configure('Danger.TButton', background=self.colors['danger'], foreground='white', font=('Segoe UI', 10, 'bold'), padding=(20, 10))
        style.map('Danger.TButton', background=[('active', '#dc2626')])

        style.configure('Outline.TButton', background=self.colors['card'], foreground=self.colors['text'], font=('Segoe UI', 9), padding=(15, 8))
        style.map('Outline.TButton', background=[('active', self.colors['border'])])

    def create_widgets(self):
        """Create the main UI."""
        # Header
        header = tk.Frame(self.root, bg=self.colors['bg'])
        header.pack(fill='x', padx=30, pady=(20, 10))

        tk.Label(header, text="🏭 " + self.APP_NAME, font=('Segoe UI', 18, 'bold'),
                 bg=self.colors['bg'], fg=self.colors['text']).pack(anchor='w')
        tk.Label(header, text=f"نسخه {self.VERSION} — سیستم مدیریت تولید صنعتی",
                 font=('Segoe UI', 9), bg=self.colors['bg'], fg=self.colors['text_muted']).pack(anchor='w')

        # Separator
        tk.Frame(self.root, bg=self.colors['border'], height=1).pack(fill='x', padx=30, pady=5)

        # Status Card
        status_card = tk.Frame(self.root, bg=self.colors['card'], highlightbackground=self.colors['border'],
                               highlightthickness=1, bd=0)
        status_card.pack(fill='x', padx=30, pady=10)

        tk.Label(status_card, text="📊 وضعیت سیستم", font=('Segoe UI', 11, 'bold'),
                 bg=self.colors['card'], fg=self.colors['accent'], anchor='w').pack(fill='x', padx=15, pady=(10, 5))

        self.status_frame = tk.Frame(status_card, bg=self.colors['card'])
        self.status_frame.pack(fill='x', padx=15, pady=(0, 10))

        self.status_labels = {}
        for i, (key, label) in enumerate([
            ('python', 'Python'), ('django', 'Django'), ('venv', 'محیط مجازی'),
            ('db', 'دیتابیس'), ('server', 'سرور')
        ]):
            row = tk.Frame(self.status_frame, bg=self.colors['card'])
            row.pack(fill='x', pady=2)
            tk.Label(row, text=label, font=('Segoe UI', 9), bg=self.colors['card'],
                     fg=self.colors['text_muted'], width=15, anchor='w').pack(side='left')
            lbl = tk.Label(row, text="بررسی...", font=('Segoe UI', 9, 'bold'),
                          bg=self.colors['card'], fg=self.colors['warning'], anchor='w')
            lbl.pack(side='left')
            self.status_labels[key] = lbl

        # Buttons
        btn_frame = tk.Frame(self.root, bg=self.colors['bg'])
        btn_frame.pack(fill='x', padx=30, pady=10)

        self.start_btn = tk.Button(btn_frame, text="▶️  اجرای سرور", font=('Segoe UI', 11, 'bold'),
                                   bg=self.colors['success'], fg='white', relief='flat',
                                   padx=25, pady=10, cursor='hand2', command=self.toggle_server)
        self.start_btn.pack(side='left', padx=(0, 10))

        self.stop_btn = tk.Button(btn_frame, text="⏹️  توقف سرور", font=('Segoe UI', 11, 'bold'),
                                  bg=self.colors['danger'], fg='white', relief='flat',
                                  padx=25, pady=10, cursor='hand2', command=self.stop_server, state='disabled')
        self.stop_btn.pack(side='left', padx=(0, 10))

        tk.Button(btn_frame, text="🌐  مرورگر", font=('Segoe UI', 10),
                  bg=self.colors['accent'], fg='white', relief='flat',
                  padx=20, pady=10, cursor='hand2', command=self.open_browser).pack(side='left', padx=(0, 10))

        tk.Button(btn_frame, text="⚙️  نصب/آپدیت", font=('Segoe UI', 10),
                  bg=self.colors['card'], fg=self.colors['text'], relief='flat',
                  padx=20, pady=10, cursor='hand2', command=self.install_deps,
                  highlightbackground=self.colors['border'], highlightthickness=1).pack(side='left')

        # Log area
        log_frame = tk.Frame(self.root, bg=self.colors['card'], highlightbackground=self.colors['border'],
                             highlightthickness=1, bd=0)
        log_frame.pack(fill='both', expand=True, padx=30, pady=(5, 15))

        tk.Label(log_frame, text="📋 گزارش", font=('Segoe UI', 10, 'bold'),
                 bg=self.colors['card'], fg=self.colors['accent'], anchor='w').pack(fill='x', padx=10, pady=(8, 2))

        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, bg='#0f0f23', fg='#a0aec0',
                                                   font=('Consolas', 9), relief='flat', bd=0,
                                                   insertbackground='#a0aec0', selectbackground=self.colors['accent'])
        self.log_text.pack(fill='both', expand=True, padx=10, pady=(0, 8))

    def log(self, message, color='#a0aec0'):
        """Add message to log."""
        self.log_text.insert('end', f"  {message}\n")
        self.log_text.see('end')
        self.log_text.update()

    def check_status(self):
        """Check system status."""
        def _check():
            # Python
            self.status_labels['python'].config(text=f"✓ {sys.version.split()[0]}", fg=self.colors['success'])

            # Venv
            venv_path = self.project_dir / 'venv' / 'Scripts' / 'python.exe'
            if venv_path.exists():
                self.status_labels['venv'].config(text="✓ نصب شده", fg=self.colors['success'])
            else:
                self.status_labels['venv'].config(text="✗ یافت نشد", fg=self.colors['danger'])

            # Django
            try:
                result = subprocess.run([str(venv_path), '-c', 'import django; print(django.get_version())'],
                                       capture_output=True, text=True, timeout=10, cwd=str(self.project_dir))
                if result.returncode == 0:
                    self.status_labels['django'].config(text=f"✓ {result.stdout.strip()}", fg=self.colors['success'])
                else:
                    self.status_labels['django'].config(text="✗ نصب نشده", fg=self.colors['danger'])
            except Exception:
                self.status_labels['django'].config(text="✗ خطا", fg=self.colors['danger'])

            # Database
            db_path = self.project_dir / 'db.sqlite3'
            if db_path.exists():
                size = db_path.stat().st_size / 1024
                self.status_labels['db'].config(text=f"✓ SQLite ({size:.0f} KB)", fg=self.colors['success'])
            else:
                self.status_labels['db'].config(text="✗ یافت نشد", fg=self.colors['danger'])

            # Server
            self.status_labels['server'].config(text="● متوقف", fg=self.colors['text_muted'])

        threading.Thread(target=_check, daemon=True).start()

    def toggle_server(self):
        """Start or stop the server."""
        if self.is_running:
            self.stop_server()
        else:
            self.start_server()

    def start_server(self):
        """Start the ERP server."""
        def _start():
            self.log("🚀 در حال راه‌اندازی سرور...")
            self.is_running = True
            self.start_btn.config(state='disabled', text="⏳ در حال راه‌اندازی...")
            self.stop_btn.config(state='normal')
            self.status_labels['server'].config(text="● در حال راه‌اندازی", fg=self.colors['warning'])

            venv_python = self.project_dir / 'venv' / 'Scripts' / 'python.exe'
            if not venv_python.exists():
                venv_python = Path(sys.executable)

            try:
                # Run migrations first
                self.log("📦 اجرای مایگریشن‌ها...")
                result = subprocess.run([str(venv_python), 'manage.py', 'migrate', '--run-syncdb'],
                                       capture_output=True, text=True, timeout=60, cwd=str(self.project_dir))
                if result.returncode == 0:
                    self.log("✓ مایگریشن‌ها با موفقیت اجرا شد")
                else:
                    self.log(f"⚠️ خطا در مایگریشن: {result.stderr[:200]}")

                # Start server
                self.log(f"🌐 شروع سرور روی پورت {self.PORT}...")
                self.server_process = subprocess.Popen(
                    [str(venv_python), '-m', 'waitress',
                     f'--host=0.0.0.0', f'--port={self.PORT}',
                     f'--threads={os.cpu_count() or 4}',
                     'erp_project.wsgi:application'],
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    cwd=str(self.project_dir), text=True, bufsize=1
                )

                self.is_running = True
                self.start_btn.config(state='disabled', text="✅ سرور در حال اجرا")
                self.status_labels['server'].config(text=f"● اجرا شده (:{self.PORT})", fg=self.colors['success'])
                self.log(f"✅ سرور با موفقیت راه‌اندازی شد: http://127.0.0.1:{self.PORT}")

                # Read output
                for line in self.server_process.stdout:
                    if line.strip():
                        self.log(f"  {line.strip()}")

            except Exception as e:
                self.log(f"❌ خطا: {str(e)}")
                self.is_running = False
                self.start_btn.config(state='normal', text="▶️  اجرای سرور")
                self.stop_btn.config(state='disabled')
                self.status_labels['server'].config(text="● خطا", fg=self.colors['danger'])

        threading.Thread(target=_start, daemon=True).start()

    def stop_server(self):
        """Stop the server."""
        if self.server_process:
            self.log("⏹️ در حال توقف سرور...")
            self.server_process.terminate()
            self.server_process.wait(timeout=5)
            self.server_process = None
        self.is_running = False
        self.start_btn.config(state='normal', text="▶️  اجرای سرور")
        self.stop_btn.config(state='disabled')
        self.status_labels['server'].config(text="● متوقف", fg=self.colors['text_muted'])
        self.log("✓ سرور متوقف شد")

    def open_browser(self):
        """Open the browser."""
        import webbrowser
        webbrowser.open(f"http://127.0.0.1:{self.PORT}")
        self.log(f"🌐 مرورگر باز شد: http://127.0.0.1:{self.PORT}")

    def install_deps(self):
        """Install/update dependencies."""
        def _install():
            self.log("📦 در حال نصب وابستگی‌ها...")
            venv_python = self.project_dir / 'venv' / 'Scripts' / 'python.exe'

            if not venv_python.exists():
                self.log("📦 ایجاد محیط مجازی...")
                subprocess.run([sys.executable, '-m', 'venv', 'venv'],
                             cwd=str(self.project_dir), timeout=120)
                venv_python = self.project_dir / 'venv' / 'Scripts' / 'python.exe'

            result = subprocess.run([str(venv_python), '-m', 'pip', 'install', '-r', 'requirements.txt'],
                                   capture_output=True, text=True, timeout=300, cwd=str(self.project_dir))
            if result.returncode == 0:
                self.log("✓ وابستگی‌ها با موفقیت نصب شد")
                self.check_status()
            else:
                self.log(f"❌ خطا: {result.stderr[:200]}")

        threading.Thread(target=_install, daemon=True).start()

    def run(self):
        """Run the application."""
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def on_close(self):
        """Handle window close."""
        if self.is_running:
            self.stop_server()
        self.root.destroy()


if __name__ == '__main__':
    app = ERPLauncher()
    app.run()
