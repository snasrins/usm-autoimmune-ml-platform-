# Dr. Myra Setup Guide: Natural Language Understanding with Gemma + SHAP

## 🎯 Overview

Dr. Myra is an AI-powered clinical ML assistant that combines:
- **Gemma-4-E4B LLM** for natural language understanding
- **SHAP explanations** for model interpretability
- **Platform context** about ML pipeline and workflow
- **Clinical knowledge** about SLE and autoimmune diseases

## ✅ What Was Fixed

### 1. API Path Mismatch (FIXED)
- **Before:** Frontend calling `/api/v1/explainability/chat` ❌
- **After:** Frontend calling `/api/v1/ml/chat` ✅
- **Backend endpoint:** `/api/v1/ml/chat` (explainability router under `/ml` prefix)

### 2. Debugging Logs (ADDED)
Console logs now track:
```javascript
🤖 Dr. Myra API Call: { message, context, historyLength }
✅ Dr. Myra Response: { response, model, tokens_generated }
❌ Dr. Myra chat error: [error details]
```

## 🔧 How Dr. Myra Works

### Architecture Flow:
```
User Message
    ↓
ChatbotWidget.jsx → explainabilityAPI.chatWithDrMyra()
    ↓
POST /api/v1/ml/chat
    ↓
explainability.py → chat_with_ai()
    ↓
GemmaConversationalService.chat()
    ↓
Lazy Load Gemma-4-E4B model (first call only)
    ↓
Generate response with transformers
    ↓
Return natural language response
```

### Fallback Mode:
If Gemma fails to load, Dr. Myra uses **rule-based responses** instead of LLM.

## 🧪 Testing Natural Language Understanding

### Step 1: Open Browser Console
**Chrome:** F12 → Console tab  
**Firefox:** F12 → Console tab

### Step 2: Ask Dr. Myra a Question
Open chat bubble → Type: `"explain the platform to me"`

### Step 3: Check Console Logs

**Success (Gemma LLM):**
```
🤖 Dr. Myra API Call: { message: "explain the platform to me", ... }
✅ Dr. Myra Response: { 
  response: "The USM ML Platform is a comprehensive...", 
  model: "gemma-4-E4B",  <-- REAL LLM!
  tokens_generated: 127,
  device: "cuda" 
}
```

**Fallback Mode:**
```
✅ Dr. Myra Response: { 
  response: "I'm currently operating in limited mode...",
  model: "fallback-rules",  <-- NOT using LLM
  tokens_generated: 0,
  device: "cpu"
}
```

**Error (Path mismatch or backend down):**
```
❌ Dr. Myra chat error: Error: Request failed with status code 404
Error details: { detail: "Not Found" }
```

## 🚀 Enabling Gemma LLM (Natural Language)

### Requirements Check:

1. **Python Dependencies** (Already in requirements.txt ✅)
```bash
torch>=2.4.0
transformers>=4.38.0
accelerate>=0.25.0
```

2. **Backend Server Running:**
```powershell
# Check if backend is up
curl http://100.106.132.15:8001/health

# Should return:
# { "status": "healthy", "ml_features": true, "gpu_available": true }
```

3. **Hugging Face Model Access:**

Gemma models require authentication. Set environment variable:

```powershell
# In .env file or environment
HUGGINGFACE_TOKEN=hf_your_token_here
```

Get token: https://huggingface.co/settings/tokens

### Model Download (First Call Only):

When Dr. Myra is first used, Gemma-4-E4B will download (~9GB):

**Backend logs will show:**
```
INFO: Loading Gemma-4-E4B model from Hugging Face...
INFO: Downloading model...
INFO: Gemma-4-E4B loaded on GPU with float16
INFO: ✅ Gemma-4-E4B model loaded successfully!
```

**Subsequent calls:** Model stays in memory, instant responses.

## 🐛 Troubleshooting

### Issue 1: Still Getting Hardcoded Responses

**Check console logs:**
```javascript
❌ Dr. Myra chat error: Error: Request failed with status code 404
```

**Solution:** 
- Verify backend is running on http://100.106.132.15:8001
- Check CORS allows localhost:3001
- Verify JWT token in localStorage

### Issue 2: Backend Says "Fallback Mode"

**Backend logs show:**
```
WARNING: Gemma service will operate in fallback mode (rule-based responses)
ERROR: Error loading Gemma-4-E4B model: ...
```

**Common causes:**
1. **Missing Hugging Face token** → Set `HUGGINGFACE_TOKEN`
2. **Not enough VRAM** → Gemma-4-E4B needs ~8GB GPU memory
3. **transformers version too old** → Upgrade: `pip install --upgrade transformers`
4. **No internet** → Model needs to download first time

**Solution:**
```bash
# Check GPU memory
nvidia-smi

# Test transformers
python -c "from transformers import AutoTokenizer; print('OK')"

# Manual model download
python
>>> from transformers import AutoModelForCausalLM
>>> model = AutoModelForCausalLM.from_pretrained("google/gemma-4-E4B")
```

### Issue 3: Model Loads But Responses Are Slow

**First call:** 20-30 seconds (model loading)  
**Subsequent calls:** 2-5 seconds (normal generation time)

**If always slow:**
- Check device in logs: Should be `"device": "cuda"` not `"cpu"`
- Verify GPU is available: `torch.cuda.is_available()`

### Issue 4: "Model Not Found" Error

**Error:** `google/gemma-4-E4B not found`

**Note:** Gemma-4-E4B might not exist yet (as of April 2026). Alternative models:

```python
# In gemma_conversational_service.py line 75, change:
model_id = "google/gemma-2-9b-it"  # Stable alternative
# OR
model_id = "google/gemma-2b"  # Lightweight version
```

## 🧠 Natural Language Capabilities

Once Gemma is working, Dr. Myra can understand:

### Platform Questions:
- "How do I preprocess my data?"
- "What's the difference between LASSO and PCA?"
- "Walk me through the training pipeline"
- "Why do we need winsorization?"

### Clinical Questions:
- "What does a SLEDAI score of 12 indicate?"
- "Explain Anti-dsDNA antibodies"
- "What are common SLE biomarkers?"

### SHAP Interpretability:
- "Why did the model predict severe disease?"
- "Which features contributed most?"
- "Explain this SHAP waterfall plot"

### Data Queries:
- "Show me patients with high CRP"
- "Find records with missing complement values"
- "Generate analysis code"

## 📊 Verification Checklist

- [ ] Frontend console shows `🤖 Dr. Myra API Call`
- [ ] Backend logs show request to `/api/v1/ml/chat`
- [ ] Response shows `"model": "gemma-4-E4B"` (not "fallback-rules")
- [ ] Token count > 0 in response
- [ ] Natural language response (not template)
- [ ] Contextual answers based on conversation history
- [ ] Page-aware responses (knows current tab/workflow)

## 🎯 Expected Behavior

**Natural Language Input:**
```
User: "explain the platform to me"
```

**Gemma LLM Response:**
```
The USM Autoimmune ML Platform is a comprehensive end-to-end system for 
predicting SLE disease severity. The workflow consists of 8 main stages:

1. **Data Upload**: Import patient records from CSV/Excel files or extract 
   from PDFs using Qwen OCR...
2. **Labeling**: Assign severity labels (Mild/Moderate/Severe) using SLEDAI 
   scores...
[Natural, contextual explanation continues...]
```

**Fallback Response (hardcoded):**
```
I understand you're asking about "explain the platform to me".

Here are some things I can help with:
• Platform navigation and tutorials
• Data queries and analysis
...
```

## 🔬 Advanced: Custom Context Integration

Dr. Myra receives platform context automatically:

```javascript
// In ChatbotWidget.jsx
const context = {
  current_page: location.pathname,  // e.g., "/data-preparation"
  page_context: getContextualGreeting()  // e.g., "I see you're on Training page"
};
```

**Backend receives:**
```python
{
  "message": "How do I start training?",
  "context": {
    "current_page": "/training",
    "page_context": "I see you're on the Training page..."
  },
  "conversation_history": [...]
}
```

**Gemma uses this to generate page-aware responses!**

## 📝 Summary

✅ **Fixed:** API path mismatch  
✅ **Added:** Console debugging logs  
✅ **Verified:** Backend endpoint exists and is registered  
✅ **Ready:** Gemma LLM integration (requires model download)  

**To enable natural language:**
1. Ensure backend is running
2. Set `HUGGINGFACE_TOKEN` if using gated models
3. Let Gemma download on first use (~9GB)
4. Check console logs to verify `model: "gemma-4-E4B"`

**Current state:** Falls back to rules if Gemma not loaded, but path is now correct!
