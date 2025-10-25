<#
.SYNOPSIS
  Cria um GitHub Release e faz upload de um asset (instalador) usando a API (sem gh).

.DESCRIPTION
  - Solicita um Personal Access Token (PAT) com scope 'repo' de forma segura.
  - Cria o release (tag) ou localiza o release existente se a tag já existir.
  - Faz upload do arquivo especificado como asset.
  - Opcionalmente grava/commita/pusha um update_config.json para ativar o sistema de atualização.

.PARAMETER AssetPath
  Caminho local para o arquivo a enviar (ex: .\Output\instalador_CatalogoDePecas_v1.7.2.exe).

.PARAMETER NotesFile
  Arquivo com as notas do release (ex: .\RELEASE_NOTES_v1.7.2.md).

.PARAMETER RepoOwner
  Dono do repositório (default: ricardofebronio19).

.PARAMETER RepoName
  Nome do repositório (default: CATALOGOGERAL).

.PARAMETER TagName
  Tag do release (default: v1.7.2).

.PARAMETER ReleaseName
  Título do release (default: CatalogoDePecas v1.7.2).

.PARAMETER UpdateConfig
  Switch: se presente, atualiza `update_config.json` local com campos básicos e tenta commitar/pushar.

.EXAMPLE
  .\create_github_release_api.ps1 -AssetPath .\Output\instalador_CatalogoDePecas_v1.7.2.exe -NotesFile .\RELEASE_NOTES_v1.7.2.md -UpdateConfig
#>

param(
    [Parameter(Mandatory=$true)] [string]$AssetPath,
    [Parameter(Mandatory=$true)] [string]$NotesFile,
    [string]$RepoOwner = "ricardofebronio19",
    [string]$RepoName = "CATALOGOGERAL",
    [string]$TagName = "v1.7.2",
    [string]$ReleaseName = "CatalogoDePecas v1.7.2",
    [switch]$UpdateConfig
)

function Read-SecretToken {
    Write-Host "Insira seu GitHub Personal Access Token (scopes: repo) e pressione Enter:" -ForegroundColor Yellow
    $secure = Read-Host -AsSecureString
    $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        $plain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
    } finally {
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
    return $plain
}

# Validações básicas
if (!(Test-Path $AssetPath)) {
    Write-Error "Arquivo de asset não encontrado: $AssetPath"
    exit 1
}
if (!(Test-Path $NotesFile)) {
    Write-Error "Arquivo de notas não encontrado: $NotesFile"
    exit 1
}

# Lê token de forma segura
$token = Read-SecretToken

$notes = Get-Content -Raw -Path $NotesFile
$body = @{
    tag_name = $TagName
    name     = $ReleaseName
    body     = $notes
    draft    = $false
    prerelease = $false
} | ConvertTo-Json -Depth 10

$headers = @{
    Authorization = "token $token"
    Accept        = "application/vnd.github.v3+json"
    'User-Agent'  = 'powershell'
}

$apiBase = "https://api.github.com/repos/$RepoOwner/$RepoName"

# Função para obter release (por tag)
function Get-Release-ByTag {
    param($tag)
    try {
        $url = "$apiBase/releases/tags/$tag"
        return Invoke-RestMethod -Method Get -Uri $url -Headers $headers -ErrorAction Stop
    } catch {
        return $null
    }
}

# 1) Tentar criar o release
$release = $null
try {
    Write-Host "Criando release '$TagName'..." -ForegroundColor Cyan
    $createUrl = "$apiBase/releases"
    $release = Invoke-RestMethod -Method Post -Uri $createUrl -Headers $headers -Body $body -ContentType 'application/json' -ErrorAction Stop
    Write-Host "Release criado: $($release.html_url)" -ForegroundColor Green
} catch {
    # Se tag já existe, recupera o release existente
    if ($_.Exception.Response -and $_.Exception.Response.StatusCode.Value__ -eq 422) {
        Write-Host "Tag '$TagName' já existe. Tentando localizar o release associado..." -ForegroundColor Yellow
        $release = Get-Release-ByTag -tag $TagName
        if ($null -eq $release) {
            Write-Error "Não foi possível localizar o release para a tag '$TagName'. Erro: $_"
            exit 1
        } else {
            Write-Host "Release encontrado: $($release.html_url)" -ForegroundColor Green
        }
    } else {
        Write-Error "Erro ao criar release: $_"
        exit 1
    }
}

# 2) Fazer upload do asset
$upload_url = $release.upload_url -replace '\{.*$',''
$fileName = [System.IO.Path]::GetFileName($AssetPath)
$assetUploadUrl = "$upload_url?name=$fileName"

Write-Host "Iniciando upload do asset '$fileName'..." -ForegroundColor Cyan
try {
    Invoke-RestMethod -Method Post -Uri $assetUploadUrl -Headers @{ Authorization = "token $token"; 'User-Agent'='powershell'; 'Content-Type'='application/octet-stream' } -InFile $AssetPath -ErrorAction Stop
    Write-Host "Upload concluído com sucesso." -ForegroundColor Green
} catch {
    Write-Error "Erro no upload do asset: $_"
    exit 1
}

# 3) (Opcional) Atualizar update_config.json local e commitar/push
if ($UpdateConfig) {
    $updateObj = @{
        latest_version = $TagName.TrimStart('v')
        download_url = "https://github.com/$RepoOwner/$RepoName/releases/download/$TagName/$fileName"
        release_notes = ($notes -replace "`r`n", "`n")    # manter nova linha padrão
        size_mb = "{0:N0}" -f ((Get-Item $AssetPath).Length / 1MB)
    }
    $json = $updateObj | ConvertTo-Json -Depth 10
    $updatePath = Join-Path -Path (Get-Location) -ChildPath "update_config.json"
    Write-Host "Gravando $updatePath ..." -ForegroundColor Cyan
    $json | Out-File -FilePath $updatePath -Encoding UTF8

    # Tenta commitar e push (se git disponível)
    if (Get-Command git -ErrorAction SilentlyContinue) {
        try {
            git add $updatePath
            git commit -m "chore(release): update_config for $TagName"
            git push
            Write-Host "update_config.json commitado e pushado." -ForegroundColor Green
        } catch {
            Write-Warning "Falha ao commitar/pushar update_config.json automaticamente. Revise manualmente. Erro: $_"
        }
    } else {
        Write-Warning "Git não encontrado no PATH. update_config.json gravado, por favor commit/ push manualmente."
    }
}

Write-Host "`nOperação concluída com sucesso." -ForegroundColor Green
Write-Host "Release URL: $($release.html_url)" -ForegroundColor Cyan
Write-Host "Asset: $($assetUploadUrl)" -ForegroundColor Cyan
