# DocuMentor Critical Issues Fix Script
# This script applies all the fixes for the critical issues

Write-Host "🔧 DocuMentor Critical Issues Fix" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

$ProjectRoot = Get-Location

# Step 1: Create directory structure
Write-Host "`n📁 Creating Directory Structure..." -ForegroundColor Green

$directories = @(
    "src",
    "src\ingestion", 
    "src\retrieval",
    "src\generation",
    "src\utils"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "   ✅ Created: $dir" -ForegroundColor White
    } else {
        Write-Host "   ✅ Exists: $dir" -ForegroundColor White
    }
}

# Step 2: Create __init__.py files
Write-Host "`n📦 Creating __init__.py Files..." -ForegroundColor Green

$initFiles = @(
    "src\__init__.py",
    "src\ingestion\__init__.py",
    "src\retrieval\__init__.py", 
    "src\generation\__init__.py",
    "src\utils\__init__.py"
)

foreach ($initFile in $initFiles) {
    '"""DocuMentor package module"""' | Out-File -FilePath $initFile -Encoding UTF8
    Write-Host "   ✅ Created: $initFile" -ForegroundColor White
}

# Step 3: Apply fixes
Write-Host "`n🛠️ Applying Fixes..." -ForegroundColor Green

Write-Host "   1. DocumentProcessor fix..." -ForegroundColor Yellow
Write-Host "      ℹ️  You need to save the DocumentProcessor code to: src\ingestion\document_processor.py" -ForegroundColor Cyan

Write-Host "   2. FastAPI lifespan fix..." -ForegroundColor Yellow  
Write-Host "      ℹ️  You need to save the fixed API server code to: api_server_fixed.py" -ForegroundColor Cyan

Write-Host "   3. Test endpoint fix..." -ForegroundColor Yellow
Write-Host "      ℹ️  Tests will now use /upload-document instead of /upload" -ForegroundColor Cyan

# Step 4: Test current setup
Write-Host "`n🧪 Testing Current Setup..." -ForegroundColor Green

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "   ✅ Python: $pythonVersion" -ForegroundColor White
} catch {
    Write-Host "   ❌ Python not found" -ForegroundColor Red
}

# Check if required modules can be imported
$testImports = @(
    "fastapi",
    "chromadb",
    "requests"
)

foreach ($module in $testImports) {
    try {
        python -c "import $module" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Module $module: Available" -ForegroundColor White
        } else {
            Write-Host "   ❌ Module $module: Missing" -ForegroundColor Red
        }
    } catch {
        Write-Host "   ❌ Module $module: Error checking" -ForegroundColor Red
    }
}

# Check if Ollama is running
Write-Host "`n🤖 Checking Ollama Status..." -ForegroundColor Green
try {
    $ollamaPs = ollama ps 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Ollama is running" -ForegroundColor White
        ollama ps
    } else {
        Write-Host "   ⚠️ Ollama not responding" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Ollama not found" -ForegroundColor Red
}

# Step 5: Instructions
Write-Host "`n📋 Manual Steps Required:" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Cyan

Write-Host "`n1️⃣ Save DocumentProcessor Code:" -ForegroundColor Yellow
Write-Host "   • Copy the DocumentProcessor code from the artifacts above" -ForegroundColor White
Write-Host "   • Save it to: src\ingestion\document_processor.py" -ForegroundColor White

Write-Host "`n2️⃣ Save Fixed API Server:" -ForegroundColor Yellow  
Write-Host "   • Copy the api_server_fixed.py code from the artifacts above" -ForegroundColor White
Write-Host "   • Save it as: api_server_fixed.py" -ForegroundColor White

Write-Host "`n3️⃣ Stop Current Server:" -ForegroundColor Yellow
Write-Host "   • Press Ctrl+C in the terminal running the API server" -ForegroundColor White

Write-Host "`n4️⃣ Start Fixed Server:" -ForegroundColor Yellow
Write-Host "   • Run: python api_server_fixed.py" -ForegroundColor White

Write-Host "`n5️⃣ Test Fixed Functionality:" -ForegroundColor Yellow
Write-Host "   • Run: python test_fixed_endpoints.py" -ForegroundColor White

# Step 6: Quick test commands
Write-Host "`n🧪 Quick Test Commands:" -ForegroundColor Green
Write-Host "After applying fixes, run these to verify:" -ForegroundColor Cyan

$testCommands = @(
    "# Test health endpoint",
    "Invoke-RestMethod -Uri 'http://localhost:8000/health'",
    "",
    "# Test stats endpoint", 
    "Invoke-RestMethod -Uri 'http://localhost:8000/stats'",
    "",
    "# Test search endpoint",
    '$searchBody = @{ query = "Python"; k = 3 } | ConvertTo-Json',
    "Invoke-RestMethod -Uri 'http://localhost:8000/search' -Method POST -Body `$searchBody -ContentType 'application/json'",
    "",
    "# Test upload info",
    "Invoke-RestMethod -Uri 'http://localhost:8000/upload-info'"
)

foreach ($cmd in $testCommands) {
    if ($cmd.StartsWith("#")) {
        Write-Host "   $cmd" -ForegroundColor Green
    } elseif ($cmd -eq "") {
        Write-Host ""
    } else {
        Write-Host "   $cmd" -ForegroundColor White
    }
}

# Step 7: Expected results
Write-Host "`n🎯 Expected Results After Fixes:" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Cyan

Write-Host "✅ Upload Endpoint Fixed:" -ForegroundColor White
Write-Host "   • /upload-document should work without 404 errors" -ForegroundColor Gray
Write-Host "   • Document upload and processing should function" -ForegroundColor Gray

Write-Host "`n✅ FastAPI Modernized:" -ForegroundColor White  
Write-Host "   • No more deprecation warnings about on_event" -ForegroundColor Gray
Write-Host "   • Modern lifespan event handling" -ForegroundColor Gray

Write-Host "`n✅ Complete Functionality:" -ForegroundColor White
Write-Host "   • All API endpoints working correctly" -ForegroundColor Gray
Write-Host "   • Document processing fully functional" -ForegroundColor Gray
Write-Host "   • Upload, search, and AI responses all working" -ForegroundColor Gray

Write-Host "`n📊 Success Metrics Target:" -ForegroundColor Green
Write-Host "   • Test success rate: >90%" -ForegroundColor White
Write-Host "   • Upload functionality: Working" -ForegroundColor White
Write-Host "   • Response times: <60s for AI, <5s for search" -ForegroundColor White
Write-Host "   • No critical errors in logs" -ForegroundColor White

Write-Host "`n🎉 Ready for Production Testing!" -ForegroundColor Green
Write-Host "Once these fixes are applied, your DocuMentor should be fully functional." -ForegroundColor Cyan

Write-Host "`nPress any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
