from pathlib import Path
import hashlib
import shutil
from typing import Dict
from storage.base import StorageProvider
from datatypes import FileInfo

class LocalStorageProvider(StorageProvider):
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path).resolve()
        if not self.base_path.exists():
            raise ValueError(f"Directory doesn't exist: {self.base_path}")
    
    def list_files(self) -> Dict[Path, FileInfo]:
        files = {}
        for file_path in self.base_path.rglob('*'):
            if file_path.is_file():
                relative_path = file_path.relative_to(self.base_path)
                stat = file_path.stat()
                files[relative_path] = FileInfo(
                    path=file_path,
                    relative_path=relative_path,
                    size=stat.st_size,
                    mtime=stat.st_mtime
                )
        return files

    def get_file_hash(self, file_path: Path) -> str:
        hash_md5 = hashlib.md5()
        full_path = self.base_path / file_path if not file_path.is_absolute() else file_path
        with open(full_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def copy_file(self, source: Path, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    
    def file_exists(self, file_path: Path) -> bool:
        full_path = self.base_path / file_path
        return full_path.exists()
