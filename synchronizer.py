from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from datetime import datetime
from typing import Dict, List

from datatypes import SyncAction, SyncResult
from state import SyncState
from conflict import ConflictResolver
from storage.base import StorageProvider

class FileSynchronizer:
    def __init__(self, provider_a: StorageProvider, provider_b: StorageProvider,
                 config: Dict, state_file: Path, dry_run: bool = False):
        self.provider_a = provider_a
        self.provider_b = provider_b
        self.config = config
        self.dry_run = dry_run
        self.state = SyncState(state_file)
        self.conflict_resolver = ConflictResolver(Path(config.get('conflict_dir', './conflicts')))
        self.logger = self._setup_logger()
        self.results_lock = Lock()
        self.results: List[SyncResult] = []
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('FileSynchronizer')
        logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(self.config.get('log_file', 'sync.log'))
        fh.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        if not logger.handlers:
            logger.addHandler(fh)
            logger.addHandler(ch)
        return logger

    def _should_ignore_file(self, file_path: Path) -> bool:
        ignore_patterns = self.config.get('ignore_patterns', [])
        for pattern in ignore_patterns:
            if file_path.match(pattern):
                return True
        allowed_extensions = self.config.get('allowed_extensions', [])
        if allowed_extensions and file_path.suffix not in allowed_extensions:
            return True
        return False

    def _determine_sync_actions(self) -> List[SyncAction]:
        files_a = self.provider_a.list_files()
        files_b = self.provider_b.list_files()
        files_a = {k: v for k, v in files_a.items() if not self._should_ignore_file(k)}
        files_b = {k: v for k, v in files_b.items() if not self._should_ignore_file(k)}
        actions = []
        all_files = set(files_a.keys()) | set(files_b.keys())
        for file_path in all_files:
            if file_path in files_a and file_path not in files_b:
                actions.append(SyncAction(
                    action_type='copy',
                    source_path=files_a[file_path].path,
                    dest_path=self.provider_b.base_path / file_path,
                    reason='New file in dirA'
                ))
            elif file_path not in files_a and file_path in files_b:
                actions.append(SyncAction(
                    action_type='copy',
                    source_path=files_b[file_path].path,
                    dest_path=self.provider_a.base_path / file_path,
                    reason='New file in dirB'
                ))
            else:
                file_a = files_a[file_path]
                file_b = files_b[file_path]
                hash_a = self.provider_a.get_file_hash(file_a.path)
                hash_b = self.provider_b.get_file_hash(file_b.path)
                if hash_a == hash_b:
                    self.state.update_sync_time(str(file_path), max(file_a.mtime, file_b.mtime))
                    self.state.update_file_hash(str(file_path), hash_a)
                else:
                    last_sync = self.state.get_last_sync_time(str(file_path))
                    if last_sync is None:
                        actions.extend(self.conflict_resolver.resolve_conflict(
                            file_a, file_b, self.provider_a, self.provider_b
                        ))
                    elif file_a.mtime > last_sync and file_b.mtime > last_sync:
                        actions.extend(self.conflict_resolver.resolve_conflict(
                            file_a, file_b, self.provider_a, self.provider_b
                        ))
                    elif file_a.mtime > last_sync:
                        actions.append(SyncAction(
                            action_type='update',
                            source_path=file_a.path,
                            dest_path=file_b.path,
                            reason='Updated in dirA'
                        ))
                    elif file_b.mtime > last_sync:
                        actions.append(SyncAction(
                            action_type='update',
                            source_path=file_b.path,
                            dest_path=file_a.path,
                            reason='Updated in dirB'
                        ))
        return actions

    def _execute_action(self, action: SyncAction) -> SyncResult:
        try:
            if not self.dry_run:
                if action.action_type in ['copy', 'update']:
                    self.provider_a.copy_file(action.source_path, action.dest_path)
                elif action.action_type == 'conflict':
                    action.dest_path.parent.mkdir(parents=True, exist_ok=True)
                    import shutil
                    shutil.copy2(action.source_path, action.dest_path)
                relative_path = None
                try:
                    relative_path = action.source_path.relative_to(self.provider_a.base_path)
                except ValueError:
                    try:
                        relative_path = action.source_path.relative_to(self.provider_b.base_path)
                    except ValueError:
                        relative_path = action.source_path.name
                if relative_path is not None:
                    self.state.update_sync_time(str(relative_path), datetime.now().timestamp())
            self.logger.info(f"{action.action_type.upper()}: {action.source_path} -> {action.dest_path} ({action.reason})")
            return SyncResult(success=True, action=action)
        except Exception as e:
            self.logger.error(f"Failed to {action.action_type} {action.source_path}: {str(e)}")
            return SyncResult(success=False, action=action, error=str(e))

    def sync(self) -> Dict[str, int]:
        self.logger.info(f"Starting {'DRY RUN' if self.dry_run else 'synchronization'}")
        actions = self._determine_sync_actions()
        if not actions:
            self.logger.info("No synchronization needed, directories are in sync")
            return {'total': 0, 'success': 0, 'failed': 0, 'conflicts': 0}
        self.logger.info(f"Found {len(actions)} actions to perform")
        max_workers = self.config.get('max_workers', 5)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_action = {executor.submit(self._execute_action, action): action
                                for action in actions}
            for future in as_completed(future_to_action):
                result = future.result()
                with self.results_lock:
                    self.results.append(result)
        if not self.dry_run:
            self.state.save_state()
        summary = {
            'total': len(self.results),
            'success': sum(1 for r in self.results if r.success),
            'failed': sum(1 for r in self.results if not r.success),
            'conflicts': sum(1 for r in self.results if r.action.action_type == 'conflict')
        }
        self.logger.info(f"Synchronization complete: {summary}")
        return summary
