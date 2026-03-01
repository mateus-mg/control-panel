#!/usr/bin/env python3
"""
CLI Manager for Control Panel System
Command-line interface for managing HD drives, Docker containers, and system services
"""

# Flexible import to handle direct execution and importing
try:
    from .log_config import get_logger, log_success, log_error, log_warning, log_info, log_mount, log_docker, log_systemd
except ImportError:
    # When executed directly, use absolute imports
    import sys
    from pathlib import Path
    # Add scripts directory to path
    script_dir = Path(__file__).parent
    sys.path.insert(0, str(script_dir))

    from log_config import get_logger, log_success, log_error, log_warning, log_info, log_mount, log_docker, log_systemd

import sys
import os
import subprocess
import signal
import time
import filecmp
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.box import SIMPLE
from datetime import datetime, timedelta
from rich.prompt import Prompt

# Add scripts directory to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

console = Console()
logger = get_logger(__name__)


class CLIManager:
    """CLI manager for Control Panel System"""

    def __init__(self):
        """Initialize CLI manager"""
        self.script_dir = Path(os.getenv('SCRIPT_PATH', os.getcwd()))
        self.pid_file = self.script_dir / '.daemon.pid'
        self.log_file = self.script_dir / 'logs' / 'daemon.log'

        # HD Configuration
        self.hd_mount_point = "/media/mateus/Servidor"
        self.hd_uuid = "35feb867-8ee2-49a9-a1a5-719a67e3975a"
        self.hd_label = "Servidor"

        # Docker Configuration
        self.docker_compose_dir = Path("/home/mateus")
        self.docker_compose_file = self.docker_compose_dir / "docker-compose.yml"

    def show_interactive_menu(self):
        """Show interactive main menu"""
        from rich.prompt import Prompt
        while True:
            console.print("\n[bold cyan]🎛️ Control Panel System[/bold cyan]")
            console.print("[bold]Select an operation:[/bold]\n")

            # Options with submenus first (alphabetical), then other options (alphabetical)
            options = {
                "1": "Manage backups",
                "2": "Manage Docker containers",
                "3": "Manage HD drives",
                "4": "Manage systemd services",
                "5": "Run diagnostics",
                "6": "Sync files",
                "7": "View logs",
                "8": "View system status",
                "9": "Exit"
            }

            for key, value in options.items():
                console.print(f"  [bold cyan][{key}][/bold cyan]  {value}")

            try:
                choice = Prompt.ask("\n[bold]Your choice[/bold]", choices=list(
                    options.keys()), default="9")

                if choice == '1':
                    self.show_backup_menu()
                elif choice == '2':
                    self.show_docker_menu()
                elif choice == '3':
                    self.show_hd_menu()
                elif choice == '4':
                    self.show_systemd_menu()
                elif choice == '5':
                    self.diagnostics_interactive()
                elif choice == '6':
                    self.sync_interactive()
                elif choice == '7':
                    lines = Prompt.ask(
                        "How many log lines do you want to see?", default="50", show_default=True)
                    self.view_logs_interactive(int(lines))
                elif choice == '8':
                    self.show_status_interactive()
                elif choice == '9':
                    console.print("[green]Exiting... Goodbye![/green]")
                    break

                # Pause before showing the menu again
                input("\nPress Enter to continue...")

            except KeyboardInterrupt:
                console.print("\n[red]Operation cancelled by user.[/red]")
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

    def get_docker_services(self):
        """Get list of available Docker services"""
        try:
            os.chdir(self.docker_compose_dir)
            result = subprocess.run(['docker', 'compose', 'config', '--services'],
                                    capture_output=True, text=True)
            if result.stdout:
                return result.stdout.strip().split('\n')
            return []
        except Exception:
            return []

    def select_docker_service(self, include_all_option=True):
        """Select a Docker service from a numbered list

        Args:
            include_all_option: If True, adds "All services" option

        Returns:
            Selected service name, None for "All services", or False if cancelled
        """
        services = self.get_docker_services()

        if not services:
            console.print("[red]No services found in docker-compose.yml[/red]")
            return False

        console.print("\n[bold cyan]🐳 Select a service:[/bold cyan]\n")

        # Build options dict - services numbered 1-N
        options = {}

        for idx, service in enumerate(services, start=1):
            options[str(idx)] = service

        # Display services first (1-N)
        for idx, service in enumerate(services, start=1):
            console.print(f"  [bold cyan][{idx}][/bold cyan]  {service}")

        # Add "All services" as [0] at the END
        all_services_key = None
        if include_all_option:
            all_services_key = "0"
            options[all_services_key] = "All services"
            console.print(f"  [bold cyan][0][/bold cyan]  All services")

        try:
            choice = Prompt.ask("\n[bold]Your choice[/bold]", choices=list(options.keys()))

            if choice == all_services_key:
                return None  # All services
            else:
                return options[choice]

        except KeyboardInterrupt:
            console.print("\n[red]Selection cancelled[/red]")
            return False

    def show_docker_menu(self):
        """Show interactive Docker management menu"""
        from rich.prompt import Prompt
        while True:
            console.print("\n[bold cyan]🐳 Docker Management[/bold cyan]")
            console.print("[bold]Select an operation:[/bold]\n")

            options = {
                "1": "Start Docker services",
                "2": "Stop Docker services",
                "3": "Restart Docker services",
                "4": "View running containers",
                "5": "View Docker logs",
                "6": "Clean old containers",
                "7": "Pull updated images",
                "8": "List services",
                "9": "Return to main menu"
            }

            for key, value in options.items():
                console.print(f"  [bold cyan][{key}][/bold cyan]  {value}")

            try:
                choice = Prompt.ask("\n[bold]Your choice[/bold]", choices=list(
                    options.keys()), default="9")

                if choice == '1':
                    service = self.select_docker_service(
                        include_all_option=True)
                    if service is not False:  # Not cancelled
                        self.start_docker_interactive(service)
                elif choice == '2':
                    service = self.select_docker_service(
                        include_all_option=True)
                    if service is not False:
                        self.stop_docker_interactive(service)
                elif choice == '3':
                    service = self.select_docker_service(
                        include_all_option=True)
                    if service is not False:
                        self.restart_docker_interactive(service)
                elif choice == '4':
                    self.show_docker_ps()
                elif choice == '5':
                    service = self.select_docker_service(
                        include_all_option=False)
                    if service:
                        self.show_docker_logs(service)
                elif choice == '6':
                    service = self.select_docker_service(
                        include_all_option=True)
                    if service is not False:
                        self.clean_docker_interactive(service)
                elif choice == '7':
                    self.pull_docker_images()
                elif choice == '8':
                    self.list_docker_services()
                elif choice == '9':
                    break
                else:
                    console.print(
                        "[red]Invalid option. Please choose a valid option.[/red]")

                # Pause before showing the menu again
                if choice != '9':
                    input("\nPress Enter to continue...")

            except KeyboardInterrupt:
                console.print("\n[red]Operation cancelled by user.[/red]")
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

    def show_systemd_menu(self):
        """Show interactive systemd management menu"""
        from rich.prompt import Prompt
        while True:
            console.print(
                "\n[bold cyan]⚙️ Systemd Services Management[/bold cyan]")
            console.print("[bold]Select an operation:[/bold]\n")

            options = {
                "1": "View keepalive service status",
                "2": "Start keepalive service",
                "3": "Restart keepalive service",
                "4": "Stop keepalive service",
                "5": "Enable keepalive service",
                "6": "Disable keepalive service",
                "7": "View keepalive logs",
                "8": "Return to main menu"
            }

            for key, value in options.items():
                console.print(f"  [bold cyan][{key}][/bold cyan]  {value}")

            try:
                choice = Prompt.ask("\n[bold]Your choice[/bold]", choices=list(
                    options.keys()), default="8")

                if choice == '1':
                    self.systemd_keepalive_status()
                elif choice == '2':
                    self.systemd_keepalive_start()
                elif choice == '3':
                    self.systemd_keepalive_restart()
                elif choice == '4':
                    self.systemd_keepalive_stop()
                elif choice == '5':
                    self.systemd_keepalive_enable()
                elif choice == '6':
                    self.systemd_keepalive_disable()
                elif choice == '7':
                    follow = Prompt.ask(
                        "Follow logs? (y/n)", choices=["y", "n"], default="n")
                    self.systemd_keepalive_logs(follow == "y")
                elif choice == '8':
                    break
                else:
                    console.print(
                        "[red]Invalid option. Please choose a valid option.[/red]")

                # Pause before showing the menu again
                input("\nPress Enter to continue...")

            except KeyboardInterrupt:
                console.print("\n[red]Operation cancelled by user.[/red]")
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

    def show_hd_menu(self):
        """Show interactive HD drives management menu"""
        from rich.prompt import Prompt
        while True:
            console.print(
                "\n[bold cyan]💾 HD Drives Management[/bold cyan]")
            console.print("[bold]Select an operation:[/bold]\n")

            options = {
                "1": "Mount HD drive",
                "2": "Unmount HD drive",
                "3": "Fix mount point",
                "4": "Keep HD alive (monitor mode)",
                "5": "Check active mounts",
                "6": "Return to main menu"
            }

            for key, value in options.items():
                console.print(f"  [bold cyan][{key}][/bold cyan]  {value}")

            try:
                choice = Prompt.ask("\n[bold]Your choice[/bold]", choices=list(
                    options.keys()), default="6")

                if choice == '1':
                    self.mount_hd_interactive()
                elif choice == '2':
                    self.unmount_hd_interactive()
                elif choice == '3':
                    self.fix_mount_point_interactive()
                elif choice == '4':
                    self.keepalive_hd_interactive()
                elif choice == '5':
                    self.check_mounts()
                elif choice == '6':
                    break

                # Pause before showing the menu again
                if choice != '6':
                    input("\nPress Enter to continue...")

            except KeyboardInterrupt:
                console.print("\n[red]Operation cancelled by user.[/red]")
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

    def show_backup_menu(self):
        """Show interactive backup management menu"""
        from rich.prompt import Prompt
        while True:
            console.print(
                "\n[bold cyan]📦 Backup Subsystem Management[/bold cyan]")
            console.print("[bold]Select an operation:[/bold]\n")

            options = {
                "1": "Daemon Management",
                "2": "Manage Backup Sources",
                "3": "Configure Destination",
                "4": "Configure Schedule (Global)",
                "5": "Configure Retention (Global)",
                "6": "Run Backup Now",
                "7": "View Statistics",
                "8": "View History",
                "9": "View Configuration",
                "10": "Return to main menu"
            }

            for key, value in options.items():
                console.print(f"  [bold cyan][{key}][/bold cyan]  {value}")

            try:
                choice = Prompt.ask("\n[bold]Your choice[/bold]", choices=list(
                    options.keys()), default="10")

                if choice == '1':
                    self.show_backup_daemon_menu()
                elif choice == '2':
                    self.show_backup_sources_menu()
                elif choice == '3':
                    self.backup_set_destination()
                elif choice == '4':
                    self.backup_set_schedule()
                elif choice == '5':
                    self.backup_set_retention()
                elif choice == '6':
                    self.backup_run_now()
                elif choice == '7':
                    self.backup_show_stats()
                elif choice == '8':
                    self.backup_show_history()
                elif choice == '9':
                    self.backup_show_config()
                elif choice == '10':
                    break
                else:
                    console.print(
                        "[red]Invalid option. Please choose a valid option.[/red]")

                # Pause before showing the menu again
                if choice != '10':
                    input("\nPress Enter to continue...")

            except KeyboardInterrupt:
                console.print("\n[red]Operation cancelled by user.[/red]")
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

    def show_backup_daemon_menu(self):
        """Show backup daemon management submenu"""
        from rich.prompt import Prompt
        while True:
            console.print(
                "\n[bold cyan]📦 Backup Daemon Management[/bold cyan]")
            console.print("[bold]Select an operation:[/bold]\n")

            options = {
                "1": "Start daemon",
                "2": "Stop daemon",
                "3": "Restart daemon",
                "4": "View status",
                "5": "Return"
            }

            for key, value in options.items():
                console.print(f"  [bold cyan][{key}][/bold cyan]  {value}")

            try:
                choice = Prompt.ask("\n[bold]Your choice[/bold]", choices=list(
                    options.keys()), default="5")

                if choice == '1':
                    self.backup_daemon_start()
                elif choice == '2':
                    self.backup_daemon_stop()
                elif choice == '3':
                    self.backup_daemon_restart()
                elif choice == '4':
                    self.backup_daemon_status()
                elif choice == '5':
                    break

                if choice != '5':
                    input("\nPress Enter to continue...")

            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

    def show_backup_sources_menu(self):
        """Show backup sources management submenu"""
        from rich.prompt import Prompt
        while True:
            console.print(
                "\n[bold cyan]📦 Backup Sources Management[/bold cyan]")
            console.print("[bold]Select an operation:[/bold]\n")

            options = {
                "1": "Add source",
                "2": "Remove source",
                "3": "Enable/Disable source",
                "4": "List sources",
                "5": "Configure source schedule",
                "6": "Configure source retention",
                "7": "Return"
            }

            for key, value in options.items():
                console.print(f"  [bold cyan][{key}][/bold cyan]  {value}")

            try:
                choice = Prompt.ask("\n[bold]Your choice[/bold]", choices=list(
                    options.keys()), default="7")

                if choice == '1':
                    self.backup_add_source()
                elif choice == '2':
                    self.backup_remove_source()
                elif choice == '3':
                    self.backup_toggle_source()
                elif choice == '4':
                    self.backup_list_sources()
                elif choice == '5':
                    self.backup_set_source_schedule()
                elif choice == '6':
                    self.backup_set_source_retention()
                elif choice == '7':
                    break

                if choice != '7':
                    input("\nPress Enter to continue...")

            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

    # ========== Backup Methods ==========

    def backup_daemon_start(self):
        """Start backup daemon"""
        import subprocess
        script_path = Path(__file__).parent / 'backup_cli.py'
        subprocess.run([sys.executable, str(script_path), 'daemon-start'])

    def backup_daemon_stop(self):
        """Stop backup daemon"""
        import subprocess
        script_path = Path(__file__).parent / 'backup_cli.py'
        subprocess.run([sys.executable, str(script_path), 'daemon-stop'])

    def backup_daemon_restart(self):
        """Restart backup daemon"""
        import subprocess
        script_path = Path(__file__).parent / 'backup_cli.py'
        subprocess.run([sys.executable, str(script_path), 'daemon-restart'])

    def backup_daemon_status(self):
        """Show backup daemon status"""
        import subprocess
        script_path = Path(__file__).parent / 'backup_cli.py'
        subprocess.run([sys.executable, str(script_path), 'daemon-status'])

    def backup_set_destination(self):
        """Set backup destination"""
        from rich.prompt import Prompt
        base_path = Prompt.ask("Enter base path for backups",
                               default="/media/mateus/Servidor")
        folder = Prompt.ask("Enter backup folder name", default="backups")

        import subprocess
        script_path = Path(__file__).parent / 'backup_cli.py'
        subprocess.run([sys.executable, str(script_path),
                       'set-destination', base_path, '--folder', folder])

    def backup_set_schedule(self):
        """Set global backup schedule"""
        from rich.prompt import Prompt
        console.print("\n[bold]Frequency options:[/bold]")
        console.print("  1. hourly - Every hour")
        console.print("  2. daily - Once per day")
        console.print("  3. weekly - Once per week")
        console.print("  4. monthly - Once per month")
        console.print("  5. custom - Specific days")

        freq_choice = Prompt.ask("Choose frequency", choices=["1", "2", "3", "4", "5"], default="2")
        freq_map = {"1": "hourly", "2": "daily", "3": "weekly", "4": "monthly", "5": "custom"}
        frequency = freq_map[freq_choice]

        time_val = Prompt.ask("Enter time (HH:MM)", default="02:00")
        days = None
        if frequency == "custom":
            days = Prompt.ask("Enter days (e.g., mon,wed,fri)", default="mon,wed,fri")

        import subprocess
        script_path = Path(__file__).parent / 'backup_cli.py'
        cmd = [sys.executable, str(script_path), 'set-schedule',
               '--frequency', frequency, '--time', time_val]
        if days:
            cmd.extend(['--days', days])
        subprocess.run(cmd)

    def backup_set_retention(self):
        """Set global retention policy"""
        from rich.prompt import Prompt
        daily = Prompt.ask("Daily backups to keep", default="7")
        weekly = Prompt.ask("Weekly backups to keep", default="4")
        monthly = Prompt.ask("Monthly backups to keep", default="6")
        max_age = Prompt.ask("Max age in days (0 = unlimited)", default="180")
        min_space = Prompt.ask("Min free space in GB", default="10")

        import subprocess
        script_path = Path(__file__).parent / 'backup_cli.py'
        subprocess.run([sys.executable, str(script_path), 'set-retention',
                       '--daily', daily, '--weekly', weekly, '--monthly', monthly,
                       '--max-age', max_age, '--min-space', min_space])

    def backup_add_source(self):
        """Add a backup source"""
        from rich.prompt import Prompt
        path = Prompt.ask("Enter source path")

        # Validate path
        if not Path(path).exists():
            console.print(f"[red]Path does not exist: {path}[/red]")
            return

        recursive = Prompt.ask("Include subdirectories recursively?",
                               choices=["y", "n"], default="y") == "y"

        console.print("\n[bold]Frequency options:[/bold]")
        console.print("  1. daily - Once per day")
        console.print("  2. weekly - Once per week")
        console.print("  3. monthly - Once per month")
        freq_choice = Prompt.ask("Choose frequency", choices=["1", "2", "3"], default="1")
        freq_map = {"1": "daily", "2": "weekly", "3": "monthly"}
        frequency = freq_map[freq_choice]

        time_val = Prompt.ask("Enter backup time (HH:MM)", default="02:00")

        day = None
        day_of_week = None
        if frequency == "monthly":
            day = Prompt.ask("Day of month (1-28)", default="1", validate=lambda x: x.isdigit() and 1 <= int(x) <= 28)
            day = int(day)
        elif frequency == "weekly":
            console.print("  1. Sunday")
            console.print("  2. Monday")
            console.print("  3. Tuesday")
            console.print("  4. Wednesday")
            console.print("  5. Thursday")
            console.print("  6. Friday")
            console.print("  7. Saturday")
            dow_choice = Prompt.ask("Choose day", choices=["1", "2", "3", "4", "5", "6", "7"], default="1")
            dow_map = {"1": "sunday", "2": "monday", "3": "tuesday", "4": "wednesday",
                      "5": "thursday", "6": "friday", "7": "saturday"}
            day_of_week = dow_map[dow_choice]

        priority = Prompt.ask("Priority", choices=["low", "medium", "high"], default="medium")
        description = Prompt.ask("Description (optional)", default="")
        exclude = Prompt.ask("Exclude patterns (comma-separated, optional)", default="")

        import subprocess
        script_path = Path(__file__).parent / 'backup_cli.py'
        cmd = [sys.executable, str(script_path), 'add-source', path]
        if recursive:
            cmd.append('--recursive')
        cmd.extend(['--frequency', frequency, '--time', time_val])
        if day:
            cmd.extend(['--day', str(day)])
        if day_of_week:
            cmd.extend(['--day-of-week', day_of_week])
        cmd.extend(['--priority', priority])
        if description:
            cmd.extend(['--description', description])
        if exclude:
            cmd.extend(['--exclude', exclude])
        subprocess.run(cmd)

    def backup_remove_source(self):
        """Remove a backup source"""
        from rich.prompt import Prompt
        self.backup_list_sources()
        path = Prompt.ask("Enter source path to remove")

        import subprocess
        script_path = Path(__file__).parent / 'backup_cli.py'
        subprocess.run([sys.executable, str(script_path), 'remove-source', path])

    def backup_toggle_source(self):
        """Toggle source enabled status"""
        from rich.prompt import Prompt
        self.backup_list_sources()
        path = Prompt.ask("Enter source path to toggle")

        import subprocess
        script_path = Path(__file__).parent / 'backup_cli.py'
        subprocess.run([sys.executable, str(script_path), 'toggle-source', path])

    def backup_list_sources(self):
        """List all backup sources"""
        import subprocess
        script_path = Path(__file__).parent / 'backup_cli.py'
        subprocess.run([sys.executable, str(script_path), 'list-sources'])

    def backup_set_source_schedule(self):
        """Set schedule for a specific source"""
        from rich.prompt import Prompt
        self.backup_list_sources()
        path = Prompt.ask("Enter source path")

        frequency = Prompt.ask("Frequency", choices=["daily", "weekly", "monthly", "custom"], default="daily")
        time_val = Prompt.ask("Time (HH:MM)", default="02:00")
        day_of_week = None
        day = None

        if frequency in ["weekly", "custom"]:
            day_of_week = Prompt.ask("Day of week (e.g., sunday)", default="sunday")
        elif frequency == "monthly":
            day = Prompt.ask("Day of month (1-28)", default="1")

        import subprocess
        script_path = Path(__file__).parent / 'backup_cli.py'
        cmd = [sys.executable, str(script_path), 'set-source-schedule',
               path, '--frequency', frequency, '--time', time_val]
        if day_of_week:
            cmd.extend(['--day-of-week', day_of_week])
        if day:
            cmd.extend(['--day', day])
        subprocess.run(cmd)

    def backup_set_source_retention(self):
        """Set retention for a specific source"""
        from rich.prompt import Prompt
        self.backup_list_sources()
        path = Prompt.ask("Enter source path")

        daily = Prompt.ask("Daily backups to keep", default="7")
        weekly = Prompt.ask("Weekly backups to keep", default="4")
        monthly = Prompt.ask("Monthly backups to keep", default="6")
        max_age = Prompt.ask("Max age in days", default="180")

        import subprocess
        script_path = Path(__file__).parent / 'backup_cli.py'
        subprocess.run([sys.executable, str(script_path), 'set-source-retention',
                       path, '--daily', daily, '--weekly', weekly,
                       '--monthly', monthly, '--max-age', max_age])

    def backup_run_now(self):
        """Run backup immediately"""
        from rich.prompt import Prompt
        run_all = Prompt.ask("Backup all sources?", choices=["y", "n"], default="y")

        import subprocess
        script_path = Path(__file__).parent / 'backup_cli.py'
        if run_all == "y":
            subprocess.run([sys.executable, str(script_path), 'run'])
        else:
            self.backup_list_sources()
            path = Prompt.ask("Enter source path")
            subprocess.run([sys.executable, str(script_path), 'run', '--source', path])

    def backup_show_stats(self):
        """Show backup statistics"""
        import subprocess
        script_path = Path(__file__).parent / 'backup_cli.py'
        subprocess.run([sys.executable, str(script_path), 'stats'])

    def backup_show_history(self):
        """Show backup history"""
        from rich.prompt import Prompt
        limit = Prompt.ask("Number of entries", default="10")

        import subprocess
        script_path = Path(__file__).parent / 'backup_cli.py'
        subprocess.run([sys.executable, str(script_path), 'history', '--limit', limit])

    def backup_show_config(self):
        """Show backup configuration"""
        import subprocess
        script_path = Path(__file__).parent / 'backup_cli.py'
        subprocess.run([sys.executable, str(script_path), 'config'])

    def handle_backup_command(self, args):
        """Handle backup subsystem commands"""
        import subprocess
        script_path = Path(__file__).parent / 'backup_cli.py'
        cmd = [sys.executable, str(script_path)] + args
        subprocess.run(cmd)

    def mount_hd_interactive(self):
        """Interactive HD mounting"""
        console.print("\n[bold cyan]📀 Mounting HD Drive[/bold cyan]")

        try:
            # Check if already mounted
            if self.is_hd_mounted():
                log_warning(
                    logger, f"HD already mounted at {self.hd_mount_point}")
                return

            # Auto-detect device by UUID/label
            hd_device = self.get_device_by_uuid()

            if not hd_device:
                log_error(
                    logger, f"HD not detected (UUID: {self.hd_uuid}). Check the connection.")
                return

            console.print(f"[green]✓ HD device detected: {hd_device}[/green]")

            # Create mount point if needed
            subprocess.run(
                ['sudo', 'mkdir', '-p', self.hd_mount_point], check=False)
            subprocess.run(['sudo', 'chown', 'mateus:mateus',
                           self.hd_mount_point], check=False)

            # Mount the drive
            result = subprocess.run(['sudo', 'mount', f'UUID={self.hd_uuid}', self.hd_mount_point],
                                    capture_output=True, text=True)

            if result.returncode == 0:
                log_success(
                    logger, f"HD mounted successfully at {self.hd_mount_point}")
            else:
                log_error(logger, f"Failed to mount HD: {result.stderr}")

        except Exception as e:
            log_error(logger, f"Error mounting HD: {str(e)}")

    def unmount_hd_interactive(self):
        """Interactive HD unmounting"""
        console.print("\n[bold cyan]📤 Unmounting HD Drive[/bold cyan]")

        try:
            if not self.is_hd_mounted():
                log_warning(logger, f"HD not mounted at {self.hd_mount_point}")
                return

            # Sync before unmount
            subprocess.run(['/bin/sync'], check=False)

            # Try normal unmount
            result = subprocess.run(['sudo', 'umount', self.hd_mount_point],
                                    capture_output=True, text=True)

            if result.returncode == 0:
                log_success(logger, f"HD unmounted from {self.hd_mount_point}")
            else:
                # Try lazy unmount
                console.print(
                    "[yellow]! Normal unmount failed, trying lazy unmount...[/yellow]")
                subprocess.run(
                    ['sudo', 'umount', '-l', self.hd_mount_point], check=False)
                log_success(
                    logger, f"Lazy unmount applied to {self.hd_mount_point}")

        except Exception as e:
            log_error(logger, f"Error unmounting HD: {str(e)}")

    def is_hd_mounted(self):
        """Check if HD is mounted"""
        result = subprocess.run(['mountpoint', '-q', self.hd_mount_point],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return result.returncode == 0

    def get_device_by_uuid(self):
        """Get device by UUID"""
        try:
            result = subprocess.run(['blkid', '-U', self.hd_uuid],
                                    capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()

            # Fallback: search by label
            result = subprocess.run(['blkid', '-L', self.hd_label],
                                    capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()

            return None
        except Exception:
            return None

    def show_status_interactive(self):
        """Show system status"""
        console.print("\n[bold cyan]📊 System Status[/bold cyan]")

        # HD status
        console.print("\n[bold]📀 HD Status:[/bold]")
        if self.is_hd_mounted():
            log_success(logger, f"MOUNTED at {self.hd_mount_point}")
            try:
                result = subprocess.run(['df', '-h', self.hd_mount_point],
                                        capture_output=True, text=True)
                if result.stdout:
                    # Show df output directly (preserves formatting)
                    console.print(result.stdout)
            except Exception as e:
                console.print(f"[red]Error getting disk usage: {e}[/red]")
        else:
            log_error(logger, f"NOT MOUNTED")
            detected_device = self.get_device_by_uuid()
            if detected_device:
                console.print(
                    f"[yellow]i Device detected: {detected_device}[/yellow]")
            else:
                console.print("[yellow]i Device: NOT DETECTED[/yellow]")

        # Docker status
        console.print("\n[bold]🐳 Docker Status:[/bold]")
        try:
            if subprocess.run(['docker', 'ps'],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
                result = subprocess.run(['docker', 'ps', '--format', '{{json .}}'],
                                        capture_output=True, text=True)
                if result.stdout:
                    # Parse JSON output to create a properly formatted Rich table
                    import json
                    containers = []
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            try:
                                containers.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue

                    if containers:
                        table = Table(title="Running Containers",
                                      show_header=True, header_style="bold blue")
                        table.add_column("Name", style="dim",
                                         min_width=15, max_width=30)
                        table.add_column("Status", min_width=15, max_width=25)
                        table.add_column("Ports", min_width=20,
                                         max_width=50, overflow="fold")

                        for container in containers:
                            name = container.get('Names', 'N/A')
                            status = container.get('Status', 'N/A')
                            ports = container.get('Ports', 'N/A')

                            # Limit the length of ports display
                            if len(ports) > 50:
                                ports = ports[:47] + "..."

                            table.add_row(name, status, ports)

                        console.print(table)
                    else:
                        console.print("   No running containers")
                else:
                    console.print("   No running containers")
            else:
                console.print("[red]✗ Docker not available[/red]")
        except Exception as e:
            console.print(f"[red]Error checking Docker: {e}[/red]")

    def start_docker_interactive(self, service=None):
        """Start Docker services interactively"""
        console.print(
            f"\n[bold cyan]🚀 Starting Docker{' service: ' + service if service else ' all services'}[/bold cyan]")

        try:
            os.chdir(self.docker_compose_dir)

            cmd = ['docker', 'compose', '--ansi', 'never', 'up', '-d']
            if service:
                cmd.append(service)

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                log_success(
                    logger, f"Docker{' service: ' + service if service else ' services'} started")
            else:
                log_error(
                    logger, f"Failed to start Docker services: {result.stderr}")

        except Exception as e:
            log_error(logger, f"Error starting Docker: {str(e)}")

    def stop_docker_interactive(self, service=None):
        """Stop Docker services interactively"""
        console.print(
            f"\n[bold cyan]⏹️ Stopping Docker{' service: ' + service if service else ' all services'}[/bold cyan]")

        try:
            os.chdir(self.docker_compose_dir)

            cmd = ['docker', 'compose', '--ansi', 'never', 'stop']
            if service:
                cmd.append(service)

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                log_success(
                    logger, f"Docker{' service: ' + service if service else ' services'} stopped")
            else:
                log_error(
                    logger, f"Failed to stop Docker services: {result.stderr}")

        except Exception as e:
            log_error(logger, f"Error stopping Docker: {str(e)}")

    def restart_docker_interactive(self, service=None):
        """Restart Docker services interactively"""
        console.print(
            f"\n[bold cyan]🔄 Restarting Docker{' service: ' + service if service else ' all services'}[/bold cyan]")

        try:
            os.chdir(self.docker_compose_dir)

            cmd = ['docker', 'compose', '--ansi', 'never', 'restart']
            if service:
                cmd.append(service)

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                log_success(
                    logger, f"Docker{' service: ' + service if service else ' services'} restarted")
            else:
                log_error(
                    logger, f"Failed to restart Docker services: {result.stderr}")

        except Exception as e:
            log_error(logger, f"Error restarting Docker: {str(e)}")

    def show_docker_ps(self):
        """Show running Docker containers"""
        console.print("\n[bold cyan]📋 Running Containers[/bold cyan]")

        try:
            result = subprocess.run(['docker', 'ps', '--format', '{{json .}}'],
                                    capture_output=True, text=True)
            if result.stdout:
                # Parse JSON output to create a properly formatted Rich table
                import json
                import shutil
                containers = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            containers.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue

                if containers:
                    # Check terminal width and adjust table accordingly
                    try:
                        term_width = shutil.get_terminal_size().columns
                    except:
                        term_width = 80

                    # Use compact layout for narrow terminals
                    use_compact = term_width < 120

                    if use_compact:
                        # Compact table for narrow terminals
                        table = Table(title="Running Containers",
                                      show_header=True, header_style="bold blue", box=SIMPLE, expand=True)
                        table.add_column("Name", style="dim", min_width=15, max_width=25, no_wrap=False)
                        table.add_column("Status", style="default", min_width=18, max_width=22, no_wrap=False)
                        table.add_column("Ports", style="default", min_width=15, overflow="fold")
                    else:
                        # Full table for wide terminals
                        table = Table(title="Running Containers",
                                      show_header=True, header_style="bold blue", box=SIMPLE, expand=True)
                        table.add_column("Name", style="dim", min_width=15, max_width=30, no_wrap=False)
                        table.add_column("Status", style="default", min_width=20, max_width=25, no_wrap=False)
                        table.add_column("Ports", style="default", min_width=25, max_width=60, overflow="fold")

                    for container in containers:
                        name = container.get('Names', 'N/A')
                        status = container.get('Status', 'N/A')
                        ports = container.get('Ports', 'N/A')

                        table.add_row(name, status, ports)

                    console.print(table)
                else:
                    console.print("   No running containers")
            else:
                console.print("   No running containers")
        except Exception as e:
            console.print(f"[red]Error listing containers: {e}[/red]")

    def show_docker_logs(self, service):
        """Show Docker service logs"""
        console.print(
            f"\n[bold cyan]📜 Docker Logs for {service}[/bold cyan]")

        try:
            result = subprocess.run(['docker', 'compose', 'logs', service],
                                    capture_output=True, text=True)
            if result.stdout:
                # Show last 20 lines
                lines = result.stdout.split('\n')
                for line in lines[-20:]:
                    console.print(line)
            else:
                console.print("   No logs available")
        except Exception as e:
            console.print(f"[red]Error getting logs: {e}[/red]")

    def clean_docker_interactive(self, service=None):
        """Clean old Docker containers"""
        console.print(
            f"\n[bold cyan]🧹 Cleaning Docker{' container: ' + service if service else ' all containers'}[/bold cyan]")

        try:
            os.chdir(self.docker_compose_dir)

            cmd = ['docker', 'compose', '--ansi', 'never', 'rm', '-f', '-s']
            if service:
                cmd.append(service)

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                log_success(
                    logger, f"Old Docker{' container: ' + service if service else ' containers'} removed")
            else:
                log_error(
                    logger, f"Failed to clean Docker containers: {result.stderr}")

        except Exception as e:
            log_error(logger, f"Error cleaning Docker: {str(e)}")

    def pull_docker_images(self):
        """Pull updated Docker images"""
        console.print("\n[bold cyan]⬇️ Pulling Updated Images[/bold cyan]")

        try:
            os.chdir(self.docker_compose_dir)

            result = subprocess.run(['docker', 'compose', '--ansi', 'never', 'pull'],
                                    capture_output=True, text=True)

            if result.returncode == 0:
                log_success(logger, "Docker images updated")
            else:
                log_error(logger, f"Failed to pull images: {result.stderr}")

        except Exception as e:
            log_error(logger, f"Error pulling images: {str(e)}")

    def list_docker_services(self):
        """List Docker services"""
        console.print("\n[bold cyan]📋 Available Docker Services[/bold cyan]")

        try:
            os.chdir(self.docker_compose_dir)

            result = subprocess.run(['docker', 'compose', 'config', '--services'],
                                    capture_output=True, text=True)

            if result.stdout:
                services = result.stdout.strip().split('\n')
                for service in services:
                    console.print(f"  • {service}")
            else:
                console.print("   No services found")
        except Exception as e:
            console.print(f"[red]Error listing services: {e}[/red]")

    def keepalive_hd_interactive(self):
        """Keep HD alive interactively"""
        console.print(
            "\n[bold cyan]💓 Starting keepalive mode (60s interval)[/bold cyan]")
        console.print("[cyan]i Press Ctrl+C to stop[/cyan]")

        try:
            retry_count = 0
            max_retries = 5
            loop_seconds = 60

            while True:
                if not self.is_hd_mounted():
                    retry_count += 1
                    console.print(
                        f"[yellow]! HD not mounted, attempt {retry_count} of {max_retries}...[/yellow]")

                    if retry_count >= max_retries:
                        console.print(
                            "[red]✗ Retry limit reached. Pausing for 5 minutes before retrying.[/red]")
                        retry_count = 0
                        time.sleep(300)
                        continue

                    if self.mount_hd_interactive():
                        console.print(
                            "[green]✓ HD remounted successfully[/green]")
                        retry_count = 0
                    else:
                        console.print(
                            "[red]✗ Failed to remount HD. Retrying in {loop_seconds} seconds.[/red]")
                        time.sleep(loop_seconds)
                else:
                    retry_count = 0
                    console.print(
                        f"[green]✓ HD mounted at {self.hd_mount_point}[/green]")
                    # Touch marker file to avoid wear
                    marker_file = os.path.join(
                        self.hd_mount_point, '.keepalive')
                    try:
                        with open(marker_file, 'a'):
                            os.utime(marker_file, None)
                    except:
                        pass  # Ignore errors touching marker file

                time.sleep(loop_seconds)

        except KeyboardInterrupt:
            console.print("\n[red]💓 Keepalive stopped by user[/red]")

    def fix_mount_point_interactive(self):
        """Fix mount point interactively"""
        console.print("\n[bold cyan]🔧 Fixing Mount Point[/bold cyan]")

        try:
            # Remove mount point if exists
            if os.path.isdir(self.hd_mount_point):
                subprocess.run(
                    ['sudo', 'rmdir', self.hd_mount_point], check=False)

            # Create new mount point
            subprocess.run(
                ['sudo', 'mkdir', '-p', self.hd_mount_point], check=True)
            subprocess.run(['sudo', 'chown', 'mateus:mateus',
                           self.hd_mount_point], check=True)

            log_success(logger, f"Mount point fixed: {self.hd_mount_point}")

        except Exception as e:
            log_error(logger, f"Error fixing mount point: {str(e)}")

    def sync_interactive(self):
        """Sync files interactively"""
        console.print("\n[bold cyan]🔄 Synchronizing Files[/bold cyan]")

        try:
            # Ensure directories exist
            os.makedirs(os.path.expanduser("~/.local/bin"), exist_ok=True)
            os.makedirs(os.path.expanduser("~/scripts"), exist_ok=True)

            # Get project root directory (parent of scripts directory)
            project_root = Path(__file__).resolve().parent.parent

            # Copy Python scripts to ~/scripts/
            source_scripts_dir = project_root / 'scripts'
            dest_scripts_dir = Path.home() / 'scripts'

            python_files = ['cli_manager.py',
                            'log_config.py', 'log_formatter.py']
            for py_file in python_files:
                source_file = source_scripts_dir / py_file
                dest_file = dest_scripts_dir / py_file

                if source_file.exists():
                    needs_copy = True
                    if dest_file.exists():
                        if filecmp.cmp(str(source_file), str(dest_file), shallow=False):
                            needs_copy = False
                            log_info(
                                logger, f"Python script unchanged: {py_file}")

                    if needs_copy:
                        subprocess.run(
                            ['cp', '-p', str(source_file), str(dest_file)], check=True)
                        log_success(logger, f"Python script copied: {py_file}")

            # Copy control_panel.sh to ~/scripts/ (backup bash wrapper)
            source_script = project_root / 'control_panel.sh'
            dest_script = Path.home() / 'scripts' / 'control_panel.sh'

            if not source_script.exists():
                log_error(logger, f"Source script not found: {source_script}")
                return

            needs_copy = True
            if dest_script.exists():
                if filecmp.cmp(str(source_script), str(dest_script), shallow=False):
                    needs_copy = False
                    log_info(
                        logger, f"Script unchanged, skipping copy: {dest_script}")

            if needs_copy:
                subprocess.run(['cp', '-p', str(source_script),
                               str(dest_script)], check=True)
                subprocess.run(['chmod', '+x', str(dest_script)], check=True)
                log_success(logger, f"Script copied to: {dest_script}")

            # Create bash wrapper only if it doesn't exist or content changed
            dest_wrapper = Path.home() / '.local' / 'bin' / 'control-panel'
            wrapper_content = '''#!/usr/bin/env bash
# control-panel wrapper - Uses home scripts backup (no HD dependency)
# Activates venv from project directory if available

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Project directory is parent of script directory (assuming script is in ~/.local/bin)
PROJECT_DIR="$(dirname "$SCRIPT_DIR")/scripts/control-panel"
HOME_SCRIPTS_DIR="$HOME/scripts"

# Check if home scripts exist
if [ ! -f "$HOME_SCRIPTS_DIR/cli_manager.py" ]; then
    echo "✗ ERROR: Cannot find control-panel scripts in ~/scripts/"
    echo ""
    echo "i SOLUTIONS:"
    echo "   1. Mount the HD first:"
    echo "      sudo mount <your-hd-mount-point>"
    echo "   2. Then run sync from the HD:"
    echo "      cd <project-directory>"
    echo "      ./control-panel sync"
    echo ""
    echo "   3. Or manually copy the scripts:"
    echo "      mkdir -p ~/scripts"
    echo "      cp <project-directory>/scripts/*.py ~/scripts/"
    exit 1
fi

# Try to use project venv if HD is mounted
if [ -d "$PROJECT_DIR/venv" ] && [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
    cd "$PROJECT_DIR"
    exec python3 scripts/cli_manager.py "$@"
fi

# Fallback: use system Python with home scripts
exec python3 "$HOME_SCRIPTS_DIR/cli_manager.py" "$@"
'''

            # Check if wrapper needs to be created or updated
            needs_wrapper = True
            if dest_wrapper.exists():
                try:
                    existing_content = dest_wrapper.read_text()
                    # Compare content (ignore shebang line for flexibility)
                    if wrapper_content.strip() in existing_content or existing_content.strip() == wrapper_content.strip():
                        needs_wrapper = False
                        log_info(logger, "Bash wrapper unchanged, skipping creation")
                except Exception:
                    pass  # If can't read, recreate wrapper

            if needs_wrapper:
                dest_wrapper.parent.mkdir(parents=True, exist_ok=True)
                with open(dest_wrapper, 'w') as f:
                    f.write(wrapper_content)
                subprocess.run(['chmod', '+x', str(dest_wrapper)], check=True)
                log_success(logger, "Bash wrapper created: ~/.local/bin/control-panel")

            # Copy docker-compose.yml from HD to home directory
            source_docker_compose = Path(
                "/media/mateus/Servidor/scripts/docker-compose.yml")
            dest_docker_compose = os.path.expanduser("~/docker-compose.yml")

            if source_docker_compose.exists():
                # Only copy if file is different or doesn't exist
                needs_copy = True
                if os.path.exists(dest_docker_compose):
                    if filecmp.cmp(str(source_docker_compose), dest_docker_compose, shallow=False):
                        needs_copy = False
                        log_info(
                            logger, f"Docker Compose unchanged, skipping copy: {dest_docker_compose}")

                if needs_copy:
                    subprocess.run(
                        ['cp', '-p', str(source_docker_compose), dest_docker_compose], check=True)
                    log_success(
                        logger, f"Docker Compose file copied to: {dest_docker_compose}")
            else:
                log_warning(
                    logger, f"Docker Compose file not found: {source_docker_compose}")

        except Exception as e:
            log_error(logger, f"Error syncing files: {str(e)}")

    def view_logs_interactive(self, lines=50):
        """View logs interactively"""
        console.print(f"\n[bold cyan]📜 Last {lines} Log Entries[/bold cyan]")

        log_file = os.path.expanduser("~/.control-panel.log")
        if os.path.isfile(log_file):
            try:
                result = subprocess.run(['tail', '-n', str(lines), log_file],
                                        capture_output=True, text=True)
                console.print(result.stdout)
            except Exception as e:
                console.print(f"[red]Error reading logs: {e}[/red]")
        else:
            console.print(f"[red]✗ Log file not found: {log_file}[/red]")

    def diagnostics_interactive(self):
        """Run diagnostics"""
        console.print("\n[bold cyan]🔍 Running Diagnostics[/bold cyan]")

        try:
            # Check HD
            console.print("\n[bold]📀 HD Check:[/bold]")
            if self.is_hd_mounted():
                console.print("[green]✓ HD is mounted[/green]")
                result = subprocess.run(['df', '-h', self.hd_mount_point],
                                        capture_output=True, text=True)
                console.print(result.stdout)
            else:
                console.print("[red]✗ HD is not mounted[/red]")

            # Check Docker
            console.print("\n[bold]🐳 Docker Check:[/bold]")
            try:
                result = subprocess.run(['docker', '--version'],
                                        capture_output=True, text=True)
                if result.returncode == 0:
                    console.print(
                        f"[green]✓ Docker: {result.stdout.strip()}[/green]")
                else:
                    console.print("[red]✗ Docker: Not available[/red]")
            except Exception:
                console.print("[red]✗ Docker: Not available[/red]")

            # Check disk space
            console.print("\n[bold]💾 Disk Space:[/bold]")
            try:
                result = subprocess.run(['df', '-h'],
                                        capture_output=True, text=True)
                console.print(result.stdout)
            except Exception as e:
                console.print(f"[red]Error checking disk space: {e}[/red]")

        except Exception as e:
            log_error(logger, f"Error running diagnostics: {str(e)}")

    def systemd_keepalive_status(self):
        """Check keepalive service status"""
        console.print("\n[bold cyan]⚙️ Keepalive Service Status[/bold cyan]")

        try:
            result = subprocess.run(['systemctl', 'status', 'control-panel-keepalive.service'],
                                    capture_output=True, text=True)
            console.print(result.stdout)
        except Exception as e:
            console.print(f"[red]Error checking service status: {e}[/red]")

    def systemd_keepalive_start(self):
        """Start keepalive service"""
        console.print(
            "\n[bold cyan]🚀 Starting Keepalive Service[/bold cyan]")

        try:
            result = subprocess.run(['sudo', 'systemctl', 'start', 'control-panel-keepalive.service'],
                                    capture_output=True, text=True)
            if result.returncode == 0:
                log_success(logger, "Keepalive service started")
            else:
                log_error(logger, f"Failed to start service: {result.stderr}")
        except Exception as e:
            log_error(logger, f"Error starting service: {str(e)}")

    def systemd_keepalive_restart(self):
        """Restart keepalive service"""
        console.print(
            "\n[bold cyan]🔄 Restarting Keepalive Service[/bold cyan]")

        try:
            result = subprocess.run(['sudo', 'systemctl', 'restart', 'control-panel-keepalive.service'],
                                    capture_output=True, text=True)
            if result.returncode == 0:
                log_success(logger, "Keepalive service restarted")
            else:
                log_error(
                    logger, f"Failed to restart service: {result.stderr}")
        except Exception as e:
            log_error(logger, f"Error restarting service: {str(e)}")

    def systemd_keepalive_stop(self):
        """Stop keepalive service"""
        console.print(
            "\n[bold cyan]⏹️ Stopping Keepalive Service[/bold cyan]")

        try:
            result = subprocess.run(['sudo', 'systemctl', 'stop', 'control-panel-keepalive.service'],
                                    capture_output=True, text=True)
            if result.returncode == 0:
                log_success(logger, "Keepalive service stopped")
            else:
                log_error(logger, f"Failed to stop service: {result.stderr}")
        except Exception as e:
            log_error(logger, f"Error stopping service: {str(e)}")

    def systemd_keepalive_enable(self):
        """Enable keepalive service"""
        console.print(
            "\n[bold cyan]✅ Enabling Keepalive Service[/bold cyan]")

        try:
            result = subprocess.run(['sudo', 'systemctl', 'enable', 'control-panel-keepalive.service'],
                                    capture_output=True, text=True)
            if result.returncode == 0:
                log_success(logger, "Keepalive service enabled")
            else:
                log_error(logger, f"Failed to enable service: {result.stderr}")
        except Exception as e:
            log_error(logger, f"Error enabling service: {str(e)}")

    def systemd_keepalive_disable(self):
        """Disable keepalive service"""
        console.print(
            "\n[bold cyan]❌ Disabling Keepalive Service[/bold cyan]")

        try:
            result = subprocess.run(['sudo', 'systemctl', 'disable', 'control-panel-keepalive.service'],
                                    capture_output=True, text=True)
            if result.returncode == 0:
                log_success(logger, "Keepalive service disabled")
            else:
                log_error(
                    logger, f"Failed to disable service: {result.stderr}")
        except Exception as e:
            log_error(logger, f"Error disabling service: {str(e)}")

    def systemd_keepalive_logs(self, follow=False):
        """View keepalive service logs"""
        console.print("\n[bold cyan]📜 Keepalive Service Logs[/bold cyan]")

        try:
            cmd = ['journalctl', '-u',
                   'control-panel-keepalive.service', '-n', '50']
            if follow:
                cmd.append('-f')

            result = subprocess.run(cmd, capture_output=True, text=True)
            console.print(result.stdout)
        except Exception as e:
            console.print(f"[red]Error viewing logs: {e}[/red]")

    def show_menu(self):
        """Show main menu with help information"""
        from rich.panel import Panel
        from rich.text import Text

        # Create a panel with the help information
        help_text = Text()
        help_text.append("Available commands:\n", style="bold cyan")
        help_text.append(
            "  status                            - Show system status\n")
        help_text.append(
            "  mount                             - Mount the HD drive\n")
        help_text.append(
            "  unmount                           - Unmount the HD drive\n")
        help_text.append(
            "  keepalive                         - Keep HD alive (monitor mode)\n")
        help_text.append(
            "  fix                               - Fix mount point structure\n")
        help_text.append(
            "  sync                              - Sync files and update\n")
        help_text.append("\nDocker Management:\n", style="bold yellow")
        help_text.append(
            "  start [service]                   - Start Docker services\n")
        help_text.append(
            "  stop [service]                    - Stop Docker services\n")
        help_text.append(
            "  restart [service]                 - Restart Docker services\n")
        help_text.append(
            "  ps                                - List running containers\n")
        help_text.append(
            "  logs <service>                    - Show Docker service logs\n")
        help_text.append(
            "  clean [service]                   - Clean old containers\n")
        help_text.append(
            "  pull                              - Pull updated images\n")
        help_text.append(
            "  services                          - List available services\n")
        help_text.append("\nSystemd Management:\n", style="bold yellow")
        help_text.append(
            "  keepalive-status                 - Check keepalive service status\n")
        help_text.append(
            "  keepalive-start                  - Start keepalive service\n")
        help_text.append(
            "  keepalive-restart                - Restart keepalive service\n")
        help_text.append(
            "  keepalive-stop                   - Stop keepalive service\n")
        help_text.append(
            "  keepalive-enable                 - Enable keepalive service\n")
        help_text.append(
            "  keepalive-disable                - Disable keepalive service\n")
        help_text.append(
            "  keepalive-logs                   - View keepalive logs\n")
        help_text.append("\nOther Commands:\n", style="bold yellow")
        help_text.append(
            "  logs                              - Show script logs\n")
        help_text.append(
            "  diagnose                          - Run system diagnostics\n")
        help_text.append(
            "  interactive                       - Start interactive menu\n")
        help_text.append(
            "  help                              - Show this help\n")
        help_text.append("\nExamples:\n", style="bold green")
        help_text.append("  control-panel mount\n")
        help_text.append("  control-panel status\n")
        help_text.append("  control-panel start jellyfin\n")
        help_text.append("  control-panel logs prowlarr\n")
        help_text.append("  control-panel interactive\n")

        console.print(
            "\n[bold cyan]🎛️ Control Panel System - CLI Manager[/bold cyan]\n")
        console.print(
            Panel(help_text, title="Commands Help", border_style="blue"))


def main():
    """Main entry point"""
    cli_manager = CLIManager()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "interactive":
            cli_manager.show_interactive_menu()
        elif command == "help" or command == "--help" or command == "-h":
            cli_manager.show_menu()
        elif command == "keepalive":
            cli_manager.keepalive_hd_interactive()
        elif command == "status":
            cli_manager.show_status_interactive()
        elif command == "mount":
            cli_manager.mount_hd_interactive()
        elif command == "unmount":
            cli_manager.unmount_hd_interactive()
        elif command == "fix":
            cli_manager.fix_mount_point_interactive()
        elif command == "sync":
            cli_manager.sync_interactive()
        elif command == "logs":
            lines = 50
            if len(sys.argv) > 2:
                try:
                    lines = int(sys.argv[2])
                except ValueError:
                    pass
            cli_manager.view_logs_interactive(lines)
        elif command == "diagnose":
            cli_manager.diagnostics_interactive()
        elif command == "keepalive-status":
            cli_manager.systemd_keepalive_status()
        elif command == "keepalive-start":
            cli_manager.systemd_keepalive_start()
        elif command == "keepalive-restart":
            cli_manager.systemd_keepalive_restart()
        elif command == "keepalive-stop":
            cli_manager.systemd_keepalive_stop()
        elif command == "keepalive-enable":
            cli_manager.systemd_keepalive_enable()
        elif command == "keepalive-disable":
            cli_manager.systemd_keepalive_disable()
        elif command == "keepalive-logs":
            follow = len(sys.argv) > 2 and sys.argv[2] == "-f"
            cli_manager.systemd_keepalive_logs(follow)
        elif command == "backup-daemon-run":
            # Run backup daemon (for systemd service)
            from backup_daemon import run_daemon
            run_daemon()
        elif command == "backup":
            self.handle_backup_command(sys.argv[2:])
        elif command.startswith("backup-"):
            self.handle_backup_command([command.replace("backup-", "")] + sys.argv[2:])
        else:
            console.print(
                f"[yellow]Command '{command}' not yet implemented in Python version[/yellow]")
            console.print(
                "[yellow]Use 'control-panel --help' for available commands[/yellow]")
    else:
        cli_manager.show_interactive_menu()


if __name__ == "__main__":
    main()
