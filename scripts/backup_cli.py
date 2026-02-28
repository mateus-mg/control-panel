#!/usr/bin/env python3
"""
Backup CLI

Command-line interface for backup subsystem.
Provides commands for managing backups, configuration, and daemon.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

# Add scripts directory to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from backup_config import BackupConfigManager
from backup_manager import BackupManager
from backup_daemon import BackupDaemon
from log_config import get_logger, log_success, log_error, log_warning, log_info

console = Console()
logger = get_logger("Backup")


class BackupCLI:
    """CLI for backup subsystem"""

    def __init__(self):
        self.config_manager = BackupConfigManager()
        self.backup_manager = BackupManager()
        self.daemon = BackupDaemon()

    # ========== Daemon Management ==========

    def daemon_start(self):
        """Start backup daemon"""
        if self.daemon.is_running():
            console.print("[yellow]Backup daemon is already running[/yellow]")
            log_warning(logger, "Backup daemon is already running")
            return

        log_info(logger, "Starting backup daemon")
        try:
            import subprocess
            subprocess.Popen(
                [sys.executable, str(Path(__file__).parent / 'backup_daemon.py')],
                start_new_session=True
            )
            log_success(logger, "Backup daemon started")
        except Exception as e:
            log_error(logger, f"Failed to start daemon: {e}")

    def daemon_stop(self):
        """Stop backup daemon"""
        if not self.daemon.is_running():
            console.print("[yellow]Backup daemon is not running[/yellow]")
            log_warning(logger, "Backup daemon is not running")
            return

        log_info(logger, "Stopping backup daemon")
        if self.daemon.stop():
            log_success(logger, "Backup daemon stopped")
        else:
            log_error(logger, "Failed to stop daemon")

    def daemon_restart(self):
        """Restart backup daemon"""
        log_info(logger, "Restarting backup daemon")
        self.daemon_stop()
        import time
        time.sleep(2)
        self.daemon_start()

    def daemon_status(self):
        """Show daemon status"""
        status = self.daemon.get_status()

        if status['running']:
            console.print(Panel(
                f"[green]Running[/green]\n"
                f"PID: {status.get('pid', 'N/A')}\n"
                f"Started: {status.get('started_at', 'N/A')}\n"
                f"Uptime: {status.get('uptime_seconds', 0)} seconds",
                title="Backup Daemon",
                border_style="green"
            ))
        else:
            console.print(Panel(
                "[red]Stopped[/red]",
                title="Backup Daemon",
                border_style="red"
            ))

    # ========== Destination Configuration ==========

    def set_destination(self, base_path: str, backup_folder: str = "backups"):
        """Set backup destination"""
        log_info(logger, f"Setting backup destination to {base_path}/{backup_folder}")

        if self.config_manager.set_backup_destination(base_path, backup_folder):
            log_success(logger, f"Destination set: {base_path}/{backup_folder}")

            # Show space info
            space = self.config_manager.check_destination_space()
            if space.get('exists'):
                console.print(f"  Total: {space.get('total_gb', 'N/A')} GB")
                console.print(f"  Free: {space.get('free_gb', 'N/A')} GB")
                console.print(f"  Usage: {space.get('usage_percent', 'N/A')}%")
        else:
            log_error(logger, f"Failed to set destination: {base_path}/{backup_folder}")

    def check_destination(self):
        """Check backup destination"""
        space = self.config_manager.check_destination_space()

        if space.get('exists'):
            table = Table(title="Backup Destination")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Status", "Exists")
            table.add_row("Total Space", f"{space.get('total_gb', 'N/A')} GB")
            table.add_row("Used Space", f"{space.get('used_gb', 'N/A')} GB")
            table.add_row("Free Space", f"{space.get('free_gb', 'N/A')} GB")
            table.add_row("Usage", f"{space.get('usage_percent', 'N/A')}%")
            table.add_row("Minimum Required", f"{space.get('minimum_free_gb', 'N/A')} GB")

            is_sufficient = space.get('is_sufficient', False)
            status = "[green]Sufficient[/green]" if is_sufficient else "[red]Insufficient[/red]"
            table.add_row("Space Status", status)

            console.print(table)
        else:
            log_error(logger, space.get('error', 'Unknown error'))

    # ========== Global Schedule Configuration ==========

    def set_schedule(self, frequency: str, time: str, days: str = None):
        """Set global backup schedule"""
        days_of_week = None
        if days:
            days_of_week = [d.strip() for d in days.split(',')]

        log_info(logger, f"Setting global schedule: {frequency} at {time}")

        if self.config_manager.set_schedule(enabled=True, frequency=frequency, time=time, days_of_week=days_of_week):
            log_success(logger, f"Schedule set: {frequency} at {time}")
        else:
            log_error(logger, "Failed to set schedule. Invalid parameters.")

    def set_retention(self, daily: int, weekly: int, monthly: int, max_age: int, min_space: int):
        """Set global retention policy"""
        log_info(logger, f"Setting retention: daily={daily}, weekly={weekly}, monthly={monthly}, max_age={max_age}")

        if self.config_manager.set_retention(
            daily_count=daily,
            weekly_count=weekly,
            monthly_count=monthly,
            max_age_days=max_age,
            min_free_space_gb=min_space
        ):
            log_success(logger, "Retention policy set")
        else:
            log_error(logger, "Failed to set retention policy")

    # ========== Source Management ==========

    def add_source(self, path: str, recursive: bool, frequency: str, time: str,
                   day: int = None, day_of_week: str = None,
                   daily_retention: int = 7, weekly_retention: int = 4,
                   monthly_retention: int = 6, max_age: int = 180,
                   priority: str = "medium", description: str = "",
                   exclude: str = None):
        """Add a backup source with individual configuration"""
        log_info(logger, f"Adding backup source: {path}")

        # Build schedule
        schedule = {
            "enabled": True,
            "frequency": frequency,
            "time": time,
            "days_of_week": [day_of_week] if day_of_week else ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
            "day_of_month": day
        }

        # Build retention
        retention = {
            "daily_count": daily_retention,
            "weekly_count": weekly_retention,
            "monthly_count": monthly_retention,
            "max_age_days": max_age
        }

        # Parse exclude patterns
        exclude_patterns = []
        if exclude:
            exclude_patterns = [p.strip() for p in exclude.split(',')]

        if self.config_manager.add_source(
            path=path,
            recursive=recursive,
            exclude_patterns=exclude_patterns,
            schedule=schedule,
            retention=retention,
            priority=priority,
            description=description
        ):
            log_success(logger, f"Source added: {path}")
        else:
            log_error(logger, f"Failed to add source: {path}")

    def remove_source(self, path: str):
        """Remove a backup source"""
        log_info(logger, f"Removing backup source: {path}")

        if self.config_manager.remove_source(path):
            log_success(logger, f"Source removed: {path}")
        else:
            log_error(logger, f"Source not found: {path}")

    def toggle_source(self, path: str):
        """Toggle source enabled status"""
        result = self.config_manager.toggle_source(path)
        if result is not None:
            status = "enabled" if result else "disabled"
            log_success(logger, f"Source {status}: {path}")
        else:
            log_error(logger, f"Source not found: {path}")

    def list_sources(self):
        """List all configured sources"""
        sources = self.config_manager.list_sources()

        if not sources:
            console.print("[yellow]No backup sources configured[/yellow]")
            return

        table = Table(title="Backup Sources")
        table.add_column("Path", style="cyan", min_width=40)
        table.add_column("Status", style="green")
        table.add_column("Frequency", style="yellow")
        table.add_column("Next Backup", style="blue")
        table.add_column("Priority", style="magenta")

        for source in sources:
            status = "[green]+[/green]" if source['enabled'] else "[red]-[/red]"
            next_backup = source['next_backup']
            if next_backup:
                next_str = next_backup.strftime('%Y-%m-%d %H:%M')
            else:
                next_str = "N/A"

            table.add_row(
                source['path'],
                status,
                f"{source['frequency']} @ {source['time']}",
                next_str,
                source['priority']
            )

        console.print(table)
        console.print(f"\nTotal: {len(sources)} sources configured")

    # ========== Source-Specific Configuration ==========

    def set_source_schedule(self, path: str, frequency: str, time: str,
                            day: int = None, day_of_week: str = None):
        """Set schedule for a specific source"""
        days_of_week = [day_of_week] if day_of_week else None

        log_info(logger, f"Setting source schedule: {path} - {frequency} at {time}")

        if self.config_manager.set_source_schedule(
            path=path,
            frequency=frequency,
            time=time,
            days_of_week=days_of_week,
            day_of_month=day
        ):
            log_success(logger, f"Schedule updated for: {path}")
        else:
            log_error(logger, f"Failed to update schedule: {path}")

    def set_source_retention(self, path: str, daily: int, weekly: int, monthly: int, max_age: int):
        """Set retention for a specific source"""
        log_info(logger, f"Setting source retention: {path}")

        if self.config_manager.set_source_retention(
            path=path,
            daily_count=daily,
            weekly_count=weekly,
            monthly_count=monthly,
            max_age_days=max_age
        ):
            log_success(logger, f"Retention updated for: {path}")
        else:
            log_error(logger, f"Failed to update retention: {path}")

    # ========== Backup Execution ==========

    def run_backup(self, source_path: str = None):
        """Run backup manually"""
        if source_path:
            # Find source by path
            sources = self.config_manager.get_sources()
            source = next((s for s in sources if s['path'] == source_path), None)
            if not source:
                log_error(logger, f"Source not found: {source_path}")
                return
            log_info(logger, f"Running backup for: {source_path}")
        else:
            log_info(logger, "Running backup for all enabled sources")

        try:
            success, stats = self.backup_manager.run_backup(source=source)

            if success:
                log_success(logger, f"Backup completed - {stats['total_files']} files, {stats['total_size'] / (1024**2):.1f} MB")
            else:
                log_warning(logger, f"Backup completed with errors: {stats.get('errors', [])}")
        except Exception as e:
            log_error(logger, f"Backup failed: {e}")

    # ========== Statistics and History ==========

    def show_stats(self):
        """Show backup statistics"""
        state = self.config_manager.get_state()
        space = self.backup_manager.get_space_info()

        table = Table(title="Backup Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        # Last backup info
        last_backup = state.get('last_backup')
        if last_backup:
            table.add_row("Last Backup", last_backup.get('started_at', 'N/A'))
            table.add_row("Last Backup Status", last_backup.get('status', 'N/A'))
            table.add_row("Last Backup Duration", f"{last_backup.get('duration_seconds', 0):.1f} seconds")
            table.add_row("Last Backup Files", str(last_backup.get('total_files', 0)))
            table.add_row("Last Backup Size", f"{last_backup.get('total_size', 0) / (1024**2):.1f} MB")

        # Statistics
        stats = state.get('statistics', {})
        table.add_row("Total Backups", str(stats.get('total_backups', 0)))
        table.add_row("Successful", str(stats.get('successful_backups', 0)))
        table.add_row("Failed", str(stats.get('failed_backups', 0)))

        # Space info
        if space.get('error') is None:
            table.add_row("Backups Size", f"{space.get('backups_size_gb', 0):.2f} GB")
            table.add_row("Total Space", f"{space.get('total_gb', 0):.2f} GB")
            table.add_row("Free Space", f"{space.get('free_gb', 0):.2f} GB")
            table.add_row("Usage", f"{space.get('usage_percent', 0):.1f}%")

        console.print(table)

    def show_history(self, limit: int = 10):
        """Show backup history"""
        history = self.backup_manager.get_backup_history(limit)

        if not history:
            console.print("[yellow]No backup history available[/yellow]")
            return

        table = Table(title=f"Backup History (Last {limit})")
        table.add_column("Date", style="cyan")
        table.add_column("Type", style="yellow")
        table.add_column("Status", style="green")
        table.add_column("Duration", style="blue")
        table.add_column("Files", style="magenta")
        table.add_column("Size", style="red")

        for backup in history:
            date = backup.get('started_at', 'N/A')[:10]
            backup_type = backup.get('type', 'N/A')
            status = "[green]OK[/green]" if backup.get('status') == 'success' else "[yellow]WARN[/yellow]"
            duration = f"{backup.get('duration_seconds', 0):.0f}s"
            files = str(backup.get('total_files', 0))
            size = f"{backup.get('total_size', 0) / (1024**2):.1f} MB"

            table.add_row(date, backup_type, status, duration, files, size)

        console.print(table)

    def show_config(self):
        """Show full configuration"""
        config = self.config_manager.get_config()

        console.print(Panel("[bold cyan]Backup Configuration[/bold cyan]"))

        # Destination
        dest = config.get('destination', {})
        console.print(f"\n[bold]Destination:[/bold]")
        console.print(f"  Path: {dest.get('full_path', 'N/A')}")
        console.print(f"  Auto Create: {dest.get('auto_create', False)}")
        console.print(f"  Min Free Space: {dest.get('min_free_space_gb', 5)} GB")

        # Global Schedule
        schedule = config.get('schedule', {})
        console.print(f"\n[bold]Global Schedule:[/bold]")
        console.print(f"  Enabled: {schedule.get('enabled', False)}")
        console.print(f"  Frequency: {schedule.get('frequency', 'N/A')}")
        console.print(f"  Time: {schedule.get('time', 'N/A')}")

        # Global Retention
        retention = config.get('retention', {})
        console.print(f"\n[bold]Global Retention:[/bold]")
        console.print(f"  Daily: {retention.get('daily_count', 0)}")
        console.print(f"  Weekly: {retention.get('weekly_count', 0)}")
        console.print(f"  Monthly: {retention.get('monthly_count', 0)}")
        console.print(f"  Max Age: {retention.get('max_age_days', 0)} days")

        # Sources
        sources = config.get('sources', [])
        console.print(f"\n[bold]Sources ({len(sources)}):[/bold]")
        for source in sources:
            status = "[green]+[/green]" if source.get('enabled') else "[red]-[/red]"
            console.print(f"  {status} {source.get('path', 'N/A')}")
            console.print(f"      Frequency: {source.get('schedule', {}).get('frequency', 'N/A')}")
            console.print(f"      Priority: {source.get('priority', 'medium')}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Backup Subsystem CLI")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Daemon commands
    subparsers.add_parser('daemon-start', help='Start backup daemon')
    subparsers.add_parser('daemon-stop', help='Stop backup daemon')
    subparsers.add_parser('daemon-restart', help='Restart backup daemon')
    subparsers.add_parser('daemon-status', help='Show daemon status')

    # Destination commands
    dest_parser = subparsers.add_parser('set-destination', help='Set backup destination')
    dest_parser.add_argument('base_path', help='Base path for backups')
    dest_parser.add_argument('--folder', default='backups', help='Backup folder name')

    subparsers.add_parser('check-destination', help='Check backup destination')

    # Schedule commands
    schedule_parser = subparsers.add_parser('set-schedule', help='Set global schedule')
    schedule_parser.add_argument('--frequency', required=True, help='Frequency (hourly/daily/weekly/monthly/custom)')
    schedule_parser.add_argument('--time', required=True, help='Time (HH:MM)')
    schedule_parser.add_argument('--days', help='Days of week (comma-separated)')

    retention_parser = subparsers.add_parser('set-retention', help='Set global retention')
    retention_parser.add_argument('--daily', type=int, default=7, help='Daily backups to keep')
    retention_parser.add_argument('--weekly', type=int, default=4, help='Weekly backups to keep')
    retention_parser.add_argument('--monthly', type=int, default=6, help='Monthly backups to keep')
    retention_parser.add_argument('--max-age', type=int, default=180, help='Max age in days')
    retention_parser.add_argument('--min-space', type=int, default=10, help='Min free space in GB')

    # Source commands
    add_parser = subparsers.add_parser('add-source', help='Add backup source')
    add_parser.add_argument('path', help='Source path')
    add_parser.add_argument('--recursive', action='store_true', default=True, help='Include subdirectories')
    add_parser.add_argument('--frequency', default='daily', help='Backup frequency')
    add_parser.add_argument('--time', default='02:00', help='Backup time (HH:MM)')
    add_parser.add_argument('--day', type=int, help='Day of month (for monthly)')
    add_parser.add_argument('--day-of-week', help='Day of week (for weekly)')
    add_parser.add_argument('--daily-retention', type=int, default=7, help='Daily backups to keep')
    add_parser.add_argument('--weekly-retention', type=int, default=4, help='Weekly backups to keep')
    add_parser.add_argument('--monthly-retention', type=int, default=6, help='Monthly backups to keep')
    add_parser.add_argument('--max-age', type=int, default=180, help='Max age in days')
    add_parser.add_argument('--priority', default='medium', help='Priority (low/medium/high)')
    add_parser.add_argument('--description', default='', help='Description')
    add_parser.add_argument('--exclude', help='Exclude patterns (comma-separated)')

    remove_parser = subparsers.add_parser('remove-source', help='Remove backup source')
    remove_parser.add_argument('path', help='Source path')

    toggle_parser = subparsers.add_parser('toggle-source', help='Toggle source')
    toggle_parser.add_argument('path', help='Source path')

    subparsers.add_parser('list-sources', help='List backup sources')

    # Source-specific config
    source_schedule_parser = subparsers.add_parser('set-source-schedule', help='Set source schedule')
    source_schedule_parser.add_argument('path', help='Source path')
    source_schedule_parser.add_argument('--frequency', required=True, help='Frequency')
    source_schedule_parser.add_argument('--time', required=True, help='Time (HH:MM)')
    source_schedule_parser.add_argument('--day', type=int, help='Day of month')
    source_schedule_parser.add_argument('--day-of-week', help='Day of week')

    source_retention_parser = subparsers.add_parser('set-source-retention', help='Set source retention')
    source_retention_parser.add_argument('path', help='Source path')
    source_retention_parser.add_argument('--daily', type=int, default=7, help='Daily backups')
    source_retention_parser.add_argument('--weekly', type=int, default=4, help='Weekly backups')
    source_retention_parser.add_argument('--monthly', type=int, default=6, help='Monthly backups')
    source_retention_parser.add_argument('--max-age', type=int, default=180, help='Max age')

    # Execution commands
    run_parser = subparsers.add_parser('run', help='Run backup')
    run_parser.add_argument('--source', help='Specific source path')

    # Info commands
    subparsers.add_parser('stats', help='Show statistics')
    history_parser = subparsers.add_parser('history', help='Show backup history')
    history_parser.add_argument('--limit', type=int, default=10, help='Number of entries')
    subparsers.add_parser('config', help='Show configuration')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    cli = BackupCLI()

    # Execute command
    commands = {
        'daemon-start': cli.daemon_start,
        'daemon-stop': cli.daemon_stop,
        'daemon-restart': cli.daemon_restart,
        'daemon-status': cli.daemon_status,
        'set-destination': lambda: cli.set_destination(args.base_path, args.folder),
        'check-destination': cli.check_destination,
        'set-schedule': lambda: cli.set_schedule(args.frequency, args.time, args.days),
        'set-retention': lambda: cli.set_retention(args.daily, args.weekly, args.monthly, args.max_age, args.min_space),
        'add-source': lambda: cli.add_source(
            args.path, args.recursive, args.frequency, args.time,
            args.day, args.day_of_week, args.daily_retention,
            args.weekly_retention, args.monthly_retention, args.max_age,
            args.priority, args.description, args.exclude
        ),
        'remove-source': lambda: cli.remove_source(args.path),
        'toggle-source': lambda: cli.toggle_source(args.path),
        'list-sources': cli.list_sources,
        'set-source-schedule': lambda: cli.set_source_schedule(args.path, args.frequency, args.time, args.day, args.day_of_week),
        'set-source-retention': lambda: cli.set_source_retention(args.path, args.daily, args.weekly, args.monthly, args.max_age),
        'run': lambda: cli.run_backup(args.source),
        'stats': cli.show_stats,
        'history': lambda: cli.show_history(args.limit),
        'config': cli.show_config
    }

    if args.command in commands:
        commands[args.command]()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
