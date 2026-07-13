import json
import os
import shutil
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.db import models
from django.utils import timezone


class UpdateLog(models.Model):
    """لاگ آپدیت‌ها"""
    STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('downloading', 'در حال دانلود'),
        ('updating', 'در حال آپدیت'),
        ('success', 'موفق'),
        ('failed', 'ناموفق'),
        ('rollback', 'بازگشت'),
    ]

    version_from = models.CharField(max_length=50, verbose_name='ورژن قبلی')
    version_to = models.CharField(max_length=50, verbose_name='ورژن جدید')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    backup_path = models.CharField(max_length=500, blank=True, verbose_name='مسیر بک‌آپ')
    error_message = models.TextField(blank=True, verbose_name='پیام خطا')
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان شروع')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان پایان')
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='توسط کاربر'
    )

    class Meta:
        verbose_name = 'لاگ آپدیت'
        verbose_name_plural = 'لاگ‌های آپدیت'
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.version_from} → {self.version_to} ({self.get_status_display()})"

    def complete_success(self):
        self.status = 'success'
        self.completed_at = timezone.now()
        self.save()

    def complete_failed(self, error):
        self.status = 'failed'
        self.error_message = error
        self.completed_at = timezone.now()
        self.save()


class VersionManager:
    """مدیریت ورژن‌ها"""

    VERSION_FILE = Path(settings.BASE_DIR) / 'version.json'

    @classmethod
    def get_current_version(cls):
        """دریافت ورژن فعلی"""
        if cls.VERSION_FILE.exists():
            with open(cls.VERSION_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('version', '1.0.0')
        return '1.0.0'

    @classmethod
    def get_version_info(cls):
        """دریافت اطلاعات کامل ورژن"""
        if cls.VERSION_FILE.exists():
            with open(cls.VERSION_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'version': '1.0.0',
            'last_updated': None,
            'changelog': ''
        }

    @classmethod
    def update_version(cls, new_version, changelog=''):
        """آپدیت ورژن"""
        data = {
            'version': new_version,
            'last_updated': datetime.now().isoformat(),
            'changelog': changelog
        }
        with open(cls.VERSION_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def get_git_repo_url(cls):
        """دریافت آدرس ریپازیتوری GitHub"""
        return os.getenv('GITHUB_REPO_URL', '')

    @classmethod
    def check_git_available(cls):
        """بررسی وجود git"""
        try:
            result = subprocess.run(
                ['git', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    @classmethod
    def check_remote_updates(cls):
        """بررسی آپدیت‌های موجود از GitHub Releases"""
        repo_url = cls.get_git_repo_url()
        if not repo_url:
            return {'available': False, 'error': 'آدرس GitHub تنظیم نشده'}

        try:
            import requests
            # Extract owner/repo from URL
            # https://github.com/owner/repo.git -> owner/repo
            parts = repo_url.replace('https://github.com/', '').replace('.git', '').split('/')
            if len(parts) != 2:
                return {'available': False, 'error': 'آدرس GitHub نامعتبر'}
            owner, repo = parts

            # Get latest release from GitHub API
            api_url = f'https://api.github.com/repos/{owner}/{repo}/releases/latest'
            response = requests.get(api_url, timeout=15)
            if response.status_code == 404:
                return {'available': False, 'message': 'هنوز ریلیزی منتشر نشده'}
            if response.status_code != 200:
                return {'available': False, 'error': f'خطا: {response.status_code}'}

            release = response.json()
            remote_version = release.get('tag_name', '').lstrip('v')
            current_version = cls.get_current_version()

            if remote_version != current_version:
                # Find EXE asset
                exe_asset = None
                for asset in release.get('assets', []):
                    if asset['name'].endswith('.exe'):
                        exe_asset = {
                            'name': asset['name'],
                            'url': asset['browser_download_url'],
                            'size': asset['size'],
                        }
                        break

                return {
                    'available': True,
                    'remote_version': remote_version,
                    'current_version': current_version,
                    'release_name': release.get('name', ''),
                    'release_body': release.get('body', ''),
                    'exe_asset': exe_asset,
                    'release_url': release.get('html_url', ''),
                }
            else:
                return {'available': False, 'message': f'ورژن فعلی ({current_version}) به‌روز است'}

        except requests.exceptions.RequestException as e:
            return {'available': False, 'error': f'خطا در اتصال: {str(e)}'}
        except Exception as e:
            return {'available': False, 'error': str(e)}

    @classmethod
    def create_backup(cls):
        """ایجاد بک‌آپ قبل از آپدیت"""
        backup_dir = Path(settings.BASE_DIR) / 'backups'
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'backup_{timestamp}'
        backup_path = backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)

        # Backup database
        db_source = Path(settings.BASE_DIR) / 'db.sqlite3'
        if db_source.exists():
            shutil.copy2(db_source, backup_path / 'db.sqlite3')

        # Backup version file
        version_file = Path(settings.BASE_DIR) / 'version.json'
        if version_file.exists():
            shutil.copy2(version_file, backup_path / 'version.json')

        # Backup .env
        env_file = Path(settings.BASE_DIR) / '.env'
        if env_file.exists():
            shutil.copy2(env_file, backup_path / '.env')

        # Backup media folder (just important files)
        media_source = Path(settings.BASE_DIR) / 'media'
        if media_source.exists():
            media_backup = backup_path / 'media'
            if media_backup.exists():
                shutil.rmtree(media_backup)
            shutil.copytree(media_source, media_backup, dirs_exist_ok=True)

        # Create backup info
        info = {
            'timestamp': timestamp,
            'version': cls.get_current_version(),
            'files': os.listdir(backup_path)
        }
        with open(backup_path / 'info.json', 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)

        return str(backup_path)

    @classmethod
    def perform_update(cls, user=None):
        """اجرای آپدیت از GitHub Release"""
        import requests

        current_version = cls.get_current_version()
        log = UpdateLog.objects.create(
            version_from=current_version,
            version_to='pending',
            triggered_by=user
        )

        try:
            # Step 1: Check for latest release
            log.status = 'downloading'
            log.save()

            repo_url = cls.get_git_repo_url()
            parts = repo_url.replace('https://github.com/', '').replace('.git', '').split('/')
            owner, repo = parts

            api_url = f'https://api.github.com/repos/{owner}/{repo}/releases/latest'
            response = requests.get(api_url, timeout=15)
            release = response.json()
            remote_version = release.get('tag_name', '').lstrip('v')

            # Step 2: Create backup
            backup_path = cls.create_backup()
            log.backup_path = backup_path

            # Step 3: Download EXE from release
            exe_asset = None
            for asset in release.get('assets', []):
                if asset['name'].endswith('.exe'):
                    exe_asset = asset
                    break

            if exe_asset:
                # Download the EXE
                exe_url = exe_asset['browser_download_url']
                exe_response = requests.get(exe_url, timeout=120)
                exe_path = Path(settings.BASE_DIR) / exe_asset['name']
                with open(exe_path, 'wb') as f:
                    f.write(exe_response.content)

            # Step 4: Pull latest code (for Python files)
            log.status = 'updating'
            log.save()

            if cls.check_git_available():
                subprocess.run(['git', 'pull', 'origin', 'main'],
                             capture_output=True, timeout=120, cwd=str(settings.BASE_DIR))

            # Step 5: Update dependencies
            pip_path = sys.executable
            subprocess.run([pip_path, '-m', 'pip', 'install', '-r', 'requirements.txt'],
                         capture_output=True, timeout=300, cwd=str(settings.BASE_DIR))

            # Step 6: Run migrations
            subprocess.run([pip_path, 'manage.py', 'migrate', '--noinput'],
                         capture_output=True, timeout=120, cwd=str(settings.BASE_DIR))

            # Step 7: Collect static
            subprocess.run([pip_path, 'manage.py', 'collectstatic', '--noinput'],
                         capture_output=True, timeout=120, cwd=str(settings.BASE_DIR))

            # Step 8: Update version
            new_version = cls.get_current_version()
            log.version_to = new_version
            log.complete_success()

            return {
                'success': True,
                'version_from': current_version,
                'version_to': new_version,
                'backup_path': backup_path
            }

        except Exception as e:
            log.complete_failed(str(e))
            raise

    @classmethod
    def rollback(cls, backup_path):
        """بازگشت به بک‌آپ"""
        backup_dir = Path(backup_path)
        if not backup_dir.exists():
            raise Exception('بک‌آپ یافت نشد')

        # Restore database
        db_backup = backup_dir / 'db.sqlite3'
        if db_backup.exists():
            shutil.copy2(db_backup, Path(settings.BASE_DIR) / 'db.sqlite3')

        # Restore version file
        version_backup = backup_dir / 'version.json'
        if version_backup.exists():
            shutil.copy2(version_backup, Path(settings.BASE_DIR) / 'version.json')

        # Restore .env
        env_backup = backup_dir / '.env'
        if env_backup.exists():
            shutil.copy2(env_backup, Path(settings.BASE_DIR) / '.env')

        # Restore media
        media_backup = backup_dir / 'media'
        if media_backup.exists():
            media_dest = Path(settings.BASE_DIR) / 'media'
            if media_dest.exists():
                shutil.rmtree(media_dest)
            shutil.copytree(media_backup, media_dest)

        return True

    @classmethod
    def get_backups(cls):
        """لیست بک‌آپ‌ها"""
        backup_dir = Path(settings.BASE_DIR) / 'backups'
        if not backup_dir.exists():
            return []

        backups = []
        for item in backup_dir.iterdir():
            if item.is_dir():
                info_file = item / 'info.json'
                if info_file.exists():
                    with open(info_file, 'r', encoding='utf-8') as f:
                        info = json.load(f)
                    info['path'] = str(item)
                    info['size'] = sum(
                        f.stat().st_size for f in item.rglob('*') if f.is_file()
                    )
                    backups.append(info)

        return sorted(backups, key=lambda x: x['timestamp'], reverse=True)
