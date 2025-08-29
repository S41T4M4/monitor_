#!/usr/bin/env python3
"""
CLI para monitorar e controlar automações que rodam via crontab.
Sistema de monitoramento de ~12 automações .NET com logs e status.

Autor: Sistema de Automação JC
Versão: 1.0.0
"""

import argparse
import sqlite3
import sys
import re
from datetime import datetime
from typing import Optional, Dict

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box


class LogParser:
    """Parser para analisar logs reais das automações."""
    
    def __init__(self):
        # Padrões para identificar diferentes elementos nos logs
        self.execution_header_pattern = re.compile(
            r'=== Execução: (.+?) ===',
            re.IGNORECASE
        )
        
        # Padrões para identificar sucesso
        self.success_patterns = [
            r'Data da última atualização inserida na tabela de controle \(sucesso\)',
            r'Linhas afetadas: \d+',
            r'Nova linha inserida na tabela CONTROL com sucesso',
            r'Conexão aberta com sucesso',
            r'Finalizado sem erros',
            r'concluída com sucesso',
            r'processados com sucesso'
        ]
        
        # Padrões para identificar falhas
        self.failure_patterns = [
            r'Erro:',
            r'Falha:',
            r'Exception:',
            r'Error:',
            r'Timeout',
            r'falhou',
            r'erro'
        ]
        
        # Padrões para identificar execução em andamento
        self.pending_patterns = [
            r'Processamento iniciado',
            r'Iniciando',
            r'Aguardando',
            r'Processando'
        ]
    
    def parse_execution_date(self, log_content: str) -> Optional[str]:
        """Extrai a data de execução do cabeçalho do log."""
        match = self.execution_header_pattern.search(log_content)
        if match:
            try:
                # Converter a data encontrada para formato padrão
                date_str = match.group(1).strip()
                # Parse da data no formato "Wed Aug 20 09:23:03 AM -03 2025"
                # Remover timezone para simplificar
                date_str_clean = date_str.replace(" -03", "")
                parsed_date = datetime.strptime(
                    date_str_clean, 
                    "%a %b %d %I:%M:%S %p %Y"
                )
                return parsed_date.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                # Se falhar, tentar outros formatos
                try:
                    # Formato alternativo: "8/20/2025 9:23:06 AM"
                    parsed_date = datetime.strptime(
                        date_str, 
                        "%m/%d/%Y %I:%M:%S %p"
                    )
                    return parsed_date.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    return None
        return None
    
    def determine_status(self, log_content: str) -> str:
        """Determina o status da automação baseado no conteúdo do log."""
        log_lower = log_content.lower()
        
        # Verificar se há padrões de sucesso
        for pattern in self.success_patterns:
            if re.search(pattern, log_content, re.IGNORECASE):
                return "OK"
        
        # Verificar se há padrões de falha
        for pattern in self.failure_patterns:
            if re.search(pattern, log_content, re.IGNORECASE):
                return "FAIL"
        
        # Verificar se há padrões de execução em andamento
        for pattern in self.pending_patterns:
            if re.search(pattern, log_content, re.IGNORECASE):
                return "PENDING"
        
        # Se não encontrar padrões específicos, assumir OK se não houver erros
        if "erro" not in log_lower and "error" not in log_lower:
            return "OK"
        
        return "FAIL"
    
    def extract_key_info(self, log_content: str) -> Dict[str, str]:
        """Extrai informações chave do log."""
        info = {}
        
        # Data de execução
        exec_date = self.parse_execution_date(log_content)
        if exec_date:
            info['execution_date'] = exec_date
        
        # Status
        info['status'] = self.determine_status(log_content)
        
        # Mensagem resumida
        lines = log_content.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('===') and not line.startswith('lsfnjdn'):
                # Encontrar a primeira linha significativa
                if len(line) > 10:  # Linha com conteúdo real
                    info['message'] = line[:100] + "..." if len(line) > 100 else line
                    break
        
        return info


class AutomationCLI:
    """CLI principal para gerenciamento de automações."""
    
    def __init__(self, db_path: str = "automation.db"):
        self.db_path = db_path
        self.console = Console()
        self.log_parser = LogParser()
        self.init_database()
    
    def init_database(self):
        """Inicializa o banco SQLite com as tabelas necessárias."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabela de automações
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS automations (
                        name TEXT PRIMARY KEY,
                        schedule TEXT,
                        behavior TEXT,
                        last_status TEXT DEFAULT 'NONE',
                        last_run TIMESTAMP
                    )
                """)
                
                # Tabela de logs
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        automation TEXT,
                        timestamp TIMESTAMP,
                        status TEXT,
                        message TEXT,
                        FOREIGN KEY (automation) REFERENCES automations (name)
                    )
                """)
                
                conn.commit()
                self.console.print("[green]✓[/green] Banco de dados inicializado com sucesso")
                
        except sqlite3.Error as e:
            self.console.print(f"[red]✗[/red] Erro ao inicializar banco: {e}")
            sys.exit(1)
    
    def seed_mock_data(self):
        """Insere dados de exemplo para simulação das automações."""
        mock_automations = [
            # Automações diárias às 8h
            ("C1", "0 8 * * *", "Import de Vendas - Execução diária"),
            ("CAT1", "0 8 * * *", "Categorização - Execução diária"),
            ("NC1", "0 8 * * *", "Notas de Crédito - Execução diária"),
            ("PG1", "0 8 * * *", "Pagamentos - Execução diária"),
            ("PR2", "0 8 * * *", "Processamento de Pedidos 2 - Execução diária"),
            
            # Automações de hora em hora (8h-17h)
            ("CR1", "0 8-17 * * *", "Controle de Receitas - A cada hora"),
            ("NF1", "0 8-17 * * *", "Notas Fiscais 1 - A cada hora"),
            ("NF2", "0 8-17 * * *", "Notas Fiscais 2 - A cada hora"),
            ("P1", "0 8-17 * * *", "Produtos 1 - A cada hora"),
            ("P2", "0 8-17 * * *", "Produtos 2 - A cada hora"),
            
            # Automações de 1h30 em 1h30
            ("EM1", "0 8,11,14,17 * * *", "Estoque e Movimentação - A cada 1h30"),
            ("EM1", "30 9,12,15 * * *", "Estoque e Movimentação - A cada 1h30"),
            
            # Automações de 2 em 2 horas (8h-16h)
            ("ODC1", "0 8,10,12,14,16 * * *", "Ordens de Compra 1 - A cada 2h"),
            ("ODC2", "0 8,10,12,14,16 * * *", "Ordens de Compra 2 - A cada 2h"),
            ("ORC1", "0 8,10,12,14,16 * * *", "Ordens de Recebimento - A cada 2h"),
            ("PR1", "0 8,10,12,14,16 * * *", "Processamento de Pedidos 1 - A cada 2h"),
            
            # Automação V1 (frequência a definir)
            ("V1", "0 9 * * *", "Validação - Execução diária")
        ]
        
        mock_logs = [
            # C1 - Import de Vendas (diário às 8h)
            ("C1", "2025-08-29 08:00:00", "OK", 
             "Import de vendas concluído. 156 registros processados"),
            ("C1", "2025-08-28 08:00:00", "OK", 
             "Import de vendas concluído. 142 registros processados"),
            
            # CAT1 - Categorização (diário às 8h)
            ("CAT1", "2025-08-29 08:00:00", "OK", 
             "Categorização concluída. 89 produtos categorizados"),
            
            # CR1 - Controle de Receitas (hora em hora 8h-17h)
            ("CR1", "2025-08-29 10:00:01", "OK", 
             "Conta inserida/atualizada com sucesso na tabela CR1!"),
            ("CR1", "2025-08-29 09:00:01", "OK", 
             "Conta inserida/atualizada com sucesso na tabela CR1!"),
            ("CR1", "2025-08-29 08:00:01", "OK", 
             "Conta inserida/atualizada com sucesso na tabela CR1!"),
            
            # NF1 - Notas Fiscais 1 (hora em hora 8h-17h)
            ("NF1", "2025-08-29 10:00:00", "OK", 
             "15 notas fiscais processadas com sucesso"),
            ("NF1", "2025-08-29 09:00:00", "OK", 
             "12 notas fiscais processadas com sucesso"),
            
            # NF2 - Notas Fiscais 2 (hora em hora 8h-17h)
            ("NF2", "2025-08-29 10:00:00", "OK", 
             "8 notas fiscais processadas com sucesso"),
            ("NF2", "2025-08-29 09:00:00", "FAIL", 
             "Erro: Falha na validação de dados"),
            
            # EM1 - Estoque e Movimentação (1h30 em 1h30)
            ("EM1", "2025-08-29 09:30:00", "OK", 
             "Movimentação de estoque concluída. 45 itens atualizados"),
            ("EM1", "2025-08-29 08:00:00", "OK", 
             "Movimentação de estoque concluída. 38 itens atualizados"),
            
            # ODC1 - Ordens de Compra 1 (2 em 2h 8h-16h)
            ("ODC1", "2025-08-29 10:00:00", "OK", 
             "Ordens de compra processadas. 12 ordens criadas"),
            ("ODC1", "2025-08-29 08:00:00", "OK", 
             "Ordens de compra processadas. 8 ordens criadas"),
            
            # V1 - Validação (diário às 9h)
            ("V1", "2025-08-29 09:00:00", "OK", 
             "Validação concluída. 0 inconsistências encontradas")
        ]
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Inserir automações
                cursor.executemany("""
                    INSERT OR REPLACE INTO automations 
                    (name, schedule, behavior, last_status, last_run)
                    VALUES (?, ?, ?, ?, ?)
                """, [
                    (name, schedule, behavior, "NONE", None) 
                    for name, schedule, behavior in mock_automations
                ])
                
                # Inserir logs
                cursor.executemany("""
                    INSERT INTO logs (automation, timestamp, status, message)
                    VALUES (?, ?, ?, ?)
                """, mock_logs)
                
                # Atualizar status e última execução das automações
                for automation_name, timestamp, status, message in mock_logs:
                    cursor.execute("""
                        UPDATE automations 
                        SET last_status = ?, last_run = ?
                        WHERE name = ? AND 
                        (last_run IS NULL OR last_run < ?)
                    """, (status, timestamp, automation_name, timestamp))
                
                conn.commit()
                self.console.print("[green]✓[/green] Dados mock inseridos com sucesso")
                
        except sqlite3.Error as e:
            self.console.print(f"[red]✗[/red] Erro ao inserir dados mock: {e}")
    
    def test_log_parsing(self, log_content: str):
        """Testa o parsing de um log real."""
        self.console.print("[bold blue]🔍 Testando Parser de Logs[/bold blue]\n")
        
        # Mostrar o log original
        self.console.print("[bold]Log Original:[/bold]")
        self.console.print(f"[white]{log_content}[/white]\n")
        
        # Analisar o log
        info = self.log_parser.extract_key_info(log_content)
        
        # Mostrar resultados da análise
        self.console.print("[bold]Resultados da Análise:[/bold]")
        
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
        table.add_column("Campo", style="cyan")
        table.add_column("Valor", style="white")
        
        for field, value in info.items():
            if field == 'status':
                color = self.get_status_color(value)
                value_display = f"[{color}]{value}[/{color}]"
            else:
                value_display = str(value) if value else "N/A"
            
            table.add_row(field.replace('_', ' ').title(), value_display)
        
        self.console.print(table)
        
        # Mostrar padrões encontrados
        self.console.print("\n[bold]Padrões Identificados:[/bold]")
        
        # Data de execução
        exec_date = self.log_parser.parse_execution_date(log_content)
        if exec_date:
            self.console.print(f"📅 [green]Data de Execução:[/green] {exec_date}")
        else:
            self.console.print("📅 [red]Data de Execução:[/red] Não encontrada")
        
        # Status
        status = self.log_parser.determine_status(log_content)
        status_color = self.get_status_color(status)
        self.console.print(f"📊 [green]Status Detectado:[/green] [{status_color}]{status}[/{status_color}]")
        
        # Mensagem resumida
        if 'message' in info:
            self.console.print(f"💬 [green]Mensagem:[/green] {info['message']}")
    
    def add_real_log(self, automation_name: str, log_content: str):
        """Adiciona um log real ao banco usando o parser."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verificar se a automação existe
                cursor.execute(
                    "SELECT name FROM automations WHERE name = ?", 
                    (automation_name,)
                )
                if not cursor.fetchone():
                    self.console.print(
                        f"[red]✗[/red] Automação '{automation_name}' não encontrada"
                    )
                    return
                
                # Analisar o log
                info = self.log_parser.extract_key_info(log_content)
                
                # Usar a data de execução se encontrada, senão usar timestamp atual
                timestamp = info.get('execution_date', 
                                   datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                status = info.get('status', 'NONE')
                message = info.get('message', 'Log processado automaticamente')
                
                # Inserir log
                cursor.execute("""
                    INSERT INTO logs (automation, timestamp, status, message)
                    VALUES (?, ?, ?, ?)
                """, (automation_name, timestamp, status, message))
                
                # Atualizar status da automação
                cursor.execute("""
                    UPDATE automations 
                    SET last_status = ?, last_run = ?
                    WHERE name = ?
                """, (status, timestamp, automation_name))
                
                conn.commit()
                
                status_color = self.get_status_color(status)
                self.console.print(f"[green]✓[/green] Log processado para '{automation_name}':")
                self.console.print(f"  📅 Data: {timestamp}")
                self.console.print(f"  📊 Status: [{status_color}]{status}[/{status_color}]")
                self.console.print(f"  💬 Mensagem: {message}")
                
        except sqlite3.Error as e:
            self.console.print(f"[red]✗[/red] Erro ao processar log: {e}")
    
    def get_status_color(self, status: str) -> str:
        """Retorna a cor apropriada para cada status."""
        colors = {
            "OK": "green",
            "FAIL": "red", 
            "PENDING": "yellow",
            "NONE": "white"
        }
        return colors.get(status, "white")
    
    def show_all_status(self):
        """Exibe o status de todas as automações."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name, schedule, behavior, last_status, last_run
                    FROM automations
                    ORDER BY name
                """)
                
                automations = cursor.fetchall()
                
                if not automations:
                    self.console.print("[yellow]Nenhuma automação encontrada[/yellow]")
                    return
                
                # Criar tabela
                table = Table(
                    title="[bold blue]Status das Automações[/bold blue]",
                    box=box.ROUNDED,
                    show_header=True,
                    header_style="bold magenta"
                )
                
                table.add_column("Nome", style="cyan", no_wrap=True)
                table.add_column("Agendamento", style="white")
                table.add_column("Comportamento", style="white")
                table.add_column("Último Status", style="bold")
                table.add_column("Última Execução", style="white")
                
                for name, schedule, behavior, status, last_run in automations:
                    status_color = self.get_status_color(status)
                    status_text = f"[{status_color}]{status}[/{status_color}]"
                    
                    last_run_str = last_run if last_run else "Nunca"
                    
                    table.add_row(
                        name,
                        schedule,
                        behavior,
                        status_text,
                        last_run_str
                    )
                
                self.console.print(table)
                
        except sqlite3.Error as e:
            self.console.print(f"[red]✗[/red] Erro ao consultar status: {e}")
    
    def show_automation_history(self, automation_name: str, date_filter: Optional[str] = None):
        """Exibe o histórico de uma automação específica."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verificar se a automação existe
                cursor.execute(
                    "SELECT name FROM automations WHERE name = ?", 
                    (automation_name,)
                )
                if not cursor.fetchone():
                    self.console.print(
                        f"[red]✗[/red] Automação '{automation_name}' não encontrada"
                    )
                    return
                
                # Construir query com filtro de data se fornecido
                query = """
                    SELECT timestamp, status, message
                    FROM logs
                    WHERE automation = ?
                """
                params = [automation_name]
                
                if date_filter:
                    query += " AND DATE(timestamp) = ?"
                    params.append(date_filter)
                
                query += " ORDER BY timestamp DESC LIMIT 50"
                
                cursor.execute(query, params)
                logs = cursor.fetchall()
                
                if not logs:
                    self.console.print(f"[yellow]Nenhum log encontrado para '{automation_name}'[/yellow]")
                    return
                
                # Criar tabela de histórico
                table = Table(
                    title=f"[bold blue]Histórico da Automação: {automation_name}[/bold blue]",
                    box=box.ROUNDED,
                    show_header=True,
                    header_style="bold magenta"
                )
                
                table.add_column("Data/Hora", style="cyan", no_wrap=True)
                table.add_column("Status", style="bold")
                table.add_column("Mensagem", style="white")
                
                for timestamp, status, message in logs:
                    status_color = self.get_status_color(status)
                    status_text = f"[{status_color}]{status}[/{status_color}]"
                    
                    table.add_row(
                        timestamp,
                        status_text,
                        message[:80] + "..." if len(message) > 80 else message
                    )
                
                self.console.print(table)
                
                # Mostrar estatísticas
                total_runs = len(logs)
                success_count = sum(1 for _, status, _ in logs if status == "OK")
                fail_count = sum(1 for _, status, _ in logs if status == "FAIL")
                pending_count = sum(1 for _, status, _ in logs if status == "PENDING")
                
                stats_panel = Panel(
                    f"Total de execuções: {total_runs} | "
                    f"Sucessos: [green]{success_count}[/green] | "
                    f"Falhas: [red]{fail_count}[/red] | "
                    f"Pendentes: [yellow]{pending_count}[/yellow]",
                    title="[bold]Estatísticas[/bold]",
                    border_style="blue"
                )
                
                self.console.print(stats_panel)
                
        except sqlite3.Error as e:
            self.console.print(f"[red]✗[/red] Erro ao consultar histórico: {e}")
    
    def force_execution(self, automation_name: str):
        """Executa uma automação forçadamente (mock)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verificar se a automação existe
                cursor.execute(
                    "SELECT name FROM automations WHERE name = ?", 
                    (automation_name,)
                )
                if not cursor.fetchone():
                    self.console.print(
                        f"[red]✗[/red] Automação '{automation_name}' não encontrada"
                    )
                    return
                
                # Simular execução (mock)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Simular diferentes cenários baseados no nome da automação
                if "C1" in automation_name:
                    status = "OK"
                    message = "Processando dados... Inseridos 145 registros. Finalizado sem erros"
                elif "C2" in automation_name:
                    status = "OK"
                    message = "Sincronização concluída. 67 produtos atualizados"
                elif "C3" in automation_name:
                    status = "PENDING"
                    message = "Processamento iniciado... Aguardando recursos"
                else:
                    status = "OK"
                    message = f"Execução forçada concluída com sucesso em {timestamp}"
                
                # Inserir log
                cursor.execute("""
                    INSERT INTO logs (automation, timestamp, status, message)
                    VALUES (?, ?, ?, ?)
                """, (automation_name, timestamp, status, message))
                
                # Atualizar status da automação
                cursor.execute("""
                    UPDATE automations 
                    SET last_status = ?, last_run = ?
                    WHERE name = ?
                """, (status, timestamp, automation_name))
                
                conn.commit()
                
                status_color = self.get_status_color(status)
                self.console.print(f"[green]✓[/green] Automação '{automation_name}' executada com status: [{status_color}]{status}[/{status_color}]")
                self.console.print(f"[white]Mensagem: {message}[/white]")
                
        except sqlite3.Error as e:
            self.console.print(f"[red]✗[/red] Erro ao executar automação: {e}")
    
    def tail_logs(self, automation_name: str, lines: int = 10):
        """Exibe os logs mais recentes de uma automação (como tail -f)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verificar se a automação existe
                cursor.execute(
                    "SELECT name FROM automations WHERE name = ?", 
                    (automation_name,)
                )
                if not cursor.fetchone():
                    self.console.print(
                        f"[red]✗[/red] Automação '{automation_name}' não encontrada"
                    )
                    return
                
                # Buscar logs mais recentes
                cursor.execute("""
                    SELECT timestamp, status, message
                    FROM logs
                    WHERE automation = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (automation_name, lines))
                
                logs = cursor.fetchall()
                
                if not logs:
                    self.console.print(f"[yellow]Nenhum log encontrado para '{automation_name}'[/yellow]")
                    return
                
                # Exibir logs em formato de texto
                self.console.print(f"[bold blue]Últimos {len(logs)} logs de '{automation_name}':[/bold blue]\n")
                
                for timestamp, status, message in reversed(logs):  # Reverter para ordem cronológica
                    status_color = self.get_status_color(status)
                    status_text = f"[{status_color}]{status}[/{status_color}]"
                    
                    self.console.print(f"[cyan]{timestamp}[/cyan] [{status_text}] {message}")
                
                self.console.print(f"\n[yellow]Use 'status {automation_name}' para histórico completo[/yellow]")
                
        except sqlite3.Error as e:
            self.console.print(f"[red]✗[/red] Erro ao consultar logs: {e}")
    
    def run(self):
        """Executa o CLI principal."""
        parser = argparse.ArgumentParser(
            description="CLI para monitorar e controlar automações crontab",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Exemplos de uso:
  automations.py status                    # Status de todas as automações
  automations.py status C1                 # Histórico da automação C1
  automations.py status C1 2025-01-27     # Histórico filtrado por data
  automations.py force C1                  # Executa automação C1
  automations.py tail C1                   # Últimos logs da automação C1
  automations.py tail C1 20                # Últimos 20 logs da automação C1
  automations.py test-log                  # Testa parsing de log real
  automations.py add-log C1                # Adiciona log real da C1 ao banco
            """
        )
        
        parser.add_argument(
            "command",
            choices=["status", "force", "tail", "test-log", "add-log"],
            help="Comando a executar"
        )
        
        parser.add_argument(
            "automation_name",
            nargs="?",
            help="Nome da automação (ex: C1, C2, etc.)"
        )
        
        parser.add_argument(
            "date_or_lines",
            nargs="?",
            help="Data (YYYY-MM-DD) para status ou número de linhas para tail"
        )
        
        args = parser.parse_args()
        
        # Validações
        if args.command in ["force", "tail"] and not args.automation_name:
            self.console.print("[red]✗[/red] Nome da automação é obrigatório para este comando")
            parser.print_help()
            return
        
        # Executar comando
        if args.command == "status":
            if not args.automation_name:
                self.show_all_status()
            else:
                self.show_automation_history(args.automation_name, args.date_or_lines)
        
        elif args.command == "force":
            self.force_execution(args.automation_name)
        
        elif args.command == "tail":
            lines = int(args.date_or_lines) if args.date_or_lines and args.date_or_lines.isdigit() else 10
            self.tail_logs(args.automation_name, lines)
        
        elif args.command == "test-log":
            # Testar com o log real da C1
            test_log = """=== Execução: Wed Aug 20 09:23:03 AM -03 2025 ===
lsfnjdn5/3/2024 9:28:21 AM
lsfnjdnData Source=dadosjcdecor.database.windows.net;User ID=jcdados;Password=BandodeDados2024$;Initial Catalog=DadosJC>8/20/2025 9:23:06 AM - Conexão com o banco de dados estabelecida.
8/20/2025 9:23:06 AM - Obtendo pedidos da API...
IdCliente: 37997466
DataCadCliente: 8/18/2025 2:13:21 PM
DataModCliente: 8/18/2025 5:40:10 PM
Inserindo nova linha na tabela CONTROL...
Conexão aberta com sucesso.
Linhas afetadas: 1
Nova linha inserida na tabela CONTROL com sucesso.
8/20/2025 9:27:41 AM - Data da última atualização inserida na tabela de controle (sucesso)."""
            
            self.test_log_parsing(test_log)
        
        elif args.command == "add-log":
            if not args.automation_name:
                self.console.print("[red]✗[/red] Nome da automação é obrigatório para este comando")
                return
            
            # Usar o log de exemplo da C1
            test_log = """=== Execução: Wed Aug 20 09:23:03 AM -03 2025 ===
lsfnjdn5/3/2024 9:28:21 AM
lsfnjdnData Source=dadosjcdecor.database.windows.net;User ID=jcdados;Password=BandodeDados2024$;Initial Catalog=DadosJC>8/20/2025 9:23:06 AM - Conexão com o banco de dados estabelecida.
8/20/2025 9:23:06 AM - Obtendo pedidos da API...
IdCliente: 37997466
DataCadCliente: 8/18/2025 2:13:21 PM
DataModCliente: 8/18/2025 5:40:10 PM
Inserindo nova linha na tabela CONTROL...
Conexão aberta com sucesso.
Linhas afetadas: 1
Nova linha inserida na tabela CONTROL com sucesso.
8/20/2025 9:27:41 AM - Data da última atualização inserida na tabela de controle (sucesso)."""
            
            self.add_real_log(args.automation_name, test_log)


def main():
    """Função principal."""
    console = Console()
    
    try:
        cli = AutomationCLI()
        
        # Se não houver argumentos, mostrar dados mock e status
        if len(sys.argv) == 1:
            console.print("[bold blue]🚀 CLI de Automações JC[/bold blue]")
            console.print("[yellow]Inicializando com dados mock...[/yellow]")
            cli.seed_mock_data()
            console.print("\n[bold]Status atual das automações:[/bold]")
            cli.show_all_status()
            console.print("\n[yellow]Use 'python automations.py --help' para ver os comandos disponíveis[/yellow]")
        else:
            cli.run()
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Operação cancelada pelo usuário[/yellow]")
    except Exception as e:
        console.print(f"[red]✗[/red] Erro inesperado: {e}")


if __name__ == "__main__":
    main()
