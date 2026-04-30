"""
Quick Lab Test Seed Generator
Generates SQL to seed lab_test_definitions from dataset analysis
"""
import sys
sys.path.append('.')

# Read dataset columns from our analysis
SLE_COLUMNS = [
    "WBC", "NEU%", "LYM%", "HGB", "PLT",  # CBC
    "CRP", "ESR", "ALB", "GLO",  # Inflammation
    "Urinary protein", "Urine protein quantification", "ACR", "24-hour urine protein quantification",  # Kidney
    "CD3", "CD4", "CD8", "NK", "CD19",  # Immune cells
    "C3", "C4",  # Complement
    "IgG", "IgM", "IgE", "IgA",  # Immunoglobulins
    "SLEDAI",  # Disease activity
    "ANA", "nRNP/Sm", "SM", "SSA", "RO-52", "SSB", "Scl70", "Jo1", "CENPB", 
    "dsDNA", "Nucleosome", "Histone", "Ribosomal P protein",  # Autoantibodies
    "RNP70", "JO-1", "Scl-70", "AMA-2",  # More autoantibodies
    "Anti-β 2 glycoprotein Ig(GAM)", "Anticardiolipin antibody IgG", "Anticardiolipin anti-antibody IGM",  # APL
    "PR3", "GBM", "MPO",  # ANCA
    "25-OH VitD",  # Vitamin
]

print(f"📊 Lab Test Seed Data Generator")
print(f"=" * 80)
print(f"\n✅ Found {len(SLE_COLUMNS)} SLE tests")
print(f"\n🔧 Generating SQL INSERT statements...")
print(f"\nCopy this SQL and run it on the server:\n")
print(f"=" * 80)

# Generate SQL
for i, col in enumerate(SLE_COLUMNS, 1):
    # Normalize test code
    test_code = col.lower().replace(" ", "_").replace("-", "_").replace("%", "_percent")
    test_code = test_code.replace("'", "").replace("(", "").replace(")", "")
    test_code = test_code.replace("β", "beta").replace("_", "_").strip("_")
    test_code = test_code.replace("__", "_")
    
    # Categorize
    if col in ["WBC", "NEU%", "LYM%", "HGB", "PLT"]:
        category = "Hematology"
    elif col in ["CRP", "ESR", "ALB", "GLO"]:
        category = "Inflammation"
    elif "protein" in col.lower() or "ACR" in col:
        category = "Kidney_Function"
    elif col in ["CD3", "CD4", "CD8", "NK", "CD19"]:
        category = "Immune_Cells"
    elif col in ["C3", "C4"]:
        category = "Complement"
    elif col in ["IgG", "IgM", "IgE", "IgA"]:
        category = "Immunoglobulin"
    elif "SLEDAI" in col:
        category = "Clinical_Score"
    elif "Anti" in col or col in ["ANA", "SM", "SSA", "SSB", "dsDNA", "Nucleosome", "Histone", 
                                    "Ribosomal P protein", "RNP70", "JO-1", "Scl-70", "AMA-2",
                                    "nRNP/Sm", "Scl70", "Jo1", "CENPB", "RO-52"]:
        category = "Autoantibody"
    elif col in ["PR3", "GBM", "MPO"]:
        category = "ANCA"
    elif "Vit" in col:
        category = "Vitamin"
    else:
        category = "Other"
    
    # Data type
    if "%" in col or col in ["ANA", "SM", "SSA", "SSB", "Scl70", "Jo1", "CENPB", "dsDNA", 
                              "Nucleosome", "Histone", "nRNP/Sm", "Urinary protein"]:
        data_type = "qualitative"
    else:
        data_type = "numeric"
    
    print(f"INSERT INTO lab_test_definitions (test_code, test_name, test_category, data_type, relevant_diseases, is_active)")
    print(f"VALUES ('{test_code}', '{col}', '{category}', '{data_type}', ARRAY['SLE'], true);")

print(f"\n" + "=" * 80)
print(f"\n✅ Generated {len(SLE_COLUMNS)} INSERT statements")
print(f"\n📋 Next: Create similar for Sjogren tests (106 more)")
