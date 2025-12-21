# 🎛️ Control Panel - Server Manager

![GitHub release (latest by date)](https://img.shields.io/github/v/release/mateus-mg/control-panel?label=release)

Bash script to manage external HD and Docker containers on a home server.


## 🚀 Installation

### Recommended Structure (with external HD support)

```bash
# 1. Copy script to home (ALWAYS available)
cp painel.sh /path/to/home/painel.sh
chmod +x /path/to/home/painel.sh

# 2. Create global symlink
sudo ln -s /path/to/home/painel.sh /usr/local/bin/painel


# Test
painel status
```


## 📋 Quick Usage

### Server Startup
```bash
painel mount        # Mount external HD
painel start        # Start all containers
painel keepalive    # Keep system active (Ctrl+C to exit)
```

### Server Shutdown
```bash
painel stop         # Stop containers
painel unmount      # Unmount HD
```

### Manage Specific Services
```bash
painel services                      # List available services
painel start jellyfin                # Start only Jellyfin
painel start jellyfin --no-deps      # Start without dependencies
painel stop qbittorrent              # Stop only qBittorrent
painel restart plex                  # Restart only Plex
painel restart plex --clean          # Restart and clean containers
painel logs prowlarr -f              # View Prowlarr logs in real time
```


## 📚 Commands

### HD Management
| Command | Description |
|---------|-------------|
| `painel mount` | Mount external HD |
| `painel unmount` | Unmount HD (stops containers first) |
| `painel check` | Show active mounts |
| `painel fix` | Fix mount point |
| `painel force-mount` | Force full remount |

### Docker Management
| Command | Description |
|---------|-------------|
| `painel start [service] [--clean] [--no-deps]` | Start containers (all or specific, with options) |
| `painel stop [service]` | Stop containers (all or specific) |
| `painel restart [service] [--clean]` | Restart containers (all or specific, with cleanup) |
| `painel clean [service]` | Remove orphan containers (all or specific) |
| `painel ps` | List running containers |
| `painel logs <service> [-f]` | Show service logs (use -f to follow) |
| `painel stats [service]` | Show real-time CPU/memory usage |
| `painel health` | Check health of all containers |

### Docker Maintenance & Utilities
| Command | Description |
|---------|-------------|
| `painel services` | List all available services |
| `painel pull` | Pull updated images |
| `painel rebuild [service] [--cache]` | Rebuild containers (NO cache by default, or with cache) |
| `painel update-all` | Smart update: pull images, restart only updated containers |
| `painel networks` | List Docker networks |
| `painel volumes` | List Docker volumes |
| `painel prune` | Remove unused resources |
| `painel diagnose` | Detailed diagnostic (HD & Docker) |

### Monitoring
| Command | Description |
|---------|-------------|
| `painel status` | Full system status |
| `painel keepalive` | Continuous monitoring mode |

### Log Management
| Command | Description |
|---------|-------------|
| `painel view-logs [n]` | View the last `n` lines of the script log file (default: 50) |

### Example: View Logs
```bash
painel view-logs 100  # View the last 100 lines of the script log file
```

### Updated Error Handling
- Improved error messages for better debugging.
- Logs now include detailed context for easier troubleshooting.


## 🔄 Sync Files

### Synchronize Files and Create Symlink
```bash
painel sync
```

This command performs the following actions:
1. Copies the `control_panel.sh` script and `docker-compose.yml` from the external HD to the home directory.
2. Creates or updates a global symlink at `/usr/local/bin/panel` pointing to the script.
3. Ensures the files are up-to-date before copying.

### Example
```bash
painel sync  # Synchronize files and update symlink
```


## ⚙️ Configuration

### HD Configuration
Update the following variables in the script to match your system:

```bash
HD_MOUNT_POINT="/path/to/mount"
HD_UUID="your-hd-uuid"
HD_LABEL="your-hd-label"
HD_TYPE="ext4"
DOCKER_COMPOSE_DIR="/path/to/docker-compose"
```

### Docker Compose
Ensure your `docker-compose.yml` file is located in the directory specified by `DOCKER_COMPOSE_DIR`.

### .service File
If using the `.service` file for automatic mounting, update the `ExecStart` line to match your HD configuration:

```ini
ExecStart=/usr/bin/mount UUID=your-hd-uuid /path/to/mount
```


##  Keepalive Mode

Keeps the HD active and monitors containers:

```bash
painel keepalive
```

- Checks HD every 30 seconds
- Automatically remounts if disconnected
- Restarts stopped containers
- **Ctrl+C to stop**


## 🐛 Troubleshooting

### HD does not mount
```bash
painel fix           # Fix mount point
painel force-mount   # Force mount
lsblk                # Check device
```

### Containers do not start
```bash
painel status                    # Check system
painel logs <service-name>       # View logs
painel diagnose                  # Full diagnostic
```


## 📝 Logs

Os logs do painel são armazenados no arquivo `~/.painel.log`. Cada mensagem inclui um timestamp no formato ISO (`YYYY-MM-DD HH:MM:SS`).

### Exemplo de Logs
```log
2025-12-20 16:31:01 - Service stopped: qbittorrent
2025-12-20 16:35:22 - Service started: cloudflared
```

### Rotação de Logs
- O sistema mantém apenas as últimas 500 linhas no arquivo principal.
- Para evitar perda de informações, recomenda-se implementar um sistema de arquivamento manual ou automático (ex.: `painel.log.1`, `painel.log.2`).

### Solução de Problemas com Logs
- **Mensagens repetitivas**: Verifique se há redundância no script.
- **Erros específicos**: Consulte as mensagens detalhadas no log para identificar falhas em comandos Docker ou montagem do HD.


## 🛠️ Original .service Configuration

The original configuration of the `hdmount.service` file is as follows:

```ini
[Unit]
Description=Mount external HD before Docker
DefaultDependencies=no
After=local-fs.target
Before=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/mount /media/mateus/Servidor

[Install]
WantedBy=multi-user.target
```

### Instructions Before Moving

1. Ensure the `.service` file is correctly configured for your system.
2. Move the file to the systemd directory:
   ```bash
   sudo mv /path/to/hdmount.service /etc/systemd/system/
   ```
3. Reload systemd to recognize the new service:
   ```bash
   sudo systemctl daemon-reload
   ```
4. Enable the service to start on boot:
   ```bash
   sudo systemctl enable hdmount.service
   ```
5. Start the service manually to test:
   ```bash
   sudo systemctl start hdmount.service
   ```

