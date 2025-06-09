"""File system utility functions."""

import os
import shutil
from pathlib import Path
from typing import List, Optional, Generator, Union
import tempfile
import hashlib


def ensure_directory_exists(path: Union[str, Path]) -> Path:
    """Ensure directory exists, create if it doesn't."""
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def safe_remove_file(file_path: Union[str, Path]) -> bool:
    """Safely remove file, return True if successful."""
    try:
        Path(file_path).unlink(missing_ok=True)
        return True
    except Exception:
        return False


def safe_remove_directory(dir_path: Union[str, Path]) -> bool:
    """Safely remove directory and its contents."""
    try:
        shutil.rmtree(dir_path, ignore_errors=True)
        return True
    except Exception:
        return False


def get_file_size(file_path: Union[str, Path]) -> int:
    """Get file size in bytes, return 0 if file doesn't exist."""
    try:
        return Path(file_path).stat().st_size
    except (OSError, FileNotFoundError):
        return 0


def get_file_hash(file_path: Union[str, Path], algorithm: str = 'md5') -> Optional[str]:
    """Calculate file hash using specified algorithm."""
    try:
        hash_obj = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception:
        return None


def copy_file_safe(src: Union[str, Path], dst: Union[str, Path]) -> bool:
    """Safely copy file, creating destination directories if needed."""
    try:
        src_path = Path(src)
        dst_path = Path(dst)
        
        if not src_path.exists():
            return False
        
        # Ensure destination directory exists
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(src_path, dst_path)
        return True
    except Exception:
        return False


def find_files(directory: Union[str, Path], 
               pattern: str = "*", 
               recursive: bool = True) -> Generator[Path, None, None]:
    """Find files matching pattern in directory."""
    path_obj = Path(directory)
    
    if not path_obj.exists() or not path_obj.is_dir():
        return
    
    if recursive:
        yield from path_obj.rglob(pattern)
    else:
        yield from path_obj.glob(pattern)


def get_available_filename(base_path: Union[str, Path]) -> Path:
    """Get available filename by adding number suffix if file exists."""
    path_obj = Path(base_path)
    
    if not path_obj.exists():
        return path_obj
    
    base_name = path_obj.stem
    suffix = path_obj.suffix
    parent = path_obj.parent
    
    counter = 1
    while True:
        new_name = f"{base_name}_{counter}{suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            return new_path
        counter += 1


def create_temp_file(suffix: str = "", prefix: str = "temp_", 
                    directory: Optional[Union[str, Path]] = None) -> Path:
    """Create a temporary file and return its path."""
    fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=directory)
    os.close(fd)  # Close the file descriptor, keep the file
    return Path(temp_path)


def create_temp_directory(suffix: str = "", prefix: str = "temp_",
                         directory: Optional[Union[str, Path]] = None) -> Path:
    """Create a temporary directory and return its path."""
    temp_dir = tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=directory)
    return Path(temp_dir)


def get_directory_size(directory: Union[str, Path]) -> int:
    """Get total size of directory in bytes."""
    total_size = 0
    try:
        for file_path in find_files(directory, "*", recursive=True):
            if file_path.is_file():
                total_size += get_file_size(file_path)
    except Exception:
        pass
    return total_size


def cleanup_old_files(directory: Union[str, Path], 
                     max_age_days: int, 
                     pattern: str = "*") -> int:
    """Remove files older than max_age_days, return count of removed files."""
    import time
    
    removed_count = 0
    max_age_seconds = max_age_days * 24 * 60 * 60
    current_time = time.time()
    
    try:
        for file_path in find_files(directory, pattern, recursive=True):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    if safe_remove_file(file_path):
                        removed_count += 1
    except Exception:
        pass
    
    return removed_count


def is_file_locked(file_path: Union[str, Path]) -> bool:
    """Check if file is locked (being used by another process)."""
    try:
        with open(file_path, 'a'):
            return False
    except (IOError, OSError):
        return True


def get_file_extension(file_path: Union[str, Path]) -> str:
    """Get file extension (without the dot)."""
    return Path(file_path).suffix.lstrip('.')


def normalize_path(path: Union[str, Path]) -> Path:
    """Normalize path (resolve relative paths, etc.)."""
    return Path(path).resolve()
