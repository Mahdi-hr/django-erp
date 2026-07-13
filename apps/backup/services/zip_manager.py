"""
ZIP manager for backup operations.
Handles creating and reading backup ZIP files.
"""
import json
import hashlib
import os
import tempfile
import zipfile
from datetime import datetime
from typing import Optional, Tuple


BACKUP_ZIP_NAME = 'backup.json'
METADATA_ZIP_NAME = 'metadata.json'
README_ZIP_NAME = 'README.txt'
VERSION_ZIP_NAME = 'version.json'
CHECKSUM_ZIP_NAME = 'checksum.txt'


def create_backup_zip(
    backup_data: dict,
    metadata: dict,
    version_info: dict,
    output_path: Optional[str] = None,
) -> Tuple[str, int, str]:
    """
    Create a backup ZIP file.

    Args:
        backup_data: The actual backup data
        metadata: Backup metadata
        version_info: Version compatibility info
        output_path: Optional output path. If None, creates temp file.

    Returns:
        Tuple of (file_path, file_size, checksum)
    """
    if output_path is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(tempfile.gettempdir(), f'erp_backup_{timestamp}.zip')

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Write backup data
        backup_json = json.dumps(backup_data, default=str, ensure_ascii=False, indent=2)
        zf.writestr(BACKUP_ZIP_NAME, backup_json)

        # Write metadata
        metadata_json = json.dumps(metadata, default=str, ensure_ascii=False, indent=2)
        zf.writestr(METADATA_ZIP_NAME, metadata_json)

        # Write version info
        version_json = json.dumps(version_info, default=str, ensure_ascii=False, indent=2)
        zf.writestr(VERSION_ZIP_NAME, version_json)

        # Write README
        readme = _generate_readme(metadata)
        zf.writestr(README_ZIP_NAME, readme)

    # Calculate checksum
    checksum = _calculate_checksum(output_path)
    file_size = os.path.getsize(output_path)

    # Add checksum to the zip
    with zipfile.ZipFile(output_path, 'a', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(CHECKSUM_ZIP_NAME, checksum)

    return output_path, file_size, checksum


def read_backup_zip(zip_path: str) -> Tuple[dict, dict, dict, str]:
    """
    Read a backup ZIP file.

    Args:
        zip_path: Path to the ZIP file

    Returns:
        Tuple of (backup_data, metadata, version_info, checksum)

    Raises:
        ValueError: If ZIP is invalid or missing required files
    """
    if not os.path.exists(zip_path):
        raise ValueError('فایل بکاپ یافت نشد')

    with zipfile.ZipFile(zip_path, 'r') as zf:
        # Read backup data
        if BACKUP_ZIP_NAME not in zf.namelist():
            raise ValueError('فایل backup.json در بکاپ وجود ندارد')
        backup_data = json.loads(zf.read(BACKUP_ZIP_NAME).decode('utf-8'))

        # Read metadata
        if METADATA_ZIP_NAME not in zf.namelist():
            raise ValueError('فایل metadata.json در بکاپ وجود ندارد')
        metadata = json.loads(zf.read(METADATA_ZIP_NAME).decode('utf-8'))

        # Read version info
        version_info = {}
        if VERSION_ZIP_NAME in zf.namelist():
            version_info = json.loads(zf.read(VERSION_ZIP_NAME).decode('utf-8'))

        # Read checksum
        checksum = ''
        if CHECKSUM_ZIP_NAME in zf.namelist():
            checksum = zf.read(CHECKSUM_ZIP_NAME).decode('utf-8')

    return backup_data, metadata, version_info, checksum


def verify_checksum(zip_path: str) -> bool:
    """
    Verify the checksum of a backup ZIP file.

    Args:
        zip_path: Path to the ZIP file

    Returns:
        True if checksum is valid
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            if CHECKSUM_ZIP_NAME not in zf.namelist():
                return False
            stored_checksum = zf.read(CHECKSUM_ZIP_NAME).decode('utf-8')

        # Calculate current checksum without the checksum file
        temp_path = zip_path + '.tmp'
        with zipfile.ZipFile(zip_path, 'r') as zf_in:
            with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as zf_out:
                for item in zf_in.infolist():
                    if item.filename != CHECKSUM_ZIP_NAME:
                        zf_out.writestr(item, zf_in.read(item.filename))

        current_checksum = _calculate_checksum(temp_path)
        os.remove(temp_path)

        return stored_checksum == current_checksum
    except Exception:
        return False


def _calculate_checksum(file_path: str) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def _generate_readme(metadata: dict) -> str:
    """Generate README content for the backup."""
    lines = [
        '=== ERP Backup File ===',
        '',
        f'Created: {metadata.get("created_at", "N/A")}',
        f'By: {metadata.get("created_by", "N/A")}',
        f'Type: {metadata.get("backup_type", "N/A")}',
        f'Version: {metadata.get("backup_version", "N/A")}',
        f'Total Records: {metadata.get("total_records", 0)}',
        '',
        'Contents:',
        '  - backup.json: Complete database backup',
        '  - metadata.json: Backup metadata and statistics',
        '  - version.json: Version compatibility info',
        '',
        'To restore, use the ERP Backup Restore feature.',
    ]
    return '\n'.join(lines)
