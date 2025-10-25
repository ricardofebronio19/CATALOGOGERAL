# RELEASE NOTES — v1.7.4

Data: 2025-10-25

Resumo das mudanças

- Corrigido comportamento do executável instalado para aceitar subcomandos (ex.: import-csv) quando launcher adicionava um token extra em argv.
- Robusto tratamento de encoding de I/O (stdout/stderr) para evitar crashes com caracteres Unicode/emoji no Windows.
- Adicionado carrossel na página inicial que exibe as imagens dos 4 últimos produtos adicionados (suporta imagens e vídeos).
- Melhorias visuais no carrossel: transição por fade, indicadores, legendas e prevenção de esticamento das imagens.
- Nova ação na interface: exportar resultados de busca para CSV (botão na página de resultados).
- Remoção persistente de sugestões automáticas (`SugestaoIgnorada`) com suporte a desfazer (undo) no frontend.
- Ajustes de layout: rodapé não-fixo, redução da altura do cabeçalho de montadora nas páginas de detalhe.
- Correções e melhorias diversas em importação, vinculação de imagens e scripts de build/packaging.

Notas de migração

- A migração adicionou o modelo `SugestaoIgnorada`. Em instalações existentes, execute a rotina de inicialização do banco para criar a nova tabela:

```python
from app import create_app, inicializar_banco
app = create_app()
with app.app_context():
    inicializar_banco(app, reset=False)
```

- Se você estiver produzindo o instalador, atualize a URL de download em `update_config.json` apontando para o release `v1.7.4` (já atualizado neste commit).

Obrigado!
