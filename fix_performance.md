# 🔧 Fix DocuMentor Performance Issues

## Issue Analysis
Your tests show:
- ✅ **Search working perfectly** (2.3s response times)
- ✅ **212 docs loaded correctly**
- ❌ **AI Q&A timing out** (>120s)
- ❌ **Upload endpoint 404/timeout**

The root cause is likely **Gemma 3 getting stuck** on complex prompts with large context.

## Quick Fixes

### 1. Optimize Ollama Settings

**Stop and restart Gemma 3 with better settings:**

```powershell
# Stop the current model
ollama stop gemma3:4b

# Set environment variables for better performance
$env:OLLAMA_NUM_CTX = "4096"
$env:OLLAMA_NUM_PREDICT = "500"
$env:OLLAMA_NUM_GPU_LAYERS = "0"

# Restart the model
ollama run gemma3:4b
```

### 2. Update .env Configuration

Edit your `.env` file:

```env
# Optimized LLM Configuration for Performance
OLLAMA_MODEL=gemma3:4b
MODEL_N_CTX=4096        # Reduced from 8192
MODEL_N_GPU_LAYERS=0
TEMPERATURE=0.1
MAX_TOKENS=500          # Reduced from 2048
TOP_P=0.9

# Keep existing Vector Database settings
CHROMA_PERSIST_DIRECTORY=./data/vectordb
COLLECTION_NAME=documenter
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
```

### 3. Restart Services

```powershell
# 1. Stop API server (Ctrl+C)
# 2. Restart Ollama with new settings (above)
# 3. Restart API server
python api_server.py
```

## Manual Quick Test

Test with a simple question first:

### Using PowerShell:
```powershell
$body = @{
    question = "What is Python?"
    k = 3
    temperature = 0.1
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/ask" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 60
```

### Using Browser:
1. Go to: `http://localhost:8000/docs`
2. Click on `/ask` endpoint
3. Click "Try it out"
4. Use this simple test:
```json
{
  "question": "What is Python?",
  "k": 3,
  "temperature": 0.1
}
```

## Expected Results After Optimization

- **Simple questions**: 15-30 seconds
- **Complex questions**: 30-60 seconds  
- **Search**: Continue working at 2-3 seconds
- **Upload**: Should work (was likely timeout issue)

## Troubleshooting Steps

### If Still Timing Out:

1. **Try even smaller model:**
```powershell
ollama pull gemma3:2b
# Then update .env: OLLAMA_MODEL=gemma3:2b
```

2. **Check resource usage:**
```powershell
ollama ps
Get-Process ollama
```

3. **Test Ollama directly:**
```powershell
# Save and run the diagnostic script above
python diagnose_gemma3.py
```

### Upload Endpoint Fix

The upload 404 error suggests an endpoint issue. Check if your `api_server.py` has the upload endpoint defined. If not, it might be missing from your version.

## Success Indicators

After applying fixes, you should see:
- ✅ Simple questions answered in 15-30s
- ✅ Complex questions in 30-60s  
- ✅ No more timeout errors
- ✅ Upload endpoint working
- ✅ Overall success rate >80%

## Alternative: Quick Test Mode

If you want to test functionality without waiting for slow responses, you can temporarily modify the system to use fallback responses while debugging Gemma 3 performance.





