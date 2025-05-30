from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict
from datatypes import FileInfo

class StorageProvider(ABC):
    @abstractmethod
    def list_files(self) -> Dict[Path, FileInfo]:
        pass
    
    @abstractmethod
    def get_file_hash(self, file_path: Path) -> str:
        pass
    
    @abstractmethod
    def copy_file(self, source: Path, destination: Path) -> None:
        pass
    
    @abstractmethod
    def file_exists(self, file_path: Path) -> bool:
        pass
