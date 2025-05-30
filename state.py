import json
from pathlib import Path
from threading import Lock
from typing import Dict, Optional

class SyncState:
    def __init__(self, state_file: Path):
        self.state_file = Path(state_file)
        self.state = self._load_state()
        self.lock = Lock()
    
    def _load_state(self) -> Dict:
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {'last_sync': {}, 'file_hashes': {}}
    
    def save_state(self):
        with self.lock:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2, default=str)
    
    def get_last_sync_time(self, file_path: str) -> Optional[float]:
        return self.state['last_sync'].get(file_path)
    
    def update_sync_time(self, file_path: str, mtime: float):
        with self.lock:
            self.state['last_sync'][file_path] = mtime
    
    def get_file_hash(self, file_path: str) -> Optional[str]:
        return self.state['file_hashes'].get(file_path)
    
    def update_file_hash(self, file_path: str, file_hash: str):
        with self.lock:
            self.state['file_hashes'][file_path] = file_hash
