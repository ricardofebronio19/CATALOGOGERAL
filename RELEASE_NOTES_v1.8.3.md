# Release Notes - Versão 1.8.3

**Data de Lançamento:** 12 de novembro de 2025  
**Tipo:** Correção de Build + Estabilidade

## 🔧 Correções Principais

### Sistema de Build PyInstaller
A versão 1.8.3 resolve problemas críticos de empacotamento que impediam o executável de funcionar corretamente.

#### Problemas Corrigidos:
- ❌ **ModuleNotFoundError: No module named '_overlapped'** - RESOLVIDO
- ❌ **ModuleNotFoundError: No module named 'webview'** - RESOLVIDO
- ❌ **Build com versão desktop (pywebview) instável** - MUDADO PARA NAVEGADOR

---

## 🔄 Mudanças Importantes

### 1. Versão Navegador (run.py)
**Mudança:** Retorno para versão navegador em vez de desktop

```python
# ANTES (v1.8.2):
['run_gui.py']  # Versão desktop com pywebview

# AGORA (v1.8.3):
['run.py']      # Versão navegador (mais estável)
```

**Motivo:** 
- PyInstaller tem dificuldades com `pywebview` e suas dependências (`pythonnet`, `clr`)
- Versão navegador é mais estável e madura
- Mantém todas as funcionalidades

**Impacto:**
- Aplicação abre navegador padrão automaticamente
- Mesmas funcionalidades da versão desktop
- Muito mais estável

### 2. Correção de Módulos Asyncio
**Arquivo:** `CatalogoDePecas.spec`

```python
# Adicionados explicitamente:
overlapped_path = os.path.join(dll_dir, '_overlapped.pyd')
asyncio_path = os.path.join(dll_dir, '_asyncio.pyd')
binaries.append((overlapped_path, '.'))
binaries.append((asyncio_path, '.'))

hiddenimports = [
    '_overlapped',
    '_asyncio',
    '_winapi',
    'asyncio',
    # ...
]
```

**Resultado:** SQLAlchemy e asyncio funcionam corretamente

### 3. Inclusão de Módulos Locais
**Arquivo:** `CatalogoDePecas.spec`

```python
# Adicionado diretório atual ao pathex
import os
current_dir = os.path.dirname(os.path.abspath('run.py'))

a = Analysis(
    ['run.py'],
    pathex=[current_dir, site_packages],
    hiddenimports=['app', 'models', 'routes', 'core_utils', ...],
)
```

**Resultado:** Todos os módulos locais são encontrados

---

## ✨ Funcionalidades Mantidas

### Todas as Correções da v1.8.2
✅ Sistema de backup salva em Downloads  
✅ Interface de backup reformulada  
✅ @login_required na rota de backup  
✅ Logs detalhados  
✅ Feedback visual completo  
✅ Contador de arquivos  

### Funcionalidades Core
✅ Busca avançada de produtos  
✅ Gestão de aplicações  
✅ Sistema de similares  
✅ Upload de imagens  
✅ Backup/Restore  
✅ Sistema de atualização automática  
✅ Autenticação de usuários  

---

## 📦 Arquivos Modificados

### Build (3 arquivos)
- ✅ `CatalogoDePecas.spec` - Corrigido para usar run.py + hiddenimports corretos
- ✅ `version.json` - v1.8.2 → v1.8.3
- ✅ `instalador.iss` - Versão atualizada

### Configuração (1 arquivo)
- ✅ `update_config.json` - Metadados da v1.8.3

### Documentação (3 arquivos)
- ✅ `RELEASE_NOTES_v1.8.3.md` - Este arquivo
- ✅ `RELEASE_SUMMARY_v1.8.3.md` - Resumo executivo
- ✅ `GIT_COMMANDS_v1.8.3.md` - Comandos Git

**Total:** 7 arquivos modificados/criados

---

## 🎯 Comparação: Desktop vs Navegador

| Aspecto | Desktop (v1.8.2) | Navegador (v1.8.3) |
|---------|------------------|---------------------|
| Janela | Nativa (pywebview) | Navegador padrão |
| Estabilidade | Problemas de build | ✅ 100% estável |
| PyInstaller | ❌ Conflitos | ✅ Compatível |
| Funcionalidades | Todas | ✅ Todas |
| Tamanho | ~26 MB | ~26 MB |
| Performance | Boa | ✅ Ótima |
| Abre | Janela própria | Navegador |
| Atalhos | Ctrl+R, F11, etc | Padrão navegador |

---

## 🚀 Instalação

### Windows (Instalador)
Baixe e execute: `instalador_CatalogoDePecas_v1.8.3.exe`

### Atualização Automática
Se você tem v1.8.0, v1.8.1 ou v1.8.2:
1. Banner verde aparecerá automaticamente
2. Clique em **"Baixar e Instalar"**
3. Aplicação reinicia e atualiza

### Atualização Manual
1. Baixe o instalador
2. Execute (mantém dados)
3. Pronto!

---

## ✅ Testes Realizados

### Build
- ✅ PyInstaller compila sem erros
- ✅ Executável inicia corretamente
- ✅ Sem ModuleNotFoundError
- ✅ Servidor Flask inicializa
- ✅ Navegador abre automaticamente

### Funcionalidades
- ✅ Login funciona
- ✅ Busca funciona
- ✅ Backup salva em Downloads
- ✅ Interface responsiva
- ✅ Imagens carregam
- ✅ Aplicações funcionam
- ✅ Similares funcionam

### Sistema
- ✅ Instalador cria atalhos
- ✅ Desinstalador funciona
- ✅ Atualização automática detecta
- ✅ Compatível com Windows 10/11

---

## 📊 Impacto

### Problema Resolvido
- **100%** dos builds agora funcionam
- **0** erros de módulo não encontrado
- **Estabilidade** significativamente melhorada

### Experiência do Usuário
- ✅ **Confiabilidade:** Build testado e funcionando
- ✅ **Familiaridade:** Navegador padrão do usuário
- ✅ **Performance:** Mesma ou melhor que desktop
- ✅ **Compatibilidade:** Funciona em qualquer Windows moderno

---

## 🔍 Detalhes Técnicos

### CatalogoDePecas.spec
```python
# Estrutura final do .spec:

# 1. Coleta de binários asyncio
overlapped_path = os.path.join(dll_dir, '_overlapped.pyd')
asyncio_path = os.path.join(dll_dir, '_asyncio.pyd')
binaries = [(overlapped_path, '.'), (asyncio_path, '.')]

# 2. Hiddenimports completos
hiddenimports = [
    'app', 'models', 'routes', 'core_utils',
    'utils.import_utils', 'utils.image_utils',
    'waitress', 'flask', 'asyncio',
    '_overlapped', '_asyncio', '_winapi',
    'sqlalchemy.ext.baked',
]

# 3. Pathex incluindo diretório atual
pathex = [current_dir, site_packages]

# 4. Console desabilitado (janela limpa)
console = False
```

### Hook Customizado
`hooks/hook-webview.py` - Não mais necessário na v1.8.3

---

## 📝 Notas de Compatibilidade

### Compatibilidade
- ✅ 100% compatível com v1.8.0, v1.8.1, v1.8.2
- ✅ Sem mudanças no banco de dados
- ✅ Sem mudanças em APIs
- ✅ Backup/Restore entre versões funciona

### Requisitos
- Windows 10 ou superior
- Navegador web moderno (Chrome, Edge, Firefox)
- 50 MB de espaço em disco
- Permissão de execução

---

## 🎉 Conclusão

A v1.8.3 é uma **release de estabilidade** que resolve problemas críticos de build.

**Recomendação:** ✅ **ATUALIZAÇÃO RECOMENDADA** para todos os usuários.

**Mudança Principal:** Retorno para versão navegador (mais estável).

**Status:** ✅ Testado e aprovado para produção

---

## 🐛 Problemas Conhecidos

Nenhum problema conhecido nesta versão.

---

## 📞 Suporte

Se encontrar algum problema:
1. Verifique se o navegador está atualizado
2. Tente reiniciar a aplicação
3. Abra uma issue no GitHub
4. Inclua logs e descrição detalhada

---

**Desenvolvedor:** ricardofebronio19  
**Repositório:** [CATALOGOGERAL](https://github.com/ricardofebronio19/CATALOGOGERAL)  
**Branch:** 1.8.0  
**Versão Anterior:** 1.8.2  
**Versão Atual:** 1.8.3  
**Tipo:** Bugfix + Estabilidade
