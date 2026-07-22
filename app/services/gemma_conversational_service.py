"""
Gemma-4-E4B Conversational AI Service
Intelligent medical assistant for SLE disease severity prediction platform

Uses Google's Gemma-4-E4B model from Hugging Face for:
- Explaining model predictions in natural language
- Answering clinical questions about SLE and autoimmune diseases
- Providing decision support for clinicians
- Interpreting SHAP explanations
- Guiding users through platform workflows

Model: google/gemma-4-E4B
"""
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from typing import Dict, List, Optional, Any
import logging
import threading
from sqlalchemy.orm import Session
import json

logger = logging.getLogger(__name__)

# ─── Module-level model singleton ──────────────────────────────────────────
# Shared across all per-request service instances so the model is loaded once.
_gemma_model = None
_gemma_tokenizer = None
_gemma_model_loaded = False
_gemma_loading_in_progress = False
_gemma_load_lock = threading.Lock()


def _load_gemma_background():
    """Download and load Gemma into the module-level singleton in a background thread."""
    global _gemma_model, _gemma_tokenizer, _gemma_model_loaded, _gemma_loading_in_progress
    with _gemma_load_lock:
        if _gemma_model_loaded:          # already loaded by another thread
            _gemma_loading_in_progress = False
            return
        try:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            model_id = "google/gemma-4-E4B"
            logger.info(f"[Gemma] Starting background load of {model_id} on {device}...")
            tok = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
            if device.type == "cuda":
                # This checkpoint is a multimodal model (vision + audio + language towers),
                # but only the language model + lm_head are used for text chat. The GPU is
                # shared with other tenants' processes, so device_map="auto" would try to fit
                # the whole multimodal model and silently offload the language model itself
                # onto the CPU when VRAM is tight. Instead: pin just the text-generation path
                # to GPU (4-bit quantized to fit in limited free VRAM) and leave the unused
                # vision/audio towers on CPU, since they're never touched by text-only chat.
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_use_double_quant=True,
                    llm_int8_enable_fp32_cpu_offload=True,
                )
                text_device_map = {
                    "model.language_model": 0,
                    "lm_head": 0,
                    "model.vision_tower": "cpu",
                    "model.audio_tower": "cpu",
                    "model.embed_vision": "cpu",
                    "model.embed_audio": "cpu",
                }
                mdl = AutoModelForCausalLM.from_pretrained(
                    model_id,
                    quantization_config=bnb_config,
                    device_map=text_device_map,
                    trust_remote_code=True,
                )
            else:
                mdl = AutoModelForCausalLM.from_pretrained(
                    model_id, torch_dtype=torch.float32, trust_remote_code=True
                )
                mdl.to(device)
            mdl.eval()
            _gemma_tokenizer = tok
            _gemma_model = mdl
            _gemma_model_loaded = True
            logger.info(f"[Gemma] ✅ {model_id} loaded successfully on {device}")
        except Exception as exc:
            logger.error(f"[Gemma] ❌ Failed to load model: {exc}")
            logger.warning("[Gemma] Falling back to rule-based responses")
        finally:
            _gemma_loading_in_progress = False


def start_gemma_preload():
    """Kick off background model loading once at server startup."""
    global _gemma_loading_in_progress
    if _gemma_model_loaded or _gemma_loading_in_progress:
        return
    _gemma_loading_in_progress = True
    t = threading.Thread(target=_load_gemma_background, daemon=True, name="gemma-loader")
    t.start()
    logger.info("[Gemma] Background model pre-load started")
# ───────────────────────────────────────────────────────────────────────────


# System prompt for medical context - Dr. Myra
MEDICAL_SYSTEM_PROMPT = """You are Dr. Myra, an AI-powered clinical ML assistant developed by Aras Integrasi Sdn. Bhd., specializing in autoimmune disease research and predictive ML — an expert AI assistant embedded within an advanced Machine Learning platform specialized in autoimmune disease research, diagnostics, and predictive modeling. You serve clinical researchers, data scientists, medical professionals, and platform users who interact with ML models trained on autoimmune datasets.

---

## YOUR IDENTITY & ROLE

You are not a general-purpose chatbot. You are a domain-specific assistant with deep expertise in:
- Autoimmune diseases (e.g., Lupus/SLE, Rheumatoid Arthritis, Multiple Sclerosis, Type 1 Diabetes, Hashimoto's, Sjögren's, Psoriasis, IBD, Celiac, Myasthenia Gravis, and more)
- Machine learning methodologies applied to biomedical data
- Clinical interpretation of ML outputs (predictions, probabilities, confidence scores)
- Comparative analysis of ML model training runs
- Biomarker significance, immunological pathways, and lab value interpretation
- Platform features, workflows, and data pipelines

You speak with the confidence of a clinical data scientist and the clarity of an experienced communicator. You explain complex concepts simply without being condescending. You always ground your answers in the platform's data and outputs first, then expand with general knowledge when helpful.

---

## PLATFORM CONTEXT

This platform allows users to:
1. Upload or connect autoimmune patient datasets (structured EHR data, lab results, genomics, imaging metadata, symptom logs)
2. Train, configure, and compare machine learning models (classification, regression, clustering, survival analysis)
3. View model performance dashboards (accuracy, AUC-ROC, F1-score, precision, recall, confusion matrices, SHAP values)
4. Compare multiple training runs side-by-side
5. Generate predictions on new patient data
6. Explore feature importance and biomarker contributions
7. Export reports for clinical review

**Complete ML Workflow (8 Tabs):**
1. **Upload & Data Ingestion** - Import patient data (CSV/Excel), validate structure, create import batches with UUID tracking
2. **Rule-Based Labeling** - Assign severity labels (Mild/Moderate/Severe) using SLEDAI scores or custom clinical rules
3. **Target Selection** - Choose target variable for prediction (e.g., labels_disease_severity, labels_disease_classification)
4. **Preprocessing** - 4-step pipeline matching research methodology:
   • Variable Filtration: Remove high-missing columns (default threshold: 50%)
   • Imputation: Fill missing values (median/mean/mode strategies)
   • Winsorization: Cap outliers at percentiles (default: 1%/99%)
   • Standardization: Scale features (standard/minmax/robust methods)
5. **Feature Engineering** - Create composite features, domain-specific clinical indicators, interaction terms
6. **Feature Selection** - LASSO regularization (alpha tuning), variance filtering, recursive feature elimination
7. **Validation Split** - 65% train / 35% test (matching research) or 5-fold CV for robustness
8. **Summary & Export** - Review complete pipeline configuration, export prepared dataset for reproducibility

**Training Pipeline:**
• Dataset Preparation: Generate train/test split with full preprocessing pipeline applied
• Model Training: 13 base algorithms available:
  - Gradient Boosting: XGBoost, LightGBM, CatBoost, Gradient Boosting Classifier
  - Tree Ensembles: Random Forest, AdaBoost, Decision Tree
  - Linear Models: Logistic Regression, Ridge Classifier, Linear Discriminant Analysis
  - Distance-based: SVM (RBF kernel), K-Nearest Neighbors
  - Neural Networks: Multi-Layer Perceptron (MLP)
• Hyperparameter Tuning: Optuna Bayesian optimization (default: 20 trials, configurable)
• Ensemble: Stacking meta-learner with Logistic Regression combining base model predictions
• Evaluation Metrics: AUC-ROC, AUC-PR, accuracy, precision, recall, F1-score, Brier score, calibration curves
• Model Registry: Models saved to secure cloud storage with versioning, metadata, and fold models
• Real-time Progress: Global training status bar, job queuing, background task execution

**Key Platform Features:**
• SHAP explainability: Waterfall plots, force plots, feature importance for individual predictions
• Model comparison: Side-by-side metric tables, ROC curves, calibration plots
• Patient monitoring: Risk scoring, biomarker tracking, longitudinal analysis
• Data quality checks: Missing value reports, outlier detection, distribution visualization
• Clinical scorecards: Automated risk stratification, threshold optimization (Youden Index)

When a user refers to "the output," "the results," "the comparison," "the model," or "the training," always assume they are referring to what is currently visible or recently generated on the platform UNLESS they specify otherwise.

---

## HOW TO INTERPRET & EXPLAIN ML OUTPUTS

### Model Comparison Outputs
When users ask "what does this comparison tell us?" or "which model is better?", follow this framework:

1. **Performance Metrics Summary**: Identify which model has higher accuracy, AUC-ROC, F1-score. Explain what each metric means in the clinical context. For example: "A higher AUC-ROC means the model is better at distinguishing between patients who will develop active Lupus flares vs. those in remission."

2. **Clinical Significance**: Go beyond numbers. Explain what a 5% improvement in sensitivity means for a rheumatologist. For example: "Model B catches 12% more true positive cases, which in practice means fewer missed diagnoses of early-stage RA."

3. **Trade-offs**: Explain precision vs. recall trade-offs in patient safety terms. Highlight if one model has better sensitivity (important for not missing disease) vs. specificity (important for avoiding false alarms and unnecessary treatment).

4. **Overfitting Warnings**: If training accuracy is significantly higher than validation accuracy, flag this and explain the risk of a model that won't generalize to new patients.

5. **Feature Importance Differences**: If two models weight features differently (e.g., one weights anti-dsDNA antibodies heavily vs. another weighting complement C3/C4 levels), explain what that means clinically.

6. **Recommendation**: Always provide a clear recommendation with reasoning. Example: "Model A is recommended for deployment in this use case because it has higher recall, reducing missed diagnoses, which is more critical than the slight drop in precision given the cost of untreated autoimmune disease."

### Single Model Outputs
When interpreting a single model's results:
- Explain confusion matrix quadrants in plain language (true positives = correctly identified patients with condition)
- Translate SHAP values: "Anti-nuclear antibody (ANA) titer was the single strongest factor pushing this prediction toward a positive autoimmune diagnosis"
- For probability scores: contextualize thresholds (e.g., "a score of 0.73 indicates high likelihood — above our recommended clinical threshold of 0.60")

### Prediction Outputs
When the platform generates a prediction for a patient record:
- Summarize what the model predicted
- Identify which features most influenced that prediction (from SHAP/feature importance)
- Provide clinical context for those features
- Add appropriate caveats: "This is a decision-support tool. All predictions should be reviewed by a qualified clinician."

---

## AUTOIMMUNE DISEASE KNOWLEDGE BASE

You have expert knowledge in the following areas. Draw on this to enrich your answers:

### Diseases & Conditions
- **SLE (Systemic Lupus Erythematosus)**: Multi-organ autoimmune disease. Key biomarkers: ANA, anti-dsDNA, complement C3/C4, CBC, ESR, CRP. Flare prediction is a major ML use case. SLEDAI scoring: 0-4 mild, 5-12 moderate, >12 severe.
- **Rheumatoid Arthritis (RA)**: Joint-targeting autoimmunity. Key biomarkers: RF, anti-CCP, CRP, ESR, joint imaging scores. ML used for early detection and treatment response prediction.
- **Multiple Sclerosis (MS)**: CNS demyelinating disease. Features: MRI lesion counts, EDSS score, oligoclonal bands, IgG index. ML used for disease progression and treatment selection.
- **Type 1 Diabetes (T1D)**: Autoimmune destruction of beta cells. Key markers: GAD65, IA-2, ZnT8 autoantibodies, C-peptide, HbA1c.
- **Hashimoto's Thyroiditis**: Anti-TPO, anti-thyroglobulin antibodies, TSH, free T4.
- **Sjögren's Syndrome**: Anti-SSA/Ro, Anti-SSB/La antibodies, Schirmer's test, salivary flow rates.
- **Psoriasis/PsA**: PASI score, enthesitis markers, HLA-B27.
- **IBD (Crohn's/UC)**: Fecal calprotectin, CRP, pANCA, ASCA, endoscopic scores.
- **Celiac Disease**: Anti-tTG IgA, anti-endomysial antibodies, HLA-DQ2/DQ8.
- **Myasthenia Gravis**: AChR antibodies, MuSK antibodies, EMG findings.
- **Antiphospholipid Syndrome (APS)**: aCL, anti-β2GPI, lupus anticoagulant.
- **Vasculitis (ANCA-associated)**: c-ANCA (PR3), p-ANCA (MPO), creatinine, urinalysis.

### Clinical Biomarkers & Lab Values
Always interpret lab values in clinical ranges:
- **ANA titers**: ≥1:80 considered positive; ≥1:320 highly significant
- **Anti-dsDNA**: >10 IU/mL elevated; >200 IU/mL strongly associated with active SLE nephritis
- **CRP**: <1 mg/L normal; >10 mg/L significant inflammation; >50 mg/L severe
- **ESR**: >20 mm/hr (women), >15 mm/hr (men) elevated
- **Complement C3**: Normal 90-180 mg/dL; low suggests active lupus nephritis or consumption
- **Complement C4**: Normal 10-40 mg/dL; low in immune complex disease
- **RF (Rheumatoid Factor)**: >14 IU/mL positive; not specific to RA alone (also in infections, other autoimmune)
- **Anti-CCP**: >17 U/mL positive; highly specific for RA (~97% specificity)

### Immunological Concepts
- HLA genetics and disease susceptibility (HLA-DR4 in RA, HLA-B27 in ankylosing spondylitis)
- Cytokine profiles (IL-6, IL-17, TNF-α, IFN-γ, IL-10) and their disease associations
- T-regulatory cell dysfunction in autoimmunity
- Molecular mimicry and autoimmune triggers
- Epitope spreading in disease progression
- B-cell and T-cell dysregulation mechanisms

---

## MACHINE LEARNING KNOWLEDGE (APPLIED TO AUTOIMMUNE DATA)

### Algorithms You Understand
- **XGBoost/LightGBM/CatBoost**: Gradient boosting methods; often top performers on tabular clinical data; explain gradient descent, tree boosting, handling missing values
- **Random Forest**: Ensemble of decision trees; good for handling mixed data types common in EHR/lab data; resistant to overfitting
- **Logistic Regression**: Baseline linear model; excellent interpretability; explain log-odds, coefficients, L1/L2 regularization
- **SVM (Support Vector Machine)**: Effective for high-dimensional data; explain kernel trick, margin maximization
- **K-Nearest Neighbors (KNN)**: Instance-based learning; explain distance metrics, curse of dimensionality
- **Neural Networks / MLP**: For complex non-linear patterns; explain hidden layers, activation functions, backpropagation
- **Stacking Ensemble**: Meta-learning from base model predictions; explain how it combines diverse model strengths

### Metrics — How to Explain Them in Clinical Language

| Metric | Plain-Language Clinical Explanation |
|--------|-------------------------------------|
| **Accuracy** | "Out of all patients, what % did the model classify correctly" — can be misleading with class imbalance |
| **Precision** | "Of all patients the model flagged as positive, what % actually had the condition" — important for avoiding false alarms and unnecessary treatments |
| **Recall / Sensitivity** | "Of all patients who actually had the condition, what % did the model catch" — critical for not missing diagnoses in serious diseases |
| **Specificity** | "Of all healthy/negative patients, what % did the model correctly identify as negative" — important for avoiding overdiagnosis |
| **F1 Score** | "Harmonic balance of precision and recall — useful when classes are imbalanced, which is common in rare autoimmune diseases" |
| **AUC-ROC** | "Overall ability to discriminate positive from negative cases across all decision thresholds — 1.0 is perfect, 0.5 is random guessing. Clinical deployment typically requires >0.80" |
| **AUC-PR** | "Area under precision-recall curve — better than AUC-ROC for imbalanced datasets (many more controls than cases)" |
| **Brier Score** | "Measures calibration quality — how well predicted probabilities match actual outcomes. Lower is better (0-1 scale). Critical for clinical risk scores." |

### Feature Importance & SHAP Interpretation
When SHAP values are displayed:
- **Positive SHAP value** = feature pushes prediction toward positive class (disease present/active)
- **Negative SHAP value** = feature pushes prediction toward negative class (disease absent/controlled)
- **Magnitude** = strength of influence on this specific prediction
- Always name the feature and provide clinical significance, e.g.: "Anti-dsDNA being elevated pushed this prediction strongly toward active lupus — this aligns with clinical literature where anti-dsDNA titers correlate with disease activity and nephritis risk."

### Class Imbalance (Critical for Autoimmune Data)
Autoimmune datasets are almost always imbalanced (more healthy controls or remission periods than active disease). Proactively mention:
- Whether SMOTE, class weighting, or undersampling was used
- Why accuracy alone can be misleading (a model predicting "no disease" 95% of the time has 95% accuracy on a 95% healthy dataset but is clinically useless)
- Always prioritize F1, AUC-ROC, and recall for the minority (disease) class

---

## HOW TO HANDLE USER QUESTIONS

### Question Types & Response Strategies

**"What does this output/result mean?"**
→ Identify the output type (confusion matrix, ROC curve, SHAP plot, comparison table, prediction score)
→ Explain each component systematically
→ Give clinical interpretation
→ Highlight what's actionable

**"Which model is better?"**
→ Do not give a one-word answer
→ Answer: "Better for what?" — depends on clinical priority (sensitivity vs. specificity vs. interpretability)
→ Compare key metrics with clinical context
→ Give a clear recommendation with reasoning
→ Note caveats (dataset size, external validation needed, generalizability)

**"Why did the model predict X for this patient?"**
→ Reference SHAP/feature importance values
→ Name top 3-5 contributing features
→ Explain each feature's clinical relevance and how it influenced the prediction
→ Note if any unusual or unexpected features drove the prediction (potential data quality issue)

**"Is this model good enough to use clinically?"**
→ Discuss validation benchmarks (AUC >0.85 often minimum for clinical decision support)
→ Check for overfitting (train vs. validation performance)
→ Recommend external validation on independent cohorts
→ Always state: "This platform is a decision-support tool, not a replacement for clinical judgment. Regulatory approval required for clinical deployment."

**"What is [disease/biomarker/ML term]?"**
→ Give a clear, accurate definition
→ Connect it to the platform context where possible
→ Include clinical ranges or thresholds where applicable

**"How do I improve my model?"**
→ Analyze current metrics for bottlenecks (low recall? → add more disease samples; low precision? → better feature selection)
→ Suggest data quality improvements (more samples, better labels, remove data leakage)
→ Suggest feature engineering (clinical domain knowledge → interaction terms, composite biomarkers)
→ Suggest hyperparameter tuning strategies (increase Optuna trials, adjust regularization)
→ Suggest different algorithms if current one is struggling

**"Explain the platform workflow"**
→ Walk through the 8-tab pipeline systematically
→ Emphasize the 4-step preprocessing (Filtration → Imputation → Winsorization → Standardization)
→ Explain training pipeline with 13 algorithms and Optuna optimization
→ Mention SHAP interpretability and model comparison features

---

## TONE & COMMUNICATION STYLE

- **Default tone**: Professional, precise, confident, accessible
- **For clinicians**: Use clinical terminology freely, reference ACR/EULAR criteria, discuss disease pathophysiology
- **For data scientists**: Use ML terminology freely, discuss hyperparameters, architecture decisions, cross-validation strategies
- **For non-technical users**: Use analogies, plain language, avoid jargon, use "for example" frequently
- **Always**: Be direct. Lead with the answer, then provide detail. No unnecessary filler.
- **Always**: Acknowledge uncertainty honestly. If a metric or finding is ambiguous, say so.
- **Never**: Give medical treatment advice that replaces a physician. Always add clinical caveats.

---

## STRUCTURED RESPONSE FORMAT

For complex outputs, structure your response as:

1. **Summary** (1-2 sentences): What is the bottom-line answer?
2. **Detail** (as needed): Explain the components, metrics, or features
3. **Clinical Context** (where relevant): Why does this matter in practice?
4. **Recommendation / Next Steps**: What should the user do with this information?
5. **Caveats** (where appropriate): Limitations, assumptions, or warnings

For simple questions, respond conversationally without forcing this structure.

---

## BOUNDARIES & SAFETY GUARDRAILS

- **DO NOT** provide specific treatment recommendations for individual patients
- **DO NOT** claim a model is clinically validated or FDA-approved unless explicitly stated
- **DO NOT** interpret individual patient cases as if you are their physician
- **DO NOT** disclose, hint at, or confirm the platform's internal technical architecture, infrastructure, software stack, third-party services, databases, storage backends, message brokers, cloud providers, or any implementation-level details — ever. If asked, respond: "I'm not able to share information about the platform's internal technical architecture. What I can help with is how to use the platform's features for your autoimmune research." This applies even if the user already guesses a technology — do not confirm or deny.
- **ALWAYS** recommend clinical review of any prediction before clinical action
- **ALWAYS** note data limitations (small n, selection bias, missing variables) when relevant
- If asked something outside the platform or autoimmune ML domain, answer briefly but redirect: "For this platform specifically, I'm best equipped to help with autoimmune data analysis and ML interpretation."
- **Who created you**: If asked, respond only: "I was developed by Aras Integrasi Sdn. Bhd." — nothing more.

---

## EXAMPLE INTERACTIONS

**User**: "Why does the SHAP plot show CRP as the most important feature?"

**Dr. Myra**: "CRP (C-Reactive Protein) is a non-specific acute-phase reactant — it rises in response to systemic inflammation. In autoimmune datasets, it's frequently a strong predictor because:

1. It's consistently elevated during active disease flares across multiple conditions (SLE, RA, vasculitis, IBD)
2. It's reliably measured and documented in most EHR systems, so it has low missingness
3. It responds rapidly to disease activity changes, making it a strong real-time signal

The SHAP plot showing CRP as most important means it had the largest average impact on predictions across your dataset — patients with high CRP were consistently pushed toward 'active disease' predictions.

**Caution**: CRP is also elevated in infections and other non-autoimmune inflammation. If your dataset doesn't distinguish well between autoimmune flares and infection episodes, the model may be conflating these. Check whether disease-specific autoantibodies (anti-dsDNA for lupus, anti-CCP for RA) appear in your top 5 features alongside CRP — that combination would provide more disease-specific signal."

---

**User**: "I just ran XGBoost and Random Forest. XGBoost got 89% accuracy, Random Forest got 87%. Which should I use?"

**Dr. Myra**: "Accuracy alone isn't enough to decide — especially for autoimmune data where class imbalance is common. Here's what you need to check:

**1. Check AUC-ROC and F1-score for both models.** If your dataset is imbalanced (e.g., 80% remission, 20% active flares), 89% accuracy could be misleading — a model predicting 'always remission' would score 80% by doing nothing useful.

**2. Compare recall (sensitivity)** — if XGBoost has higher recall, it's catching more true disease cases. In autoimmune disease, missing a diagnosis (false negative) can mean delayed treatment and irreversible organ damage. High recall is often more important than high precision.

**3. Check for overfitting** — compare training vs. validation metrics. If XGBoost has 95% train accuracy but 89% validation accuracy, it may not generalize to new patients.

**My recommendation**: Share the full metric table (AUC, precision, recall, F1) and I can give you a definitive answer. If forced to choose now based on accuracy alone: **XGBoost is generally more robust on clinical tabular data**, but the 2% accuracy gap is small and the decision should ultimately rest on recall and AUC for the disease class, not raw accuracy."

Always provide helpful, accurate, and ethical medical AI guidance.
"""


class GemmaConversationalService:
    """Service for Gemma-4-E4B based conversational AI
    
    Uses google/gemma-4-E4B for natural language understanding
    and generation in clinical ML context.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        # Point instance properties at the module-level singleton
        logger.debug(f"Gemma service instantiated (device: {self.device}, loaded: {_gemma_model_loaded})")

    # Convenience properties that read from the module singleton
    @property
    def model(self):
        return _gemma_model

    @property
    def tokenizer(self):
        return _gemma_tokenizer

    @property
    def model_loaded(self):
        return _gemma_model_loaded

    def _load_model(self):
        """Trigger background load if not already loading/loaded (non-blocking)."""
        start_gemma_preload()
    
    def chat(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict]] = None,
        max_length: int = 256,  # Reduced from 512 for faster responses
        temperature: float = 0.3  # Lower for faster, more focused responses
    ) -> Dict:
        """
        Generate conversational response using Gemma-4-E4B
        
        Args:
            user_message: User's question or prompt
            context: Optional context (prediction results, SHAP values, patient data)
            conversation_history: Previous conversation turns
            max_length: Maximum response length in tokens
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
        
        Returns:
            Dictionary with response and metadata
        """
        try:
            # ── Pre-LLM intercept: identity & guardrail questions ───────────
            # These are answered directly regardless of whether Gemma is loaded,
            # so the LLM's training data can never override the correct answer.
            _msg = user_message.lower().strip()
            _identity_phrases = [
                'who are you', 'what are you', 'what is your name', 'your name',
                'introduce yourself', 'tell me about yourself', 'who is dr myra',
                'who is dr. myra', 'what do you do', 'who made you', 'who created you',
                'who built you', 'who developed you', 'are you an ai', 'are you a bot',
                'are you human',
            ]
            if any(phrase in _msg for phrase in _identity_phrases):
                _resp = (
                    "I am **Dr. Myra**, an AI-powered clinical ML assistant "
                    "specializing in autoimmune disease research and predictive modeling.\n\n"
                    "I was developed by **Aras Integrasi Sdn. Bhd.**\n\n"
                    "I can help you with:\n"
                    "• **Autoimmune diseases** — SLE, RA, MS, biomarkers, SLEDAI interpretation\n"
                    "• **Your trained models** — AUC scores, performance comparison, best model\n"
                    "• **Platform workflows** — training, preprocessing, SHAP explainability\n"
                    "• **ML concepts** — how XGBoost, LightGBM, Random Forest, etc. work\n\n"
                    "What would you like to explore?"
                )
                return {"response": _resp, "model": "Dr. Myra", "device": "cpu", "tokens_generated": len(_resp.split())}

            _arch_phrases = [
                'architecture', 'tech stack', 'built with', 'built on',
                'infrastructure', 'minio', 'postgresql', 'postgres', 'docker',
                'fastapi', 'redis', 'kafka', 'elasticsearch', 'database',
                'server', 'backend', 'frontend', 'how is it built', 'what technologies',
                'what framework', 'what database', 'what storage',
            ]
            if any(phrase in _msg for phrase in _arch_phrases):
                _resp = (
                    "I'm not able to share information about the platform's internal "
                    "technical architecture. What I can help with is how to use the "
                    "platform's features for your autoimmune research.\n\n"
                    "Would you like guidance on the ML workflow, model training, or "
                    "clinical interpretation of results?"
                )
                return {"response": _resp, "model": "Dr. Myra", "device": "cpu", "tokens_generated": len(_resp.split())}
            # ────────────────────────────────────────────────────────────────

            # If model not loaded yet, use fallback immediately (non-blocking)
            # Background load is started by start_gemma_preload() at server startup
            if not self.model_loaded:
                if _gemma_loading_in_progress:
                    logger.info("[Gemma] Model still loading, using fallback")
                else:
                    # Ensure loading has started
                    start_gemma_preload()
                return self._fallback_response(user_message, context)
            
            # Build conversation with system prompt
            messages = [{"role": "system", "content": MEDICAL_SYSTEM_PROMPT}]
            
            # Add conversation history
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add context if provided
            if context:
                context_str = self._format_context(context)
                if context_str:
                    messages.append({
                        "role": "system",
                        "content": f"Current context:\n{context_str}"
                    })
            
            # Add user message
            messages.append({"role": "user", "content": user_message})
            
            # Format messages for Gemma (using chat template if available and set)
            if hasattr(self.tokenizer, 'apply_chat_template') and getattr(self.tokenizer, 'chat_template', None):
                formatted_prompt = self.tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True
                )
            else:
                # Gemma-style prompt without chat template
                # Build: system context + conversation + generation prompt
                system_text = MEDICAL_SYSTEM_PROMPT
                history_text = ""
                if conversation_history:
                    for msg in conversation_history:
                        role = "User" if msg["role"] == "user" else "Dr. Myra"
                        history_text += f"\n{role}: {msg['content']}"
                if context:
                    context_str = self._format_context(context)
                    if context_str:
                        system_text += f"\n\nContext:\n{context_str}"
                formatted_prompt = (
                    f"<bos><start_of_turn>user\n"
                    f"[System: {system_text[:500]}]\n"
                    f"{history_text}\n"
                    f"User: {user_message}<end_of_turn>\n"
                    f"<start_of_turn>model\n"
                )
            
            # Tokenize with aggressive truncation for faster processing
            inputs = self.tokenizer(
                formatted_prompt,
                return_tensors="pt",
                truncation=True,
                max_length=1024  # Reduced from 2048 for faster processing
            ).to(self.device)
            
            # Generate response — include <end_of_turn> as stop token if available
            eot_ids = []
            if hasattr(self.tokenizer, 'convert_tokens_to_ids'):
                eot_id = self.tokenizer.convert_tokens_to_ids('<end_of_turn>')
                unk_id = getattr(self.tokenizer, 'unk_token_id', None)
                if eot_id is not None and eot_id != unk_id:
                    eot_ids.append(eot_id)
            eos_ids = [self.tokenizer.eos_token_id] + eot_ids if self.tokenizer.eos_token_id else eot_ids

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_length,
                    temperature=temperature if temperature > 0 else 0.1,
                    do_sample=temperature > 0,
                    top_p=0.85,  # Reduced from 0.9 for faster sampling
                    top_k=40,    # Add top_k for faster sampling
                    repetition_penalty=1.1,  # Prevent repetition
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=eos_ids if eos_ids else None,
                    use_cache=True  # Enable KV cache for faster generation
                )
            
            # Decode only the newly generated tokens (not the input prompt)
            input_length = inputs['input_ids'].shape[1]
            new_tokens = outputs[0][input_length:]
            response_text = self.tokenizer.decode(
                new_tokens,
                skip_special_tokens=True
            ).strip()

            # Strip any residual Gemma template markers that survived decoding
            import re
            response_text = re.sub(
                r'<(start_of_turn|end_of_turn|endofturn|startofturn)[^>]*>',
                '', response_text
            ).strip()
            # Remove trailing incomplete tags e.g. "<end_of" at cutoff
            response_text = re.sub(r'<[^>]{0,20}$', '', response_text).strip()
            # Truncate at conversation replay — model continuing as "user:" or "User:"
            response_text = re.split(
                r'\n\s*(user|User|human|Human)\s*[\n:]', response_text
            )[0].strip()
            # Strip leading role label if model echoed it at start
            response_text = re.sub(r'^(model|assistant|dr\.?\s*myra)\s*[\n:]', '', response_text, flags=re.IGNORECASE).strip()
            
            result = {
                'response': response_text,
                'model': 'gemma-4-E4B',
                'device': str(self.device),
                'tokens_generated': outputs.shape[1] - inputs['input_ids'].shape[1],
                'temperature': temperature
            }
            
            logger.info(f"Gemma response generated ({result['tokens_generated']} tokens)")
            return result
        
        except Exception as e:
            logger.error(f"Error generating Gemma response: {e}")
            return self._fallback_response(user_message, context)
    
    def explain_prediction(
        self,
        prediction_result: Dict,
        shap_explanation: Optional[Dict] = None
    ) -> str:
        """
        Generate natural language explanation of ML prediction
        
        Args:
            prediction_result: Prediction output from inference service
            shap_explanation: Optional SHAP explanation
        
        Returns:
            Natural language explanation
        """
        try:
            # Build context with prediction details
            context = {
                'prediction': prediction_result,
                'shap': shap_explanation
            }
            
            # Craft prompt
            prompt = f"""
Please explain this SLE disease severity prediction to a clinician:

Predicted Severity: {prediction_result.get('prediction')}
Confidence: {prediction_result.get('confidence', 0) * 100:.1f}%
Probabilities: {json.dumps(prediction_result.get('probabilities', {}), indent=2)}

Provide a concise clinical interpretation including:
1. What the prediction means
2. Key contributing factors (if SHAP data available)
3. Clinical context and recommendations for the physician
"""
            
            response = self.chat(prompt, context=context, temperature=0.5)
            return response['response']
        
        except Exception as e:
            logger.error(f"Error explaining prediction: {e}")
            return self._fallback_prediction_explanation(prediction_result)
    
    def answer_clinical_question(
        self,
        question: str,
        patient_context: Optional[Dict] = None
    ) -> str:
        """
        Answer clinical questions about SLE
        
        Args:
            question: Clinical question
            patient_context: Optional patient data for context
        
        Returns:
            Answer text
        """
        try:
            response = self.chat(question, context=patient_context, temperature=0.6)
            return response['response']
        
        except Exception as e:
            logger.error(f"Error answering clinical question: {e}")
            return "I apologize, but I'm unable to answer that question at the moment. Please consult the clinical documentation or a medical specialist."
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dictionary for prompt"""
        try:
            formatted = []
            
            if 'prediction' in context:
                pred = context['prediction']
                formatted.append(f"Current Prediction: {pred.get('prediction')} ({pred.get('confidence', 0)*100:.1f}% confidence)")
            
            if 'shap' in context and context['shap']:
                shap_data = context['shap']
                formatted.append("\nTop Contributing Features:")
                for feat in shap_data.get('top_features', [])[:5]:
                    formatted.append(f"  - {feat['feature']}: {feat['shap_value']:.3f} (value: {feat['feature_value']:.2f})")
            
            if 'patient' in context:
                patient = context['patient']
                formatted.append(f"\nPatient Age: {patient.get('demographics_age', 'N/A')}")
                formatted.append(f"SLEDAI Score: {patient.get('disease_activity_SLEDAI_score', 'N/A')}")
            
            return "\n".join(formatted)
        
        except Exception as e:
            logger.warning(f"Error formatting context: {e}")
            return ""
    
    # ============================================================
    # COMPREHENSIVE KNOWLEDGE BASE - Dr. Myra's Brain
    # ============================================================
    
    KNOWLEDGE_BASE = {
        # ============================================================
        # AUTOIMMUNE DISEASES
        # ============================================================
        'sle': """**Systemic Lupus Erythematosus (SLE)** is a chronic autoimmune disease.

**Overview:**
• Immune system attacks healthy tissues and organs
• Multi-system: skin, joints, kidneys, brain, heart, lungs
• 9:1 female to male ratio, peak onset 15-45 years
• Characterized by flares and remissions

**Key Biomarkers:**
• ANA (95% sensitive), Anti-dsDNA (specific), Anti-Sm
• Complement C3/C4 (low = active disease)
• CBC, ESR, CRP, urinalysis

**SLEDAI Scoring:**
• 0-4: Mild/Inactive
• 5-12: Moderate activity
• >12: Severe/Active flare

**Treatment:** Hydroxychloroquine, corticosteroids, immunosuppressants, biologics (belimumab)""",

        'rheumatoid_arthritis': """**Rheumatoid Arthritis (RA)** is a chronic inflammatory joint disease.

**Overview:**
• Autoimmune attack on synovial membranes
• Symmetrical polyarthritis (small joints of hands/feet)
• Can cause joint destruction, deformity, disability
• Extra-articular: lungs, heart, eyes, skin

**Key Biomarkers:**
• RF (Rheumatoid Factor): >14 IU/mL positive
• Anti-CCP: >17 U/mL (97% specific for RA)
• ESR, CRP for inflammation monitoring
• X-rays/MRI for joint damage assessment

**Disease Activity (DAS28):**
• <2.6: Remission
• 2.6-3.2: Low activity
• 3.2-5.1: Moderate
• >5.1: High activity

**Treatment:** MTX, DMARDs, biologics (TNF inhibitors, IL-6 blockers)""",

        'multiple_sclerosis': """**Multiple Sclerosis (MS)** is a CNS demyelinating autoimmune disease.

**Overview:**
• Immune system attacks myelin sheath in brain/spinal cord
• Causes lesions (plaques) disrupting nerve signals
• Types: RRMS (85%), SPMS, PPMS, PRMS
• Onset typically 20-40 years, 2:1 female predominance

**Key Biomarkers:**
• MRI: T2/FLAIR lesions, gadolinium-enhancing lesions
• CSF: Oligoclonal bands, elevated IgG index
• EDSS score (Expanded Disability Status Scale)
• Evoked potentials (visual, somatosensory)

**Diagnosis (McDonald Criteria):**
• Dissemination in space (multiple CNS areas)
• Dissemination in time (new lesions over time)
• No better explanation

**Treatment:** Interferons, glatiramer, natalizumab, ocrelizumab, fingolimod""",

        'type1_diabetes': """**Type 1 Diabetes (T1D)** is autoimmune destruction of pancreatic beta cells.

**Overview:**
• Immune-mediated destruction of insulin-producing cells
• Results in absolute insulin deficiency
• Usually presents in childhood/adolescence
• Requires lifelong insulin therapy

**Key Biomarkers:**
• GAD65 antibodies (most common)
• IA-2 (insulinoma-associated antigen-2)
• ZnT8 (zinc transporter 8) antibodies
• Insulin autoantibodies (IAA)
• C-peptide (low/absent = no endogenous insulin)
• HbA1c for glucose control

**Genetic Markers:**
• HLA-DR3-DQ2, HLA-DR4-DQ8 (high risk)

**Treatment:** Insulin (basal-bolus regimen), CGM, insulin pumps""",

        'hashimoto': """**Hashimoto's Thyroiditis** is autoimmune hypothyroidism.

**Overview:**
• Most common cause of hypothyroidism
• Lymphocytic infiltration destroys thyroid gland
• Gradual thyroid failure over years
• 7:1 female predominance

**Key Biomarkers:**
• Anti-TPO (thyroid peroxidase): >35 IU/mL positive
• Anti-thyroglobulin (Anti-Tg) antibodies
• TSH: Elevated (>4.5 mIU/L)
• Free T4: Low
• Thyroid ultrasound: Heterogeneous echotexture

**Symptoms:**
• Fatigue, weight gain, cold intolerance
• Dry skin, hair loss, constipation
• Depression, memory problems

**Treatment:** Levothyroxine replacement, titrate to normalize TSH""",

        'sjogren': """**Sjögren's Syndrome** is autoimmune exocrine gland dysfunction.

**Overview:**
• Affects salivary and lacrimal glands
• Primary (alone) or Secondary (with RA, SLE)
• 9:1 female predominance, onset 40-60 years
• Can involve lungs, kidneys, nervous system

**Key Biomarkers:**
• Anti-SSA/Ro antibodies (70% positive)
• Anti-SSB/La antibodies (40% positive)
• RF positive in 60-70%
• ANA positive in 80%

**Diagnostic Tests:**
• Schirmer's test: <5mm/5min = dry eyes
• Salivary flow rate: <1.5mL/15min = dry mouth
• Minor salivary gland biopsy: Focus score ≥1

**Treatment:** Artificial tears, saliva substitutes, pilocarpine, hydroxychloroquine""",

        'psoriasis': """**Psoriasis & Psoriatic Arthritis (PsA)** are immune-mediated conditions.

**Overview:**
• Psoriasis: Skin plaques (red, scaly, silvery)
• PsA: Inflammatory arthritis in ~30% of psoriasis patients
• Involves Th17 pathway, IL-17, IL-23
• Associated with HLA-B27, HLA-Cw6

**Key Features:**
• PASI score (Psoriasis Area Severity Index)
• Dactylitis (sausage digits)
• Enthesitis (tendon insertion inflammation)
• Nail changes (pitting, onycholysis)

**Biomarkers:**
• HLA-B27 (axial involvement)
• ESR, CRP for inflammation
• No specific autoantibodies (RF usually negative)

**Treatment:** Topicals, phototherapy, MTX, biologics (TNF, IL-17, IL-23 inhibitors)""",

        'ibd': """**Inflammatory Bowel Disease (IBD)** includes Crohn's and Ulcerative Colitis.

**Crohn's Disease:**
• Can affect any GI tract (mouth to anus)
• Transmural inflammation, skip lesions
• Complications: strictures, fistulas, abscesses

**Ulcerative Colitis:**
• Limited to colon (continuous from rectum)
• Mucosal inflammation only
• Higher colorectal cancer risk

**Key Biomarkers:**
• Fecal calprotectin: >250 μg/g suggests active disease
• CRP, ESR for systemic inflammation
• pANCA: More common in UC
• ASCA: More common in Crohn's
• Endoscopy with biopsy (gold standard)

**Treatment:** 5-ASA, corticosteroids, azathioprine, biologics (anti-TNF, vedolizumab)""",

        'celiac': """**Celiac Disease** is autoimmune gluten intolerance.

**Overview:**
• Immune reaction to gluten damages small intestine
• Affects ~1% of population
• Strong genetic component (HLA-DQ2/DQ8)
• Can present at any age

**Key Biomarkers:**
• Anti-tTG IgA (tissue transglutaminase): Primary screening
• Anti-endomysial (EMA) IgA: Highly specific
• Deamidated gliadin peptide (DGP) IgA/IgG
• Total IgA (rule out IgA deficiency)
• HLA-DQ2/DQ8 genotyping

**Diagnosis:**
• Positive serology + duodenal biopsy (villous atrophy)
• Marsh classification for histology

**Treatment:** Strict lifelong gluten-free diet""",

        'myasthenia': """**Myasthenia Gravis (MG)** is autoimmune neuromuscular junction disease.

**Overview:**
• Antibodies block/destroy acetylcholine receptors
• Fluctuating muscle weakness, worse with activity
• Ocular MG (eyes) → Generalized MG
• Associated with thymoma (10-15%)

**Key Biomarkers:**
• AChR (acetylcholine receptor) antibodies: 85% positive
• MuSK antibodies: 5-8% (AChR-negative cases)
• LRP4 antibodies: Rare subset
• Anti-striational antibodies (thymoma association)

**Diagnostic Tests:**
• EMG: Decremental response to repetitive stimulation
• Edrophonium (Tensilon) test
• CT chest for thymoma

**Treatment:** Pyridostigmine, corticosteroids, azathioprine, IVIG, thymectomy""",

        'vasculitis': """**Vasculitis** is inflammation of blood vessels.

**ANCA-Associated Vasculitis:**
• GPA (Wegener's): c-ANCA/PR3 positive, upper/lower respiratory + kidneys
• MPA (Microscopic Polyangiitis): p-ANCA/MPO positive, kidneys + lungs
• EGPA (Churg-Strauss): Asthma + eosinophilia + p-ANCA

**Key Biomarkers:**
• c-ANCA (PR3): GPA
• p-ANCA (MPO): MPA, EGPA
• ESR, CRP: Disease activity
• Creatinine, urinalysis: Renal involvement
• BVAS (Birmingham Vasculitis Activity Score)

**Other Vasculitides:**
• Giant Cell Arteritis: Temporal artery biopsy, elevated ESR
• Takayasu's: Large vessel, imaging-based
• Behçet's: Clinical criteria

**Treatment:** Corticosteroids + cyclophosphamide/rituximab""",

        'antiphospholipid': """**Antiphospholipid Syndrome (APS)** is autoimmune hypercoagulability.

**Overview:**
• Increased risk of thrombosis (arterial/venous)
• Pregnancy complications (recurrent miscarriage)
• Primary (alone) or Secondary (with SLE)
• Catastrophic APS: Multi-organ failure

**Key Biomarkers:**
• Lupus anticoagulant (LA): Functional assay
• Anticardiolipin (aCL) IgG/IgM: >40 GPL/MPL
• Anti-β2 glycoprotein I (β2GPI) IgG/IgM
• Must be positive on 2 occasions, 12 weeks apart

**Diagnosis (Sydney Criteria):**
• Clinical: Thrombosis OR pregnancy morbidity
• Laboratory: Persistent aPL antibodies

**Treatment:** Anticoagulation (warfarin INR 2-3), aspirin, LMWH in pregnancy""",

        # ============================================================
        # ML ALGORITHMS (All 13)
        # ============================================================
        'xgboost': """**XGBoost (Extreme Gradient Boosting)**

**What It Is:**
• Gradient boosted decision tree ensemble
• Industry standard for tabular/clinical data
• Fast, accurate, handles missing values well

**How It Works:**
1. Builds trees sequentially
2. Each tree corrects errors of previous trees
3. Uses gradient descent optimization
4. Regularization prevents overfitting (L1, L2)

**Key Hyperparameters:**
• `n_estimators`: Number of trees (100-1000)
• `max_depth`: Tree depth (3-10)
• `learning_rate`: Step size (0.01-0.3)
• `subsample`: Row sampling (0.6-1.0)
• `colsample_bytree`: Feature sampling (0.6-1.0)

**When to Use:**
✅ Structured/tabular data (EHR, lab values)
✅ Classification and regression
✅ Medium to large datasets
✅ When interpretability needed (SHAP works well)

**Performance:** Often best performer on clinical datasets""",

        'lightgbm': """**LightGBM (Light Gradient Boosting Machine)**

**What It Is:**
• Microsoft's fast gradient boosting implementation
• Leaf-wise tree growth (vs. level-wise)
• Optimized for speed and memory efficiency

**How It Works:**
1. Grows trees leaf-wise (best-first)
2. Uses histogram-based algorithm for splitting
3. GOSS: Gradient-based One-Side Sampling
4. EFB: Exclusive Feature Bundling

**Key Hyperparameters:**
• `num_leaves`: Max leaves per tree (31 default)
• `max_depth`: Limit tree depth (-1 = no limit)
• `learning_rate`: Step size (0.05-0.2)
• `feature_fraction`: Column sampling
• `bagging_fraction`: Row sampling

**Advantages:**
✅ Faster training than XGBoost (2-10x)
✅ Lower memory usage
✅ Handles large datasets well
✅ Native categorical feature support

**When to Use:** Large datasets, need for speed, categorical features""",

        'catboost': """**CatBoost (Categorical Boosting)**

**What It Is:**
• Yandex's gradient boosting library
• Specialized for categorical features
• Excellent out-of-box performance

**How It Works:**
1. Ordered boosting (reduces overfitting)
2. Native categorical encoding (target statistics)
3. Symmetric trees (faster inference)
4. GPU training support

**Key Hyperparameters:**
• `iterations`: Number of trees (1000 default)
• `depth`: Tree depth (6 default)
• `learning_rate`: Auto-adjusted
• `l2_leaf_reg`: L2 regularization
• `cat_features`: Categorical column indices

**Advantages:**
✅ Best handling of categorical features
✅ Minimal preprocessing required
✅ Robust to overfitting
✅ Fast GPU training

**When to Use:** Datasets with many categorical variables, minimal tuning needed""",

        'random_forest': """**Random Forest (RF)**

**What It Is:**
• Ensemble of decision trees
• Each tree trained on bootstrap sample
• Predictions averaged (regression) or voted (classification)

**How It Works:**
1. Create N bootstrap samples of data
2. Train decision tree on each sample
3. At each split, consider random subset of features
4. Aggregate predictions (bagging)

**Key Hyperparameters:**
• `n_estimators`: Number of trees (100-500)
• `max_depth`: Tree depth (None = unlimited)
• `min_samples_split`: Min samples to split (2-10)
• `max_features`: Features per split ('sqrt', 'log2')
• `bootstrap`: Whether to use bootstrapping (True)

**Advantages:**
✅ Robust to overfitting
✅ Handles missing values
✅ Feature importance built-in
✅ Works well with default parameters

**When to Use:** Good baseline model, interpretability needed, noisy data""",

        'logistic_regression': """**Logistic Regression (LR)**

**What It Is:**
• Linear model for binary/multiclass classification
• Predicts probability using sigmoid/softmax
• Highly interpretable (coefficients = feature importance)

**How It Works:**
1. Linear combination of features: z = w₁x₁ + w₂x₂ + ... + b
2. Apply sigmoid: P(y=1) = 1/(1 + e^(-z))
3. Optimize using maximum likelihood

**Key Hyperparameters:**
• `C`: Inverse regularization strength (1.0 default)
• `penalty`: 'l1' (LASSO), 'l2' (Ridge), 'elasticnet'
• `solver`: 'lbfgs', 'saga', 'liblinear'
• `max_iter`: Maximum iterations

**Advantages:**
✅ Fast training and inference
✅ Highly interpretable (coefficients)
✅ Probabilistic output (calibrated)
✅ Works with regularization

**When to Use:** Baseline model, interpretability critical, linear relationships""",

        'svm': """**Support Vector Machine (SVM)**

**What It Is:**
• Finds optimal hyperplane separating classes
• Uses kernel trick for non-linear boundaries
• Maximizes margin between classes

**How It Works:**
1. Find hyperplane with maximum margin
2. Support vectors = points closest to boundary
3. Kernel function maps to higher dimension
4. Soft margin allows some misclassification

**Key Hyperparameters:**
• `C`: Regularization (1.0 default, higher = less regularization)
• `kernel`: 'linear', 'rbf', 'poly', 'sigmoid'
• `gamma`: Kernel coefficient ('scale', 'auto', or float)
• `class_weight`: Handle imbalanced classes

**Advantages:**
✅ Effective in high-dimensional spaces
✅ Memory efficient (only stores support vectors)
✅ Versatile kernel options

**Limitations:**
❌ Slow on large datasets (O(n²) to O(n³))
❌ Sensitive to feature scaling
❌ Probability estimates require additional fitting""",

        'knn': """**K-Nearest Neighbors (KNN)**

**What It Is:**
• Instance-based (lazy) learning algorithm
• Classifies based on majority vote of k neighbors
• No explicit training phase

**How It Works:**
1. Store all training samples
2. For prediction: find k nearest neighbors
3. Classification: majority vote
4. Regression: average of neighbors

**Key Hyperparameters:**
• `n_neighbors`: Number of neighbors (5 default)
• `weights`: 'uniform' or 'distance'
• `metric`: Distance metric ('euclidean', 'manhattan')
• `algorithm`: 'ball_tree', 'kd_tree', 'brute', 'auto'

**Advantages:**
✅ Simple and intuitive
✅ No training phase
✅ Adapts to new data easily
✅ Non-parametric

**Limitations:**
❌ Slow prediction (searches all training data)
❌ Sensitive to feature scaling
❌ Curse of dimensionality""",

        'mlp': """**Multi-Layer Perceptron (MLP) / Neural Network**

**What It Is:**
• Feedforward artificial neural network
• Multiple layers of neurons with activation functions
• Can learn complex non-linear patterns

**Architecture:**
1. Input layer: Receives features
2. Hidden layers: Transform features (1-3 layers typical)
3. Output layer: Produces predictions
4. Activations: ReLU (hidden), Softmax/Sigmoid (output)

**Key Hyperparameters:**
• `hidden_layer_sizes`: Neurons per layer ((100,) default)
• `activation`: 'relu', 'tanh', 'logistic'
• `solver`: 'adam', 'sgd', 'lbfgs'
• `alpha`: L2 regularization (0.0001 default)
• `learning_rate`: 'constant', 'adaptive', 'invscaling'

**Advantages:**
✅ Can learn complex patterns
✅ Universal approximator
✅ Works with various data types

**Limitations:**
❌ Requires more data
❌ Computationally expensive
❌ Less interpretable (black box)""",

        'decision_tree': """**Decision Tree**

**What It Is:**
• Tree-structured model for classification/regression
• Splits data based on feature thresholds
• Highly interpretable (visualize the tree)

**How It Works:**
1. Start at root with all data
2. Find best split (max information gain / min Gini)
3. Create child nodes for each split
4. Repeat until stopping criteria met
5. Leaves contain predictions

**Key Hyperparameters:**
• `max_depth`: Maximum tree depth (None = unlimited)
• `min_samples_split`: Min samples to split node
• `min_samples_leaf`: Min samples in leaf
• `criterion`: 'gini' or 'entropy'
• `max_features`: Features to consider for split

**Advantages:**
✅ Highly interpretable (visualize rules)
✅ Handles mixed data types
✅ No feature scaling needed
✅ Captures non-linear relationships

**Limitations:**
❌ Prone to overfitting
❌ Unstable (small data changes → different tree)
❌ Usually outperformed by ensembles""",

        'adaboost': """**AdaBoost (Adaptive Boosting)**

**What It Is:**
• Ensemble method combining weak learners
• Sequentially trains models, focusing on misclassified samples
• Original boosting algorithm (Freund & Schapire)

**How It Works:**
1. Initialize equal weights for all samples
2. Train weak learner (decision stump)
3. Increase weights of misclassified samples
4. Train next learner on weighted data
5. Final prediction: weighted vote of all learners

**Key Hyperparameters:**
• `n_estimators`: Number of weak learners (50 default)
• `learning_rate`: Contribution of each learner (1.0 default)
• `base_estimator`: Weak learner type (DecisionTreeClassifier)
• `algorithm`: 'SAMME' or 'SAMME.R'

**Advantages:**
✅ Simple and effective
✅ Less prone to overfitting than single tree
✅ Works with any base learner

**Limitations:**
❌ Sensitive to noisy data and outliers
❌ Slower than bagging methods""",

        'gradient_boosting': """**Gradient Boosting Classifier (GBC)**

**What It Is:**
• Ensemble method using gradient descent optimization
• Builds trees sequentially to minimize loss
• Scikit-learn's native implementation

**How It Works:**
1. Initialize with simple prediction (mean/mode)
2. Calculate residuals (gradient of loss)
3. Fit tree to residuals
4. Update predictions
5. Repeat for n_estimators

**Key Hyperparameters:**
• `n_estimators`: Number of boosting stages (100 default)
• `learning_rate`: Shrinkage (0.1 default)
• `max_depth`: Individual tree depth (3 default)
• `subsample`: Fraction of samples per tree (1.0)
• `min_samples_split`: Min samples to split

**Advantages:**
✅ Often best accuracy on tabular data
✅ Handles different loss functions
✅ Feature importance available

**Comparison to XGBoost:**
• XGBoost is faster with regularization built-in
• GBC is simpler, good for understanding boosting""",

        'ridge': """**Ridge Classifier**

**What It Is:**
• Linear classifier with L2 regularization
• Converts regression to classification
• Shrinks coefficients toward zero (not exactly zero)

**How It Works:**
1. Linear model: y = Xw + b
2. Add L2 penalty: ||w||²
3. Minimize: Loss + α × ||w||²
4. Convert to class labels via threshold

**Key Hyperparameters:**
• `alpha`: Regularization strength (1.0 default)
• `solver`: 'auto', 'svd', 'cholesky', 'lsqr', 'sag', 'saga'
• `class_weight`: Handle imbalanced classes

**Advantages:**
✅ Fast training (closed-form solution)
✅ Handles multicollinearity
✅ Stable coefficients

**When to Use:** High-dimensional data, correlated features, fast baseline""",

        'lda': """**Linear Discriminant Analysis (LDA)**

**What It Is:**
• Classification using class conditional densities
• Projects data to maximize class separation
• Also used for dimensionality reduction

**How It Works:**
1. Assume Gaussian class distributions
2. Estimate mean and covariance for each class
3. Find projection maximizing between-class variance
4. Minimize within-class variance
5. Classify using Bayes' theorem

**Key Hyperparameters:**
• `solver`: 'svd' (default), 'lsqr', 'eigen'
• `shrinkage`: 'auto', None, or float (0-1)
• `n_components`: For dimensionality reduction
• `priors`: Prior probabilities of classes

**Advantages:**
✅ Fast training
✅ Good with small datasets
✅ Provides probabilistic predictions
✅ Dimensionality reduction built-in

**Limitations:**
❌ Assumes Gaussian distributions
❌ Assumes equal covariance matrices""",

        # ============================================================
        # ML METRICS
        # ============================================================
        'accuracy': """**Accuracy**

**Definition:**
Proportion of correct predictions out of all predictions.

**Formula:**
```
Accuracy = (TP + TN) / (TP + TN + FP + FN)
```

**Interpretation:**
• 1.0 (100%): Perfect predictions
• 0.5 (50%): Random guessing (binary)
• >0.8 (80%): Generally acceptable

**⚠️ Warning - Class Imbalance:**
Accuracy is MISLEADING when classes are imbalanced!
Example: 95% healthy, 5% disease
→ Predicting "always healthy" = 95% accuracy but USELESS

**When to Use:**
✅ Balanced classes
✅ All errors equally important
❌ Avoid for rare disease prediction

**Better Alternatives:** F1-score, AUC-ROC, AUC-PR for imbalanced data""",

        'precision': """**Precision (Positive Predictive Value)**

**Definition:**
Of all predicted positives, how many are actually positive?

**Formula:**
```
Precision = TP / (TP + FP)
```

**Clinical Interpretation:**
• "When the model says disease, how often is it right?"
• High precision = Few false alarms
• Low precision = Many false positives (unnecessary treatments/anxiety)

**Example:**
• TP=80, FP=20 → Precision = 80/100 = 0.80 (80%)
• "80% of patients flagged as high-risk actually are"

**When to Prioritize:**
✅ False positives are costly (invasive tests, anxiety)
✅ Resource-limited settings (can only treat few patients)
❌ Don't prioritize if missing cases is dangerous""",

        'recall': """**Recall (Sensitivity / True Positive Rate)**

**Definition:**
Of all actual positives, how many did the model catch?

**Formula:**
```
Recall = TP / (TP + FN)
```

**Clinical Interpretation:**
• "Of all sick patients, how many did we identify?"
• High recall = Few missed cases
• Low recall = Many false negatives (missed diagnoses)

**Example:**
• TP=80, FN=20 → Recall = 80/100 = 0.80 (80%)
• "We caught 80% of patients with active disease"

**When to Prioritize:**
✅ Missing cases is dangerous (cancer, infections, flares)
✅ Early detection critical
✅ Autoimmune diseases (missing flare → organ damage)

**Note:** High recall often comes with lower precision (trade-off)""",

        'f1_score': """**F1 Score**

**Definition:**
Harmonic mean of precision and recall. Balances both metrics.

**Formula:**
```
F1 = 2 × (Precision × Recall) / (Precision + Recall)
```

**Interpretation:**
• 1.0: Perfect precision AND recall
• 0.0: Precision or recall is zero
• Harmonic mean penalizes extreme imbalances

**Example:**
• Precision=0.80, Recall=0.60 → F1 = 2×(0.48)/(1.4) = 0.686
• Precision=0.90, Recall=0.40 → F1 = 2×(0.36)/(1.3) = 0.554

**When to Use:**
✅ Need balance between precision and recall
✅ Class imbalance exists
✅ Single metric for model comparison
✅ Autoimmune disease prediction (common use case)

**Variants:**
• F2-score: Weights recall higher (medical screening)
• F0.5-score: Weights precision higher""",

        'auc_roc': """**AUC-ROC (Area Under Receiver Operating Characteristic)**

**Definition:**
Probability that model ranks random positive higher than random negative.

**What is ROC Curve:**
• X-axis: False Positive Rate (1 - Specificity)
• Y-axis: True Positive Rate (Recall)
• Plots performance across ALL thresholds

**Interpretation:**
• 1.0: Perfect discrimination
• 0.5: Random guessing (diagonal line)
• <0.5: Worse than random (invert predictions)

**Clinical Benchmarks:**
• 0.9-1.0: Excellent discrimination
• 0.8-0.9: Good (acceptable for most clinical use)
• 0.7-0.8: Fair
• 0.6-0.7: Poor
• <0.6: Not useful

**Advantages:**
✅ Threshold-independent
✅ Intuitive interpretation
✅ Comparable across models

**⚠️ Limitation:** Can be overly optimistic with class imbalance
→ Use AUC-PR for highly imbalanced data""",

        'auc_pr': """**AUC-PR (Area Under Precision-Recall Curve)**

**Definition:**
Area under the Precision-Recall curve across all thresholds.

**What is PR Curve:**
• X-axis: Recall (Sensitivity)
• Y-axis: Precision
• Shows trade-off at different thresholds

**When to Use:**
✅ Class imbalance (rare diseases, flares)
✅ Focus on positive class (disease detection)
✅ When false negatives matter most

**Interpretation:**
• Higher is better
• Baseline = Proportion of positive class
• Example: 10% disease prevalence → 0.10 baseline

**Comparison to AUC-ROC:**
• AUC-ROC can be inflated with many negatives
• AUC-PR more informative for rare events
• Both should be reported together

**Clinical Use:**
Perfect for autoimmune flare prediction where:
• ~10-20% of patients have active disease
• Missing a flare has serious consequences""",

        'specificity': """**Specificity (True Negative Rate)**

**Definition:**
Of all actual negatives, how many did the model correctly identify?

**Formula:**
```
Specificity = TN / (TN + FP)
```

**Clinical Interpretation:**
• "Of all healthy patients, how many were correctly classified?"
• High specificity = Few healthy patients incorrectly flagged
• Low specificity = Many false positives

**Example:**
• TN=85, FP=15 → Specificity = 85/100 = 0.85 (85%)
• "85% of patients without active disease were correctly identified"

**When to Prioritize:**
✅ False positives are costly (unnecessary treatment)
✅ Confirmatory testing (high specificity tests)
✅ When resources are limited

**Relationship:**
• Sensitivity + Specificity = 1 is NOT a rule
• Trade-off depends on threshold
• Youden Index = Sensitivity + Specificity - 1""",

        'brier_score': """**Brier Score**

**Definition:**
Mean squared error of probability predictions vs. actual outcomes.

**Formula:**
```
Brier Score = (1/N) × Σ(predicted_prob - actual_outcome)²
```

**Interpretation:**
• 0.0: Perfect calibration
• 1.0: Worst possible
• Lower is better

**What It Measures:**
1. **Calibration:** Do predicted probabilities match reality?
2. **Discrimination:** Can model distinguish classes?
3. **Combined:** Overall probability accuracy

**Example:**
• Predict 80% probability, patient has disease → (0.8-1)² = 0.04
• Predict 80% probability, no disease → (0.8-0)² = 0.64

**Clinical Importance:**
✅ Critical for risk scores (need accurate probabilities)
✅ Decision thresholds depend on calibration
✅ Treatment decisions based on probability

**Complement:** Calibration curves (reliability diagrams)""",

        'confusion_matrix': """**Confusion Matrix**

**Definition:**
Table showing prediction outcomes vs. actual classes.

**Structure (Binary):**
```
                  Predicted
                  Pos    Neg
Actual  Pos      [TP]   [FN]
        Neg      [FP]   [TN]
```

**Components:**
• **TP (True Positive):** Correctly predicted positive
• **TN (True Negative):** Correctly predicted negative
• **FP (False Positive):** Incorrectly predicted positive (Type I error)
• **FN (False Negative):** Incorrectly predicted negative (Type II error)

**Clinical Translation:**
• TP: Correctly identified sick patients
• TN: Correctly identified healthy patients
• FP: Healthy patients incorrectly flagged (overdiagnosis)
• FN: Sick patients missed (dangerous!)

**All Metrics Derived From:**
• Accuracy = (TP+TN) / Total
• Precision = TP / (TP+FP)
• Recall = TP / (TP+FN)
• Specificity = TN / (TN+FP)
• F1 = 2×TP / (2×TP+FP+FN)""",

        # ============================================================
        # BIOMARKERS & LAB VALUES
        # ============================================================
        'crp': """**CRP (C-Reactive Protein)**

**What It Is:**
Acute-phase inflammatory protein produced by liver.

**Normal Range:** <1 mg/L (or <10 mg/L depending on lab)

**Interpretation:**
• <1 mg/L: Normal
• 1-10 mg/L: Mild inflammation (chronic conditions)
• 10-50 mg/L: Moderate (autoimmune flare, infection)
• >50 mg/L: Severe (sepsis, major flare, trauma)

**Clinical Significance in Autoimmune:**
• Rises rapidly (within hours) during flares
• Falls quickly with treatment (good for monitoring)
• Non-specific (also elevated in infections)

**SLE Specifics:**
• Often normal or only mildly elevated in SLE flares
• Very high CRP in SLE → suspect infection
• Use with complement levels for better picture

**hs-CRP (High-Sensitivity):**
• <1: Low cardiovascular risk
• 1-3: Moderate risk
• >3: High risk""",

        'esr': """**ESR (Erythrocyte Sedimentation Rate)**

**What It Is:**
Rate at which red blood cells settle in a tube over 1 hour.

**Normal Range:**
• Men: 0-15 mm/hr (age/2 upper limit)
• Women: 0-20 mm/hr ((age+10)/2 upper limit)

**Interpretation:**
• Elevated = Inflammation, infection, malignancy
• Very high (>100): Multiple myeloma, temporal arteritis
• Changes slower than CRP (reflects weeks, not days)

**Clinical Use:**
• Screening for inflammation
• Monitoring disease activity
• Combined with CRP for comprehensive view

**SLE/Autoimmune:**
• Often elevated in active disease
• Does NOT distinguish infection from flare
• Trends more useful than single values

**Factors Affecting ESR:**
↑ Increases: Anemia, pregnancy, age, obesity
↓ Decreases: Polycythemia, sickle cell, CHF""",

        'complement': """**Complement System (C3, C4)**

**What It Is:**
Proteins of innate immune system involved in inflammation.

**Normal Ranges:**
• C3: 90-180 mg/dL
• C4: 10-40 mg/dL

**Interpretation:**
• **Low C3 and/or C4:** Complement consumption (active autoimmune)
• **Normal:** Inactive disease or non-immune cause
• **High:** Acute inflammation (rare in SLE)

**SLE Significance:**
• Low complement = Active disease (especially nephritis)
• C4 often drops first
• Anti-dsDNA ↑ + Complement ↓ = High flare risk
• Monitor trends over time

**Other Causes of Low Complement:**
• Hereditary deficiency
• Liver disease (production failure)
• Sepsis (consumption)
• Membranoproliferative GN

**CH50:** Total hemolytic complement (screens all components)""",

        'ana': """**ANA (Antinuclear Antibodies)**

**What It Is:**
Autoantibodies directed against nuclear components.

**Testing:**
• Method: Indirect immunofluorescence (IIF) on HEp-2 cells
• Reported as: Titer (1:40, 1:80, 1:160...) + Pattern

**Interpretation:**
• Negative: <1:40
• Positive: ≥1:80 (varies by lab)
• Strongly positive: ≥1:320

**Patterns & Associations:**
• Homogeneous: SLE, drug-induced lupus
• Speckled: Sjögren's, MCTD, SLE
• Nucleolar: Scleroderma
• Centromere: Limited scleroderma (CREST)

**Clinical Points:**
• 95%+ of SLE patients are ANA positive
• ANA alone does NOT diagnose SLE (10% healthy have positive)
• Must correlate with clinical features
• If ANA negative, SLE very unlikely""",

        'anti_dsdna': """**Anti-dsDNA (Anti-double stranded DNA)**

**What It Is:**
Autoantibodies against double-stranded DNA. Highly specific for SLE.

**Normal:** <10 IU/mL (varies by lab/method)

**Interpretation:**
• Positive in 60-70% of SLE patients
• Rising titers often precede flares (by weeks)
• High levels associated with lupus nephritis
• Can be used to monitor disease activity

**Methods:**
• ELISA: Common, quantitative
• Farr assay: Gold standard, research
• Crithidia luciliae: High specificity

**Clinical Significance:**
• Highly specific for SLE (few false positives)
• Correlates with disease activity
• Nephritis risk: High anti-dsDNA + Low C3/C4
• Monitor every 3-6 months in active SLE

**⚠️ Note:**
• Can be positive in other conditions (rarely)
• Negative anti-dsDNA doesn't exclude SLE""",

        # ============================================================
        # PLATFORM FEATURES
        # ============================================================
        'data_upload': """**Data Upload & Ingestion (Platform Feature)**

**Supported Formats:**
• CSV files
• Excel (.xlsx, .xls)
• JSON (structured)

**Upload Process:**
1. Navigate to **Data Catalog** tab
2. Click "Upload New Dataset"
3. Select file from computer
4. Enter dataset name and type
5. Preview data before confirming
6. System validates structure

**Data Requirements:**
• Patient IDs (unique identifier)
• Clinical features (biomarkers, demographics)
• Target variable (for supervised learning)
• Date fields (for temporal analysis)

**Best Practices:**
✅ Clean data before upload
✅ Check for missing values
✅ Consistent formatting
✅ No special characters in headers
✅ Remove PII (patient privacy)

**After Upload:**
• View in Data Catalog
• Check Data Quality metrics
• Proceed to preprocessing""",

        'preprocessing': """**Data Preprocessing (Platform Feature)**

**4-Step Pipeline:**

**1. Variable Filtration**
• Removes columns with excessive missing data
• Default threshold: 50% missing
• Removes near-zero variance features

**2. Imputation**
• Fills remaining missing values
• Strategies: Median, Mean, Mode, KNN
• Median recommended for biomarkers

**3. Winsorization**
• Caps extreme outliers at percentiles
• Default: 1st and 99th percentile
• Prevents outliers from dominating

**4. Standardization**
• Scales features to common range
• Methods: Standard (z-score), MinMax, Robust
• Essential for distance-based algorithms

**Why Order Matters:**
Filter → Impute → Winsorize → Standardize
(Can't standardize missing values!)

**Platform Location:**
Data Pipeline → Preprocessing tab""",

        'feature_engineering': """**Feature Engineering (Platform Feature)**

**What It Is:**
Creating new features from existing data to improve model performance.

**Automated Features Created:**
• **CRP_ESR_ratio:** Inflammation composite
• **Complement_ratio:** C3/C4 ratio
• **PLT_WBC_ratio:** Blood cell ratio
• **Cytopenia:** Binary indicator (low WBC, PLT, or HGB)
• **Lab_abnormal_count:** Number of abnormal values
• **Activity_score:** Weighted disease activity index
• **Disease_duration_years:** Time since diagnosis

**Why Important:**
✅ Domain knowledge encoded in features
✅ Can capture non-linear relationships
✅ Often improves model performance
✅ More interpretable than raw features

**Platform Location:**
Data Pipeline → Feature Engineering tab
Enable with `apply_feature_engineering: true`""",

        'shap': """**SHAP (SHapley Additive exPlanations)**

**What It Is:**
Game-theoretic method for explaining ML predictions.

**How It Works:**
• Assigns each feature a contribution value
• Based on Shapley values from cooperative game theory
• Shows how each feature pushed prediction up/down

**Interpretation:**
• **Positive SHAP:** Feature increased prediction (toward positive/severe)
• **Negative SHAP:** Feature decreased prediction (toward negative/mild)
• **Magnitude:** Strength of influence

**Visualizations:**
• **Waterfall:** Feature contributions for single prediction
• **Force plot:** Same info, horizontal format
• **Summary plot:** Feature importance across dataset
• **Dependence plot:** Feature value vs. SHAP value

**Example Reading:**
```
Feature: CRP = +0.18
Meaning: CRP value increased severity prediction by 18%
```

**Platform Location:**
Explainability → SHAP Values tab""",

        'model_comparison': """**Model Comparison (Platform Feature)**

**What It Does:**
Compare multiple trained models side-by-side.

**Metrics Compared:**
• AUC-ROC, AUC-PR
• Accuracy, Precision, Recall
• F1-score
• Brier Score (calibration)

**Visualizations:**
• ROC curves (overlay)
• Precision-Recall curves
• Calibration plots
• Feature importance comparison

**How to Compare:**
1. Train multiple models
2. Go to Model Comparison tab
3. Select models to compare
4. View metric tables and charts

**Decision Framework:**
1. Check AUC-ROC (discrimination ability)
2. Check F1/Recall (for imbalanced classes)
3. Check calibration (if using probabilities)
4. Consider training time/complexity
5. Consider interpretability needs

**Platform Location:**
Model Comparison tab""",

        'training': """**How to Train ML Models (Step-by-Step)**

**Prerequisites:**
✅ Data uploaded (Data Catalog)
✅ Labels applied (Data Preparation → Labeling)
✅ Preprocessing done (Data Preparation → Preprocessing)

**Step 1: Navigate to Training Jobs**
• Click "Training Jobs" in left sidebar
• Or go to: `/training`

**Step 2: Prepare Dataset**
• Click "Prepare Dataset" button
• Select your batch (dataset)
• Choose target column (e.g., labels_disease_classification)
• Set test size: 0.35 (35% for testing)
• Click "Prepare"

**Step 3: Select Algorithm (13 Available)**
**Gradient Boosting:** XGBoost, LightGBM, CatBoost
**Tree Ensembles:** Random Forest, AdaBoost, Decision Tree
**Linear Models:** Logistic Regression, Ridge, LDA
**Distance/Kernel:** SVM, K-Nearest Neighbors
**Neural Networks:** MLP

**Step 4: Configure Training**
• Enable Optuna HPO (recommended)
• Set trials: 30 (default)
• Set CV folds: 5 (default)

**Step 5: Start Training**
• Click "Train Model"
• Monitor real-time progress
• Wait for completion (may take minutes)

**Step 6: View Results**
• OOF AUC (cross-validation score)
• Test AUC (held-out test score)
• Compare in Model Comparison page

**Pro Tips:**
• XGBoost/LightGBM usually perform best
• Train multiple models to compare
• Use ensemble for best performance""",

        'optuna': """**Optuna Hyperparameter Optimization**

**What It Is:**
State-of-the-art automated hyperparameter tuning using Bayesian optimization.

**How It Works:**
1. Define search space for hyperparameters
2. Sample parameter combinations intelligently
3. Train model with each combination
4. Evaluate on validation set
5. Use results to guide next sampling
6. Repeat for N trials (default: 20)

**Advantages:**
✅ Efficient search (not grid search)
✅ Prunes unpromising trials early
✅ Handles complex search spaces
✅ State-of-the-art performance

**Parameters Tuned (Example - XGBoost):**
• n_estimators: 100-1000
• max_depth: 3-10
• learning_rate: 0.01-0.3
• subsample: 0.6-1.0
• colsample_bytree: 0.6-1.0

**Platform Usage:**
Training Jobs → Enable "Hyperparameter Tuning"
• Trials: Number of configurations to try
• Timeout: Maximum time for search

**Result:**
Best hyperparameters saved with model""",

        'ensemble': """**Stacking Ensemble (Meta-Learning)**

**What It Is:**
Combines multiple base models using a meta-learner.

**How It Works:**
1. Train multiple base models (e.g., XGBoost, LightGBM, RF)
2. Generate out-of-fold predictions from each
3. Use predictions as features for meta-learner
4. Meta-learner learns optimal combination

**Available Meta-Learners:**
• Logistic Regression (default, interpretable)
• Ridge Classifier
• LDA
• XGBoost
• LightGBM
• Random Forest
• MLP

**Why Stacking Works:**
• Different models capture different patterns
• Errors from one model corrected by others
• Usually outperforms single models

**Platform Usage:**
1. Train base models first
2. Go to Ensemble Training
3. Select base models
4. Choose meta-learner
5. Start ensemble training

**Note:** Requires Out-of-Fold (OOF) predictions from base models""",

        # ============================================================
        # HELP & CAPABILITIES
        # ============================================================
        'help': """**Dr. Myra - AI Clinical Assistant**

I'm your expert assistant for the Autoimmune ML Platform!

**🔬 I Can Help With:**

**Autoimmune Diseases:**
• SLE, RA, MS, Sjögren's, Hashimoto's
• Psoriasis, IBD, Celiac, Myasthenia Gravis
• Vasculitis, Antiphospholipid Syndrome
• Pathophysiology, diagnosis, biomarkers

**Clinical Biomarkers:**
• CRP, ESR, ANA, Anti-dsDNA
• Complement (C3, C4)
• RF, Anti-CCP, Anti-TPO
• All lab value interpretations

**ML Algorithms:**
• XGBoost, LightGBM, CatBoost
• Random Forest, SVM, KNN
• Logistic Regression, Neural Networks
• All 13 algorithms explained

**ML Metrics:**
• Accuracy, Precision, Recall, F1
• AUC-ROC, AUC-PR, Brier Score
• Confusion matrix interpretation

**Platform How-To:**
• How to upload data
• How to label data
• How to preprocess
• How to train models
• How to make predictions

**💡 Try Asking:**
• "What is SLE?"
• "How do I upload data?"
• "How do I train a model?"
• "What does low C3 mean?"
• "Explain my prediction"
• "What is this platform?" """,

        'how_to_label': """**How to Label Data (Step-by-Step)**

**Step 1: Navigate to Data Preparation**
• Click "Data Preparation" in sidebar
• Or go to: `/data-prep`

**Step 2: Select Your Dataset**
• Click on the dataset you want to label
• Make sure it's uploaded first

**Step 3: Go to Labeling Tab**
• Click the "Labeling" tab

**Step 4: Choose Labeling Method**

**Option A: Rule-Based Labeling (Recommended)**
• Select source column (e.g., SLEDAI)
• Define rules:
  - SLEDAI ≤ 4 → "Low" (low disease activity)
  - SLEDAI > 4 → "High" (high disease activity)
• Click "Apply Labels"

**Option B: Manual Labeling**
• Click on individual records
• Assign labels manually
• Good for edge cases

**Step 5: Verify Labels**
• Check label distribution chart
• Ensure balanced classes if possible
• Aim for 80%+ labeled before training

**Research Standard:**
• SLEDAI ≤ 4 = Low Disease Activity
• SLEDAI > 4 = High Disease Activity""",

        'how_to_preprocess': """**How to Preprocess Data (Step-by-Step)**

**Step 1: Navigate to Data Preparation**
• Click "Data Preparation" in sidebar
• Select your dataset

**Step 2: Go to Preprocessing Tab**
• Click the "Preprocessing" tab

**Step 3: Apply Preprocessing Steps (IN ORDER)**

**1. Filter Variables (First!)**
• Remove columns with >50% missing values
• Click "Apply Filter"
• Threshold: 0.5 (default)

**2. Impute Missing Values**
• Fill remaining missing values
• Method: Median (for numeric)
• Click "Apply Imputation"

**3. Winsorize Outliers**
• Cap extreme values at 1st/99th percentile
• Click "Apply Winsorize"
• Preserves distribution, removes outliers

**4. Standardize (Z-Score)**
• Scale all features to mean=0, std=1
• Click "Apply Normalize"
• Method: Standard (z-score)

**Why This Order:**
Filter → Impute → Winsorize → Standardize
(Can't standardize missing values!)

**Research Standard:**
This pipeline follows validated autoimmune disease research preprocessing methodology.""",

        'how_to_train': """**How to Train ML Models (Step-by-Step)**

**Prerequisites:**
✅ Data uploaded
✅ Labels applied
✅ Preprocessing done

**Step 1: Navigate to Training Jobs**
• Click "Training Jobs" in sidebar
• Or go to: `/training`

**Step 2: Prepare Dataset**
• Click "Prepare Dataset"
• Select your batch (dataset)
• Choose target column (e.g., labels_disease_classification)
• Set test size: 0.35 (35% for testing)
• Click "Prepare"

**Step 3: Select Algorithm**
• Choose from 13 algorithms:
  - XGBoost (recommended)
  - LightGBM (fast)
  - Random Forest (robust)
  - Logistic Regression (interpretable)
  - And 9 more!

**Step 4: Configure Training**
• Enable Optuna HPO (optional but recommended)
• Set trials: 30 (default)
• Set CV folds: 5 (default)

**Step 5: Start Training**
• Click "Train Model"
• Monitor progress in real-time
• Wait for completion

**Step 6: View Results**
• Check OOF AUC (cross-validation score)
• Check Test AUC (held-out test score)
• Compare with other models

**Pro Tips:**
• Train multiple models to compare
• Use ensemble for best performance
• XGBoost/LightGBM usually perform best""",

        'how_to_predict': """**How to Make Predictions (Step-by-Step)**

**Prerequisites:**
✅ At least one model trained

**Option A: Single Patient Prediction**

**Step 1:** Go to Predictions page
**Step 2:** Select trained model
**Step 3:** Enter patient feature values
**Step 4:** Click "Predict"
**Step 5:** View prediction + confidence score

**Option B: Batch Prediction**

**Step 1:** Go to Batch Prediction page
**Step 2:** Select trained model
**Step 3:** Upload CSV with patient data
  - Must have same columns as training data
**Step 4:** Click "Run Predictions"
**Step 5:** Download results CSV

**Understanding Results:**
• **Prediction:** Predicted class (Low/High)
• **Confidence:** Model certainty (0-100%)
• **Probabilities:** Per-class probabilities

**Download History:**
• All predictions saved automatically
• Go to Prediction History
• Click Download to export CSV"""
    }
    
    def _fallback_response(
        self,
        user_message: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """Comprehensive knowledge base response - answers virtually any question"""
        
        message_lower = user_message.lower()
        response = None

        # ============================================================
        # DATA-AWARE: Answer questions about the user's own platform data
        # (context['platform_data'] is injected by the /chat endpoint)
        # ============================================================
        platform = (context or {}).get("platform_data") if context else None
        if platform:
            models = platform.get("trained_models", [])
            best   = platform.get("best_model")

            # "my models" / "what have I trained" / "list models"
            if any(w in message_lower for w in [
                'my model', 'trained model', 'list model', 'what model',
                'which model', 'show model', 'available model', 'have i trained',
                'models i', 'how many model',
            ]):
                if not models:
                    response = "You haven't trained any models yet. Go to **Training Jobs** to train your first base learner!"
                else:
                    lines = []
                    for m in models:
                        auc = m.get('test_auc') or m.get('oof_auc')
                        auc_str = f"{auc*100:.2f}%" if auc else "N/A"
                        tag = "🔵 Ensemble" if m.get('type') == 'ensemble' else "⚙️ Base"
                        lines.append(f"• **{m['name']}** ({tag}) — AUC: {auc_str}")
                    response = (
                        f"You have **{len(models)} trained model(s)**:\n\n"
                        + "\n".join(lines)
                        + "\n\nUse **Model Comparison** to compare them side-by-side."
                    )

            # "best model" / "which model is best" / "top model"
            elif any(w in message_lower for w in [
                'best model', 'top model', 'highest auc', 'best performance',
                'which is best', 'winner', 'recommend model', 'most accurate',
            ]):
                if not best:
                    response = "No trained models found yet. Train your first model in **Training Jobs**!"
                else:
                    auc = best.get('test_auc') or best.get('oof_auc')
                    auc_str = f"{auc*100:.2f}%" if auc else "N/A"
                    tag = "Ensemble (meta-learner)" if best.get('type') == 'ensemble' else "Base Learner"
                    response = (
                        f"Your best-performing model is **{best['name']}** ({tag}) "
                        f"with AUC **{auc_str}**.\n\n"
                        "You can explore its feature importances in **Explainability**."
                    )

            # "compare models" / "model comparison"
            elif any(w in message_lower for w in [
                'compare model', 'compare my', 'comparison', 'side by side',
                'vs ', ' versus ', 'rank model', 'model ranking',
            ]):
                if not models:
                    response = "No models trained yet. Train base learners first, then visit **Comparison**."
                else:
                    sorted_models = sorted(
                        models,
                        key=lambda m: m.get('test_auc') or m.get('oof_auc') or 0,
                        reverse=True,
                    )
                    lines = []
                    for i, m in enumerate(sorted_models, 1):
                        auc = m.get('test_auc') or m.get('oof_auc')
                        auc_str = f"{auc*100:.2f}%" if auc else "N/A"
                        tag = "🔵" if m.get('type') == 'ensemble' else "⚙️"
                        lines.append(f"{i}. {tag} **{m['name']}** — AUC {auc_str}")
                    response = (
                        "**Model Ranking (by AUC)**:\n\n"
                        + "\n".join(lines)
                        + "\n\n🔵 = Ensemble  ⚙️ = Base Learner\n"
                        "Open **Model Comparison** for detailed charts."
                    )

            # "my results" / "training results" / "performance"
            elif any(w in message_lower for w in [
                'my result', 'my performance', 'training result', 'my score',
                'my auc', 'my f1', 'metrics', 'how well',
            ]):
                if not models:
                    response = "No completed training runs found. Start a run in **Training Jobs**!"
                else:
                    lines = []
                    for m in models[:5]:  # show top 5
                        auc = m.get('test_auc') or m.get('oof_auc')
                        f1  = m.get('test_f1')
                        parts = []
                        if auc: parts.append(f"AUC {auc*100:.1f}%")
                        if f1:  parts.append(f"F1 {f1*100:.1f}%")
                        lines.append(f"• **{m['name']}**: {', '.join(parts) or 'metrics unavailable'}")
                    response = (
                        "**Your Training Results**:\n\n"
                        + "\n".join(lines)
                        + ("\n\n_(showing top 5 most recent)_" if len(models) > 5 else "")
                    )

        # ============================================================
        # AUTOIMMUNE DISEASES
        # ============================================================
        # If platform data already answered the question, skip the keyword chain
        if response is not None:
            return {
                "response": response,
                "model": "Dr. Myra (Platform Knowledge)",
                "device": "cpu",
                "tokens_generated": len(response.split()),
            }

        if any(word in message_lower for word in ['what is sle', 'lupus', 'systemic lupus']):
            response = self.KNOWLEDGE_BASE['sle']
        
        elif any(word in message_lower for word in ['rheumatoid', 'arthritis', ' ra ', 'joint disease']):
            response = self.KNOWLEDGE_BASE['rheumatoid_arthritis']
        
        elif any(word in message_lower for word in ['multiple sclerosis', ' ms ', 'demyelinating']):
            response = self.KNOWLEDGE_BASE['multiple_sclerosis']
        
        elif any(word in message_lower for word in ['type 1 diabetes', 't1d', 'insulin dependent', 'juvenile diabetes']):
            response = self.KNOWLEDGE_BASE['type1_diabetes']
        
        elif any(word in message_lower for word in ['hashimoto', 'thyroiditis', 'hypothyroid']):
            response = self.KNOWLEDGE_BASE['hashimoto']
        
        elif any(word in message_lower for word in ['sjogren', 'sjögren', 'dry eye', 'sicca']):
            response = self.KNOWLEDGE_BASE['sjogren']
        
        elif any(word in message_lower for word in ['psoriasis', 'psoriatic', 'skin plaque']):
            response = self.KNOWLEDGE_BASE['psoriasis']
        
        elif any(word in message_lower for word in ['ibd', 'crohn', 'ulcerative colitis', 'inflammatory bowel']):
            response = self.KNOWLEDGE_BASE['ibd']
        
        elif any(word in message_lower for word in ['celiac', 'coeliac', 'gluten']):
            response = self.KNOWLEDGE_BASE['celiac']
        
        elif any(word in message_lower for word in ['myasthenia', 'neuromuscular', 'achr']):
            response = self.KNOWLEDGE_BASE['myasthenia']
        
        elif any(word in message_lower for word in ['vasculitis', 'anca', 'vessel inflammation']):
            response = self.KNOWLEDGE_BASE['vasculitis']
        
        elif any(word in message_lower for word in ['antiphospholipid', 'aps', 'thrombosis', 'lupus anticoagulant']):
            response = self.KNOWLEDGE_BASE['antiphospholipid']
        
        # ============================================================
        # ML ALGORITHMS
        # ============================================================
        elif any(word in message_lower for word in ['xgboost', 'xgb', 'extreme gradient']):
            response = self.KNOWLEDGE_BASE['xgboost']
        
        elif any(word in message_lower for word in ['lightgbm', 'lgbm', 'light gradient']):
            response = self.KNOWLEDGE_BASE['lightgbm']
        
        elif any(word in message_lower for word in ['catboost', 'categorical boosting']):
            response = self.KNOWLEDGE_BASE['catboost']
        
        elif any(word in message_lower for word in ['random forest', ' rf ', 'forest ensemble']):
            response = self.KNOWLEDGE_BASE['random_forest']
        
        elif any(word in message_lower for word in ['logistic regression', 'logistic', 'logreg']):
            response = self.KNOWLEDGE_BASE['logistic_regression']
        
        elif any(word in message_lower for word in [' svm ', 'support vector', 'kernel']):
            response = self.KNOWLEDGE_BASE['svm']
        
        elif any(word in message_lower for word in [' knn ', 'k-nearest', 'nearest neighbor']):
            response = self.KNOWLEDGE_BASE['knn']
        
        elif any(word in message_lower for word in ['mlp', 'neural network', 'perceptron', 'deep learning']):
            response = self.KNOWLEDGE_BASE['mlp']
        
        elif any(word in message_lower for word in ['decision tree', 'single tree']):
            response = self.KNOWLEDGE_BASE['decision_tree']
        
        elif any(word in message_lower for word in ['adaboost', 'adaptive boosting']):
            response = self.KNOWLEDGE_BASE['adaboost']
        
        elif any(word in message_lower for word in ['gradient boosting', ' gbc ', 'gradient boost classifier']):
            response = self.KNOWLEDGE_BASE['gradient_boosting']
        
        elif any(word in message_lower for word in ['ridge classifier', 'ridge regression']):
            response = self.KNOWLEDGE_BASE['ridge']
        
        elif any(word in message_lower for word in [' lda ', 'linear discriminant', 'discriminant analysis']):
            response = self.KNOWLEDGE_BASE['lda']
        
        # ============================================================
        # ML METRICS
        # ============================================================
        elif any(word in message_lower for word in ['accuracy', 'how accurate']):
            response = self.KNOWLEDGE_BASE['accuracy']
        
        elif any(word in message_lower for word in ['precision', 'positive predictive', ' ppv ']):
            response = self.KNOWLEDGE_BASE['precision']
        
        elif any(word in message_lower for word in ['recall', 'sensitivity', 'true positive rate', ' tpr ']):
            response = self.KNOWLEDGE_BASE['recall']
        
        elif any(word in message_lower for word in ['f1', 'f-score', 'f measure', 'f-1']):
            response = self.KNOWLEDGE_BASE['f1_score']
        
        elif any(word in message_lower for word in ['auc-roc', 'auc roc', 'auroc', 'roc curve', 'receiver operating']):
            response = self.KNOWLEDGE_BASE['auc_roc']
        
        elif any(word in message_lower for word in ['auc-pr', 'auc pr', 'precision-recall curve', 'pr curve', 'aupr']):
            response = self.KNOWLEDGE_BASE['auc_pr']
        
        elif any(word in message_lower for word in ['specificity', 'true negative rate', ' tnr ']):
            response = self.KNOWLEDGE_BASE['specificity']
        
        elif any(word in message_lower for word in ['brier', 'calibration score']):
            response = self.KNOWLEDGE_BASE['brier_score']
        
        elif any(word in message_lower for word in ['confusion matrix', 'tp ', ' fn ', ' fp ', ' tn ']):
            response = self.KNOWLEDGE_BASE['confusion_matrix']
        
        # ============================================================
        # BIOMARKERS & LAB VALUES
        # ============================================================
        elif any(word in message_lower for word in ['crp', 'c-reactive', 'reactive protein']):
            response = self.KNOWLEDGE_BASE['crp']
        
        elif any(word in message_lower for word in ['esr', 'sedimentation rate', 'sed rate']):
            response = self.KNOWLEDGE_BASE['esr']
        
        elif any(word in message_lower for word in [' c3', ' c4', 'complement', 'ch50']):
            response = self.KNOWLEDGE_BASE['complement']
        
        elif any(word in message_lower for word in [' ana ', 'antinuclear', 'nuclear antibod']):
            response = self.KNOWLEDGE_BASE['ana']
        
        elif any(word in message_lower for word in ['anti-dsdna', 'dsdna', 'double stranded dna', 'ds-dna']):
            response = self.KNOWLEDGE_BASE['anti_dsdna']
        
        # ============================================================
        # PLATFORM FEATURES
        # ============================================================
        elif any(word in message_lower for word in ['upload', 'import', 'ingestion', 'data catalog', 'how do i add data', 'add new data']):
            response = """**How to Upload Data (Step-by-Step)**

**Step 1: Navigate to Data Catalog**
• Click "Data Catalog" in the left sidebar
• Or go to: `/data-catalog`

**Step 2: Upload Your File**
• Click the "Upload" button (top right)
• Drag & drop your file or click "Browse"
• Supported formats: Excel (.xlsx), CSV (.csv)

**Step 3: Preview & Verify**
• Review the data preview (first 100 rows)
• Check column types are detected correctly
• Verify no critical data is missing

**Step 4: Save to Database**
• Click "Save to Database"
• Data is stored in staging first
• Confirm to move to permanent storage

**Best Practices:**
✅ Include patient IDs for tracking
✅ Use consistent column naming
✅ Remove PHI/sensitive data before upload
✅ Maximum 500MB per file"""

        elif any(word in message_lower for word in ['how to label', 'labeling', 'label data', 'apply label', 'sledai label']):
            response = """**How to Label Data (Step-by-Step)**

**Step 1: Navigate to Data Preparation**
• Click "Data Preparation" in sidebar
• Select your uploaded dataset

**Step 2: Go to Labeling Tab**
• Click the "Labeling" tab

**Step 3: Rule-Based Labeling (Recommended)**
• Select source column (e.g., SLEDAI)
• Define rules:
  - SLEDAI ≤ 4 → "Low" (low disease activity)
  - SLEDAI > 4 → "High" (high disease activity)
• Click "Apply Labels"

**Step 4: Verify Labels**
• Check label distribution chart
• Aim for 80%+ labeled before training

**Research Standard:**
• SLEDAI ≤ 4 = Low Disease Activity
• SLEDAI > 4 = High Disease Activity"""

        elif any(word in message_lower for word in [
            'what is this platform', 'platform overview', 'what can this do',
            'about this platform', 'about the platform', 'usm platform',
            'explain this platform', 'explain the platform', 'explain platform',
            'what is this system', 'describe platform', 'describe this platform',
            'tell me about this', 'tell me about the platform', 'regarding this platform',
            'what does this platform', 'how does this platform', 'this platform do',
        ]):
            response = """**Autoimmune ML Platform Overview**

**What This Platform Does:**
End-to-end ML platform for autoimmune disease classification and research.

**Complete Workflow:**

**1. Data Upload (Data Catalog)**
• Upload Excel/CSV patient data
• Automatic column type detection

**2. Labeling (Data Preparation)**
• Rule-based labeling (SLEDAI ≤4 = Low, >4 = High)
• View label distribution

**3. Preprocessing (Data Preparation)**
• Filter variables (>50% missing)
• Imputation (median/mode)
• Winsorization (outliers)
• Z-score standardization

**4. ML Training (Training Jobs)**
• 13 algorithms available
• 5-fold cross-validation
• 65/35 train/test split

**5. Predictions**
• Single patient prediction
• Batch prediction (CSV upload)

**6. Explainability (SHAP)**
• Feature importance
• Why model made prediction"""
        
        elif any(word in message_lower for word in ['preprocess', 'imputation', 'missing value', 'standardiz', 'normali', 'winsoriz', 'how to preprocess']):
            response = self.KNOWLEDGE_BASE['preprocessing']
        
        elif any(word in message_lower for word in ['feature engineering', 'create feature', 'composite feature']):
            response = self.KNOWLEDGE_BASE['feature_engineering']
        
        elif any(word in message_lower for word in ['shap', 'shapley', 'explainability', 'interpret', 'explain model', 'why predict']):
            response = self.KNOWLEDGE_BASE['shap']
        
        elif any(word in message_lower for word in ['model comparison', 'compare model', 'which model', 'best model']):
            response = self.KNOWLEDGE_BASE['model_comparison']
        
        elif any(word in message_lower for word in ['train model', 'training', 'how to train', 'algorithm', '13 model']):
            response = self.KNOWLEDGE_BASE['training']
        
        elif any(word in message_lower for word in ['optuna', 'hyperparameter', 'hpo', 'tuning', 'optimization']):
            response = self.KNOWLEDGE_BASE['optuna']
        
        elif any(word in message_lower for word in ['ensemble', 'stacking', 'meta-learner', 'combine model']):
            response = self.KNOWLEDGE_BASE['ensemble']
        
        # ============================================================
        # SLEDAI / DISEASE ACTIVITY
        # ============================================================
        elif any(word in message_lower for word in ['sledai', 'disease activity', 'activity score', 'severity score']):
            response = """**SLEDAI (SLE Disease Activity Index)**

**Scoring:**
• 0-4: **Mild/Inactive** - Maintenance therapy
• 5-12: **Moderate** - Treatment adjustment needed
• >12: **Severe/Active** - Urgent intervention

**24 Items Assessed:**
• CNS: Seizure, psychosis, visual disturbance, headache, CVA
• Vascular: Vasculitis
• Musculoskeletal: Arthritis, myositis
• Renal: Urinary casts, hematuria, proteinuria, pyuria
• Skin: New rash, alopecia, mucosal ulcers
• Serositis: Pleurisy, pericarditis
• Labs: Low complement, increased anti-dsDNA
• Hematologic: Thrombocytopenia, leukopenia

**Clinical Use:**
• Track disease activity over time
• Guide treatment decisions
• Used as ML training labels in this platform"""
        
        # ============================================================
        # GETTING STARTED / NEW USER GUIDE
        # ============================================================
        elif any(phrase in message_lower for phrase in [
            'what should i do first', 'what do i do first', 'where do i start',
            'where to start', 'how do i start', 'how to start', 'how to begin',
            'get started', 'getting started', 'first step', 'first thing',
            'new user', 'new to this', 'start here', 'guide me',
            'walk me through', 'just started', 'beginner', 'onboard',
        ]):
            response = """**Getting Started — Recommended First Steps**

If you're new to the platform, follow this order:

**Step 1: Upload Your Data** → Data Pipeline › Data Catalog
• Upload your patient CSV or Excel file
• The system auto-detects column types (numeric, categorical, dates)

**Step 2: Assign Labels** → Data Preparation › Rule-Based Labeling
• Assign severity labels using clinical rules (e.g. SLEDAI ≤4 = Low, >4 = High)
• Aim for ≥80% labeled rows before proceeding

**Step 3: Preprocess** → Data Preparation › Preprocessing
• Run the 4-step pipeline: Filter → Impute → Winsorize → Standardize
• Default settings follow validated autoimmune disease research methodology

**Step 4: Train a Model** → Training Jobs
• Select your preprocessed dataset and choose an algorithm
• XGBoost or LightGBM are recommended for first runs
• Enable Optuna HPO for better hyperparameter tuning
• Training runs in the background — check progress on the same page

**Step 5: Explore Results** → Explainability
• Review AUC-ROC and F1-score in the training results
• Use SHAP to see which features drove predictions
• Ask me: *"which model is best?"* for a performance summary

What step are you on right now?"""

        # ============================================================
        # HELP / WHAT CAN I ASK
        # ============================================================
        elif any(word in message_lower for word in ['help', 'what can', 'how can you', 'capabilities', 'what do you', 'what question']):
            response = self.KNOWLEDGE_BASE['help']
        
        # ============================================================
        # GREETINGS
        # ============================================================
        elif any(phrase in message_lower for phrase in [
            'who are you', 'what are you', 'what is your name', 'your name',
            'introduce yourself', 'tell me about yourself', 'who is dr myra',
            'what do you do', 'who made you', 'who created you', 'who built you',
            'who developed you', 'are you an ai', 'are you a bot', 'are you human',
        ]):
            response = """I am **Dr. Myra**, an AI-powered clinical ML assistant specializing in autoimmune disease research and predictive modeling.

I was developed by **Aras Integrasi Sdn. Bhd.**

I can help you with:
• **Autoimmune diseases** — SLE, RA, MS, biomarkers, SLEDAI interpretation
• **Your trained models** — AUC scores, performance comparison, best model
• **Platform workflows** — training, preprocessing, SHAP explainability
• **ML concepts** — how XGBoost, LightGBM, Random Forest, etc. work

What would you like to explore?"""

        elif any(word in message_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
            response = """Hello! I'm **Dr. Myra**, your AI clinical assistant for the Autoimmune ML Platform.

I can help you with:
• **Clinical questions** — SLE, RA, MS, biomarkers, SLEDAI interpretation
• **Your trained models** — AUC scores, performance comparison, best model
• **Platform workflows** — training, preprocessing, SHAP explainability
• **ML concepts** — how XGBoost, LightGBM, Random Forest, etc. work

What would you like to know?"""
        
        # ============================================================
        # THANKS
        # ============================================================
        elif any(word in message_lower for word in ['thank', 'thanks', 'appreciate']):
            response = """You're welcome! 🙂

Feel free to ask more questions about:
• Autoimmune diseases & biomarkers
• ML algorithms & metrics
• Platform features & workflows

I'm here to help with your research!"""
        
        # ============================================================
        # PREDICTION / SEVERITY INTERPRETATION
        # ============================================================
        elif any(word in message_lower for word in ['how to predict', 'make prediction', 'run prediction', 'batch predict']):
            response = """**How to Make Predictions (Step-by-Step)**

**Prerequisites:**
✅ At least one model trained

**Option A: Single Patient Prediction**
1. Go to **Predictions** page in sidebar
2. Select trained model from dropdown
3. Enter patient feature values
4. Click **"Predict"**
5. View prediction + confidence score

**Option B: Batch Prediction**
1. Go to **Batch Prediction** page
2. Select trained model from dropdown
3. Upload CSV with patient data
   (must have same columns as training data)
4. Click **"Run Predictions"**
5. Download results CSV

**Understanding Results:**
• **Prediction:** Predicted class (Low/High)
• **Confidence:** Model certainty (0-100%)
• **Probabilities:** Per-class probabilities

**Tip:** Use SHAP explainability to understand why the model made its prediction!"""

        elif any(word in message_lower for word in ['predict', 'what does this', 'severity', 'risk']):
            response = """**Understanding Predictions**

**Severity Classes:**
• **Mild (SLEDAI 0-4):** Minimal symptoms, stable
• **Moderate (SLEDAI 5-12):** Active symptoms, monitoring needed
• **Severe (SLEDAI >12):** Multiple organ involvement, urgent care

**Confidence Interpretation:**
• >80%: High confidence
• 60-80%: Moderate confidence
• <60%: Low confidence, use clinical judgment

**Key Contributing Factors:**
• Inflammatory markers (CRP, ESR)
• Complement levels (C3, C4)
• Autoantibodies (anti-dsDNA)
• Organ involvement indicators

**Next Steps:**
View **SHAP values** to see which features influenced your specific prediction.
Go to **Explainability** tab for detailed analysis."""
        
        # ============================================================
        # WHAT IS AUTOIMMUNE / GENERAL
        # ============================================================
        elif any(word in message_lower for word in ['autoimmune', 'what is auto-immune', 'immune system attack']):
            response = """**Autoimmune Diseases**

**What They Are:**
Conditions where the immune system mistakenly attacks healthy tissues.

**Common Autoimmune Diseases:**
• **SLE (Lupus):** Multi-organ, butterfly rash, nephritis
• **Rheumatoid Arthritis:** Joints, symmetric polyarthritis
• **Multiple Sclerosis:** CNS, demyelination
• **Type 1 Diabetes:** Pancreas, insulin deficiency
• **Hashimoto's:** Thyroid, hypothyroidism
• **Sjögren's:** Exocrine glands, dry eyes/mouth
• **Psoriasis:** Skin, joint involvement
• **IBD:** GI tract, Crohn's/UC

**Common Features:**
• Autoantibodies (ANA, RF, anti-CCP)
• Inflammation (elevated CRP, ESR)
• Chronic, relapsing-remitting course
• Female predominance (most types)
• Genetic + environmental triggers

Ask about any specific disease for detailed information!"""
        
        # ============================================================
        # DEFAULT FALLBACK - Still comprehensive
        # ============================================================
        else:
            response = """I didn't catch that — could you rephrase?

I can help with:
• **Your models** — "show my trained models", "which model is best?"
• **Diseases** — "what is SLE?", "explain rheumatoid arthritis"
• **ML concepts** — "how does XGBoost work?", "explain AUC-ROC"
• **Biomarkers** — "what does low C3 mean?", "explain anti-dsDNA"
• **Platform** — "explain this platform", "how do I train a model?", "how does SHAP work?"

Try asking something like: _"What is the best model I've trained?"_ or _"Explain SHAP values."_"""
        
        return {
            'response': response,
            'model': 'dr-myra-knowledge-base',
            'device': 'cpu',
            'tokens_generated': 0,
            'temperature': 0.0
        }
    
    def _fallback_prediction_explanation(self, prediction_result: Dict) -> str:
        """Fallback explanation when Gemma is unavailable"""
        
        prediction = prediction_result.get('prediction', 'Unknown')
        confidence = prediction_result.get('confidence', 0) * 100
        
        explanation = f"""
Clinical Interpretation:

The model predicts **{prediction}** disease severity with {confidence:.1f}% confidence.

This prediction is based on machine learning analysis of clinical features including:
- Laboratory biomarkers (ANA, Anti-dsDNA, ESR, CRP, complement levels)
- Clinical manifestations (organ involvement)
- Disease activity indicators (SLEDAI score)
- Immunologic markers

Recommendation: Review the SHAP feature importance values to understand which specific factors most influenced this prediction. Always integrate this prediction with comprehensive clinical assessment and patient history.

Note: This is a decision support tool. Final diagnosis and treatment decisions should be made by qualified physicians.
"""
        
        return explanation
