# 🎛️ Web Panel - Plano de Implementação

**Versão:** 1.0  
**Data:** 2026-05-16  
**Autor:** Equipo de Desenvolvimento  

---

## 1. Visão Geral

Este documento descreve o plano completo para desenvolvimento de um painel web (Web Panel) que replica e expande as funcionalidades do CLI atual do `control-panel`. O objetivo é criar uma interface web moderna, responsiva e intuitiva para gerenciar o servidor domestico.

### 1.1 Objetivos

- **Replicar** todas as funcionalidades do CLI atual em uma interface web
- **Modernizar** a experiência do usuário com dashboards e visualizações
- **Melhorar** a monitorização em tempo real dos serviços
- **Simplificar** operações complexas (backups, Docker) com UI intuitiva

### 1.2 Tecnologias Recomendadas

| Camada | Tecnologia | Justificativa |
|--------|------------|----------------|
| **Backend** | FastAPI | Async, rápido, autodocs, ideal para integrações Docker/systemd |
| **Frontend** | HTMX + TailwindCSS | Simplicidade, sem build complexo, responsivo |
| **Banco de Dados** | SQLite (arquivo local) | Persistência leve, não requer servidor extra |
| **Web Server** | Uvicorn (ASGI) | Padrão FastAPI, fácil deployment |
| **Autenticação** | JWT simples | Necessário para acesso local seguro |
| **Real-time** | Server-Sent Events (SSE) | Atualização em tempo real sem WebSockets complexos |

> **Alternativa Frontend:** Se preferir React/Vue, usar Vite como bundler. Para este plano, usaremos HTMX pela simplicidade de integração com FastAPI.

---

## 2. Análise do Projeto Atual

### 2.1 Estrutura Atual

```
control-panel/
├── control_panel.sh          # Bash - orquestração HD/Docker
├── control-panel             # Wrapper bash com auto-sync
├── scripts/
│   ├── cli_manager.py        # CLI principal (Rich)
│   ├── backup_cli.py         # Subcomandos de backup
│   ├── backup_config.py      # Configuração JSON
│   ├── backup_daemon.py      # Scheduler de backups
│   ├── backup_manager.py     # Execução rsync
│   └── log_config.py         # Logging estruturado
├── *.service                 # systemd units
└── docs/                    # MkDocs
```

### 2.2 Funcionalidades do CLI (Mapeamento)

| Menu CLI | Submenu/Opção | Comando Equivalente | Complexidade |
|----------|---------------|---------------------|--------------|
| **1. Backups** | Daemon Management | start/stop/restart/status | Baixa |
| | Manage Sources | list/add/remove/toggle | Média |
| | Configure Destination | set-destination | Baixa |
| | Configure Schedule | set-schedule | Média |
| | Configure Retention | set-retention | Média |
| | Run Backup Now | run [--source] | Média |
| | View Statistics | stats | Baixa |
| | View History | history | Baixa |
| | View Configuration | config | Baixa |
| **2. Docker** | Start Services | docker compose up | Baixa |
| | Stop Services | docker compose stop | Baixa |
| | Restart Services | docker compose restart | Baixa |
| | View Containers | docker ps | Baixa |
| | View Logs | docker compose logs | Média |
| | Clean Containers | docker compose rm | Baixa |
| | Pull Images | docker compose pull | Média |
| | List Services | docker compose config --services | Baixa |
| **3. HD Drives** | Mount HD | mount (UUID-based) | Baixa |
| | Unmount HD | umount | Baixa |
| | Fix Mount Point | rmdir + mkdir | Baixa |
| | Keep Alive | touch .keepalive loop | Baixa |
| | Check Mounts | mountpoint -q | Baixa |
| **4. Systemd** | View Status | systemctl status | Baixa |
| | Start Service | systemctl start | Baixa |
| | Stop Service | systemctl stop | Baixa |
| | Restart Service | systemctl restart | Baixa |
| | Enable Service | systemctl enable | Baixa |
| | Disable Service | systemctl disable | Baixa |
| | View Logs | journalctl | Média |
| **5. Diagnostics** | Run Diagnostics | df, docker --version, etc | Baixa |
| **6. Sync Files** | Sync | cp scripts, update wrapper | Baixa |
| **7. View Logs** | Log Viewer | tail ~/.control-panel.log | Média |
| **8. System Status** | Status Dashboard | df, docker ps | Baixa |
| **9. Clean SWAP** | Swap Cleanup | swapoff/swapon | Baixa |

---

## 3. Arquitetura do Projeto

### 3.1 Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                       │
│                    HTMX + TailwindCSS                        │
└─────────────────────────────┬───────────────────────────────┘
                              │ HTTP/SSE
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Routes  │  │   API    │  │  Auth    │  │  SSE     │  │
│  │ (HTML)   │  │ (JSON)   │  │  (JWT)   │  │ Manager  │  │
│  └────┬─────┘  └────┬─────┘  └──────────┘  └────┬─────┘  │
│       │              │                              │         │
│       └──────────────┼──────────────────────────────┘         │
│                      ▼                                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                    Service Layer                        │  │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────────────┐  │  │
│  │  │  Docker   │ │    HD     │ │     Backup        │  │  │
│  │  │  Service  │ │  Service  │ │     Service       │  │  │
│  │  └───────────┘ └───────────┘ └───────────────────────┘  │  │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────────────┐  │  │
│  │  │  Systemd  │ │   Logs    │ │   Diagnostics    │  │  │
│  │  │  Service  │ │  Service  │ │     Service       │  │  │
│  │  └───────────┘ └───────────┘ └───────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
│                      │                                        │
│                      ▼                                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                    Data Layer                          │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │   Config    │  │    State     │  │   History   │  │  │
│  │  │   JSON      │  │   JSON       │  │   JSON       │  │  │
│  │  │  (backup)   │  │  (runtime)   │  │  (backups)   │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ (system calls)
┌─────────────────────────────────────────────────────────────┐
│                      SYSTEM LAYER                            │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐  │
│  │  Docker   │ │  systemd  │ │   mount   │ │    rsync  │  │
│  │  (API)    │ │  (ctl)    │ │  (umount) │ │           │  │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Estrutura de Pastas

```
web-panel/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Configurações e constantes
│   ├── database.py             # SQLite connection
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py             # Dependencies (auth, db session)
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # Login/logout
│   │   │   ├── docker.py       # Docker management
│   │   │   ├── hd.py           # HD management
│   │   │   ├── backup.py       # Backup operations
│   │   │   ├── systemd.py      # Systemd services
│   │   │   ├── logs.py         # Log viewing
│   │   │   └── status.py       # System status
│   │   └── schemas/            # Pydantic models
│   │       ├── __init__.py
│   │       ├── docker.py
│   │       ├── backup.py
│   │       └── common.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py         # JWT handling
│   │   └── events.py           # Startup/shutdown events
│   │
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── docker_service.py
│   │   ├── hd_service.py
│   │   ├── backup_service.py
│   │   ├── systemd_service.py
│   │   ├── log_service.py
│   │   └── diagnostics_service.py
│   │
│   └── web/
│       ├── __init__.py
│       ├── routes/             # HTML page routes
│       │   ├── __init__.py
│       │   ├── dashboard.py
│       │   ├── docker.py
│       │   ├── hd.py
│       │   ├── backup.py
│       │   ├── systemd.py
│       │   └── settings.py
│       └── templates/          # Jinja2 templates
│           ├── base.html
│           ├── dashboard.html
│           ├── docker/
│           │   ├── containers.html
│           │   ├── logs.html
│           │   └── services.html
│           ├── hd/
│           │   └── mount.html
│           ├── backup/
│           │   ├── sources.html
│           │   ├── config.html
│           │   ├── history.html
│           │   └── run.html
│           ├── systemd/
│           │   └── services.html
│           ├── logs/
│           │   └── viewer.html
│           └── auth/
│               └── login.html
│
├── static/
│   ├── css/
│   │   └── custom.css          # Custom Tailwind overrides
│   └── js/
│       └── htmx.min.js
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api/
│   └── test_services/
│
├── alembic/                    # Database migrations (opcional)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 4. Endpoints da API

### 4.1 Autenticação

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/auth/login` | Login com username/password |
| POST | `/api/auth/logout` | Logout e invalidação de token |
| GET | `/api/auth/me` | Retorna usuário atual |

### 4.2 Docker

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/docker/containers` | Lista todos os containers |
| GET | `/api/docker/containers/{name}` | Detalhes de um container |
| POST | `/api/docker/containers/{name}/start` | Inicia container |
| POST | `/api/docker/containers/{name}/stop` | Para container |
| POST | `/api/docker/containers/{name}/restart` | Reinicia container |
| GET | `/api/docker/containers/{name}/logs` | Logs do container |
| GET | `/api/docker/services` | Lista serviços do compose |
| POST | `/api/docker/start` | Inicia todos os serviços |
| POST | `/api/docker/stop` | Para todos os serviços |
| POST | `/api/docker/restart` | Reinicia todos os serviços |
| POST | `/api/docker/pull` | Pull de imagens |
| POST | `/api/docker/clean` | Remove containers parados |

### 4.3 HD Management

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/hd/status` | Status do HD (montado/desmontado) |
| GET | `/api/hd/info` | Info do HD (UUID, label, espaço) |
| POST | `/api/hd/mount` | Monta HD |
| POST | `/api/hd/unmount` | Desmonta HD |
| POST | `/api/hd/fix` | Repara ponto de montagem |

### 4.4 Backup

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/backup/config` | Retorna configuração completa |
| PUT | `/api/backup/config` | Atualiza configuração global |
| GET | `/api/backup/sources` | Lista fontes de backup |
| POST | `/api/backup/sources` | Adiciona fonte |
| DELETE | `/api/backup/sources/{id}` | Remove fonte |
| PATCH | `/api/backup/sources/{id}` | Atualiza fonte |
| POST | `/api/backup/run` | Executa backup |
| GET | `/api/backup/history` | Histórico de backups |
| GET | `/api/backup/stats` | Estatísticas |
| GET | `/api/backup/daemon/status` | Status do daemon |
| POST | `/api/backup/daemon/start` | Inicia daemon |
| POST | `/api/backup/daemon/stop` | Para daemon |

### 4.5 Systemd

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/systemd/services` | Lista serviços do control-panel |
| GET | `/api/systemd/services/{name}/status` | Status de um serviço |
| POST | `/api/systemd/services/{name}/start` | Inicia serviço |
| POST | `/api/systemd/services/{name}/stop` | Para serviço |
| POST | `/api/systemd/services/{name}/restart` | Reinicia serviço |
| POST | `/api/systemd/services/{name}/enable` | Habilita serviço |
| POST | `/api/systemd/services/{name}/disable` | Desabilita serviço |
| GET | `/api/systemd/services/{name}/logs` | Logs do serviço |

### 4.6 Logs e Status

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/logs` | Logs do sistema (com paginação) |
| GET | `/api/logs/docker/{name}` | Logs Docker |
| GET | `/api/logs/stream` | SSE stream de logs |
| GET | `/api/status` | Status completo do sistema |
| GET | `/api/status/stream` | SSE stream de status |
| POST | `/api/diagnostics` | Executa diagnóstico |
| POST | `/api/swap/clean` | Limpa SWAP |
| POST | `/api/sync` | Sincroniza arquivos |

---

## 5. Modelos de Dados

### 5.1 Backup Source

```python
class BackupSource:
    id: str              # UUID único
    path: str             # Caminho de origem
    recursive: bool       # Incluir subdiretórios
    enabled: bool         # Se está ativo
    priority: str         # "high", "medium", "low"
    description: str      # Descrição opcional
    exclude_patterns: List[str]  # Padrões de exclusão
    schedule: Schedule
    retention: Retention
    added_at: datetime
    last_backup: datetime | None
```

### 5.2 Schedule

```python
class Schedule:
    enabled: bool
    frequency: str        # "hourly", "daily", "weekly", "monthly", "custom"
    time: str            # "HH:MM"
    days_of_week: List[str]  # ["monday", "wednesday", ...]
    day_of_month: int | None  # 1-28
```

### 5.3 Container Info

```python
class ContainerInfo:
    name: str
    image: str
    status: str          # "running", "exited", etc
    state: str            # "running", "paused", "restarting"
    created: str
    ports: List[PortMapping]
    cpu_percent: float
    memory_usage: MemoryInfo
```

### 5.4 System Status

```python
class SystemStatus:
    hd_mounted: bool
    hd_path: str
    hd_total_gb: float
    hd_used_gb: float
    hd_available_gb: float
    containers_running: int
    containers_total: int
    daemon_running: bool
    services: List[ServiceStatus]
```

---

## 6. Frontend - Páginas e Componentes

### 6.1 Páginas Principais

| Página | Rota | Descrição |
|--------|------|-----------|
| Login | `/login` | Autenticação |
| Dashboard | `/` | Visão geral do sistema |
| Docker | `/docker` | Containers e serviços |
| Docker Logs | `/docker/logs/{name}` | Logs de container |
| HD | `/hd` | Gerenciamento de HD |
| Backup | `/backup` | Painel de backup |
| Backup Sources | `/backup/sources` | Gerenciar fontes |
| Backup History | `/backup/history` | Histórico |
| Systemd | `/systemd` | Serviços systemd |
| Logs | `/logs` | Visualizador de logs |
| Settings | `/settings` | Configurações |

### 6.2 Componentes Reutilizáveis

```
components/
├── navbar.html          # Navegação principal
├── sidebar.html         # Menu lateral
├── status_card.html     # Card de status (HD, Docker, etc)
├── container_row.html   # Linha de container na tabela
├── service_row.html     # Linha de serviço systemd
├── backup_source_card.html
├── log_line.html        # Linha de log formatada
├── modal.html           # Modal genérico
├── confirm_dialog.html  # Diálogo de confirmação
├── toast.html           # Notificações toast
└── loading.html         # Indicador de carregamento
```

### 6.3 Wireflow - Fluxo Principal

```
┌─────────────────────────────────────────────────────────────────┐
│                          LOGIN PAGE                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    [Control Panel]                       │    │
│  │                                                          │    │
│  │    Username: [________________]                          │    │
│  │    Password: [________________]                          │    │
│  │                                                          │    │
│  │              [Entrar]                                    │    │
│  └─────────────────────────────────────────────────────────┘    │
└────────────────────────────┬────────────────────────────────────┘
                             │ Login OK
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                          DASHBOARD                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │ HD Drive │ │ Docker   │ │ Backups  │ │ Systemd  │            │
│  │ ● Mounted│ │ 4/6 run  │ │ 2 src    │ │ 2 active │            │
│  │ 2.1TB/3TB│ │ [View]   │ │ [Manage] │ │ [View]   │            │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘            │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Quick Actions                          │  │
│  │  [Start All] [Stop All] [Run Backup] [Mount HD] [Unmount]│  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Running Containers (4)                       │  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │ jellyfin   ● running   8080→8096   CPU: 12%  MEM: 2G│ │  │
│  │  │ qbittorrent● running   8080→8088   CPU: 5%   MEM: 512│ │  │
│  │  │ plex       ● running   32400      CPU: 8%   MEM: 4G  │ │  │
│  │  │ prowlarr   ● running   9696       CPU: 1%   MEM: 256 │ │  │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.4 Wireflow - Docker Management

```
┌─────────────────────────────────────────────────────────────────┐
│                        DOCKER PAGE                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Docker Services                                         │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │ All │ jellyfin │ qbittorrent │ plex │ prowlarr │ ... │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐                     │
│  │[Start]│ │[Stop] │ │[Restart]│ │[Pull] │                     │
│  └────────┘ └────────┘ └────────┘ └────────┘                     │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Container    Status    Ports       CPU     MEM     Actions │  │
│  │ ─────────────────────────────────────────────────────────│  │
│  │ jellyfin     ● running 8080→8096   12%     2GB   [▶][■][↻]│  │
│  │ qbittorrent ● running 8080→8088   5%      512MB  [▶][■][↻]│  │
│  │ plex         ● running 32400       8%      4GB   [▶][■][↻]│  │
│  │ prowlarr    ● stopped -           -       -      [▶][■][↻]│  │
│  │ sonarr      ● running 8989        3%      1GB   [▶][■][↻]│  │
│  │ radarr      ● stopped -           -       -      [▶][■][↻]│  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Click em container → Modal com Logs, Stats, Ações detalhadas   │
└─────────────────────────────────────────────────────────────────┘
```

### 6.5 Wireflow - Backup Management

```
┌─────────────────────────────────────────────────────────────────┐
│                       BACKUP PAGE                               │
│  ┌────────────────────┐  ┌────────────────────────────────────┐ │
│  │ Daemon Status      │  │ Quick Actions                      │ │
│  │ ● Running          │  │ [Run Backup Now] [Configure]        │ │
│  │ Last: 2h ago       │  │                                    │ │
│  │ Next: in 45min     │  │                                    │ │
│  └────────────────────┘  └────────────────────────────────────┘ │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Sources (3)                              [+ Add Source]  │  │
│  │ ─────────────────────────────────────────────────────────│  │
│  │ ┌──────────────────────────────────────────────────────┐  │  │
│  │ │ 📁 /media/mateus/Servidor/containers/config        │  │  │
│  │ │ Priority: HIGH │ Daily @ 02:00 │ Next: Tomorrow     │  │  │
│  │ │ Last: 2026-05-15 02:00 ✓ │ Retenção: 7/4/6       │  │  │
│  │ │ [Edit] [Run Now] [Disable] [Remove]                │  │  │
│  │ └──────────────────────────────────────────────────────┘  │  │
│  │ ┌──────────────────────────────────────────────────────┐  │  │
│  │ │ 📁 /media/mateus/Servidor/projetos/pessoal          │  │  │
│  │ │ Priority: MEDIUM │ Weekly @ Sun 03:00 │ Next: Sun   │  │  │
│  │ │ Last: 2026-05-11 03:00 ✓ │ Retenção: 0/12/6       │  │  │
│  │ │ [Edit] [Run Now] [Disable] [Remove]                │  │  │
│  │ └──────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Statistics                           [View History]       │  │
│  │ ─────────────────────────────────────────────────────────│  │
│  │ Total Backups: 45 │ Success: 43 │ Failed: 2             │  │
│  │ Space Used: 128GB │ Last Week: 5 backups                │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Implementação - Fase a Fase

### Fase 1: Setup e Autenticação (Dias 1-2)

**Objetivo:** Criar a estrutura base e autenticação.

| Tarefa | Descrição | Complexidade | Tempo |
|--------|-----------|--------------|-------|
| 1.1 | Criar estrutura de pastas | Baixa | 30min |
| 1.2 | Configurar FastAPI com templates | Baixa | 1h |
| 1.3 | Setup TailwindCSS via CDN | Baixa | 30min |
| 1.4 | Implementar autenticação JWT | Média | 2h |
| 1.5 | Criar página de login | Baixa | 1h |
| 1.6 | Criar layout base (navbar, sidebar) | Média | 2h |
| 1.7 | Implementar logout e proteção de rotas | Baixa | 1h |

**Entregáveis:**
- `app/main.py` com FastAPI configurado
- Autenticação funcional (login/logout)
- Layout base com navegação

### Fase 2: Dashboard e Status (Dias 3-4)

**Objetivo:** Exibir visão geral do sistema.

| Tarefa | Descrição | Complexidade | Tempo |
|--------|-----------|--------------|-------|
| 2.1 | Criar serviço de status (HD, Docker, etc) | Média | 2h |
| 2.2 | Implementar endpoint `/api/status` | Baixa | 1h |
| 2.3 | Criar cards de status no dashboard | Média | 2h |
| 2.4 | Implementar SSE para atualização em tempo real | Média | 2h |
| 2.5 | Adicionar ações rápidas (start/stop all) | Média | 2h |

**Entregáveis:**
- Dashboard com cards de status
- Atualização em tempo real via SSE
- Ações rápidas funcionais

### Fase 3: Docker Management (Dias 5-7)

**Objetivo:** Interface completa para Docker.

| Tarefa | Descrição | Complexidade | Tempo |
|--------|-----------|--------------|-------|
| 3.1 | Criar DockerService para wrappers Docker | Média | 2h |
| 3.2 | Implementar listagem de containers | Baixa | 1h |
| 3.3 | Criar página de containers com ações | Média | 2h |
| 3.4 | Implementar start/stop/restart via HTMX | Média | 2h |
| 3.5 | Adicionar visualização de logs | Média | 3h |
| 3.6 | Implementar stats em tempo real | Média | 2h |
| 3.7 | Adicionar pull de imagens | Baixa | 1h |

**Entregáveis:**
- Página de containers completa
- Visualização de logs
- Ações em container

### Fase 4: HD Management (Dia 8)

**Objetivo:** Interface para gerenciamento de HD.

| Tarefa | Descrição | Complexidade | Tempo |
|--------|-----------|--------------|-------|
| 4.1 | Criar HDService com comandos mount/umount | Média | 2h |
| 4.2 | Implementar endpoints de HD | Baixa | 1h |
| 4.3 | Criar página de HD com status e ações | Média | 2h |
| 4.4 | Adicionar indicadores de espaço em disco | Baixa | 1h |

**Entregáveis:**
- Página de HD com mount/unmount
- Visualização de espaço

### Fase 5: Backup Management (Dias 9-11)

**Objetivo:** Interface completa de backup.

| Tarefa | Descrição | Complexidade | Tempo |
|--------|-----------|--------------|-------|
| 5.1 | Integrar com BackupConfigManager existente | Média | 2h |
| 5.2 | Implementar CRUD de fontes | Média | 3h |
| 5.3 | Criar página de configuração (schedule, retention) | Média | 2h |
| 5.4 | Implementar execução de backup via UI | Média | 2h |
| 5.5 | Criar visualização de histórico | Média | 2h |
| 5.6 | Adicionar estatísticas e gráficos | Alta | 3h |

**Entregáveis:**
- CRUD completo de fontes
- Configuração de schedule/retention
- Histórico e estatísticas

### Fase 6: Systemd Services (Dia 12)

**Objetivo:** Gerenciamento de serviços systemd.

| Tarefa | Descrição | Complexidade | Tempo |
|--------|-----------|--------------|-------|
| 6.1 | Criar SystemdService | Média | 2h |
| 6.2 | Implementar página de serviços | Média | 2h |
| 6.3 | Adicionar ações (start/stop/enable/disable) | Média | 2h |
| 6.4 | Implementar visualização de logs | Média | 2h |

**Entregáveis:**
- Página de serviços systemd
- Logs de serviços

### Fase 7: Logs e Diagnostics (Dia 13)

**Objetivo:** Visualização de logs e diagnóstico.

| Tarefa | Descrição | Complexidade | Tempo |
|--------|-----------|--------------|-------|
| 7.1 | Criar serviço de logs | Média | 2h |
| 7.2 | Implementar visualizador de logs | Média | 3h |
| 7.3 | Adicionar filtros (busca, nível) | Média | 2h |
| 7.4 | Criar página de diagnóstico | Baixa | 1h |

**Entregáveis:**
- Visualizador de logs com busca
- Página de diagnóstico

### Fase 8: Polimento e Deployment (Dias 14-15)

**Objetivo:** Finalização e deployment.

| Tarefa | Descrição | Complexidade | Tempo |
|--------|-----------|--------------|-------|
| 8.1 | Adicionar notificações toast | Baixa | 1h |
| 8.2 | Implementar loading states | Baixa | 1h |
| 8.3 | Adicionar tratamento de erros | Média | 2h |
| 8.4 | Criar Dockerfile | Baixa | 1h |
| 8.5 | Criar docker-compose.yml | Baixa | 1h |
| 8.6 | Documentar instalação | Média | 2h |
| 8.7 | Testes finais | Média | 4h |

**Entregáveis:**
- App production-ready
- Dockerfile e compose
- Documentação

---

## 8. Estimativas Detalhadas

### 8.1 Por Funcionalidade

| Funcionalidade | Complexidade | Tempo Estimado | Prioridade |
|----------------|--------------|----------------|------------|
| Setup projeto + auth | Alta | 8h | Deve ter |
| Dashboard | Média | 6h | Deve ter |
| Docker - listar containers | Baixa | 2h | Deve ter |
| Docker - start/stop/restart | Baixa | 3h | Deve ter |
| Docker - logs | Média | 4h | Deve ter |
| Docker - stats realtime | Média | 4h | Deve ter |
| HD - status | Baixa | 1h | Deve ter |
| HD - mount/unmount | Média | 3h | Deve ter |
| Backup - listar fontes | Baixa | 2h | Deve ter |
| Backup - adicionar fonte | Média | 4h | Deve ter |
| Backup - executar backup | Média | 3h | Deve ter |
| Backup - histórico | Média | 3h | Pode esperar |
| Backup - estatísticas | Alta | 5h | Pode esperar |
| Systemd - listar serviços | Baixa | 2h | Deve ter |
| Systemd - ações | Média | 4h | Deve ter |
| Log viewer | Média | 5h | Deve ter |
| SWAP clean | Baixa | 1h | Pode esperar |
| Sync files | Baixa | 1h | Pode esperar |
| Diagnostics | Baixa | 2h | Pode esperar |

### 8.2 Resumo por Fase

| Fase | Descrição | Tempo Total |
|------|-----------|-------------|
| 1 | Setup + Auth | 8h |
| 2 | Dashboard + Status | 9h |
| 3 | Docker Management | 13h |
| 4 | HD Management | 6h |
| 5 | Backup Management | 14h |
| 6 | Systemd Services | 8h |
| 7 | Logs + Diagnostics | 8h |
| 8 | Polimento + Deploy | 12h |
| **Total** | | **~78h** (~10 dias) |

---

## 9. Requisitos de Sistema

### 9.1 Para o Servidor

- Python 3.10+
- Acesso ao socket Docker (para API Docker)
- Acesso ao systemctl (para systemd)
- Acesso sudo para mount/umount (ou PolKit configurado)
- 512MB RAM mínimo
- 1GB disco para a aplicação

### 9.2 Para o Cliente

- Browser moderno (Chrome, Firefox, Safari, Edge)
- JavaScript habilitado (para HTMX e SSE)
- Acesso à rede do servidor

---

## 10. Configuração de Segurança

### 10.1 Autenticação

```python
# Configuração sugerida
JWT_SECRET_KEY = "generated-secure-random-key"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
```

### 10.2 Permissões Necessárias

```bash
# Para mount/umount (PolKit)
# /etc/polkit-1/localauthority/50-local.d/50-mount.pkla
[Allow mount for users in wheel group]
Identity=unix-group:wheel
Action=org.freedesktop.udisks2.mount;org.freedesktop.udisks2.unmount
ResultAny=yes

# Para Docker (usuário no grupo docker)
sudo usermod -aG docker mateus

# Para systemctl (requer sudo via API)
# Implementar wrapper que usa sudo
```

### 10.3 Considerações

- [ ] Usar HTTPS em produção
- [ ] Implementar rate limiting
- [ ] Validar inputs contra injection
- [ ] Sanitizar outputs
- [ ] Manter logs de auditoria

---

## 11. Deployment

### 11.1 Via Docker Compose (Recomendado)

```yaml
# docker-compose.yml
services:
  web-panel:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /home/mateus:/home/mateus:ro
      - /etc/systemd/system:/etc/systemd/system:ro
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - USERNAME=${USERNAME}
      - PASSWORD_HASH=${PASSWORD_HASH}
    restart: unless-stopped
```

### 11.2 Via Systemd (Alternativa)

```ini
# web-panel.service
[Unit]
Description=Control Panel Web Interface
After=network.target

[Service]
Type=simple
User=mateus
WorkingDirectory=/path/to/web-panel
Environment="SECRET_KEY=xxx"
ExecStart=/path/to/web-panel/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 12. Próximos Passos

### Antes de Começar

1. [ ] Revisar e validar este plano
2. [ ] Decidir sobrestack de frontend (HTMX vs React/Vue)
3. [ ] Configurar credentials de acesso (username/password)
4. [ ] Preparar ambiente de desenvolvimento
5. [ ] Configurar controle de versão (branch `feature/web-panel`)

### Ordem de Implementação Sugerida

1. **Fase 1:** Setup + Auth (sempre primeiro)
2. **Fase 2:** Dashboard (dá visão do sistema)
3. **Fase 3:** Docker (funcionalidade mais usada)
4. **Fase 4-6:** HD, Backup, Systemd
5. **Fase 7-8:** Logs e polimento

---

## 13. Apêndice

### 13.1 Comandos Úteis

```bash
# Development
cd web-panel
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Production
sudo systemctl start web-panel
sudo systemctl enable web-panel

# Logs
journalctl -u web-panel -f
```

### 13.2 Estrutura de Arquivos de Configuração

O web-panel usará a configuração existente do `control-panel`:
- Backup config: `~/.local/share/control-panel/backup/.backup_config`
- Logs: `~/.control-panel.log`
- Scripts: `~/scripts/`

### 13.3 Contato e Suporte

Para dúvidas sobre implementação, consulte:
- `AGENTS.md` - Contexto dos agentes
- `scripts/AGENTS.md` - Detalhes dos módulos Python
- `docs/` - Documentação do projeto

---

**Documento criado:** 2026-05-16  
**Última atualização:** 2026-05-16  
**Versão:** 1.0
