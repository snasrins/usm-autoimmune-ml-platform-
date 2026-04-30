"""
Example: Feature Engineering for Autoimmune Disease Classification
Shows how to use FeatureEngineeringPipeline with your labeled data
"""
from app.core.database import SessionLocal
from app.services.ml_bridge_service import MLBridgeService
from app.ml.feature_engineering_pipeline import FeatureEngineeringPipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pandas as pd

# 1. Load your labeled data
print("Step 1: Loading labeled data...")
db = SessionLocal()
bridge = MLBridgeService(db)

# Use the batch ID with 100 SLE labels
data_result = bridge.prepare_data_for_ml(
    import_batch_id="098c33a1-f2ff-4c05-8be5-2ba9f8eeef4f",
    target_column="labels_disease_classification",
    validate=True,
    drop_unlabeled=False
)

if not data_result['success']:
    print(f"❌ Error loading data: {data_result.get('error')}")
    exit(1)

df = data_result['df']
print(f"✅ Loaded {len(df)} records")
print(f"   Columns: {df.shape[1]}")
print(f"   Target: {data_result['target_column']}")

# 2. Create feature engineering pipeline
print("\nStep 2: Setting up feature engineering...")
pipeline = FeatureEngineeringPipeline(target_column='labels_disease_classification')

# Add biomarker ratios (if columns exist)
biomarker_cols = [col for col in df.columns if 'biomarkers_' in col]
print(f"   Found{len(biomarker_cols)} biomarker columns")

if 'biomarkers_crp' in df.columns and 'biomarkers_esr' in df.columns:
    pipeline.add_ratio_feature('crp_esr_ratio', 'biomarkers_crp', 'biomarkers_esr')
    print("   ✅ Added CRP/ESR ratio")

# Add hematology ratios (if columns exist)
if 'hematology_neutrophils' in df.columns and 'hematology_lymphocytes' in df.columns:
    pipeline.add_ratio_feature('nlr', 'hematology_neutrophils', 'hematology_lymphocytes')
    print("   ✅ Added Neutrophil-Lymphocyte Ratio (NLR)")

if 'hematology_platelets' in df.columns and 'hematology_lymphocytes' in df.columns:
    pipeline.add_ratio_feature('plr', 'hematology_platelets', 'hematology_lymphocytes')
    print("   ✅ Added Platelet-Lymphocyte Ratio (PLR)")

# Add disease duration (if date column exists)
if 'clinical_diagnosis_date' in df.columns:
    pipeline.add_temporal_feature(
        'disease_duration_years',
        'clinical_diagnosis_date',
        unit='years'
    )
    print("   ✅ Added disease duration")

# 3. Apply feature engineering
print("\nStep 3: Applying feature engineering...")
df_engineered = pipeline.fit_transform(df)
print(f"✅ Engineered features: {df_engineered.shape[1]} columns (was {df.shape[1]})")

# 4. Prepare data for ML
print("\nStep 4: Preparing for model training...")
target_col = 'labels_disease_classification'

# Separate features and target
X = df_engineered.drop(columns=[target_col, 'record_id', 'import_batch_id', 'dataset_type', 'created_at'], errors='ignore')
y = df_engineered[target_col]

# Remove any columns that are all NaN
X = X.dropna(axis=1, how='all')
print(f"✅ Feature matrix: {X.shape}")
print(f"   Label distribution: {y.value_counts().to_dict()}")

# 5. Train a simple model (if you have multiple classes)
if y.nunique() > 1:
    print("\nStep 5: Training Random Forest classifier...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Fill any remaining NaN with median
    X_train = X_train.fillna(X_train.median())
    X_test = X_test.fillna(X_train.median())  # Use training median for test
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    print("\n📊 Classification Report:")
    print(classification_report(y_test, y_pred))
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\n🔝 Top 10 Most Important Features:")
    print(feature_importance.head(10).to_string(index=False))
    
else:
    print(f"\n⚠️  Only one class found: {y.unique()[0]}")
    print("   Need data from multiple disease types to train classifier")
    print("   Current data: All SLE patients")
    print("\n💡 Next steps:")
    print("   1. Label more batches with different diseases (RA, SSc, etc.)")
    print("   2. Or use this for SLE-specific biomarker analysis")

db.close()
print("\n✅ Feature engineering example complete!")
print(f"\n📖 See FEATURE_ENGINEERING_GUIDE.md for more examples")
