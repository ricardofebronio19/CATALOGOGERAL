<#
deploy_installer.ps1

Script para distribuir e executar o instalador do CatalogoDePecas em múltiplas máquinas Windows.

Requisitos:
- Credenciais administrativas nas máquinas-alvo.
- WinRM/PowerShell Remoting habilitado nas máquinas-alvo (para Invoke-Command), ou acesso administrativo ao share C$ (para cópia via SMB).
- Se usar SMB, o usuário deve ter permissão para gravar em `\\<target>\C$\Temp`.

Uso básico (modo remoto via Invoke-Command):
.
powershell
& .\scripts\deploy_installer.ps1 -InstallerPath ".\\Output\\instalador_CatalogoDePecas_v1.7.2.exe" -Targets "PC1","PC2" -Credential (Get-Credential)

Parâmetros:
-InstallerPath <string>  : caminho local para o instalador (padrão: .\Output\instalador_CatalogoDePecas_v1.7.2.exe)
-Targets <string[]>      : lista de nomes NETBIOS ou endereços IP das máquinas destino
-Credential <PSCredential>: credenciais administrativas (opcional; se omitido tenta sessão atual)
-UseCopy                 : copia o instalador para C:\Temp na máquina destino e executa (usa New-PSDrive)
-DryRun                  : apenas mostra operações sem executar
-Verbose                 : saída detalhada
#>

param(
    [string]$InstallerPath = ".\Output\instalador_CatalogoDePecas_v1.7.2.exe",
    [Parameter(Mandatory=$true)] [string[]]$Targets,
    [System.Management.Automation.PSCredential]$Credential,
    [switch]$UseCopy,
    [switch]$DryRun,
    [switch]$Verbose
)

function Test-Remoting {
    param([string]$ComputerName, [System.Management.Automation.PSCredential]$Cred)
    try {
        if ($Cred) { Test-WSMan -ComputerName $ComputerName -Credential $Cred -ErrorAction Stop | Out-Null }
        else { Test-WSMan -ComputerName $ComputerName -ErrorAction Stop | Out-Null }
        return $true
    } catch {
        return $false
    }
}

function Copy-ToCDriveTemp {
    param([string]$Computer, [string]$LocalInstaller, [System.Management.Automation.PSCredential]$Cred)
    $remoteTemp = "C:\Temp"
    $psDriveName = "Z_$($Computer -replace '[^a-zA-Z0-9]','')"

    try {
        Write-Verbose "Criando drive temporário para \\$Computer\C$"
        New-PSDrive -Name $psDriveName -PSProvider FileSystem -Root "\\$Computer\C$" -Credential $Cred -ErrorAction Stop | Out-Null
        $destDir = "${psDriveName}:\Temp"
        Invoke-Command -ComputerName $Computer -Credential $Cred -ScriptBlock { param($d) if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d | Out-Null } } -ArgumentList $destDir | Out-Null
        $destPath = Join-Path -Path "${psDriveName}:\Temp" -ChildPath ([IO.Path]::GetFileName($LocalInstaller))
        Copy-Item -Path $LocalInstaller -Destination $destPath -Force
        return "${remoteTemp}\$([IO.Path]::GetFileName($LocalInstaller))"
    } catch {
        throw "Falha ao copiar para $Computer: $_"
    } finally {
        try { Remove-PSDrive -Name $psDriveName -Force -ErrorAction SilentlyContinue } catch {}
    }
}

function Invoke-Install {
    param([string]$Computer, [string]$RemoteInstallerPath, [System.Management.Automation.PSCredential]$Cred)
    $args = '/VERYSILENT','/NORESTART'
    $script = {
        param($p, $a)
        Write-Output "Iniciando instalador: $p"
        Start-Process -FilePath $p -ArgumentList $a -Wait -NoNewWindow
        return $LASTEXITCODE
    }
    if ($DryRun) { Write-Output "[DRYRUN] Exec: Invoke-Command -ComputerName $Computer -ScriptBlock { Start-Process $RemoteInstallerPath /VERYSILENT /NORESTART }"; return }
    try {
        if ($Cred) { $res = Invoke-Command -ComputerName $Computer -Credential $Cred -ScriptBlock $script -ArgumentList $RemoteInstallerPath, $args -ErrorAction Stop }
        else { $res = Invoke-Command -ComputerName $Computer -ScriptBlock $script -ArgumentList $RemoteInstallerPath, $args -ErrorAction Stop }
        Write-Output "Instalação em $Computer finalizada com código: $res"
    } catch {
        throw "Erro ao executar instalador em $Computer: $_"
    }
}

# Validações iniciais
if (-not (Test-Path $InstallerPath)) {
    Write-Error "Instalador não encontrado em: $InstallerPath"
    exit 1
}

Write-Output "Deploy: Installer=$InstallerPath Targets=$($Targets -join ',') UseCopy=$UseCopy"

foreach ($t in $Targets) {
    Write-Output "\n===== Alvo: $t ====="

    # Testa remoting
    $canRem = Test-Remoting -ComputerName $t -Cred $Credential
    if (-not $canRem -and -not $UseCopy) {
        Write-Warning "WinRM/Remoting não disponível para $t. Tente usar -UseCopy ou habilitar WinRM. Pulando..."
        continue
    }

    try {
        if ($UseCopy) {
            Write-Output "Copiando instalador para $t..."
            if ($DryRun) { Write-Output "[DRYRUN] Copiar $InstallerPath -> \\$t\C$\Temp"; continue }
            $remotePath = Copy-ToCDriveTemp -Computer $t -LocalInstaller $InstallerPath -Cred $Credential
            Write-Output "Instalador copiado para: $remotePath"
            Write-Output "Executando instalador em $t..."
            Invoke-Install -Computer $t -RemoteInstallerPath $remotePath -Cred $Credential
        } else {
            Write-Output "Executando instalador diretamente via Invoke-Command em $t (executando a partir do caminho de rede)..."
            # Para evitar cópia, podemos executar diretamente do share de arquivos local onde o instalador está disponível
            # Mas o Invoke-Command executa no contexto remoto; precisamos primeiro copiar ou disponibilizar via share acessível.
            # Aqui assumimos que a máquina remota consegue acessar um share `\\$env:COMPUTERNAME\SharedInstallers` ou similar.

            # Se o instalador estiver em uma UNC acessível, use o caminho UNC. Caso contrário, o ideal é usar -UseCopy.
            $unc = (Resolve-Path -Path $InstallerPath).ProviderPath
            if ($unc -notmatch '^\\') {
                Write-Warning "O caminho do instalador não é um UNC. Use -UseCopy ou disponibilize o instalador via share de rede. Pulando..."
                continue
            }
            Invoke-Install -Computer $t -RemoteInstallerPath $unc -Cred $Credential
        }
    } catch {
        Write-Error "Erro no alvo $t: $_"
        continue
    }
}

Write-Output "\nDeploy concluído." 
