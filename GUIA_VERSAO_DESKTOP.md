# Guia: Versão Desktop (GUI Nativa)

## 🎯 O que mudou?

A aplicação agora pode rodar de **duas formas**:

### 1️⃣ Modo Original (Navegador)
```powershell
python run.py run
```
- Abre no navegador padrão (Chrome, Edge, Firefox)
- Ideal para desenvolvimento
- Pode ser acessada na rede (0.0.0.0)

### 2️⃣ Modo Desktop (Janela Nativa) ⭐ NOVO
```powershell
python run_gui.py
```
- Abre como aplicativo Windows nativo
- Sem navegador visível
- Parece um programa instalado
- Mesmas funcionalidades

## 🚀 Como usar a versão Desktop

### Desenvolvimento (com Python instalado)

1. **Instale a dependência**:
```powershell
pip install pywebview
```

2. **Execute**:
```powershell
python run_gui.py
```

### Produção (executável)

1. **Gere o executável**:
```powershell
.\build_gui.bat
```

2. **Instale/Distribua**:
- O arquivo gerado está em `dist\CatalogoDePecas.exe`
- Pode ser executado diretamente (duplo clique)
- Não precisa de navegador

## 🔧 Configurações Avançadas

### Personalizar a janela

Edite `run_gui.py`, função `criar_janela_principal()`:

```python
window_config = {
    'title': 'Catálogo de Peças',  # Título da janela
    'width': 1280,                 # Largura inicial
    'height': 800,                 # Altura inicial
    'resizable': True,             # Permitir redimensionar
    'fullscreen': False,           # Iniciar em tela cheia
    'min_size': (800, 600),        # Tamanho mínimo
    'background_color': '#FFFFFF', # Cor de fundo durante carregamento
}
```

### Debug durante desenvolvimento

Em `run_gui.py`, linha ~115:
```python
webview.start(
    debug=True,  # ← Mude para True para ver logs detalhados
)
```

### Usar porta diferente

Em `run_gui.py`, função `main()`:
```python
HOST = "127.0.0.1"
PORT = 8000  # ← Mude aqui
```

## 🆚 Comparação: Browser vs Desktop

| Característica | run.py (Browser) | run_gui.py (Desktop) |
|---|---|---|
| **Aparência** | Aba do navegador | Janela nativa |
| **Acesso na rede** | ✅ Sim (0.0.0.0) | ❌ Não (127.0.0.1) |
| **Ícone na taskbar** | Ícone do navegador | ✅ Ícone do app |
| **Funcionalidades** | ✅ Todas | ✅ Todas |
| **Tamanho executável** | ~35 MB | ~40 MB |
| **Melhor para** | Desenvolvimento | Produção/Usuários |

## 📦 Build com Inno Setup (Instalador)

Para criar instalador completo:

```powershell
set CREATE_INSTALLER=1
set INCLUDE_DB=1
.\build_gui.bat
```

Depois crie um `instalador_gui.iss` (baseado no existente) que aponte para `dist\CatalogoDePecas.exe`.

## ⚠️ Troubleshooting

### Janela em branco
- Verifique se o servidor Flask iniciou (olhe os logs)
- Aumente o tempo de espera em `criar_janela_principal()` (linha ~43)

### Upload de arquivos não funciona
- No modo desktop, uploads funcionam normalmente
- Certifique-se que `APP_DATA_PATH/uploads` existe

### Atualização automática
- Funciona identicamente ao modo browser
- Ao reiniciar, relança `run_gui.py` (não `run.py`)

## 🎨 Próximos Passos (Opcional)

### 1. Menu de contexto nativo
Adicione menu customizado ao clicar com botão direito:

```python
# Em run_gui.py
class API:
    def mostrar_sobre(self):
        return {"versao": "1.8.0", "autor": "ricardofebronio19"}

window = webview.create_window(
    ...,
    js_api=API()
)
```

### 2. Splash screen
Mostre logo enquanto carrega:

```python
# Crie splash_window antes da janela principal
splash = webview.create_window(
    'Carregando...', 
    html='<html><body><h1>Catálogo de Peças</h1><p>Iniciando...</p></body></html>',
    width=400, 
    height=300,
    frameless=True
)

# Após servidor pronto:
splash.destroy()
window = criar_janela_principal(...)
```

### 3. Notificações do sistema
Use `plyer` ou `win10toast` para alertas nativos.

## 📚 Documentação pywebview

- GitHub: https://github.com/r0x0r/pywebview
- Docs: https://pywebview.flowrl.com/

## 💡 Dicas

- ✅ **Mantenha ambos os modos**: `run.py` para dev, `run_gui.py` para produção
- ✅ **Teste uploads/downloads**: funcionam nativamente no pywebview
- ✅ **Performance**: janela nativa é mais leve que navegador completo
- ✅ **Distribuição**: usuários preferem `.exe` que abre diretamente

---

**Versão**: 1.8.0  
**Compatibilidade**: Windows 10/11, Python 3.8+
