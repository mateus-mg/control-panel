# Backup System Guide

## Overview

The backup subsystem provides automated incremental backups using rsync with hard links. Each source can have individual schedules and retention policies.

## Concepts

### Backup Types

| Type | Trigger | Use Case |
|------|---------|----------|
| **Daily** | Every day except Sunday and 1st of month | Regular backups |
| **Weekly** | Every Sunday | Weekly snapshots |
| **Monthly** | 1st of every month | Long-term archives |

### Incremental Backups with Hard Links

The first backup creates a full copy. Subsequent backups use hard links for unchanged files, meaning:
- Only modified files consume additional disk space
- Each backup appears as a complete filesystem
- Deleting any backup won't affect others

### Retention Policy

Automatically removes old backups based on:
- Count limits (daily/weekly/monthly)
- Maximum age in days
- Minimum free space requirement

## Configuration

### Set Backup Destination

```bash
control-panel backup set-destination /media/mateus/Servidor backups
```

### Configure Global Schedule

```bash
# Daily at 2:00 AM
control-panel backup set-schedule --frequency daily --time 02:00

# Weekly on Sunday at 3:00 AM
control-panel backup set-schedule --frequency weekly --time 03:00 --day-of-week sunday

# Specific days (Mon, Wed, Fri)
control-panel backup set-schedule --frequency custom --time 02:00 --days mon,wed,fri
```

### Configure Global Retention

```bash
control-panel backup set-retention \
  --daily 7 \
  --weekly 4 \
  --monthly 6 \
  --max-age 180 \
  --min-space 10
```

## Managing Sources

### Add a Source

```bash
# Basic source
control-panel backup add-source /path/to/data

# Full options
control-panel backup add-source /path/to/data \
  --frequency daily \
  --time 02:00 \
  --priority high \
  --description "Important data" \
  --exclude "*.tmp,*.log,__pycache__" \
  --recursive
```

### List Sources

```bash
control-panel backup list-sources
```

### Remove a Source

```bash
control-panel backup remove-source /path/to/data
```

### Toggle Source

```bash
control-panel backup toggle-source /path/to/data
```

## Per-Source Configuration

### Individual Schedule

```bash
control-panel backup set-source-schedule /path/to/data \
  --frequency monthly \
  --time 04:00 \
  --day 1
```

### Individual Retention

```bash
control-panel backup set-source-retention /path/to/data \
  --daily 0 \
  --weekly 12 \
  --monthly 6 \
  --max-age 365
```

## Running Backups

### Manual Backup

```bash
# Backup all sources
control-panel backup run

# Backup specific source
control-panel backup run --source /path/to/data
```

### Daemon Mode

```bash
# Start daemon
control-panel backup daemon-start

# Check status
control-panel backup daemon-status

# Stop daemon
control-panel backup daemon-stop
```

## Monitoring

### View Statistics

```bash
control-panel backup stats
```

### View History

```bash
control-panel backup history --limit 20
```

### Check Destination Space

```bash
control-panel backup check-destination
```

## Storage Structure

```
<destination>/backups/
├── daily/
│   ├── backup-2026-04-01_02-00/
│   ├── backup-2026-04-02_02-00/
│   └── ...
├── weekly/
│   ├── backup-2026-03-30_03-00/
│   └── ...
├── monthly/
│   ├── backup-2026-04-01_04-00/
│   └── ...
└── logs/
```

Each backup directory contains:
- Backed up files with original structure
- `_metadata.json`: Backup statistics and status
