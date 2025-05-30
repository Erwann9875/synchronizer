from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class FileInfo:
    path: Path
    relative_path: Path
    size: int
    mtime: float
    hash: Optional[str] = None

@dataclass
class SyncAction:
    action_type: str
    source_path: Path
    dest_path: Path
    reason: str

@dataclass
class SyncResult:
    success: bool
    action: SyncAction
    error: Optional[str] = None
