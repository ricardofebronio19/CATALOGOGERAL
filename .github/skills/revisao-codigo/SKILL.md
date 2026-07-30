---
name: revisao-codigo
description: Checklist reutilizavel para revisar alteracoes no repositorio com foco em bugs, riscos, regressao funcional e cobertura de testes.
---

# Revisao de Codigo

## Proposito

Use este skill quando precisar revisar uma mudanca, PR ou diff para identificar problemas reais antes de aprovar ou mesclar. O objetivo e priorizar defeitos, riscos de regressao, lacunas de teste e inconsistencias com o padrao do projeto.

## Quando usar

- Ao revisar um PR, patch ou conjunto de alteracoes locais.
- Quando o usuario pede uma code review, analise de risco ou validacao de uma mudanca.
- Quando for necessario responder com achados priorizados e acao recomendada.

## Quando nao usar

- Para implementar funcionalidade do zero.
- Para depurar runtime, salvo se a revisao apontar o ponto exato do defeito.
- Para resumo superficial sem avaliar comportamento, impacto e testes.

## Fluxo

1. Identifique a mudanca principal e o comportamento esperado.
2. Leia o codigo mais proximo do ponto de decisao, nao a superficie inteira.
3. Verifique se a mudanca altera fluxo, contratos, validacoes, persistencia, seguranca ou compatibilidade.
4. Procure efeitos colaterais em chamadores, rotas, templates, testes e migracoes relacionadas.
5. Classifique cada problema por severidade e descreva o impacto concreto.
6. Confirme se existem testes suficientes para o caminho alterado.
7. Se houver evidencias suficientes, aponte a causa raiz e a menor correcao possivel.

## Pontos de decisao

- Se a mudanca mexe em contrato publico, verifique compatibilidade com chamadas existentes.
- Se altera leitura ou escrita de dados, verifique validacao, normalizacao e integridade.
- Se toca interface, verifique estados vazios, erro, loading e acessibilidade basica.
- Se altera regras de negocio, compare com o fluxo anterior e com dados reais do projeto.
- Se nao houver evidencias suficientes, declare a incerteza e solicite o artefato minimo para confirmar.

## Critérios de qualidade

- Encontrar problemas reais, nao apenas estilo.
- Priorizar por severidade e probabilidade de impacto.
- Referenciar arquivos e linhas quando possivel.
- Explicar por que o comportamento e incorreto ou arriscado.
- Sugerir validacao objetiva, como teste, lint ou reproduzir o fluxo afetado.

## Formato da resposta

- Comece pelos achados mais graves.
- Inclua arquivo e linha para cada achado relevante.
- Se nao houver problemas, diga isso explicitamente e cite riscos residuais ou lacunas de teste.
- Termine com uma validacao breve do que foi checado.

## Validacao minima

- Rode o teste mais perto da mudanca, se existir.
- Se nao houver teste, use uma validacao estreita que exercite o caminho alterado.
- Se a revisao depender de evidencias faltando, documente exatamente o que falta.
