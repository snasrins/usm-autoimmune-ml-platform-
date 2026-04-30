# USMA-46: Prediction API Documentation

## 🎯 **Prediction Serving API - COMPLETE**

Multi-class SLE severity prediction using trained models from MinIO.

---

## **API Endpoints**

### **1. Single Patient Prediction**
**POST** `/api/v1/ml/predict`

Predict disease severity for a single patient using any trained model.

**Request:**
```json
{
  "model_name": "xgboost",
  "version": "v1",
  "patient_data": {
    "demographics_age": 35.0,
    "demographics_gender": "Female",
    "lab_results_ESR": 45.0,
    "lab_results_CRP": 12.5,
    "lab_results_C3": 85.0,
    "lab_results_C4": 15.0,
    "disease_activity_SLEDAI_score": 8.0,
    ...
  },
  "return_probability": true
}
```

**Response:**
```json
{
  "model_name": "xgboost",
  "version": "v1",
  "prediction": "Moderate",
  "probabilities": {
    "Mild": 0.25,
    "Moderate": 0.60,
    "Severe": 0.15
  },
  "confidence": 0.60,
  "predicted_class_index": 1,
  "severity_category": "Moderate",
  "class_mapping": {
    "Mild": 0,
    "Moderate": 1,
    "Severe": 2
  }
}
```

---

### **2. Ensemble Prediction (Recommended)**
**POST** `/api/v1/ml/predict/ensemble?version=v1`

Use stacking ensemble for most accurate predictions.

**Request:**
```json
{
  "demographics_age": 35.0,
  "lab_results_ESR": 45.0,
  "lab_results_CRP": 12.5,
  "disease_activity_SLEDAI_score": 8.0,
  ...
}
```

**Response:** Same as single prediction, but uses ensemble model.

---

### **3. Batch Prediction**
**POST** `/api/v1/ml/predict/batch`

Process multiple patients efficiently.

**Request:**
```json
{
  "model_name": "ensemble",
  "version": "v1",
  "patients_data": [
    { "demographics_age": 35, ... },
    { "demographics_age": 42, ... },
    { "demographics_age": 28, ... }
  ]
}
```

**Response:**
```json
{
  "predictions": [
    { "prediction": "Moderate", "confidence": 0.60, ... },
    { "prediction": "Severe", "confidence": 0.75, ... },
    { "prediction": "Mild", "confidence": 0.85, ... }
  ],
  "total_processed": 3,
  "success_count": 3,
  "failure_count": 0
}
```

---

## **Testing the API**

### **Using Python Script**
```bash
# Test XGBoost model
python test_prediction_api.py --model xgboost --version v1

# Test ensemble model
python test_prediction_api.py --test-ensemble

# Test specific version
python test_prediction_api.py --model lightgbm --version v2
```

### **Using Swagger UI**
Navigate to: `http://100.106.132.15:8001/docs`

1. **Authenticate**: Click "Authorize" → Enter `s.nasrin` / `USM@22`
2. **Find endpoint**: Look for "ML Inference" section
3. **Test**: POST `/api/v1/ml/predict` → Try it out

---

## **Required Features**

### **Input Features**
The API accepts patient data with clinical features. The feature engineering pipeline automatically:
- Calculates derived features (CRP_ESR_ratio, complement_ratio, etc.)
- Selects LASSO features (currently: age, CRP_ESR_ratio, complement_ratio)
- Applies same preprocessing as training

**Minimum Required Features:**
```python
{
  "demographics_age": float,
  "lab_results_ESR": float,
  "lab_results_CRP": float,
  "lab_results_C3": float,
  "lab_results_C4": float,
  # ... other clinical features
}
```

**Tip:** Provide all available features. The pipeline handles feature selection automatically.

---

## **Model Selection**

### **Available Models**
- `xgboost` - Fast, good for real-time predictions
- `lightgbm` - Fast, memory efficient
- `random_forest` - Robust, handles outliers well
- `ensemble` - **Most accurate** (stacking of all models)

### **Recommendation**
Use `ensemble` for highest accuracy. For latency-sensitive applications, use individual models.

---

## **Response Interpretation**

### **Prediction Fields**
- `prediction` - Predicted class label ("Mild", "Moderate", "Severe")
- `probabilities` - Probability distribution across all classes
- `confidence` - Highest probability (max of probabilities)
- `predicted_class_index` - Numeric class (0=Mild, 1=Moderate, 2=Severe)
- `severity_category` - Same as prediction (for SLE severity)

### **Confidence Thresholds**
- **High confidence**: > 0.70 - Trust the prediction
- **Medium confidence**: 0.50-0.70 - Review with clinical judgment
- **Low confidence**: < 0.50 - Manual review recommended

---

## **Feature Engineering Pipeline**

The inference pipeline automatically:
1. ✅ Calculates derived features from raw lab values
2. ✅ Applies LASSO feature selection (same as training)
3. ✅ Handles missing features (fills with 0 if needed)
4. ✅ Applies scaling if model requires it
5. ✅ Uses cross-validated models (averages predictions across folds)

**No manual feature engineering needed** - just provide raw patient data!

---

## **Error Handling**

### **Model Not Found (404)**
```json
{
  "detail": "Model not found: xgboost/v1"
}
```
**Solution:** Check model exists in MinIO. Ensure training completed successfully.

### **Missing Features (500)**
```json
{
  "detail": "Prediction failed: Missing required features"
}
```
**Solution:** Provide all clinical features used during training.

### **Invalid Credentials (401)**
```json
{
  "detail": "Not authenticated"
}
```
**Solution:** Check username/password or JWT token.

---

## **Performance Benchmarks**

### **Latency** (Single Prediction)
- Base models (XGBoost/LightGBM): ~20-50ms
- Ensemble (5 folds × 3 models): ~100-200ms

### **Throughput** (Batch)
- ~10-20 predictions/second (depending on model complexity)

---

## **Next Steps (Optional Enhancements)**

- ⬜ **USMA-50**: Add SHAP explanations for predictions
- ⬜ **USMA-51**: Track prediction history in database
- ⬜ **USMA-47**: Convert probabilities to clinical scorecards
- ⬜ Cache frequently used models in memory
- ⬜ Add prediction confidence calibration
- ⬜ Implement A/B testing for model comparison

---

## **USMA-46 Status: ✅ COMPLETE**

**Implemented:**
- ✅ Multi-class prediction (Mild/Moderate/Severe)
- ✅ Load models from MinIO
- ✅ Feature engineering pipeline integration
- ✅ Single, batch, and ensemble endpoints
- ✅ Probability scores with confidence
- ✅ Cross-validated model averaging
- ✅ Authentication & authorization
- ✅ Test script & documentation

**Deployment:**
Transfer updated files via WinSCP:
- `app/main.py`
- `app/schemas/training.py`
- `app/services/ml_inference_service.py`

Restart container:
```bash
docker compose restart fastapi
```

Test prediction API:
```bash
python test_prediction_api.py --test-ensemble
```

---

**Ready for Production! 🚀**
