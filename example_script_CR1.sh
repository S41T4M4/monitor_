#!/bin/bash
# Script de execução para automação CR1 - Controle de Receitas
# Executa de hora em hora das 8h às 17h

DOTNET_PATH=$(which dotnet)
PROJECT_PATH="/home/jc-automation/Downloads/REALTIME/CR1"
LOG_FILE="/home/jc-automation/Downloads/REALTIME/CR1/run.log"
ERROR_EMAIL="vitor@jcdecor.com.br"

# Função para log
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Início da execução
log_message "=== Execução iniciada ==="

# Verificar se o dotnet está disponível
if [ ! -f "$DOTNET_PATH" ]; then
    log_message "ERRO: dotnet não encontrado"
    echo "Erro: dotnet não encontrado em $(date)" | mail -s "CR1 Automation Error" "$ERROR_EMAIL"
    exit 1
fi

# Verificar se o projeto existe
if [ ! -d "$PROJECT_PATH" ]; then
    log_message "ERRO: Diretório do projeto não encontrado: $PROJECT_PATH"
    echo "Erro: Diretório do projeto não encontrado em $(date)" | mail -s "CR1 Automation Error" "$ERROR_EMAIL"
    exit 1
fi

# Executar a automação .NET
log_message "Iniciando controle de receitas..."
cd "$PROJECT_PATH"

# Capturar saída e código de retorno
if $DOTNET_PATH run --project "$PROJECT_PATH" >> "$LOG_FILE" 2>&1; then
    log_message "Controle de receitas concluído com sucesso"
    log_message "=== Execução finalizada ==="
    exit 0
else
    EXIT_CODE=$?
    log_message "ERRO: Falha na execução (código: $EXIT_CODE)"
    echo "Erro na automação CR1 em $(date) - Código: $EXIT_CODE" | mail -s "CR1 Automation Error" "$ERROR_EMAIL"
    log_message "=== Execução finalizada com erro ==="
    exit $EXIT_CODE
fi
