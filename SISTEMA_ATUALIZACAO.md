# Sistema de Atualização Automática - Catálogo de Peças

## Resumo do Funcionamento

O sistema de atualização automática permite que o aplicativo verifique, baixe e instale atualizações automaticamente, com aprovação do administrador.

## 🔄 Fluxo Completo de Atualização

### 1. **Verificação Automática**
- **Frequência**: A cada 6 horas automaticamente + 5 segundos após iniciar
- **Arquivo verificado**: `update_config.json` no GitHub
- **Comparação**: Usa a biblioteca `packaging` para comparar versões de forma robusta

### 2. **Notificação Visual**
- **Banner animado** aparece no topo para administradores
- **Informações mostradas**:
  - Nova versão disponível
  - Notas de lançamento
  - Tamanho do download (se disponível)
  - Botões para baixar/instalar ou dispensar

### 3. **Download e Preparação**
- **Quando o admin clica em "Baixar e Instalar"**:
  - Download do arquivo do `download_url`
  - Salvo como `update_package.zip` na pasta de dados
  - Criação do arquivo gatilho `RESTART_FOR_UPDATE`
  - Exibição da tela de reinicialização

### 4. **Instalação na Reinicialização**
- **Ao iniciar novamente**, o `run.py`:
  - Verifica se existe o gatilho `RESTART_FOR_UPDATE`
  - Extrai o `update_package.zip` sobre os arquivos atuais
  - Remove arquivos temporários
  - Reinicia automaticamente

## 📁 Arquivos Envolvidos

### Backend
- **`app.py`**: Funções `check_for_updates()` e `schedule_periodic_update_check()`
- **`routes.py`**: Rota `/admin/atualizar_aplicacao` para download
- **`run.py`**: Lógica de instalação na inicialização

### Frontend
- **`templates/base.html`**: Banner de notificação de atualização
- **`static/style.css`**: Estilos do banner animado
- **`templates/reiniciando.html`**: Tela durante a atualização

### Configuração
- **`update_config.json`** (GitHub): Informações da versão mais recente
- **`update_info.json`** (local): Cache das informações de atualização

## ⚙️ Configuração no GitHub

### Estrutura do `update_config.json`:
```json
{
  "latest_version": "1.5.0",
  "download_url": "https://github.com/user/repo/releases/download/v1.5.0/instalador.exe",
  "release_notes": "- Nova funcionalidade X\n- Correção do bug Y",
  "size_mb": "25"
}
```

### Para Lançar uma Nova Versão:

1. **Atualizar versão no código**:
   ```python
   # Em app.py
   VERSION = "1.5.0"
   ```

2. **Fazer build e upload**:
   ```bash
   # Criar executável
   ./build.bat
   
   # Fazer upload para GitHub Releases
   # (manual ou via script create_release.ps1)
   ```

3. **Atualizar configuração**:
   ```bash
   # Editar update_config.json no GitHub
   git add update_config.json
   git commit -m "Atualização para versão 1.5.0"
   git push
   ```

## 🚀 Melhorias Implementadas

### ✅ Verificação Periódica
- Verifica atualizações a cada 6 horas automaticamente
- Não sobrecarrega o servidor do GitHub

### ✅ Persistência de Informações
- Salva informações de atualização em arquivo JSON
- Mantém notificação entre reinicializações

### ✅ Interface Melhorada
- Banner visualmente atrativo com animações
- Informações detalhadas sobre a atualização
- Botão para dispensar a notificação

### ✅ Tratamento de Erros
- Timeout configurável para downloads
- Fallbacks para problemas de rede
- Logs detalhados para debug

## 🎯 Possíveis Melhorias Futuras

### 📥 Download em Background
```python
# Baixar automaticamente sem intervenção do usuário
def auto_download_update():
    if update_available and user_preferences.auto_download:
        download_update_package()
        show_install_notification()
```

### 📊 Estatísticas de Uso
```python
# Enviar dados anônimos de uso ao verificar atualizações
def send_usage_stats():
    stats = {
        "version": VERSION,
        "os": platform.system(),
        "install_date": get_install_date()
    }
    requests.post(STATS_URL, json=stats)
```

### 🔒 Verificação de Integridade
```python
# Verificar hash SHA256 do download
def verify_download_integrity(file_path, expected_hash):
    import hashlib
    with open(file_path, 'rb') as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    return file_hash == expected_hash
```

### 📅 Atualizações Agendadas
```python
# Permitir agendar instalação para horário específico
def schedule_update_install(datetime_target):
    delay = (datetime_target - datetime.now()).total_seconds()
    threading.Timer(delay, install_update).start()
```

## 🔧 Troubleshooting

### Problema: Atualização não detectada
- **Causa**: Erro de rede ou formato incorreto do JSON
- **Solução**: Verificar logs e conectividade

### Problema: Download falha
- **Causa**: URL inválida ou arquivo muito grande
- **Solução**: Verificar `download_url` e timeout

### Problema: Instalação não funciona
- **Causa**: Permissões insuficientes ou arquivo corrompido
- **Solução**: Executar como administrador e verificar integridade

## 📝 Logs e Debug

### Verificar verificação de atualizações:
```bash
# Logs aparecem no console ao iniciar o servidor
"Verificando atualizações..."
"Nova versão encontrada: X.X.X" ou "Nenhuma atualização encontrada"
```

### Verificar arquivos de estado:
- `{APP_DATA_PATH}/update_info.json` - Informações da última verificação
- `{APP_DATA_PATH}/RESTART_FOR_UPDATE` - Gatilho de instalação pendente
- `{APP_DATA_PATH}/update_package.zip` - Pacote baixado aguardando instalação