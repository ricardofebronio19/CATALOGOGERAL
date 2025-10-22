# ✅ Checklist de Release v1.7.2

## Preparação da Versão

- [x] Atualizar `version.json` para "v1.7.2"
- [x] Atualizar `build.bat` para versão 1.7.2
- [x] Atualizar `instalador.iss` para versão 1.7.2
- [x] Criar arquivo `RELEASE_NOTES_v1.7.0.md`
- [x] Atualizar `README.md` com novidades
- [x] Preparar `update_config.json` para sistema de atualização
- [x] Criar script `prepare_release.ps1`

## Testes Pré-Release

- [ ] Testar build local com `.\build.bat`
- [ ] Verificar se o instalador é criado corretamente
- [ ] Testar instalação em ambiente limpo
- [ ] Verificar funcionamento das principais funcionalidades:
  - [ ] Adicionar peças
  - [ ] Editar peças
  - [ ] Sistema de busca
  - [ ] Upload de imagens
  - [ ] Sistema de atualização automática
  - [ ] Interface visual melhorada

## Build e Publicação

- [ ] Executar `.\prepare_release.ps1 -BuildOnly` para build
- [ ] Verificar tamanho do instalador (~35MB)
- [ ] Testar instalador em máquina de teste
- [ ] Fazer commit das alterações de versão
- [ ] Criar tag `v1.7.0` no Git
- [ ] Push para GitHub
- [ ] Executar `.\prepare_release.ps1 -CreateRelease` ou criar release manual

## GitHub Release

- [ ] Criar release no GitHub com tag `v1.7.0`
- [ ] Título: "CatalogoDePecas v1.7.0"
- [ ] Anexar `instalador_CatalogoDePecas_v1.7.0.exe`
- [ ] Copiar notas de release do arquivo `RELEASE_NOTES_v1.7.0.md`
- [ ] Marcar como "Latest release"

## Atualização Automática

- [ ] Fazer commit do `update_config.json` atualizado
- [ ] Push para branch main/master
- [ ] Verificar se o sistema detecta a nova versão
- [ ] Testar download e instalação automática

## Pós-Release

- [ ] Anunciar release (se aplicável)
- [ ] Monitorar issues relacionadas ao release
- [ ] Documentar problemas conhecidos (se houver)
- [ ] Planejar próxima versão

## Comandos de Referência

```powershell
# Build local
.\prepare_release.ps1 -BuildOnly

# Build completo com release
.\prepare_release.ps1 -CreateRelease

# Apenas build (sem script)
.\build.bat

# Verificar versão atual
type version.json
```

## URLs Importantes

- **Repositório**: https://github.com/ricardofebronio19/CATALOGOGERAL
- **Releases**: https://github.com/ricardofebronio19/CATALOGOGERAL/releases
- **Config de Atualização**: https://raw.githubusercontent.com/ricardofebronio19/CATALOGOGERAL/main/update_config.json

## Notas

- Certifique-se de que o GitHub CLI (`gh`) está instalado para releases automáticos
- O sistema de atualização automática só funcionará após o `update_config.json` ser commitado
- Mantenha backup da versão anterior caso seja necessário rollback