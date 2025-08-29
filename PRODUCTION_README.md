# 🚀 CLI de Automações JCDECOR - Guia de Produção

## 📋 Visão Geral

Sistema de monitoramento e controle das **16 automações reais** da JCDECOR que executam scripts .NET via crontab no ambiente Linux de produção.

**⚠️ IMPORTANTE**: Este sistema monitora APENAS as 16 automações reais em produção. Não há automações fictícias ou de teste.

## 🎯 Automações em Produção

### Automações Diárias às 8h
- **C1** - Import de Vendas
- **CAT1** - Categorização
- **NC1** - Notas de Crédito
- **PG1** - Pagamentos
- **PR2** - Processamento de Pedidos 2

### Automação às 9h
- **V1** - Validação

### Automações de Hora em Hora (8h-17h)
- **CR1** - Controle de Receitas
- **NF1** - Notas Fiscais 1
- **NF2** - Notas Fiscais 2
- **P1** - Produtos 1
- **P2** - Produtos 2

### Automações de 1h30 em 1h30
- **EM1** - Estoque e Movimentação

### Automações de 2 em 2 Horas (8h-16h)
- **ODC1** - Ordens de Compra 1
- **ODC2** - Ordens de Compra 2
- **ORC1** - Ordens de Recebimento
- **PR1** - Processamento de Pedidos 1

## 🛠️ Instalação no Linux

### Pré-requisitos
- Ubuntu/Debian Linux
- Python 3.10+
- Usuário `jc-automation` criado
- Acesso ao diretório `/home/jc-automation/Downloads/REALTIME/`

### Instalação Automática
```bash
# 1. Baixar o projeto
cd /home/jc-automation
git clone <repositorio> automation-cli
cd automation-cli

# 2. Executar script de instalação
chmod +x install_linux.sh
./install_linux.sh
```

### Instalação Manual
```bash
# 1. Criar diretório
mkdir -p /home/jc-automation/automation-cli
cd /home/jc-automation/automation-cli

# 2. Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar permissões
chmod +x *.sh *.py
chown -R jc-automation:jc-automation .
```

## 📖 Uso em Produção

### Comandos Principais
```bash
# Status de todas as automações
python automations.py status

# Histórico de uma automação específica
python automations.py status CR1

# Histórico filtrado por data
python automations.py status CR1 2025-08-29

# Executar automação forçadamente
python automations.py force CR1

# Acompanhar logs recentes
python automations.py tail CR1 20

# Testar parsing de log
python automations.py test-log

# Adicionar log real ao banco
python automations.py add-log CR1
```

### Aliases Configurados
```bash
# Recarregar configurações
source ~/.bashrc

# Usar aliases
automation              # Abrir CLI
automation-status       # Ver status geral
automation-monitor      # Iniciar monitoramento
```

## 🔧 Configuração do Sistema

### Crontab
```bash
# Editar crontab do usuário jc-automation
crontab -e

# Adicionar linhas de monitoramento
*/5 * * * * /home/jc-automation/automation-cli/monitor.sh
0 2 * * * /home/jc-automation/automation-cli/backup.sh
0 3 * * * /home/jc-automation/automation-cli/cleanup.sh
```

### Systemd Service
```bash
# Copiar arquivo de serviço
sudo cp systemd/automation-cli.service /etc/systemd/system/

# Habilitar e iniciar serviço
sudo systemctl daemon-reload
sudo systemctl enable automation-cli
sudo systemctl start automation-cli

# Verificar status
sudo systemctl status automation-cli
```

## 📊 Monitoramento

### Monitoramento Contínuo
```bash
# Iniciar em background
nohup /home/jc-automation/automation-cli/monitor.sh > /dev/null 2>&1 &

# Verificar se está rodando
ps aux | grep monitor.sh

# Parar monitoramento
pkill -f monitor.sh
```

### Logs do Sistema
- **Logs de monitoramento**: `logs/monitor.log`
- **Status das automações**: `logs/{AUTOMACAO}_status.log`
- **Logs do CLI**: `logs/cli.log`

## 🗄️ Banco de Dados

### Estrutura
- **Arquivo**: `automation.db` (SQLite)
- **Localização**: `/home/jc-automation/automation-cli/`
- **Backup automático**: Diário às 2h da manhã
- **Retenção**: 30 dias

### Tabelas
- **`automations`**: Configuração das automações
- **`logs`**: Histórico de execuções

### Backup Manual
```bash
cd /home/jc-automation/automation-cli
source venv/bin/activate
python backup.py
```

## 🔍 Troubleshooting

### Problemas Comuns

#### Python não encontrado
```bash
# Verificar versão
python3 --version

# Instalar se necessário
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

#### Permissões negadas
```bash
# Verificar usuário
whoami

# Corrigir permissões
sudo chown -R jc-automation:jc-automation /home/jc-automation/automation-cli
chmod -R 755 /home/jc-automation/automation-cli
```

#### Ambiente virtual não ativado
```bash
# Ativar ambiente
source venv/bin/activate

# Verificar se está ativo
which python
```

### Logs de Erro
```bash
# Ver logs do sistema
tail -f logs/monitor.log

# Ver logs de uma automação específica
tail -f logs/CR1_status.log

# Ver logs do systemd
sudo journalctl -u automation-cli -f
```

## 🚀 Comandos Avançados

### Monitoramento em Tempo Real
```bash
# Acompanhar todas as automações
watch -n 5 'python automations.py status'

# Monitorar logs específicos
tail -f /home/jc-automation/Downloads/REALTIME/CR1/run.log
```

### Análise de Performance
```bash
# Ver estatísticas de execução
python automations.py stats

# Exportar dados para CSV
python automations.py export --format csv --output automations_report.csv
```

### Manutenção
```bash
# Limpeza de logs antigos
python automations.py cleanup --days 30

# Verificação de integridade
python automations.py verify

# Reparo do banco
python automations.py repair
```

## 📞 Suporte

### Contatos
- **Desenvolvedor**: Sistema de Automação JC
- **Email**: vitor@jcdecor.com.br
- **Ambiente**: Produção Linux

### Documentação
- **README Principal**: `README.md`
- **Configuração**: `production_config.py`
- **Crontab**: `example_crontab.txt`
- **Scripts**: `example_script_*.sh`

## 🔮 Próximos Passos

- [ ] Integração com sistema de notificações
- [ ] Dashboard web para monitoramento
- [ ] Alertas automáticos por email/SMS
- [ ] Relatórios de performance
- [ ] Integração com ferramentas de monitoramento (Zabbix, Nagios)

---

**Versão**: 1.0.0  
**Ambiente**: Produção Linux  
**Última Atualização**: Agosto 2025
