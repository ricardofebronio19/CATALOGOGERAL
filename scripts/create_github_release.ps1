<#
.create_github_release.ps1
Script para criar ou atualizar uma GitHub Release e anexar um asset (ZIP).

Uso recomendado:
  - Exporte seu token em uma variável de ambiente: $env:GITHUB_TOKEN = '<seu_token>'
  - Execute (padrão procura arquivos no diretório do repositório):
      .\scripts\create_github_release.ps1

Parâmetros opcionais:
  -Owner        (string)  Proprietário do repositório (default: ricardofebronio19)
  -Repo         (string)  Nome do repositório (default: CATALOGOGERAL)
  -Tag          (string)  Tag da release (default: v1.7.0)
  -ZipPath      (string)  Caminho para o arquivo ZIP a subir (default: CatalogoDePecas_v1.7.0.zip)
  -ReleaseNotes (string)  Caminho para as notas de release (default: RELEASE_NOTES_v1.7.0.md)
  -Draft        (switch)  Cria a release como draft
  -PreRelease   (switch)  Marca como prerelease

Observação de segurança: não cole tokens em chats. Prefira definir GITHUB_TOKEN como variável de ambiente antes de executar.
#>

param(
    [string] $Owner = "ricardofebronio19",
    [string] $Repo = "CATALOGOGERAL",
    [string] $Tag = "v1.7.0",
    [string] $ZipPath = "CatalogoDePecas_v1.7.0.zip",
    [string] $ReleaseNotes = "RELEASE_NOTES_v1.7.0.md",
    [switch] $Draft,
    [switch] $PreRelease
)

function Get-Token {
    if ($env:GITHUB_TOKEN) {
        return $env:GITHUB_TOKEN
    }
    Write-Host "GITHUB_TOKEN não encontrado. Você será solicitado a inserir o token (entrada escondida)." -ForegroundColor Yellow
    $secure = Read-Host "Digite seu Personal Access Token (entrada oculta)" -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        $plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto($ptr)
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) | Out-Null
    }
    return $plain
}

# Verificações iniciais
if (-not (Test-Path $ZipPath)) {
    Write-Error "Arquivo ZIP não encontrado: $ZipPath. Coloque o arquivo no diretório do repositório ou passe -ZipPath corretamente."; exit 1
}

$token = Get-Token
$headers = @{ Authorization = "token $token"; "User-Agent" = "PowerShell"; Accept = "application/vnd.github+json" }

# Lê notas de release se existir
$body = ""
if (Test-Path $ReleaseNotes) {
    $body = Get-Content -Raw -Path $ReleaseNotes
} else {
    Write-Host "Arquivo de notas de release não encontrado: $ReleaseNotes. A release será criada sem corpo de notas." -ForegroundColor Yellow
}

$tagCheckUrl = "https://api.github.com/repos/$Owner/$Repo/releases/tags/$Tag"
$release = $null
try {
    $release = Invoke-RestMethod -Uri $tagCheckUrl -Headers $headers -Method Get -ErrorAction Stop
    Write-Host "Release existente encontrada: $($release.html_url)" -ForegroundColor Green
} catch {
    if ($_.Exception -and $_.Exception.Response -and $_.Exception.Response.StatusCode.Value__ -eq 404) {
        Write-Host "Release com tag $Tag não existe. Será criada." -ForegroundColor Yellow
        $release = $null
    } else {
        Write-Error "Erro ao verificar release: $($_.Exception.Message)"; exit 1
    }
}

# Se a release não existe, cria
if (-not $release) {
    $payload = @{ tag_name = $Tag; name = "Release $Tag"; body = $body; draft = $Draft.IsPresent; prerelease = $PreRelease.IsPresent } | ConvertTo-Json -Depth 8
    $createUrl = "https://api.github.com/repos/$Owner/$Repo/releases"
    try {
        $release = Invoke-RestMethod -Uri $createUrl -Headers $headers -Method Post -Body $payload -ContentType "application/json" -ErrorAction Stop
        Write-Host "Release criada: $($release.html_url)" -ForegroundColor Green
    } catch {
        Write-Error "Falha ao criar release: $($_.Exception.Message)"; exit 1
    }
} else {
    # Delete asset with same name if exists
    $assetsUrl = $release.assets_url
    try {
        $assets = Invoke-RestMethod -Uri $assetsUrl -Headers $headers -Method Get -ErrorAction Stop
        $fileName = [IO.Path]::GetFileName($ZipPath)
        foreach ($a in $assets) {
            if ($a.name -eq $fileName) {
                Write-Host "Removendo asset existente com mesmo nome: $fileName (id: $($a.id))" -ForegroundColor Yellow
                Invoke-RestMethod -Uri "https://api.github.com/repos/$Owner/$Repo/releases/assets/$($a.id)" -Headers $headers -Method Delete -ErrorAction Stop
                Write-Host "Asset removido." -ForegroundColor Green
            }
        }
    } catch {
        Write-Host "Aviso: falha ao listar/remover assets (continuando): $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Upload do asset
$uploadTemplate = $release.upload_url
$fileName = [IO.Path]::GetFileName($ZipPath)
$uploadUrl = $uploadTemplate -replace '\{\?name,label\}', "?name=$fileName"

Write-Host "Fazendo upload de $ZipPath para a release..." -ForegroundColor Cyan
try {
    # Invoke-WebRequest com -InFile é mais apropriado para upload binário
    Invoke-WebRequest -Uri $uploadUrl -Headers $headers -Method Post -InFile $ZipPath -ContentType "application/zip" -ErrorAction Stop
    Write-Host "Upload concluído com sucesso." -ForegroundColor Green
    Write-Host "Release URL: $($release.html_url)"
} catch {
    Write-Error "Falha no upload do asset: $($_.Exception.Message)"; exit 1
}

Write-Host "Operação finalizada." -ForegroundColor Green
