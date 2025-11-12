# 🚀 NOVIDADE: Versão Desktop Nativa

## ✨ O que foi adicionado?

Agora o Catálogo de Peças pode rodar como **aplicativo Windows nativo** — sem navegador visível!

## 📋 Resumo Rápido

### Antes (v1.8.0 e anteriores)
```
Usuário clica → CatalogoDePecas.exe → Abre Chrome/Edge
```

### Agora (v1.8.0+)
```
Usuário clica → CatalogoDePecas.exe → Janela nativa do Windows ✨
```

## 🎯 Como Usar

### Opção 1: Testar agora (sem build)
```powershell
# Instalar dependência
pip install pywebview

# Executar versão desktop
python run_gui.py
```

### Opção 2: Gerar executável desktop
```powershell
# Build da versão GUI
.\build_gui.bat

# Executável gerado em:
dist\CatalogoDePecas.exe
```

## 🆚 Qual versão usar?

| Situação | Use |
|----------|-----|
| **Desenvolvimento/Debug** | `python run.py run` (navegador) |
| **Distribuição para usuários** | `.\build_gui.bat` (desktop) |
| **Acesso na rede local** | `python run.py run --host 0.0.0.0` |
| **App instalado no Windows** | `.\build_gui.bat` (desktop) |

## 📦 Arquivos Criados

- ✅ `run_gui.py` — Launcher com janela nativa (pywebview)
- ✅ `build_gui.bat` — Script de build para versão desktop
- ✅ `GUIA_VERSAO_DESKTOP.md` — Documentação completa
- ✅ `requirements.txt` — Atualizado com `pywebview`

## ⚡ Vantagens da Versão Desktop

1. ✅ **Parece app nativo** — com ícone próprio na taskbar
2. ✅ **Sem navegador** — usuário não vê Chrome/Edge aberto
3. ✅ **Mais profissional** — melhor experiência para usuários finais
4. ✅ **Mais seguro** — servidor escuta apenas em localhost
5. ✅ **Mesmas funcionalidades** — zero mudanças no código Flask
6. ✅ **Compatível com updates** — sistema de atualização funciona igual

## 🔧 Compatibilidade

- ✅ **Windows 10/11** — funciona perfeitamente
- ✅ **PyInstaller** — compatível com build existente
- ✅ **Upload/Download** — tudo funciona nativamente
- ✅ **Inno Setup** — pode criar instalador normalmente

## 📚 Documentação Completa

Ver `GUIA_VERSAO_DESKTOP.md` para:
- Personalização da janela
- Troubleshooting
- Configurações avançadas
- Comparação detalhada browser vs desktop

## 🎨 Próximos Passos (Opcional)

Futuras melhorias possíveis:
- [ ] Splash screen durante inicialização
- [ ] Menu de contexto nativo (botão direito)
- [ ] Notificações do sistema Windows
- [ ] Atalhos de teclado customizados

## ⚠️ Importante

- **Ambos os modos coexistem**: `run.py` e `run_gui.py` funcionam simultaneamente
- **Zero mudanças no Flask**: todo o código backend continua igual
- **Código compartilhado**: mesma lógica de restauração/atualização

---

**Implementado em**: 8 de novembro de 2025  
**Versão**: 1.8.0+  
**Biblioteca**: pywebview 6.1
