# Changelog

## v2.0.9 - 2026-04-23

### Fixed
- Corrigido erro ao remover item de favoritos com fallback seguro para payload JSON ou formulário
- Corrigida exclusão de peça que falhava por integridade referencial em tabelas relacionadas
- Melhorado o tratamento de rollback na exclusão para evitar erro interno e manter feedback consistente

## v2.0.8 - 2026-04-20

### ✨ Novidades
- Opção de informar **Modelo**, **Ano** e **Motor** do veículo ao enviar o carrinho via WhatsApp
- Dados do veículo são exibidos como cabeçalho antes da lista de peças na mensagem

## v2.0.7 - 2026-04-15

### 🛠️ Correções e Melhorias
- Correções de bugs reportados pelos usuários
- Melhorias de estabilidade e performance geral
- Otimizações no carregamento de dados
- Ajustes de interface e experiência do usuário

## v2.0.4 - 2026-04-09

### ✨ Navegação de Imagens
- Navegação por setas no modal de imagens com controles de teclado
- Contador visual "X de Y" para múltiplas imagens
- Auto-detecção e sincronização entre thumbnail e modal
- Reset de zoom automático ao trocar imagem

### 🔍 Busca Aprimorada  
- Melhorias na busca FTS com normalização avançada de caracteres
- Otimização nas conversões SQL com CAST apropriados
- Correções na interface de resultados com melhor responsividade
- Ajustes na performance de queries complexas

### 🎨 Melhorias UX
- Interface de busca responsiva com melhor layout
- Feedback visual aprimorado nos resultados
- Otimizações de CSS para diferentes tamanhos de tela
- Refinamentos na navegação entre páginas

### 🛠️ Manutenção
- Refatoração do código de busca FTS
- Limpeza e otimização de queries SQL
- Melhoria no tratamento de erros de busca
- Atualizações no instalador e build system

## v2.0.2 - 2026-03-28

- Correções de bugs menores
- Melhorias na estabilidade do sistema
- Otimizações de performance
- Atualização de dependências

## v2.0.0 - 2026-02-11

- Lançamento principal 2.0.0
- Ajustes de compatibilidade e correções de bugs
- Refatorações internas e otimizações de performance
- Atualização de dependências críticas
- Atualizado workflow de build e arquivos de versão

Notas: esta versão prepara o projeto para publicação no GitHub como v2.0.0.
