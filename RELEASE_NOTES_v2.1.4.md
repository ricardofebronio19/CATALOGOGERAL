# Release Notes - Versao 2.1.4

**Data**: 03 de junho de 2026  
**Versao**: 2.1.4  
**Status**: Pronto para producao

---

## Resumo

A versao 2.1.4 foca em melhorias visuais na pagina de detalhes e em refinamentos do filtro de produtos similares para facilitar a leitura e a busca de aplicacoes.

---

## Novidades

1. Melhor divisao visual da tabela de aplicacoes
- Borda externa e cabecalho mais destacados
- Separacao mais clara entre grupos de fabricante e linhas de aplicacao
- Melhor contraste em linhas alternadas

2. Melhorias visuais na tabela de produtos similares
- Divisores mais visiveis entre colunas principais
- Separacao interna das listas verticais de veiculo, ano e motor
- Estilo mais consistente para conteudo expandido

3. Refinamento do filtro de similares
- Preservacao das colunas originais para restauracao segura
- Melhor correspondencia por veiculo ao aplicar filtro
- Renderizacao direcionada para aplicacao unica quando houver match

---

## Arquivos de release atualizados

- CHANGELOG.md
- version.json
- update_config.json
- instalador.iss
- build.bat
- build_gui.bat
- prepare_release.ps1
- templates/detalhe_peca.html
- RELEASE_NOTES_v2.1.4.md

---

## Instalacao

- Arquivo esperado no release: instalador_CatalogoDePecas_v2.1.4.exe
- Compatibilidade: Windows 10/11

---

## Publicacao

1. Criar branch release/2.1.4
2. Commitar arquivos da release
3. Enviar branch para origin
4. Criar tag v2.1.4
5. Publicar release no GitHub anexando o instalador
