from pathlib import Path
import sys
import argparse
from config import load_config
from storage.local import LocalStorageProvider
from synchronizer import FileSynchronizer

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Easily keep two folders in sync!\n"
            "Copies new or updated files both ways, "
            "detects conflicts if a file changed in both places, "
            "and saves logs so you know exactly what happened."
        )
    )
    parser.add_argument(
        'dirA', type=Path,
        help='First folder to sync (for example, your main project or working copy)'
    )
    parser.add_argument(
        'dirB', type=Path,
        help='Second folder to sync (for example, a backup or mirror location)'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help="See what would happen (what files would be copied, updated, or marked as conflict) "
             "without making any actual changes."
    )
    parser.add_argument(
        '--config', type=Path,
        help="Path to an optional config file to customize things like ignored files, log location, or file types."
    )
    parser.add_argument(
        '--state-file', type=Path, default=Path('.sync_state.json'),
        help="Where to save sync history (default: .sync_state.json in the current folder). "
             "You can change this if you want to keep sync info elsewhere."
    )
    args = parser.parse_args()
    if not args.dirA.exists():
        print(f"Error: Directory doesn't exist: {args.dirA}")
        sys.exit(1)
    if not args.dirB.exists():
        print(f"Error: Directory doesn't exist: {args.dirB}")
        sys.exit(1)
    config = load_config(args.config)
    try:
        provider_a = LocalStorageProvider(args.dirA)
        provider_b = LocalStorageProvider(args.dirB)
        synchronizer = FileSynchronizer(
            provider_a=provider_a,
            provider_b=provider_b,
            config=config,
            state_file=args.state_file,
            dry_run=args.dry_run
        )
        summary = synchronizer.sync()
        sys.exit(0 if summary['failed'] == 0 else 1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
