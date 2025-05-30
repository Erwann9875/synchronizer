import configparser
from pathlib import Path
from typing import Optional, Dict

def load_config(config_file: Optional[Path]) -> Dict:
    config = {
        'max_workers': 5,
        'log_file': 'sync.log',
        'conflict_dir': './conflicts',
        'ignore_patterns': ['*.tmp', '*.temp', '.DS_Store', 'Thumbs.db'],
        'allowed_extensions': []
    }
    if config_file and Path(config_file).exists():
        parser = configparser.ConfigParser()
        parser.read(config_file)
        if 'sync' in parser:
            sync_config = parser['sync']
            config['max_workers'] = sync_config.getint('max_workers', 5)
            config['log_file'] = sync_config.get('log_file', 'sync.log')
            config['conflict_dir'] = sync_config.get('conflict_dir', './conflicts')
            if 'ignore_patterns' in sync_config:
                config['ignore_patterns'] = [p.strip() for p in sync_config['ignore_patterns'].split(',')]
            if 'allowed_extensions' in sync_config:
                extensions = [e.strip() for e in sync_config['allowed_extensions'].split(',')]
                config['allowed_extensions'] = [e if e.startswith('.') else f'.{e}' for e in extensions if e]
    return config
