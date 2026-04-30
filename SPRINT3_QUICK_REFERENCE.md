# Sprint 3 - Quick Reference Card

## 🎯 What's New Today

### ✅ **3 New ML Models**
- Ridge Classifier
- Linear Discriminant Analysis  
- Gradient Boosting

### ✅ **Clinical Scorecard System (USMA-47)**
- Risk Score: 0-100
- Risk Groups: Low/Moderate/High/Very High
- Clinical Recommendations
- Feature Contributions

### ✅ **Model Comparison Dashboard (USMA-43)**
- Compare all models side-by-side
- Rank by any metric
- Best model selection

---

## 📁 Files to Transfer (7 files)

```
✓ app/ml/training/base_models.py          (MODIFIED)
✓ app/schemas/training.py                  (MODIFIED)
✓ app/main.py                              (MODIFIED)
✓ app/services/scorecard_service.py        (NEW)
✓ app/api/endpoints/scorecard.py           (NEW)
✓ test_scorecard.py                        (NEW)
✓ FILE_TRANSFER_CHECKLIST.txt              (NEW)
```

---

## 🚀 Quick Deploy (3 Steps)

### Step 1: Transfer Files
```bash
# Use WinSCP to transfer files to:
# 100.106.132.15:/home/usm/usm-autoimmune-ml-platform/
```

### Step 2: Restart Containers
```bash
ssh usm@100.106.132.15
cd /home/usm/usm-autoimmune-ml-platform
docker-compose down
docker-compose up -d --build
```

### Step 3: Test
```bash
# Check Swagger UI
http://100.106.132.15:8001/docs

# Run tests
python3 test_scorecard.py --test all
```

---

## 🔌 New API Endpoints (6)

### Scorecard
```
POST   /api/v1/ml/scorecard              - Generate scorecard
POST   /api/v1/ml/scorecard/batch        - Batch scorecards
```

### Model Comparison
```
POST   /api/v1/ml/compare                - Compare models
GET    /api/v1/ml/compare/detailed/{model} - Model details
GET    /api/v1/ml/models/available       - List models
```

---

## 🧪 Test Commands

```bash
# Test scorecard with XGBoost
python3 test_scorecard.py --test scorecard --model xgboost

# Test model comparison
python3 test_scorecard.py --test compare

# Test all features
python3 test_scorecard.py --test all
```

---

## 📊 API Usage Example

### Generate Scorecard
```bash
curl -X POST "http://100.106.132.15:8001/api/v1/ml/scorecard" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "xgboost",
    "version": "v1",
    "patient_data": {
      "demographics_age": 35,
      "lab_results_ESR": 45,
      "disease_activity_SLEDAI_score": 8
    }
  }'
```

### Compare Models
```bash
curl -X POST "http://100.106.132.15:8001/api/v1/ml/compare" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model_names": ["xgboost", "lightgbm", "random_forest"],
    "metric": "test_auc"
  }'
```

---

## ✅ All 11 Models Supported

| Model | Type | Status |
|-------|------|--------|
| XGBoost | Tree | ✅ Ready |
| LightGBM | Tree | ✅ Ready |
| Random Forest | Tree | ✅ Ready |
| Gradient Boosting | Tree | ✅ **New** |
| AdaBoost | Tree | ✅ Ready |
| Decision Tree | Tree | ✅ Ready |
| SVM | Linear | ✅ Ready |
| MLP | Linear | ✅ Ready |
| KNN | Linear | ✅ Ready |
| Logistic Regression | Linear | ✅ Ready |
| Ridge Classifier | Linear | ✅ **New** |
| Linear Discriminant | Linear | ✅ **New** |

---

## 🎓 Risk Score Interpretation

| Score | Risk Group | Action |
|-------|------------|--------|
| 0-25 | Low Risk | Routine monitoring |
| 25-50 | Moderate Risk | Close monitoring |
| 50-75 | High Risk | Therapy escalation |
| 75-100 | Very High Risk | Urgent intervention |

---

## 📚 Documentation Files

- `SPRINT3_IMPLEMENTATION_SUMMARY.md` - Complete summary
- `FILE_TRANSFER_CHECKLIST.txt` - Transfer instructions
- `SPRINT3_QUICK_REFERENCE.md` - This file

---

## 🎉 Sprint 3 Status

| Ticket | Feature | Status |
|--------|---------|--------|
| USMA-42 | Test evaluation | ✅ |
| USMA-44 | Ensemble test eval | ✅ |
| USMA-75 | MinIO persistence | ✅ |
| USMA-109 | Train endpoint | ✅ |
| USMA-46 | Prediction API | ✅ |
| USMA-50 | SHAP + Gemma | ✅ |
| **USMA-47** | **Scorecard System** | ✅ **Done** |
| **USMA-43** | **Model Comparison** | ✅ **Done** |

---

## 🔧 Troubleshooting

### Issue: Containers won't start
```bash
docker-compose logs fastapi -f
# Look for import errors or missing dependencies
```

### Issue: Endpoints return 404
```bash
# Check router is registered in main.py
docker exec -it usm-autoimmune-ml-platform-fastapi-1 bash
python3 -c "from app.main import app; print([r.path for r in app.routes])"
```

### Issue: Model not found
```bash
# Check MinIO has models
curl http://100.106.132.15:8001/api/v1/ml/models/available
```

---

## 📞 Support

See detailed documentation in:
- `FILE_TRANSFER_CHECKLIST.txt` - Complete deployment guide
- `SPRINT3_IMPLEMENTATION_SUMMARY.md` - Technical details
- Swagger UI: `http://100.106.132.15:8001/docs`

---

🚀 **Ready for deployment!**
