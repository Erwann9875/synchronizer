# File synchronizer

This is a reliable command-line tool to **keep two directories in sync**, including all their files and subfolders, while handling conflicts and using multiple threads for speed. You can use it for backup, mirroring projects, or any situation where you want two folders to stay identical.

## Features

- **Syncs everything:** Recursively copies and updates all files and subfolders between two locations.
- **Smart conflict detection:** If the same file changed in both places since the last sync, it keeps both versions so you don’t lose data.
- **Fast (multi-threaded):** Uses multiple threads to copy files at the same time.
- **Dry-run mode:** See what would change before actually doing it.
- **Custom filtering:** Ignore files by pattern (e.g. temp files, system files) or sync only certain file types.
- **Logs everything:** Actions and errors are saved to a log file with timestamps.
- **Easy to extend:** Add support for other storage backends (like cloud buckets) if you need.
- **Remembers sync history:** Tracks what’s already been synced to detect real conflicts (not just by timestamps).

## Installation

- Python 3.7 or newer (standard library only, no need to `pip install` anything)
- Just clone or download the files

## Usage

### Run a sync

```bash
python main.py /path/to/dirA /path/to/dirB
```

### Preview changes (dry run)

Want to see what would happen without touching any files ?

```bash
python main.py /path/to/dirA /path/to/dirB --dry-run
```

### Using a configuration file

```bash
python main.py /path/to/dirA /path/to/dirB --config sync.conf
```

### Custom location for state file

```bash
python main.py /path/to/dirA /path/to/dirB --state-file /path/to/state.json
```

## Configuration example

Here’s what a sync.conf might look like:

```ini
[sync]
# Number of threads (higher is faster for lots of files)
max_workers = 5

# Log file
log_file = sync.log

# Where to put files if both sides changed the same file
conflict_dir = ./conflicts

# Ignore these patterns (comma separated)
ignore_patterns = *.tmp, *.temp, .DS_Store, Thumbs.db, __pycache__, .git

# Only sync files with these extensions (leave blank for all)
# Example: allowed_extensions = .txt, .doc, .pdf
allowed_extensions = 
```

## How syncing works

### Sync Logic

1. **New files**: If a file exists in only one folder, it’s copied to the other.
2. **Updates**: If a file changed in only one folder since last time, the newer version is copied over.
3. **Conflicts**: If both versions changed, both copies are saved in the conflicts folder with clear names and timestamps (you choose which version to keep later).

### Example conflict files :

`report_dirA_20240530_141522.txt`
`report_dirB_20240530_141522.txt`

### State & logging

Sync state is saved to a .sync_state.json file by default. This tracks what changed and when, so the tool can detect real conflicts.
All actions (copies, updates, conflicts, errors) are logged to sync.log. You can change the log file name/location in the config.

## Examples use cases

### 1. Backing up a project:

```bash
python main.py ~/Documents/Project ~/Backup/Project
```

### Only sync code files:

Make a sync.conf:
```ini
[sync]
allowed_extensions = .py, .js, .html, .css
```

Then run:
```bash
python main.py ./src ./backup --config sync.conf
```

### Handle big folders faster

In sync.conf:

```ini
[sync]
max_workers = 10
```

## How to extend
The code is organized so you can add new storage backends easily.
For example, you could add an S3 backend by making a new class that follows the same interface as `LocalStorageProvider`.

## Things to know
- Only works on local directories out of the box (cloud support could easily be added).
- Doesn’t try to resolve file conflicts automatically, you decide which version to keep if both sides changed the same file.
- Handles files by hash (no delta sync or partial update).
- All logs and state are local, nothing is uploaded or sent anywhere.

## Troubleshooting
- If you get `ModuleNotFoundError`, make sure your imports and folder structure match.
- No install needed, just run `python main.py ...` in the folder where your code is.
- Need help ? Open an issue or check the logs (sync.log) for details.

## License
This tool is open-source and free to use for your own projects, learning, or backups.
Feel free to share, modify, or suggest improvements!
