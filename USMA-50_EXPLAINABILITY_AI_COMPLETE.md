# USMA-50: ML Explainability & Conversational AI - COMPLETE

## 🎯 **Smart Interface with SHAP + Gemma-4-E4B**

Comprehensive implementation of model interpretability and intelligent conversational AI for the SLE prediction platform.

---

## **🧠 Features Implemented**

### **1. SHAP Explainability** ✅
- **TreeExplainer** for tree-based models (XGBoost, LightGBM, RandomForest, CatBoost)
- **KernelExplainer** for other models (model-agnostic)
- Feature importance ranking (top K features)
- SHAP waterfall plots (visualizations)
- Natural language explanations
- Multi-class support (Mild/Moderate/Severe)
- Explainer caching for performance

### **2. Gemma-4-E4B Conversational AI** ✅
- **Medical assistant** specialized in SLE and autoimmune diseases
- **Prediction explanations** in natural language
- **Clinical question answering** about SLE
- **Context-aware responses** (patient data, SHAP values, predictions)
- **Conversation history** support
- **Fallback mode** (rule-based responses when model unavailable)
- **GPU acceleration** (float16 on GPU, float32 on CPU)
- **Lazy loading** (model loaded only when first used)

---

## **📡 API Endpoints**

### **SHAP Explainability**

#### **1. Explain Single Prediction**
**POST** `/api/v1/ml/explain`

Get SHAP feature importance for a specific patient prediction.

**Request:**
```json
{
  "model_name": "xgboost",
  "version": "v1",
  "patient_data": {
    "demographics_age": 35,
    "lab_results_ESR": 45,
    "lab_results_CRP": 12.5,
    "disease_activity_SLEDAI_score": 8.0,
    ...
  },
  "top_k": 10,
  "generate_plot": true
}
```

**Response:**
```json
{
  "model_name": "xgboost",
  "version": "v1",
  "predicted_class": "Moderate",
  "base_value": 0.3333,
  "top_features": [
    {
      "feature": "disease_activity_SLEDAI_score",
      "shap_value": 0.45,
      "feature_value": 8.0,
      "contribution": "positive",
      "importance": 0.45
    },
    {
      "feature": "demographics_age",
      "shap_value": 0.12,
      "feature_value": 35.0,
      "contribution": "positive",
      "importance": 0.12
    }
  ],
  "explanation_text": "The model's prediction for Moderate severity is primarily driven by:\n\n1. **Disease Activity SLEDAI Score** (value: 8.00) increases the prediction by 0.450\n2. **Demographics Age** (value: 35.00) increases the prediction by 0.120\n...",
  "waterfall_plot": "iVBORw0KGgoAAAANSUhEUgAA..." // Base64 encoded PNG
}
```

---

#### **2. Explain Ensemble Prediction**
**POST** `/api/v1/ml/explain/ensemble?version=v1`

Convenience endpoint for ensemble model explanations.

**Request:**
```json
{
  "demographics_age": 35,
  "lab_results_ESR": 45,
  ...
}
```

---

### **Gemma-4-E4B Conversational AI**

#### **1. Chat with Medical AI**
**POST** `/api/v1/ml/chat`

Interactive conversation with Gemma-4-E4B about SLE and predictions.

**Request:**
```json
{
  "message": "What does a SLEDAI score of 8 indicate?",
  "context": {
    "prediction": {
      "prediction": "Moderate",
      "confidence": 0.65
    }
  },
  "conversation_history": [
    {"role": "user", "content": "Previous question..."},
    {"role": "assistant", "content": "Previous answer..."}
  ],
  "temperature": 0.7
}
```

**Response:**
```json
{
  "response": "A SLEDAI score of 8 indicates moderate disease activity in Systemic Lupus Erythematosus...",
  "model": "gemma-4-E4B",
  "device": "cuda",
  "tokens_generated": 124
}
```

---

#### **2. Explain Prediction in Natural Language**
**POST** `/api/v1/ml/explain-prediction-nl`

Convert prediction + SHAP values into clinician-friendly explanation.

**Request:**
```json
{
  "prediction_result": {
    "prediction": "Moderate",
    "confidence": 0.65,
    "probabilities": {
      "Mild": 0.25,
      "Moderate": 0.65,
      "Severe": 0.10
    }
  },
  "shap_explanation": {
    "top_features": [
      {"feature": "SLEDAI_score", "shap_value": 0.45, "feature_value": 8.0}
    ]
  }
}
```

**Response:**
```json
{
  "response": "Clinical Interpretation:\n\nThe model predicts Moderate disease severity with 65% confidence. This assessment is primarily driven by the patient's SLEDAI score of 8, which is a key indicator of moderate disease activity...",
  "model": "gemma-4-E4B",
  "device": "cuda",
  "tokens_generated": 0
}
```

---

#### **3. Ask Clinical Questions**
**POST** `/api/v1/ml/ask-clinical`

Evidence-based answers about SLE manifestations and biomarkers.

**Request:**
```json
{
  "question": "What is the significance of elevated Anti-dsDNA antibodies?",
  "patient_context": {
    "lab_results_Anti_dsDNA": 1.8,
    "disease_activity_SLEDAI_score": 10
  }
}
```

**Response:**
```json
{
  "response": "Elevated Anti-dsDNA antibodies are highly specific for SLE and correlate with disease activity, particularly renal involvement...",
  "model": "gemma-4-E4B",
  "device": "cuda",
  "tokens_generated": 0
}
```

---

#### **4. Clear Explainer Cache**
**DELETE** `/api/v1/ml/chat/clear-cache`

Clear SHAP explainer cache after model updates.

---

## **🔧 Technical Implementation**

### **SHAP Service** (`app/services/shap_explainer_service.py`)

**Key Components:**
- `SHAPExplainerService` class
- Explainer creation (TreeExplainer for trees, KernelExplainer for others)
- Multi-class SHAP value extraction
- Waterfall plot generation (matplotlib → base64 PNG)
- Natural language explanation generation
- Explainer caching (in-memory)

**Features:**
- Automatic explainer selection based on model type
- Feature engineering pipeline integration
- Handles CV models (uses fold 0 for explanation)
- Top-K feature importance ranking

---

### **Gemma Service** (`app/services/gemma_conversational_service.py`)

**Key Components:**
- `GemmaConversationalService` class
- Lazy model loading (only when first used)
- System prompt with medical context
- Conversation history management
- Context formatting (predictions, SHAP, patient data)
- Fallback mode (rule-based when model unavailable)

**Medical System Prompt:**
```
You are a knowledgeable medical AI assistant specializing in SLE...
- Explain ML predictions for disease severity
- Interpret SHAP feature importance
- Provide evidence-based insights
- Help clinicians understand risk factors
- Always emphasize predictions are decision support, not diagnoses
```

**Optimizations:**
- GPU: float16 precision (faster)
- CPU: float32 precision (accurate)
- Device auto-detection
- Chat template support
- Temperature control (0.0-1.0)

---

## **📦 Dependencies**

**Already in `requirements.txt`:**
- ✅ `shap==0.44.0` - SHAP explainability
- ✅ `matplotlib==3.8.2` - Waterfall plots
- ✅ `transformers>=4.38.0` - Hugging Face models
- ✅ `torch>=2.4.0` - PyTorch for Gemma
- ✅ `accelerate>=0.25.0` - Model acceleration
- ✅ `bitsandbytes>=0.46.1` - Quantization

**New Model:**
- 🆕 `google/gemma-4-E4B` - Auto-downloaded from Hugging Face on first use

---

## **🧪 Testing**

### **Using Test Script**

```bash
# Test SHAP explanation
python test_explainability.py --test shap --model xgboost

# Test Gemma chat
python test_explainability.py --test chat --question "What is SLE?"

# Test prediction explanation
python test_explainability.py --test explain-prediction

# Test clinical Q&A
python test_explainability.py --test clinical

# Test all features
python test_explainability.py --test all
```

### **Using Swagger UI**

Navigate to `http://100.106.132.15:8001/docs`:
1. Authenticate with `s.nasrin` / `USM@22`
2. Find "ML Explainability & AI Assistant" section
3. Try endpoints:
   - POST `/api/v1/ml/explain` - SHAP explanation
   - POST `/api/v1/ml/chat` - Chat with Gemma
   - POST `/api/v1/ml/explain-prediction-nl` - Natural language explanation

---

## **📊 SHAP Visualizations**

### **Waterfall Plot**
Shows how each feature contributes to moving the prediction from the base value (expected value) to the final prediction.

**Saved Output:**
- `shap_waterfall_xgboost_v1.png`
- `shap_waterfall_ensemble_v1.png`

**Interpretation:**
- Red bars push prediction up (toward higher severity)
- Blue bars push prediction down (toward lower severity)
- Bar length shows magnitude of contribution

---

## **💬 Conversation Examples**

### **Example 1: Understanding Predictions**
```
User: Why did the model predict Moderate severity?

Gemma: The model predicted Moderate severity based on the patient's 
SLEDAI score of 8, which falls in the moderate range (5-12). This was 
the strongest contributing factor according to the SHAP analysis, with 
a contribution of +0.45. Other factors include the patient's age (35) 
and inflammatory markers (CRP/ESR ratio). The model has 65% confidence 
in this prediction.
```

### **Example 2: Clinical Questions**
```
User: What does elevated C3/C4 complement indicate in SLE?

Gemma: Complement proteins C3 and C4 are often DECREASED (not elevated) 
in active SLE due to consumption by immune complexes. Low C3 and C4 
levels correlate with disease activity and are particularly associated 
with lupus nephritis. If you're seeing elevated levels, this might 
indicate inactive disease or an acute phase response. The complement 
ratio (C3/C4) is used by the model as a derived feature for severity 
prediction.
```

### **Example 3: SHAP Interpretation**
```
User: What does a SHAP value of +0.45 mean for SLEDAI score?

Gemma: A SHAP value of +0.45 means that the SLEDAI score of 8 increased 
the model's prediction probability for Moderate severity by 0.45 units 
compared to the baseline expectation. This is a strong positive 
contribution - the highest among all features. Essentially, this 
SLEDAI score was the most important factor pushing the prediction 
toward Moderate rather than Mild or Severe.
```

---

## **⚠️ Important Notes**

### **Model Loading**
- Gemma-4-E4B is **~8GB** (float16 on GPU)
- First API call will take **30-60 seconds** to download and load model
- Subsequent calls are fast (model cached in memory)
- Consider pre-loading model on server startup if always needed

### **GPU Requirements**
- SHAP: Runs on CPU (fast enough for tree models)
- Gemma: Strongly recommended to use GPU for acceptable latency
  - GPU: ~500ms per response
  - CPU: ~10-30s per response

### **Production Deployment**
1. Ensure GPU available for Gemma (CUDA 12.1+)
2. Pre-download Gemma model:
   ```bash
   python -c "from transformers import AutoModelForCausalLM; AutoModelForCausalLM.from_pretrained('google/gemma-4-E4B')"
   ```
3. Monitor memory usage (Gemma + training models in memory)
4. Consider dedicated inference server if high traffic

---

## **🚀 Deployment Workflow**

### **1. Transfer Files via WinSCP**
```
app/main.py
app/api/endpoints/explainability.py
app/services/shap_explainer_service.py
app/services/gemma_conversational_service.py
requirements.txt
```

### **2. Install Dependencies** (if needed)
```bash
docker compose exec fastapi pip install --upgrade transformers accelerate
```

### **3. Restart Container**
```bash
docker compose restart fastapi
```

### **4. Test Endpoints**
```bash
# From local machine
python test_explainability.py --test all
```

---

## **📈 Use Cases**

### **1. Clinical Decision Support**
- Clinician sees prediction → clicks "Explain"
- SHAP shows: SLEDAI=8 is main driver (+0.45)
- Gemma explains: "Moderate activity, monitor renal function"

### **2. Patient Education**
- Clinician asks Gemma: "Explain this to a patient"
- Gemma generates patient-friendly explanation
- Reduces consultation time

### **3. Training & Research**
- Medical students ask: "What are ACR criteria?"
- Gemma provides evidence-based education
- Helps understand model behavior

### **4. Quality Assurance**
- Review predictions with low confidence
- SHAP identifies conflicting features
- Gemma suggests which features to double-check

---

## **🎯 USMA-50 Status: ✅ COMPLETE**

**Implemented:**
- ✅ SHAP explainability for all models
- ✅ Waterfall plot visualizations
- ✅ Gemma-4-E4B conversational AI
- ✅ Prediction explanation in natural language
- ✅ Clinical question answering
- ✅ Multi-class support (Mild/Moderate/Severe)
- ✅ Context-aware conversations
- ✅ GPU acceleration
- ✅ Fallback mode for robustness
- ✅ API endpoints with authentication
- ✅ Test scripts
- ✅ Comprehensive documentation

**What We Built:**
- 🔍 **Transparent ML** - Understand WHY the model made a prediction
- 🧠 **Intelligent Interface** - Ask questions, get expert answers
- 🏥 **Clinical Context** - Medical assistant specialized in SLE
- 📊 **Visual Explanations** - Waterfall plots show feature contributions
- 💬 **Natural Language** - Convert SHAP values to human-readable text

---

## **Next Steps (Optional Enhancements)**

- ⬜ Add SHAP force plots (interactive HTML)
- ⬜ Batch SHAP explanations
- ⬜ Conversation history storage (database)
- ⬜ Fine-tune Gemma on SLE literature
- ⬜ Add citation links to clinical evidence
- ⬜ SHAP summary plots for global feature importance
- ⬜ Integration with frontend (React chat component)

---

**Ready for Smart ML Platform! 🎉**

The platform now combines:
1. **Accurate predictions** (ensemble training)
2. **Transparent explanations** (SHAP)
3. **Intelligent guidance** (Gemma-4-E4B)

This creates a complete clinical decision support system that clinicians can **trust** and **understand**.
