# Docu RAG System Performance Optimization Script
param(
    [switch]$FullOptimization = $false,
    [switch]$OllamaOptimization = $true,
    [switch]$MemoryOptimization = $true
)

Write-Host "Docu RAG System Performance Optimization" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Gray

# Set up paths
$RepoPath = "D:\Development\Docu"
$OllamaPath = "D:\ollama"
$ChromaDBPath = Join-Path $RepoPath "data\chroma_db"

# Get system specs
Write-Host "`nSystem Specifications:" -ForegroundColor Cyan
$totalRAM = [math]::Round((Get-CimInstance -ClassName Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)
$cpu = Get-CimInstance -ClassName Win32_Processor
Write-Host "   Total RAM: $totalRAM GB"
Write-Host "   CPU: $($cpu.Name)"

# Create startup script
$startupScript = @"
Write-Host "Starting Optimized Docu RAG System..." -ForegroundColor Green
Set-Location "$RepoPath"

# Activate virtual environment
if (Test-Path ".\langchain_env\Scripts\Activate.ps1") {
    Write-Host "Activating Python environment..." -ForegroundColor Cyan
    & ".\langchain_env\Scripts\Activate.ps1"
} else {
    Write-Host "ERROR: Python virtual environment not found!" -ForegroundColor Red
    exit 1
}

# Check if Ollama is running
`$ollamaProcess = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
if (-not `$ollamaProcess) {
    Write-Host "Starting Ollama server..." -ForegroundColor Cyan
    Start-Process -FilePath "$OllamaPath\ollama.exe" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 5
} else {
    Write-Host "Ollama already running" -ForegroundColor Green
}

Write-Host "`nSystem ready! You can now:" -ForegroundColor Green
Write-Host "   Run Python: python main.py" -ForegroundColor Cyan
Write-Host "   Run Streamlit app: streamlit run streamlit_app.py" -ForegroundColor Cyan
"@

$startupPath = Join-Path $RepoPath "start_optimized.ps1"
$startupScript | Out-File -FilePath $startupPath -Encoding UTF8
Write-Host "Created startup script: $startupPath" -ForegroundColor Green

Write-Host "`nOptimization Complete!" -ForegroundColor Green
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Run: .\start_optimized.ps1" -ForegroundColor Cyan
Write-Host "   2. Create the Python optimization files" -ForegroundColor Cyan
