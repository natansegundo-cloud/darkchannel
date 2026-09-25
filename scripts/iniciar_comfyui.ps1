param(
    [string]$Listen = "127.0.0.1",
    [int]$Port = 8188
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot ".comfyui\venv\Scripts\python.exe"
$main = Join-Path $projectRoot ".comfyui\ComfyUI\main.py"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Python do ComfyUI nao encontrado em: $python"
}
if (-not (Test-Path -LiteralPath $main)) {
    throw "ComfyUI nao encontrado em: $main"
}

Write-Host "Capital Oculto - ComfyUI local CPU"
Write-Host "Interface: http://${Listen}:${Port}"
Write-Host "Mantenha esta janela aberta durante a geracao. Use Ctrl+C para encerrar."

& $python $main `
    --listen $Listen `
    --port $Port `
    --cpu `
    --cache-lru 1 `
    --preview-method none `
    --disable-all-custom-nodes `
    --disable-api-nodes `
    --disable-auto-launch

exit $LASTEXITCODE
