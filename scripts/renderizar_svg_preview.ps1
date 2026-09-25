param(
    [string]$Episode = "CO-001",
    [string]$Files = "s001,s002,s003,s004,s005",
    [string]$Variant = "",
    [string]$SceneRoot = "",
    [switch]$Update
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$sceneRoot = if ($SceneRoot) {
    $candidate = if ([System.IO.Path]::IsPathRooted($SceneRoot)) { $SceneRoot } else { Join-Path $projectRoot $SceneRoot }
    [System.IO.Path]::GetFullPath($candidate)
} else {
    Join-Path $projectRoot ("assets\scenes\" + $Episode)
}
if ($Variant -and -not $SceneRoot) {
    if ($Variant -notmatch '^[a-zA-Z0-9_-]+$') {
        throw "Nome de variante invalido: $Variant"
    }
    $sceneRoot = Join-Path $sceneRoot $Variant
}

if (-not (Test-Path -LiteralPath $sceneRoot)) {
    throw "Pasta de cenas nao encontrada: $sceneRoot"
}

$browserCandidates = @(
    "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "C:\Program Files\Google\Chrome\Application\chrome.exe",
    "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
)
$browser = $browserCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $browser) {
    throw "Edge ou Chrome nao encontrado. Os SVGs continuam utilizaveis sem as previews PNG."
}

$names = $Files.Split(',') | ForEach-Object { $_.Trim().ToLowerInvariant() } | Where-Object { $_ }
if (-not $names) {
    throw "Informe ao menos um nome de SVG em -Files."
}

foreach ($name in $names) {
    if ($name -notmatch '^[a-z0-9_-]+$') {
        throw "Nome de arquivo invalido: $name"
    }
    $source = Join-Path $sceneRoot ($name + ".svg")
    if (-not (Test-Path -LiteralPath $source)) {
        throw "SVG nao encontrado: $source"
    }

    if ($name.StartsWith("prototype_") -or $name.StartsWith("review_")) {
        $destination = Join-Path $sceneRoot ($name + ".png")
    } else {
        $previewRoot = Join-Path $sceneRoot "previews"
        New-Item -ItemType Directory -Path $previewRoot -Force | Out-Null
        $destination = Join-Path $previewRoot ($name + ".png")
    }

    if ((Test-Path -LiteralPath $destination) -and -not $Update) {
        Write-Host "$name`: preservado"
        continue
    }
    if (Test-Path -LiteralPath $destination) {
        Remove-Item -LiteralPath $destination -Force
    }

    $profile = Join-Path $projectRoot (".svg-profile-" + $name)
    if (Test-Path -LiteralPath $profile) {
        Remove-Item -LiteralPath $profile -Recurse -Force
    }
    New-Item -ItemType Directory -Path $profile -Force | Out-Null
    $uri = [System.Uri]::new($source).AbsoluteUri
    $arguments = @(
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--allow-file-access-from-files",
        "--no-first-run",
        "--no-default-browser-check",
        ('--user-data-dir="' + $profile + '"'),
        ('--screenshot="' + $destination + '"'),
        "--window-size=1920,1080",
        ('"' + $uri + '"')
    )
    Start-Process -FilePath $browser -ArgumentList $arguments -WindowStyle Hidden | Out-Null

    $rendered = $false
    for ($attempt = 0; $attempt -lt 40; $attempt++) {
        if ((Test-Path -LiteralPath $destination) -and (Get-Item -LiteralPath $destination).Length -gt 1000) {
            $rendered = $true
            break
        }
        Start-Sleep -Milliseconds 500
    }

    $ownedProcesses = Get-CimInstance Win32_Process | Where-Object {
        $_.Name -in @("msedge.exe", "chrome.exe") -and $_.CommandLine -like "*$profile*"
    }
    foreach ($process in $ownedProcesses) {
        Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Milliseconds 300
    if (Test-Path -LiteralPath $profile) {
        for ($cleanupAttempt = 0; $cleanupAttempt -lt 10; $cleanupAttempt++) {
            try {
                Remove-Item -LiteralPath $profile -Recurse -Force -ErrorAction Stop
                break
            } catch {
                Start-Sleep -Milliseconds 250
            }
        }
        if (Test-Path -LiteralPath $profile) {
            Write-Warning "Perfil temporario ainda em uso; limpeza adiada: $profile"
        }
    }

    if (-not $rendered) {
        throw "Falha ao renderizar: $source"
    }
    Write-Host "$name`: renderizado -> $destination"
}
