"""
Test Research-Aligned Preprocessing Pipeline
Tests imputation, winsorization, composite features, and SLEDAI binary target

Usage:
    # Test with default settings (all preprocessing enabled)
    python3 test_preprocessing.py --batch_id 9161cd88-e7bb-4ec7-9577-a129cde949ae
    
    # Test SLEDAI binary target (study approach)
    python3 test_preprocessing.py --batch_id 9161cd88-e7bb-4ec7-9577-a129cde949ae --sledai-binary
    
    # Test without composite features
    python3 test_preprocessing.py --batch_id 9161cd88-e7bb-4ec7-9577-a129cde949ae --no-composite
"""
import requests
import json
import argparse
from typing import Dict


# API Configuration
API_BASE_URL = "http://100.106.132.15:8001"
USERNAME = "s.nasrin"
PASSWORD = "USM@22"


def get_auth_token(username: str, password: str) -> str:
    """Get JWT authentication token"""
    auth_url = f"{API_BASE_URL}/api/v1/auth/login"
    
    response = requests.post(
        auth_url,
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Authentication failed: {response.text}")


def test_preprocessing_pipeline(
    token: str,
    batch_id: str,
    use_sledai_binary: bool = False,
    apply_composite: bool = True,
    apply_imputation: bool = True,
    apply_winsorization: bool = True
):
    """
    Test the research-aligned preprocessing pipeline
    """
    print(f"\n{'='*80}")
    print(f"🧪 TESTING RESEARCH-ALIGNED PREPROCESSING PIPELINE")
    print(f"{'='*80}\n")
    
    endpoint = f"{API_BASE_URL}/api/v1/ml/train/prepare-dataset"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Configure preprocessing parameters
    request_data = {
        "batch_id": batch_id,
        "target_column": "labels_disease_severity",
        "test_size": 0.35,  # Study uses 35%
        "use_lasso_feature_selection": True,
        "lasso_alpha": 0.01,
        
        # NEW PREPROCESSING PARAMETERS
        "apply_imputation": apply_imputation,
        "imputation_numeric_strategy": "median",  # Study approach
        "imputation_categorical_strategy": "most_frequent",  # Study approach
        
        "apply_winsorization": apply_winsorization,
        "winsorize_limits": [0.01, 0.01],  # 1% and 99% percentiles (study approach)
        
        "apply_composite_features": apply_composite,
        "composite_low_percentile": 10.0,  # Study: 10th percentile for low blood counts
        "composite_high_percentile": 70.0,  # Study: 70th percentile for high liver enzymes
        
        "use_sledai_binary": use_sledai_binary,
        "sledai_threshold": 4.0,  # Study: SLEDAI > 4 = High Activity
        "sledai_column": "disease_activity_SLEDAI_score"
    }
    
    print("📋 Configuration:")
    print(f"  Batch ID: {batch_id}")
    print(f"  Target: {'SLEDAI Binary (>4)' if use_sledai_binary else 'Disease Severity (3-class)'}")
    print(f"  Imputation: {'✅ Enabled (median/mode)' if apply_imputation else '❌ Disabled'}")
    print(f"  Winsorization: {'✅ Enabled (1%/99%)' if apply_winsorization else '❌ Disabled'}")
    print(f"  Composite Features: {'✅ Enabled' if apply_composite else '❌ Disabled'}")
    print(f"\n{'─'*80}\n")
    
    print("🚀 Generating dataset with preprocessing...")
    response = requests.post(endpoint, json=request_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"✅ Dataset generation successful!\n")
        
        # Extract metadata
        metadata = result.get('metadata', {})
        preprocessing_meta = metadata.get('preprocessing_metadata', {})
        preprocessing_config = metadata.get('preprocessing_config', {})
        
        print(f"{'='*80}")
        print(f"📊 DATASET SUMMARY")
        print(f"{'='*80}\n")
        
        print(f"Total Samples:     {metadata.get('total_samples', 'N/A')}")
        print(f"Train Samples:     {metadata.get('train_samples', 'N/A')}")
        print(f"Test Samples:      {metadata.get('test_samples', 'N/A')}")
        print(f"Original Features: {metadata.get('n_features_original', 'N/A')}")
        print(f"Final Features:    {metadata.get('n_features', 'N/A')}")
        
        print(f"\n{'─'*80}")
        print(f"🎯 TARGET VARIABLE")
        print(f"{'─'*80}\n")
        
        print(f"Target Column: {metadata.get('target_column', 'N/A')}")
        print(f"Class Distribution:")
        for class_name, count in metadata.get('class_distribution', {}).items():
            print(f"  {class_name}: {count}")
        
        if metadata.get('sledai_binary_used'):
            sledai_meta = preprocessing_meta.get('sledai_binary', {})
            print(f"\n📌 SLEDAI Binary Conversion:")
            print(f"  Source: {sledai_meta.get('source_column', 'N/A')}")
            print(f"  Threshold: {sledai_meta.get('threshold', 'N/A')}")
            print(f"  Positive (>4): {sledai_meta.get('total_positive', 'N/A')}")
            print(f"  Negative (≤4): {sledai_meta.get('total_negative', 'N/A')}")
        
        print(f"\n{'─'*80}")
        print(f"🔧 PREPROCESSING APPLIED")
        print(f"{'─'*80}\n")
        
        # Imputation
        if preprocessing_meta.get('imputation'):
            impute_data = preprocessing_meta['imputation']
            print(f"✅ Imputation:")
            print(f"  Numeric Strategy: {preprocessing_config.get('imputation_numeric_strategy', 'N/A')}")
            print(f"  Categorical Strategy: {preprocessing_config.get('imputation_categorical_strategy', 'N/A')}")
            print(f"  Numeric Columns: {len(impute_data.get('numeric_columns_imputed', []))}")
            print(f"  Categorical Columns: {len(impute_data.get('categorical_columns_imputed', []))}")
            print(f"  Total Values Imputed: {impute_data.get('total_values_imputed', 0)}")
        else:
            print(f"❌ Imputation: Not applied")
        
        # Winsorization
        if preprocessing_meta.get('winsorization'):
            winsor_data = preprocessing_meta['winsorization']
            print(f"\n✅ Winsorization:")
            print(f"  Limits: {preprocessing_config.get('winsorize_limits', 'N/A')}")
            print(f"  Columns Winsorized: {len(winsor_data.get('columns_winsorized', []))}")
            total_capped = sum(v.get('total_capped', 0) for v in winsor_data.get('values_capped', {}).values())
            print(f"  Total Values Capped: {total_capped}")
        else:
            print(f"\n❌ Winsorization: Not applied")
        
        # Composite Features
        print(f"\n{'─'*80}")
        print(f"🩺 COMPOSITE PATHOLOGICAL FEATURES")
        print(f"{'─'*80}\n")
        
        feature_names = metadata.get('feature_names', [])
        composite_features = [f for f in feature_names if f in ['pancytopenia', 'cytopenia', 'liver_damage', 'high_inflammation', 'low_complement']]
        
        if composite_features:
            print(f"✅ Created {len(composite_features)} composite features:")
            for feat in composite_features:
                print(f"  • {feat}")
            print(f"\n  Low Percentile (blood counts): {preprocessing_config.get('composite_low_percentile', 'N/A')}%")
            print(f"  High Percentile (liver enzymes): {preprocessing_config.get('composite_high_percentile', 'N/A')}%")
        else:
            print(f"❌ No composite features created")
        
        # LASSO Feature Selection
        print(f"\n{'─'*80}")
        print(f"🎯 FEATURE SELECTION")
        print(f"{'─'*80}\n")
        
        if metadata.get('lasso_applied'):
            print(f"✅ LASSO Feature Selection:")
            print(f"  Alpha: {metadata.get('lasso_alpha', 'N/A')}")
            print(f"  Features Removed: {metadata.get('features_removed_by_lasso', 0)}")
            print(f"  Features Kept: {metadata.get('n_features', 'N/A')}")
        else:
            print(f"❌ LASSO: Not applied")
        
        print(f"\n{'─'*80}")
        print(f"🎓 RESEARCH ALIGNMENT STATUS")
        print(f"{'─'*80}\n")
        
        # Check alignment with research study
        checks = [
            ("Imputation (median/mode)", preprocessing_meta.get('imputation') is not None),
            ("Winsorization (1%/99%)", preprocessing_meta.get('winsorization') is not None),
            ("Composite Features", len(composite_features) > 0),
            ("LASSO Feature Selection", metadata.get('lasso_applied')),
            ("Train/Test Split (65/35)", abs(metadata.get('test_samples', 0) / metadata.get('total_samples', 1) - 0.35) < 0.05),
        ]
        
        aligned = sum(1 for _, status in checks if status)
        total = len(checks)
        
        for check_name, status in checks:
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {check_name}")
        
        print(f"\n📊 Alignment Score: {aligned}/{total} ({aligned/total*100:.0f}%)")
        
        if use_sledai_binary:
            print(f"\n💡 Using SLEDAI Binary Target (matches study approach)")
        else:
            print(f"\n💡 Using 3-class Severity (clinically valuable, different from study)")
        
        print(f"\n{'='*80}\n")
        
        return result
    
    else:
        print(f"\n❌ Dataset Generation Failed!")
        print(f"Status Code: {response.status_code}")
        print(f"Error: {response.text}\n")
        return None


def main():
    parser = argparse.ArgumentParser(description="Test Research-Aligned Preprocessing")
    parser.add_argument("--batch-id", required=True, help="Dataset batch ID")
    parser.add_argument("--sledai-binary", action="store_true", help="Use SLEDAI binary target (study approach)")
    parser.add_argument("--no-imputation", action="store_true", help="Disable imputation")
    parser.add_argument("--no-winsorization", action="store_true", help="Disable winsorization")
    parser.add_argument("--no-composite", action="store_true", help="Disable composite features")
    parser.add_argument("--username", default=USERNAME, help="API username")
    parser.add_argument("--password", default=PASSWORD, help="API password")
    
    args = parser.parse_args()
    
    try:
        # Authenticate
        print("🔐 Authenticating...")
        token = get_auth_token(args.username, args.password)
        print(f"✅ Authentication successful!\n")
        
        # Run test
        test_preprocessing_pipeline(
            token=token,
            batch_id=args.batch_id,
            use_sledai_binary=args.sledai_binary,
            apply_composite=not args.no_composite,
            apply_imputation=not args.no_imputation,
            apply_winsorization=not args.no_winsorization
        )
        
        print("\n✅ Test completed!\n")
    
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        raise


if __name__ == "__main__":
    main()
