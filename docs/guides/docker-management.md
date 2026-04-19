# Docker Management Guide

## Overview

The Control Panel provides comprehensive Docker container management through docker-compose integration with an interactive CLI interface.

## Commands

### Start Containers

```bash
# Start all containers
control-panel start

# Start specific service
control-panel start nextcloud

# Start without dependencies
control-panel start jellyfin --no-deps

# Start with clean containers (removes old ones)
control-panel start kavita --clean
```

### Stop Containers

```bash
# Stop all containers
control-panel stop

# Stop specific service
control-panel stop navidrome
```

### Restart Containers

```bash
# Restart all containers
control-panel restart

# Restart specific service
control-panel restart onlyoffice

# Restart with clean containers
control-panel restart plex --clean
```

### Container Status

```bash
# List running containers
control-panel ps

# Show resource usage
control-panel stats

# Show specific container stats
control-panel stats nextcloud

# Check health of all containers
control-panel health
```

### View Logs

```bash
# View logs for a service
control-panel logs nextcloud

# Follow logs in real-time
control-panel logs onlyoffice -f

# View last 100 lines
control-panel logs kavita | tail -100
```

## Container Health States

| State | Meaning |
|-------|---------|
| `running` | Container is up and running |
| `exited` | Container stopped |
| `restarting` | Container is restarting |
| `unhealthy` | Health check failed |

## Docker Maintenance

### List Services

```bash
control-panel services
```

Shows all services defined in your docker-compose.yml.

### Pull Updates

```bash
# Pull latest images for all services
control-panel pull

# Images are updated but containers don't restart automatically
# Use control-panel restart to apply updates
```

### Rebuild Containers

```bash
# Rebuild without cache (full rebuild)
control-panel rebuild

# Rebuild specific service
control-panel rebuild nextcloud

# Rebuild with cache (faster)
control-panel rebuild nextcloud --cache
```

### Smart Update

Updates images and restarts only services that changed:

```bash
control-panel update-all
```

This will:
1. Pull all latest images
2. Compare with running containers
3. Restart only outdated services

### Clean Up

```bash
# Remove unused containers, networks, images
control-panel prune
```

You'll be prompted to confirm before removal.

## Networks and Volumes

```bash
# List Docker networks
control-panel networks

# List Docker volumes
control-panel volumes
```

## Docker Compose Location

The system looks for docker-compose.yml in:

```python
self.docker_compose_dir = Path.home() / "path/to/docker-compose"
```

Update this in `scripts/cli_manager.py` to match your setup.

## Troubleshooting

### Container Won't Start

```bash
# Check logs
control-panel logs <service>

# Check docker-compose config
docker-compose config

# Verify volumes exist
docker volume ls
```

### Port Conflicts

If a service fails to start with port errors:

```bash
# Check what's using the port
sudo netstat -tlnp | grep <port>

# Stop the conflicting service or change the port in docker-compose.yml
```

### Out of Memory

```bash
# Check container resource usage
control-panel stats

# Increase swap if needed
sudo swapon /path/to/swapfile
```
