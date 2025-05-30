from pathlib import Path
from datetime import datetime
from typing import List
from datatypes import FileInfo, SyncAction
from storage.base import StorageProvider

class ConflictResolver:
    def __init__(self, conflict_dir: Path):
        self.conflict_dir = Path(conflict_dir)
        self.conflict_dir.mkdir(parents=True, exist_ok=True)
    
    def resolve_conflict(self, file_a: FileInfo, file_b: FileInfo,
                        provider_a: StorageProvider, provider_b: StorageProvider) -> List[SyncAction]:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        stem = file_a.relative_path.stem
        suffix = file_a.relative_path.suffix
        parent = file_a.relative_path.parent

        conflict_name_a = parent / f"{stem}_dirA_{timestamp}{suffix}"
        conflict_name_b = parent / f"{stem}_dirB_{timestamp}{suffix}"

        actions = [
            SyncAction(
                action_type='conflict',
                source_path=file_a.path,
                dest_path=self.conflict_dir / conflict_name_a,
                reason=f"Conflict: saving version from dirA"
            ),
            SyncAction(
                action_type='conflict',
                source_path=file_b.path,
                dest_path=self.conflict_dir / conflict_name_b,
                reason=f"Conflict: saving version from dirB"
            )
        ]
        return actions
