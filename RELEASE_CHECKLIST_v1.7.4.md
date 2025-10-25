# RELEASE CHECKLIST v1.7.4

Antes de criar o release no GitHub:

- [ ] Atualizar `version.json` (feito: v1.7.4)
- [ ] Atualizar `update_config.json` com `latest_version` e `download_url` (feito)
- [ ] Gerar artefatos Windows (PyInstaller onefile) e o instalador Inno (se aplicável)
- [ ] Validar que o instalador foi gerado em um caminho sem caracteres não-ASCII antes de rodar Inno
- [ ] Conferir `RELEASE_NOTES_v1.7.4.md` e incluir no corpo do release
- [ ] Tag e push: criar tag `v1.7.4` e dar push

Comandos sugeridos (PowerShell):

```powershell
# Tag e push
git add version.json update_config.json RELEASE_NOTES_v1.7.4.md RELEASE_CHECKLIST_v1.7.4.md
git commit -m "chore(release): prepare v1.7.4"
git tag -a v1.7.4 -m "Release v1.7.4"
git push origin HEAD
git push origin v1.7.4
```

Publicação no GitHub:

- Criar um Release com a tag `v1.7.4` e anexar o instalador/ZIP produzido.
- Atualizar a página `update_config.json` se você mantém um servidor/URL separado.

Verificações pós-release:

- Teste o instalador em uma máquina Windows limpa.
- Teste `import-csv` com o executável e verifique que subcomandos funcionam.
- Confirme que o app verifica atualizações e mostra a versão 1.7.4 quando disponível.
