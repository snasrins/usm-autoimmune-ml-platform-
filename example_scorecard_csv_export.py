"""
Example: Export Scorecard Reports to CSV

Demonstrates how to export scorecard data to CSV files for:
1. Clinical reporting
2. Publication tables
3. Patient tracking
4. Documentation

All CSV files are ready to open in Excel/Google Sheets!
"""

import pandas as pd
import numpy as np
from app.ml.scorecard.scorecard_generator import ScorecardGenerator
from app.ml.scorecard.dynamic_binning import BinningMethod


def example_export_scorecard_to_csv():
    """
    Complete example of generating and exporting scorecard reports
    """
    print("=" * 80)
    print("📊 SCORECARD CSV EXPORT EXAMPLE")
    print("=" * 80)
    print()
    
    # Step 1: Create sample data
    print("Step 1: Creating sample dataset...")
    print("-" * 80)
    
    np.random.seed(42)
    n_samples = 100
    
    # Create features
    X_train = pd.DataFrame({
        'NK': np.random.uniform(0.5, 15.0, n_samples),
        'C4': np.random.uniform(0.01, 0.20, n_samples),
        'IgM': np.random.uniform(0.20, 2.50, n_samples),
        'ALB': np.random.uniform(0.50, 1.50, n_samples),
        'CRP': np.random.uniform(0.10, 5.00, n_samples)
    })
    
    # Create binary target
    y_train = pd.Series(np.random.binomial(1, 0.4, n_samples))
    
    # Create test set
    n_test = 30
    X_test = pd.DataFrame({
        'NK': np.random.uniform(0.5, 15.0, n_test),
        'C4': np.random.uniform(0.01, 0.20, n_test),
        'IgM': np.random.uniform(0.20, 2.50, n_test),
        'ALB': np.random.uniform(0.50, 1.50, n_test),
        'CRP': np.random.uniform(0.10, 5.00, n_test)
    })
    y_test = pd.Series(np.random.binomial(1, 0.4, n_test))
    
    print(f"✅ Created {n_samples} training samples, {n_test} test samples")
    print()
    
    # Step 2: Create mock model
    print("Step 2: Creating mock model...")
    print("-" * 80)
    
    from sklearn.ensemble import RandomForestClassifier
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)
    
    print(f"✅ Model accuracy: {model.score(X_test, y_test):.3f}")
    print()
    
    # Step 3: Generate scorecard
    print("Step 3: Generating dynamic scorecard...")
    print("-" * 80)
    
    scorecard_gen = ScorecardGenerator(
        binning_method=BinningMethod.ROLLING_MEAN,
        n_bins=4,
        use_youden=True
    )
    
    scorecard_gen.fit(
        X_train=X_train,
        y_train=y_train,
        model=model,
        feature_names=X_train.columns.tolist()
    )
    
    print(f"✅ Scorecard fitted!")
    print(f"   Optimal threshold: {scorecard_gen.optimal_threshold_:.2f}")
    print(f"   Youden J: {scorecard_gen.threshold_metrics_['youden_j']:.4f}")
    print()
    
    # Step 4: Export to CSV files
    print("Step 4: Exporting to CSV files...")
    print("-" * 80)
    
    output_dir = "scorecard_reports"
    
    # Export comprehensive report (all CSV files)
    report_files = scorecard_gen.export_comprehensive_report(
        output_dir=output_dir,
        model_name="RandomForest",
        version="v1.0.0",
        X_test=X_test,
        y_test=y_test
    )
    
    print("✅ CSV files created:")
    for report_type, file_path in report_files.items():
        print(f"   • {report_type}: {file_path}")
    
    print()
    
    # Step 5: Show sample bin-score table
    print("Step 5: Preview bin-score table...")
    print("-" * 80)
    
    bin_table = scorecard_gen.get_scorecard_table('NK')
    if bin_table is not None:
        print("\nNK (Natural Killer Cells) Bin-Score Table:")
        print(bin_table.to_string(index=False))
    
    print()
    
    # Step 6: Export individual patient scores
    print("Step 6: Exporting patient scores...")
    print("-" * 80)
    
    patient_ids = [f"PAT{i:03d}" for i in range(1, len(X_test) + 1)]
    
    patient_scores_path = f"{output_dir}/RandomForest_v1.0.0_detailed_patient_scores.csv"
    scorecard_gen.export_patient_scores_to_csv(
        X=X_test,
        output_path=patient_scores_path,
        include_breakdown=True,
        patient_ids=patient_ids
    )
    
    print(f"✅ Patient scores exported to: {patient_scores_path}")
    print()
    
    # Step 7: Show what the CSV files contain
    print("=" * 80)
    print("📋 CSV FILE CONTENTS")
    print("=" * 80)
    print()
    
    print("1️⃣ bin_tables.csv - Transparent Bin-Score Tables")
    print("   Columns: Feature, Bin_Range, Score_Points, Sample_Count, Percentage, ...")
    print("   Use for: Clinical lookup tables, manual score calculation")
    print()
    
    print("2️⃣ threshold.csv - Youden Index Optimization Results")
    print("   Contains: Optimal threshold, sensitivity, specificity, J-statistic")
    print("   Use for: Clinical decision rules, threshold justification")
    print()
    
    print("3️⃣ patient_scores.csv - Individual Patient Risk Scores")
    print("   Columns: Patient_ID, Total_Score, Risk_Group, Feature_Scores...")
    print("   Use for: Patient tracking, longitudinal monitoring, reports")
    print()
    
    print("=" * 80)
    print("✅ COMPLETE! All CSV files ready for:")
    print("=" * 80)
    print()
    print("   📊 Clinical Reports")
    print("   📄 Publication Tables")
    print("   📈 Excel/Google Sheets Analysis")
    print("   🔬 Research Documentation")
    print("   👥 Patient Tracking")
    print()


def example_clinical_use_case():
    """
    Example: How a clinician would use the exported CSV files
    """
    print()
    print("=" * 80)
    print("🏥 CLINICAL USE CASE: Manual Score Calculation")
    print("=" * 80)
    print()
    
    print("Scenario: Clinician has patient lab results and wants to calculate risk score")
    print()
    
    print("Step 1: Open bin_tables.csv in Excel/Google Sheets")
    print("Step 2: Find patient's lab values")
    print()
    
    # Mock patient data
    patient_labs = {
        'NK': 0.85,
        'C4': 0.08,
        'IgM': 0.45,
        'ALB': 0.85,
        'CRP': 1.20
    }
    
    print("Patient Lab Results:")
    print("-" * 40)
    for lab, value in patient_labs.items():
        print(f"  {lab:8s} = {value:.2f}")
    print()
    
    print("Step 3: Look up bins in CSV table and get scores")
    print("-" * 40)
    
    # Mock bin scores (these would come from the CSV)
    mock_scores = {
        'NK': (0.85, '≤ 1.10', 1.7),
        'C4': (0.08, '0.03-0.10', 5.6),
        'IgM': (0.45, '0.32-0.67', 13.7),
        'ALB': (0.85, '0.67-1.22', 4.5),
        'CRP': (1.20, '> 0.50', 19.0)
    }
    
    total = 0
    for feature, (value, bin_range, score) in mock_scores.items():
        print(f"  {feature:8s} = {value:.2f}  →  Bin: {bin_range:12s}  →  {score:5.1f} points")
        total += score
    
    print("-" * 40)
    print(f"  Total Score: {total:.1f} points")
    print()
    
    print("Step 4: Compare to threshold (from threshold.csv)")
    print("-" * 40)
    threshold = 60.0
    print(f"  Threshold: {threshold:.1f}")
    print(f"  Patient Score: {total:.1f}")
    
    if total >= threshold:
        print(f"  ⚠️  Decision: HIGH RISK (Score ≥ {threshold:.1f})")
        print("  Recommendation: Therapy escalation, frequent monitoring")
    else:
        print(f"  ✅ Decision: LOW RISK (Score < {threshold:.1f})")
        print("  Recommendation: Routine monitoring, maintain therapy")
    
    print()
    print("✅ Clinician can verify this calculation manually from CSV tables!")
    print()


if __name__ == "__main__":
    # Run the example
    example_export_scorecard_to_csv()
    
    # Show clinical use case
    example_clinical_use_case()
    
    print()
    print("=" * 80)
    print("🎉 CSV Export Feature Complete!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Open the CSV files in Excel/Google Sheets")
    print("  2. Use bin_tables.csv for manual score calculation")
    print("  3. Use patient_scores.csv for tracking")
    print("  4. Use threshold.csv for clinical decision rules")
    print()
