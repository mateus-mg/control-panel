#!/usr/bin/env python3
"""
Log Formatter - Estrutura hierárquica padronizada para logs
Control Panel System
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


class LogSection:
    """Formatador hierárquico de logs com 3 níveis de estrutura"""

    # Separadores visuais
    SEP_MAJOR = "━" * 80
    SEP_MINOR = "─" * 80

    # Indentação por nível
    INDENT_L1 = ""
    INDENT_L2 = "  "
    INDENT_L3 = "    "

    # Símbolos (uso reduzido)
    CHECK = "✓"
    CROSS = "✗"
    ARROW = "→"
    BULLET = "•"

    @staticmethod
    def major_header(title: str, subtitle: str = None) -> List[str]:
        """
        Cabeçalho de seção principal (Nível 1)

        Args:
            title: Título principal da seção
            subtitle: Subtítulo opcional (informações adicionais)

        Returns:
            Lista de linhas formatadas

        Example:
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            SYSTEM STARTUP - 2026-02-14 22:55:03
            PID: 3334771 | Session: a7f3c | Total Cycles: 127
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        lines = [LogSection.SEP_MAJOR, title]
        if subtitle:
            lines.append(subtitle)
        lines.append(LogSection.SEP_MAJOR)
        return lines

    @staticmethod
    def minor_header(title: str) -> List[str]:
        """
        Cabeçalho de subseção (Nível 2)

        Args:
            title: Título da subseção

        Returns:
            Lista de linhas formatadas

        Example:
            ──────────────────────────────────────────────────────────
            Gospel (Mateus, Ellen) - 45 tracks | 20 done | 25 pending
            ──────────────────────────────────────────────────────────
        """
        return [LogSection.SEP_MINOR, title, LogSection.SEP_MINOR]

    @staticmethod
    def section(title: str, items: Dict[str, Any], indent: str = INDENT_L2) -> List[str]:
        """
        Seção com múltiplos items (Nível 2)

        Args:
            title: Título da seção
            items: Dicionário com pares chave-valor
            indent: String de indentação (padrão: 2 espaços)

        Returns:
            Lista de linhas formatadas

        Example:
            Database
              Tracks: 203 | Playlists: 4 | Blacklist: 8 users
              Cache: 2 playlists | Metadata: 7d validity
        """
        lines = [f"\n{title}"]

        for key, value in items.items():
            if isinstance(value, dict):
                # Sub-item (Nível 3)
                lines.append(f"{indent}{key}")
                for k, v in value.items():
                    lines.append(f"{indent}{indent}{k}: {v}")
            elif isinstance(value, list):
                # Lista de valores
                lines.append(f"{indent}{key}:")
                for item in value:
                    lines.append(f"{indent}{indent}{LogSection.BULLET} {item}")
            else:
                # Item simples
                lines.append(f"{indent}{key}: {value}")

        return lines

    @staticmethod
    def inline_section(title: str, items: Dict[str, Any], sep: str = " | ") -> str:
        """
        Seção compacta inline com separador

        Args:
            title: Título da seção inline
            items: Dicionário com pares chave-valor
            sep: Separador entre items (padrão: " | ")

        Returns:
            String formatada inline

        Example:
            "Database: Tracks: 203 | Playlists: 4 | Blacklist: 8 users"
        """
        items_str = sep.join([f"{k}: {v}" for k, v in items.items()])
        return f"{title}: {items_str}" if title else items_str

    @staticmethod
    def key_value_list(items: Dict[str, Any], sep: str = " | ", max_items: Optional[int] = None) -> str:
        """
        Lista de pares chave-valor separados inline

        Args:
            items: Dicionário com pares chave-valor
            sep: Separador entre items (padrão: " | ")
            max_items: Número máximo de items (None = todos)

        Returns:
            String formatada inline

        Example:
            "Tracks: 203 | Playlists: 4 | Blacklist: 8"
        """
        items_list = list(items.items())
        if max_items:
            items_list = items_list[:max_items]

        return sep.join([f"{k}: {v}" for k, v in items_list])

    @staticmethod
    def progress_line(current: int, total: int, label: str = "Progress",
                      extras: Optional[Dict[str, Any]] = None) -> str:
        """
        Linha de progresso com informações adicionais

        Args:
            current: Valor atual
            total: Valor total
            label: Label do progresso (padrão: "Progress")
            extras: Informações extras para adicionar

        Returns:
            String formatada

        Example:
            "[Progress: 23/25 | 2 failed | 68 quota left | Elapsed: 4m 12s]"
        """
        percentage = (current / total * 100) if total > 0 else 0
        parts = [f"{current}/{total} ({percentage:.1f}%)"]

        if extras:
            parts.extend([f"{k}: {v}" for k, v in extras.items()])

        return f"[{label}: {' | '.join(parts)}]"

    @staticmethod
    def download_item(artist: str, title: str, details: Optional[str] = None,
                      status: str = "✓", indent: str = INDENT_L2) -> List[str]:
        """
        Item de download estruturado

        Args:
            artist: Nome do artista
            title: Título da faixa
            details: Detalhes do download (tamanho, bitrate, fonte)
            status: Símbolo de status (padrão: "✓")
            indent: Indentação (padrão: 2 espaços)

        Returns:
            Lista de linhas formatadas

        Example:
            → Hillsong United - Oceans (Where Feet May Fail)
              Downloaded: 6.2MB @ 320kbps via SLSKD
        """
        lines = [f"{LogSection.ARROW} {artist} - {title}"]
        if details:
            lines.append(f"{indent}{details}")
        return lines

    @staticmethod
    def error_block(title: str, details: Dict[str, Any]) -> List[str]:
        """
        Bloco de erro estruturado

        Args:
            title: Título do erro
            details: Detalhes do erro (status, action, etc.)

        Returns:
            Lista de linhas formatadas

        Example:
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            ERROR: SPOTIFY API RATE LIMIT EXCEEDED
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            Status: 429 Too Many Requests
            Action: Cycle skipped, will resume automatically
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        lines = [LogSection.SEP_MAJOR, title, LogSection.SEP_MAJOR]
        for key, value in details.items():
            lines.append(f"{key}: {value}")
        lines.append(LogSection.SEP_MAJOR)
        return lines

    @staticmethod
    def format_duration(seconds: float) -> str:
        """
        Formata duração em horas/minutos legível

        Args:
            seconds: Duração em segundos

        Returns:
            String formatada (ex: "4h 33m", "45m", "2h 00m")
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)

        if hours > 0:
            return f"{hours}h {minutes:02d}m"
        else:
            return f"{minutes}m"

    @staticmethod
    def format_size(bytes_size: float) -> str:
        """
        Formata tamanho de arquivo em formato legível

        Args:
            bytes_size: Tamanho em bytes

        Returns:
            String formatada (ex: "8.3MB", "1.2GB")
        """
        if bytes_size >= 1024**3:
            return f"{bytes_size / (1024**3):.1f}GB"
        elif bytes_size >= 1024**2:
            return f"{bytes_size / (1024**2):.1f}MB"
        elif bytes_size >= 1024:
            return f"{bytes_size / 1024:.1f}KB"
        else:
            return f"{bytes_size:.0f}B"

    @staticmethod
    def format_timestamp(dt: Optional[datetime] = None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        Formata timestamp para formato legível

        Args:
            dt: Objeto datetime (None = agora)
            fmt: Formato de saída

        Returns:
            String formatada
        """
        if dt is None:
            dt = datetime.now()
        return dt.strftime(fmt)

    @staticmethod
    def table_row(columns: List[Any], widths: Optional[List[int]] = None, align: str = "left") -> str:
        """
        Formata linha de tabela com colunas alinhadas

        Args:
            columns: Lista de valores das colunas
            widths: Lista de larguras de cada coluna (None = auto)
            align: Alinhamento ("left", "right", "center")

        Returns:
            String formatada

        Example:
            "Downloads: 70 added | 18 unique | 30 quota left"
        """
        if widths is None:
            widths = [len(str(col)) for col in columns]

        formatted_cols = []
        for col, width in zip(columns, widths):
            col_str = str(col)
            if align == "right":
                formatted_cols.append(col_str.rjust(width))
            elif align == "center":
                formatted_cols.append(col_str.center(width))
            else:
                formatted_cols.append(col_str.ljust(width))

        return " ".join(formatted_cols)

    @staticmethod
    def summary_line(label: str, items: Dict[str, Any], sep: str = " | ") -> str:
        """
        Linha de sumário com label e items

        Args:
            label: Label da linha (será alinhado à esquerda)
            items: Dicionário de items
            sep: Separador entre items

        Returns:
            String formatada

        Example:
            "Downloads:  70 added | 18 unique | 30 quota left"
        """
        label_formatted = f"{label}:".ljust(12)
        items_str = sep.join([f"{v} {k}" for k, v in items.items()])
        return f"{label_formatted}{items_str}"


class LogBuilder:
    """Builder para construir logs complexos de forma fluente"""

    def __init__(self):
        self.lines: List[str] = []

    def add_major_header(self, title: str, subtitle: str = None) -> 'LogBuilder':
        """Adiciona cabeçalho principal"""
        self.lines.extend(LogSection.major_header(title, subtitle))
        return self

    def add_minor_header(self, title: str) -> 'LogBuilder':
        """Adiciona cabeçalho de subseção"""
        self.lines.extend(LogSection.minor_header(title))
        return self

    def add_section(self, title: str, items: Dict[str, Any], indent: str = LogSection.INDENT_L2) -> 'LogBuilder':
        """Adiciona seção com items"""
        self.lines.extend(LogSection.section(title, items, indent))
        return self

    def add_line(self, line: str) -> 'LogBuilder':
        """Adiciona linha customizada"""
        self.lines.append(line)
        return self

    def add_blank(self, count: int = 1) -> 'LogBuilder':
        """Adiciona linhas em branco"""
        self.lines.extend([""] * count)
        return self

    def build(self) -> List[str]:
        """Retorna lista de linhas construídas"""
        return self.lines

    def build_str(self, sep: str = "\n") -> str:
        """Retorna string única com todas as linhas"""
        return sep.join(self.lines)


# Funções de conveniência para casos comuns
def format_system_startup(pid: int, session_id: str, total_cycles: int,
                          storage: Dict[str, Any], docker: Dict[str, Any],
                          systemd: Dict[str, Any], checks: Dict[str, bool]) -> List[str]:
    """
    Formata log de inicialização do sistema

    Returns:
        Lista de linhas formatadas
    """
    builder = LogBuilder()

    # Header
    builder.add_major_header(
        f"CONTROL PANEL STARTUP - {LogSection.format_timestamp()}",
        f"PID: {pid} | Session: {session_id} | Total Operations: {total_cycles}"
    )

    # Storage section
    builder.add_section("Storage", storage)

    # Docker section
    builder.add_section("Docker", docker)

    # Systemd section
    builder.add_section("Systemd", systemd)

    # System checks
    check_items = {
        k: LogSection.CHECK if v else LogSection.CROSS for k, v in checks.items()}
    builder.add_section("System Checks", check_items)

    builder.add_line(LogSection.SEP_MAJOR)

    return builder.build()


def format_operation_start(operation: str, session_num: int, checks: Dict[str, bool],
                          processing: Dict[str, Any]) -> List[str]:
    """
    Formata log de início de operação

    Returns:
        Lista de linhas formatadas
    """
    builder = LogBuilder()

    builder.add_major_header(
        f"OPERATION: {operation.upper()} (Session: #{session_num}) - {LogSection.format_timestamp(None, '%H:%M:%S')}"
    )

    # Pre-flight checks inline
    check_str = " | ".join([f"{k} {LogSection.CHECK if v else LogSection.CROSS}"
                            for k, v in checks.items()])
    builder.add_line(f"Pre-Flight: {check_str}")

    # Processing info inline
    proc_str = LogSection.key_value_list(processing, sep=" | ")
    builder.add_line(f"Processing: {proc_str}")

    return builder.build()


def format_operation_complete(operation: str, duration: float, results: Dict[str, Any],
                          status: Dict[str, Any], errors: Dict[str, Any],
                          progress: Optional[Dict[str, Any]] = None,
                          next_action: Optional[str] = None) -> List[str]:
    """
    Formata log de conclusão de operação

    Returns:
        Lista de linhas formatadas
    """
    builder = LogBuilder()

    builder.add_minor_header(
        f"OPERATION: {operation.upper()} COMPLETE - Duration: {LogSection.format_duration(duration)} ({duration:.0f}s)"
    )

    # Summary lines
    builder.add_line(LogSection.summary_line("Results", results))
    builder.add_line(LogSection.summary_line("Status", status))
    builder.add_line(LogSection.summary_line("Errors", errors))

    if progress:
        builder.add_line(LogSection.summary_line("Progress", progress))

    if next_action:
        builder.add_blank()
        builder.add_line(f"Next action: {next_action}")

    return builder.build()


def format_system_shutdown(summary: Dict[str, str]) -> List[str]:
    """
    Formata log de encerramento do sistema

    Args:
        summary: Dicionário com estatísticas formatadas

    Returns:
        Lista de linhas formatadas
    """
    builder = LogBuilder()

    builder.add_major_header("CONTROL PANEL SHUTDOWN")

    builder.add_line("Final Statistics")
    for key, value in summary.items():
        builder.add_line(f"{LogSection.INDENT_L2}{LogSection.BULLET} {value}")

    builder.add_line(LogSection.SEP_MAJOR)

    return builder.build()


def format_service_start(service_name: str, status: str, stats: Dict[str, Any]) -> List[str]:
    """
    Formata log de início de serviço

    Args:
        service_name: Nome do serviço
        status: Status do serviço
        stats: Estatísticas (total, done, pending, etc.)

    Returns:
        Lista de linhas formatadas
    """
    builder = LogBuilder()

    # Título com resumo inline
    title = f"{service_name}"
    if status:
        title += f" ({status})"

    # Stats inline
    stats_parts = []
    if 'total' in stats:
        stats_parts.append(f"{stats['total']} units")
    if 'running' in stats:
        stats_parts.append(f"{stats['running']} running")
    if 'stopped' in stats:
        stats_parts.append(f"{stats['stopped']} stopped")

    if stats_parts:
        title += f" - {' | '.join(stats_parts)}"

    builder.add_minor_header(title)

    return builder.build()
