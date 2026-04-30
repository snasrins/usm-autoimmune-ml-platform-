import pandas as pd
import numpy as np

# Read Excel file
df = pd.read_excel(r'C:\Users\Syarifah\usm-autoimmune-ml-platform\Dataset\AAM-SLE-E (real data).xlsx')
df_clean = df.iloc[1:].reset_index(drop=True)

# Convert SLEDAI to numeric
sledai = pd.to_numeric(df_clean['SLEDAI'], errors='coerce')

# Create severity labels based on SLEDAI
severity = []
for s in sledai:
    if pd.isna(s):
        severity.append('Unknown')
    elif s <= 4:
        severity.append('Mild')
    elif s <= 12:
        severity.append('Moderate')
    else:
        severity.append('Severe')

df_clean['Recommended_Severity_Label'] = severity

# Create kidney involvement labels
kidney_label = []
for up in df_clean['Urinary protein']:
    if up in ['-', '无']:
        kidney_label.append('No-kidney-involvement')
    elif up == '±':
        kidney_label.append('Trace-proteinuria')
    elif up in ['+', '2+', '3+', '4+']:
        kidney_label.append('Lupus-nephritis')
    else:
        kidney_label.append('Unknown')

df_clean['Recommended_Kidney_Label'] = kidney_label

# Select key columns for labeling guide
output = df_clean[['Hospitalization number', 'Age', 'SLEDAI', 'C3', 'C4', 'Urinary protein', 
                    'Recommended_Severity_Label', 'Recommended_Kidney_Label']]

# Save to CSV
output.to_csv(r'C:\Users\Syarifah\usm-autoimmune-ml-platform\Dataset\SLE_Labeling_Guide.csv', index=False)

print('✅ Labeling guide created successfully!')
print(f'\nTotal records: {len(output)}')
print(f'\nSeverity distribution:')
print(df_clean['Recommended_Severity_Label'].value_counts().sort_index())
print(f'\nKidney involvement distribution:')
print(df_clean['Recommended_Kidney_Label'].value_counts())
print(f'\nPreview of first 10 records:')
print(output.head(10).to_string(index=False))
