#!/bin/bash
# Script de instalação para o CLI de Automações JCDECOR no Linux

set -e

echo "🚀 Instalando CLI de Automações JCDECOR no Linux..."

# Verificar se está rodando como root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Não execute este script como root!"
    echo "Use: sudo -u jc-automation ./install_linux.sh"
    exit 1
fi

# Verificar se o usuário é jc-automation
if [ "$USER" != "jc-automation" ]; then
    echo "⚠️  Aviso: Este script deve ser executado pelo usuário 'jc-automation'"
    echo "Usuário atual: $USER"
    read -p "Continuar mesmo assim? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Diretório de instalação
INSTALL_DIR="/home/jc-automation/automation-cli"
BACKUP_DIR="/home/jc-automation/backups"

echo "📁 Criando diretórios..."

# Criar diretório de instalação
mkdir -p "$INSTALL_DIR"
mkdir -p "$BACKUP_DIR"

# Criar diretório para logs do sistema
mkdir -p "$INSTALL_DIR/logs"

echo "🐍 Verificando Python..."

# Verificar se Python 3.10+ está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado!"
    echo "Instale Python 3.10+ primeiro:"
    echo "sudo apt update && sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo "❌ Python 3.10+ é necessário!"
    echo "Versão atual: $PYTHON_VERSION"
    echo "Instale Python 3.10+ primeiro"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION encontrado"

echo "📦 Criando ambiente virtual..."

# Criar ambiente virtual
cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate

echo "📥 Instalando dependências..."

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt

echo "🔧 Configurando permissões..."

# Dar permissão de execução aos scripts
chmod +x "$INSTALL_DIR"/*.sh
chmod +x "$INSTALL_DIR"/*.py

echo "📋 Criando arquivo de configuração do sistema..."

# Criar arquivo de configuração do sistema
cat > "$INSTALL_DIR/systemd/automation-cli.service" << EOF
[Unit]
Description=Automation CLI Service
After=network.target

[Service]
Type=simple
User=jc-automation
Group=jc-automation
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/python automations.py monitor
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "📊 Criando script de monitoramento..."

# Criar script de monitoramento
cat > "$INSTALL_DIR/monitor.sh" << 'EOF'
#!/bin/bash
# Script de monitoramento contínuo das automações

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Ativar ambiente virtual
source venv/bin/activate

# Função para log
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a logs/monitor.log
}

# Função para verificar se uma automação está rodando
check_automation_status() {
    local automation_name="$1"
    local log_file="logs/${automation_name}_status.log"
    
    # Verificar se o processo está rodando
    if pgrep -f "run_${automation_name}.sh" > /dev/null; then
        echo "RUNNING" > "$log_file"
        log_message "✅ $automation_name está rodando"
    else
        echo "STOPPED" > "$log_file"
        log_message "❌ $automation_name parou"
    fi
}

# Loop principal de monitoramento
log_message "🚀 Iniciando monitoramento das automações..."

while true; do
    # Verificar status de cada automação (16 automações reais)
    for automation in C1 CAT1 CR1 EM1 NC1 NF1 NF2 ODC1 ODC2 ORC1 P1 P2 PG1 PR1 PR2 V1; do
        check_automation_status "$automation"
    done
    
    # Aguardar próximo ciclo
    sleep 60
done
EOF

chmod +x "$INSTALL_DIR/monitor.sh"

echo "📝 Criando arquivo de configuração do crontab..."

# Criar arquivo de configuração do crontab
cat > "$INSTALL_DIR/crontab_config.txt" << 'EOF'
# Configuração do crontab para automações JCDECOR
# Adicione estas linhas ao crontab do usuário jc-automation

# Monitoramento do CLI a cada 5 minutos
*/5 * * * * /home/jc-automation/automation-cli/monitor.sh

# Backup diário do banco às 2h da manhã
0 2 * * * /home/jc-automation/automation-cli/backup.sh

# Limpeza de logs antigos às 3h da manhã
0 3 * * * /home/jc-automation/automation-cli/cleanup.sh
EOF

echo "🔐 Configurando permissões de arquivo..."

# Configurar permissões
chown -R jc-automation:jc-automation "$INSTALL_DIR"
chmod -R 755 "$INSTALL_DIR"

echo "📋 Criando aliases..."

# Criar aliases no .bashrc
if ! grep -q "automation-cli" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# Aliases para CLI de Automações JCDECOR" >> ~/.bashrc
    echo "alias automation='cd $INSTALL_DIR && source venv/bin/activate && python automations.py'" >> ~/.bashrc
    echo "alias automation-status='cd $INSTALL_DIR && source venv/bin/activate && python automations.py status'" >> ~/.bashrc
    echo "alias automation-monitor='cd $INSTALL_DIR && source venv/bin/activate && python automations.py monitor'" >> ~/.bashrc
fi

echo "✅ Instalação concluída com sucesso!"
echo ""
echo "📖 Para usar o CLI:"
echo "1. Recarregue o terminal: source ~/.bashrc"
echo "2. Use o comando: automation"
echo "3. Ou navegue para: cd $INSTALL_DIR"
echo "4. Ative o ambiente: source venv/bin/activate"
echo "5. Execute: python automations.py"
echo ""
echo "🔧 Para configurar o crontab:"
echo "crontab -e"
echo "Adicione as linhas do arquivo crontab_config.txt"
echo ""
echo "📊 Para monitoramento contínuo:"
echo "nohup $INSTALL_DIR/monitor.sh > /dev/null 2>&1 &"
echo ""
echo "🚀 CLI de Automações JCDECOR instalado e configurado!"
