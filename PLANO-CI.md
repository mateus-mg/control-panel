# Plano de CI/CD - control-panel

## Objetivo
Criar testes unitários básicos para CLI Python (com mocks) + lint de shell scripts + CI + proteção de branch.

## Status
- [x] Criado em: 2026-04-25
- [x] Autor: OpenCode AI

## Tarefas

### Task 1: Criar estrutura de testes Python
Criar `tests/` com:
- `test_cli_manager_init.py` — Testar inicialização do `CLIManager` (verificar paths, configs)
- `test_control_panel_wrapper.py` — Testar lógica do wrapper e paths
- `__init__.py` — Tornar tests um pacote Python

> **Nota**: Os testes mockam dependências pesadas (Rich, Docker) para evitar side effects.

### Task 2: Criar `requirements-test.txt`
Arquivo com dependências de teste para CI.

### Task 3: Criar `.github/workflows/tests.yml`
- **Trigger**: `push` em `main`, `pull_request`
- **Job `python-tests`**: Rodar pytest com mocks
- **Job `shell-lint`**: shellcheck + syntax validation

### Task 4: Configurar Branch Protection
Via `gh api`:
- Requerer 1 review de PR
- Dismiss stale reviews
- Requerer status checks: `python-tests` e `shell-lint`
- Block force pushes e deletions
- Requerer conversation resolution

## Arquivos Criados/Modificados
| Arquivo | Ação | Status |
|---------|------|--------|
| `tests/__init__.py` | Criar | Pendente |
| `tests/test_cli_manager_init.py` | Criar | Pendente |
| `tests/test_control_panel_wrapper.py` | Criar | Pendente |
| `requirements-test.txt` | Criar | Pendente |
| `.github/workflows/tests.yml` | Criar | Pendente |

## Comandos de Configuração

```bash
gh api repos/mateus-mg/control-panel/branches/main/protection \
  --method PUT \
  --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["python-tests", "shell-lint"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true
}
EOF
```

## Notas
- Projeto híbrido: Python CLI (Rich) + Bash + Docker
- Nenhum teste automatizado existia anteriormente
- Dependências de runtime estão no venv local; CI instala apenas pytest + rich para mocks
- Scripts shellcheck: `control_panel.sh`, `control-panel`, `scripts/*.sh`
