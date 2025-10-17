Param(
    [string]$TagName = "v1.5",
    [string]$ReleaseName = "CatalogoDePecas v1.5",
    [string]$Body = "Release automatica gerada pelo build script.",
    [string]$AssetPath = "dist\CatalogoDePecas.exe",
    [string]$Repo = "ricardofebronio19/CATALOGOGERAL"
)

if (-not $env:GITHUB_TOKEN) {
    Write-Error "Defina a variável de ambiente GITHUB_TOKEN com um Personal Access Token (scopes: repo)."
    exit 1
}

$headers = @{ Authorization = "token $($env:GITHUB_TOKEN)"; "User-Agent" = "catalogo-build-script" }

# 1) Criar release
$createUrl = "https://api.github.com/repos/$Repo/releases"
$bodyObj = @{ tag_name = $TagName; name = $ReleaseName; body = $Body; draft = $false; prerelease = $false } | ConvertTo-Json

Write-Host "Criando release $TagName em $Repo..."
$response = Invoke-RestMethod -Uri $createUrl -Method Post -Headers $headers -Body $bodyObj -ContentType "application/json"

if (-not $response) { Write-Error "Falha ao criar release"; exit 1 }

$uploadUrl = $response.upload_url -replace "{\?name,label}", ""
$assetName = Split-Path $AssetPath -Leaf

# 2) Upload asset
if (-not (Test-Path $AssetPath)) { Write-Error "Asset nao encontrado: $AssetPath"; exit 1 }

Write-Host "Enviando asset $assetName..."
$uploadUri = "$uploadUrl?name=$assetName"
Invoke-RestMethod -Uri $uploadUri -Method Post -Headers $headers -InFile $AssetPath -ContentType "application/octet-stream"

Write-Host "Release e asset enviados com sucesso. URL:" $response.html_url
