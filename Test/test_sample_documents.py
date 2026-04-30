#!/usr/bin/env python3
"""
Create Sample Test Documents
=============================
Purpose: Generate sample PDF and TXT files for testing the unstructured pipeline
Author: Syarifah Fajriyah
Date: March 24, 2026
"""

import os
from pathlib import Path

# Create test_documents directory
test_dir = Path("./test_documents")
test_dir.mkdir(exist_ok=True)

print("📁 Creating sample test documents in ./test_documents/")

# ═══════════════════════════════════════════════════════════
#  Sample 1: Clinical Note (TXT)
# ═══════════════════════════════════════════════════════════

clinical_note = """CLINICAL NOTES - USM Hospital Autoimmune Clinic
=====================================================

PATIENT INFORMATION:
Name: Ahmad bin Abdullah
MRN: USM2024-00123
Date: March 24, 2026
Attending: Dr. Siti Aminah (Rheumatologist)

CHIEF COMPLAINT:
Patient presents with worsening joint pain and fatigue over the past 3 months.
Morning stiffness lasting >1 hour. Butterfly rash on face noted.

HISTORY OF PRESENT ILLNESS:
35-year-old Malay female with known SLE (diagnosed 2023). Currently on:
- Hydroxychloroquine 200mg BID
- Prednisolone 5mg daily
- Methotrexate 15mg weekly

Reports recent flare with increased joint swelling (bilateral hands, wrists).
Denies fever, chest pain, or shortness of breath.

PHYSICAL EXAMINATION:
- Vital Signs: BP 120/80, HR 78, Temp 36.8°C
- Malar rash present (non-scarring)
- Synovitis: 4 swollen joints (MCPs, wrists)
- No oral ulcers noted
- Lungs: Clear bilaterally
- Heart: Regular rhythm, no murmurs

LABORATORY RESULTS (March 23, 2026):
- Anti-dsDNA: 285 IU/mL (High - indicates active disease)
- C3: 65 mg/dL (Low - normal range: 90-180)
- C4: 8 mg/dL (Low - normal range: 10-40)
- ESR: 45 mm/hr (Elevated)
- CRP: 12 mg/L (Elevated)
- WBC: 3.2 x10^9/L (Leukopenia)
- Hemoglobin: 10.5 g/dL (Anemia)
- Platelets: 145 x10^9/L (Normal)

ASSESSMENT:
1. Systemic Lupus Erythematosus (M32.10) - Active flare
   SLEDAI-2K Score: 12 (Moderate activity)
   - Active arthritis: +4
   - Malar rash: +2
   - Low complement: +2
   - Elevated anti-dsDNA: +2
   - Leukopenia: +1
   - Anemia: +1

2. Lupus nephritis - Rule out (previous Class III in 2023)

PLAN:
1. Increase Prednisolone to 15mg daily for 2 weeks
2. Continue Hydroxychloroquine and Methotrexate
3. Order:
   - Urine protein/creatinine ratio
   - Kidney biopsy if proteinuria worsens
4. Follow-up in 2 weeks
5. Consider Belimumab if no improvement

FOLLOW-UP:
Scheduled for April 7, 2026 with Dr. Siti Aminah

Signed: Dr. Siti Aminah, MBBS, MRCP
Date: March 24, 2026, 10:30 AM
"""

with open(test_dir / "sample_clinical_note.txt", "w", encoding="utf-8") as f:
    f.write(clinical_note)

print("✅ Created: sample_clinical_note.txt")

# ═══════════════════════════════════════════════════════════
#  Sample 2: Lab Report (TXT)
# ═══════════════════════════════════════════════════════════

lab_report = """LAB REPORT - USM HOSPITAL
===================================

Patient: Fatimah binti Hassan
MRN: USM2024-00456
DOB: 1988-05-15 (Age: 38)
Date Collected: March 23, 2026 08:00 AM
Date Reported: March 24, 2026 02:00 PM

ORDERED BY: Dr. Kamal Rahman (Rheumatology)

TEST RESULTS - AUTOIMMUNE PANEL:
-----------------------------------

1. ANTI-NUCLEAR ANTIBODY (ANA)
   Result: POSITIVE (1:320)
   Pattern: Speckled
   Reference: Negative (<1:40)
   ⚠️ ABNORMAL - HIGH

2. ANTI-dsDNA ANTIBODY
   Result: 145 IU/mL
   Reference: <30 IU/mL
   ⚠️ ABNORMAL - HIGH

3. ANTI-SMITH (Anti-Sm)
   Result: POSITIVE
   Reference: Negative
   ⚠️ ABNORMAL

4. ANTI-RNP
   Result: NEGATIVE
   Reference: Negative
   NORMAL

5. ANTI-SSA (Ro)
   Result: POSITIVE (>240 U/mL)
   Reference: <20 U/mL
   ⚠️ ABNORMAL - Strongly associated with Sjögren's syndrome

6. ANTI-SSB (La)
   Result: POSITIVE (125 U/mL)
   Reference: <20 U/mL
   ⚠️ ABNORMAL - Highly specific for Sjögren's syndrome

COMPLEMENT LEVELS:
-----------------------------------
7. C3 Complement
   Result: 55 mg/dL
   Reference: 90-180 mg/dL
   ⚠️ LOW - Indicates complement consumption

8. C4 Complement
   Result: 6 mg/dL
   Reference: 10-40 mg/dL
   ⚠️ LOW - Indicates active disease

INFLAMMATORY MARKERS:
-----------------------------------
9. ESR (Erythrocyte Sedimentation Rate)
   Result: 68 mm/hr
   Reference: 0-20 mm/hr
   ⚠️ ELEVATED

10. CRP (C-Reactive Protein)
    Result: 25 mg/L
    Reference: <5 mg/L
    ⚠️ ELEVATED

COMPLETE BLOOD COUNT:
-----------------------------------
11. WBC: 3.0 x10^9/L (LOW - Leukopenia)
12. Hemoglobin: 9.8 g/dL (LOW - Anemia)
13. Platelets: 130 x10^9/L (Normal)
14. Neutrophils: 65%
15. Lymphocytes: 25%
16. Monocytes: 8%

RENAL FUNCTION:
-----------------------------------
17. Creatinine: 1.2 mg/dL (Borderline high)
18. eGFR: 62 mL/min/1.73m² (Mildly reduced)
19. Urine Protein/Creatinine Ratio: 850 mg/g (ELEVATED - proteinuria)

INTERPRETATION:
-----------------------------------
Results consistent with:
1. Systemic Lupus Erythematosus (SLE) - confirmed
2. Sjögren's Syndrome overlap (Anti-SSA/SSB positive)
3. Possible lupus nephritis (proteinuria, reduced eGFR)

RECOMMENDATIONS:
- Urgent nephrology referral
- Consider kidney biopsy
- Increase immunosuppression
- Monitor renal function closely

Resulted by: Dr. Nurul Huda (Clinical Pathologist)
Contact: Lab Ext. 4567 for queries

===================================
END OF REPORT
"""

with open(test_dir / "sample_lab_report.txt", "w", encoding="utf-8") as f:
    f.write(lab_report)

print("✅ Created: sample_lab_report.txt")

# ═══════════════════════════════════════════════════════════
#  Sample 3: Simple Prescription Note (TXT)
# ═══════════════════════════════════════════════════════════

prescription = """PRESCRIPTION - USM Hospital
================================

Date: March 24, 2026
Patient: Zainab binti Yusof
MRN: USM2024-00789
Age: 42 years old
Weight: 58 kg

Diagnosis: Rheumatoid Arthritis (M06.9)

PRESCRIPTIONS:
---------------------------------

1. Methotrexate 15mg
   Route: Oral
   Frequency: Once weekly (every Monday)
   Duration: 3 months
   Quantity: 12 tablets
   
2. Folic Acid 5mg
   Route: Oral
   Frequency: Once weekly (every Tuesday - day after MTX)
   Duration: 3 months
   Quantity: 12 tablets
   
3. Prednisolone 5mg
   Route: Oral
   Frequency: Once daily in morning
   Duration: 1 month (tapering)
   Quantity: 30 tablets
   
4. Hydroxychloroquine 200mg
   Route: Oral
   Frequency: Twice daily
   Duration: 3 months
   Quantity: 180 tablets
   
5. Calcium + Vitamin D3
   Route: Oral
   Frequency: Once daily
   Duration: 3 months
   Quantity: 90 tablets

SPECIAL INSTRUCTIONS:
- Take Methotrexate with food
- Avoid alcohol while on Methotrexate
- Report any signs of infection immediately
- Monthly FBC and LFT monitoring required
- Ophthalmology review every 6 months (Hydroxychloroquine)

FOLLOW-UP:
- Next appointment: April 21, 2026
- Contact clinic if fever, unusual bruising, or severe joint pain

Prescribed by: Dr. Amir bin Hassan
Signature: ___________________
License: MMC-12345

================================
Pharmacy Ext. 3456
"""

with open(test_dir / "sample_prescription.txt", "w", encoding="utf-8") as f:
    f.write(prescription)

print("✅ Created: sample_prescription.txt")

# ═══════════════════════════════════════════════════════════
#  Sample 4: Discharge Summary (TXT)
# ═══════════════════════════════════════════════════════════

discharge_summary = """DISCHARGE SUMMARY
==========================================
USM Hospital - Rheumatology Ward
==========================================

PATIENT DETAILS:
Name: Nurul Aina binti Ahmad
MRN: USM2024-01234
IC: 880515-10-5678
Age/Gender: 38 years / Female
Admission Date: March 15, 2026
Discharge Date: March 24, 2026
Length of Stay: 9 days

ADMITTING DIAGNOSIS:
1. Systemic Lupus Erythematosus with lupus nephritis Class IV
2. Acute kidney injury
3. Severe hypertension

DISCHARGE DIAGNOSIS:
1. SLE with lupus nephritis Class IV (kidney biopsy confirmed)
2. AKI - improved (Cr 3.5 → 1.8 mg/dL)
3. HTN - controlled on medications

HOSPITAL COURSE:
-----------------------------------
Patient admitted with severe nephritic syndrome, hypertension (BP 180/110), 
and oliguria. Initial Cr was 3.5 mg/dL with proteinuria 4.5 g/24hr.

Kidney biopsy performed on Day 3 showed:
- Class IV Diffuse Proliferative Lupus Nephritis
- Activity index: 8/24
- Chronicity index: 2/12
- Moderate tubular atrophy

TREATMENT DURING ADMISSION:
1. IV Methylprednisolone 1g daily x 3 days (Days 1-3)
2. IV Cyclophosphamide 750mg (Day 5)
3. Antihypertensives: Amlodipine 10mg, Enalapril 10mg BD
4. Hydroxychloroquine 200mg BD (continued)
5. IV Hydration + Mesna for bladder protection

RESPONSE TO TREATMENT:
- Creatinine improved: 3.5 → 1.8 mg/dL
- Urine output increased: 400ml/day → 1500ml/day
- BP controlled: 180/110 → 135/85 mmHg
- Proteinuria decreased: 4.5g → 2.1g per 24hr

LABORATORY AT DISCHARGE (March 24, 2026):
-----------------------------------
- Creatinine: 1.8 mg/dL (improved from 3.5)
- eGFR: 42 mL/min/1.73m² (improved from 18)
- Urine Protein/Cr: 2100 mg/g (improved from 4500)
- Anti-dsDNA: 420 IU/mL (still elevated)
- C3: 48 mg/dL (low)
- C4: 5 mg/dL (low)
- WBC: 4.5 x10^9/L
- Hb: 9.2 g/dL (anemia)
- Platelets: 155 x10^9/L

DISCHARGE MEDICATIONS:
-----------------------------------
1. Prednisolone 40mg once daily (tapering schedule provided)
2. Hydroxychloroquine 200mg twice daily
3. Mycophenolate Mofetil 1000mg twice daily (NEW - immunosuppression)
4. Amlodipine 10mg once daily
5. Enalapril 10mg twice daily
6. Furosemide 40mg once daily
7. Calcium + Vitamin D3 once daily
8. Omeprazole 20mg once daily (gastric protection)

FOLLOW-UP PLAN:
-----------------------------------
1. Rheumatology Clinic: April 2, 2026 (1 week)
2. Nephrology Clinic: April 9, 2026 (2 weeks)
3. Laboratory investigations:
   - Weekly: FBC, Renal function, Urine PUCR
   - Monthly: Anti-dsDNA, C3, C4, LFT
4. Monthly IV Cyclophosphamide x 5 more doses (NIH protocol)
5. BP monitoring at home (target <130/80)

PATIENT EDUCATION:
- Avoid sun exposure (use SPF 50+ sunscreen)
- Avoid live vaccines while on immunosuppression
- Report immediately: Fever >38°C, bleeding, severe headache
- Medication adherence critical
- Low-salt, renal-friendly diet

PROGNOSIS:
Guarded. Class IV lupus nephritis has 60-70% response rate with aggressive 
immunosuppression. Close monitoring essential for next 6 months.

KONDISI SAAT PULANG:
General condition: Fair
Alert and oriented
Able to ambulate
Vital signs stable

Prepared by: Dr. Amir Hakim
Consultant Rheumatologist
Date: March 24, 2026
Signature: ___________________
"""

with open(test_dir / "sample_discharge_summary.txt", "w", encoding="utf-8") as f:
    f.write(discharge_summary)

print("✅ Created: sample_discharge_summary.txt")

# ═══════════════════════════════════════════════════════════
#  Sample 5: Sjogren's Syndrome Note (TXT)
# ═══════════════════════════════════════════════════════════

sjogren_note = """SJOGREN'S SYNDROME FOLLOW-UP
==========================================
USM Hospital - Rheumatology Clinic
==========================================

PATIENT: Rahimah binti Mahmud
MRN: USM2024-00567
Date: March 24, 2026

DIAGNOSIS: Primary Sjögren's Syndrome (M35.0)

PRESENTING SYMPTOMS (Review):
- Dry eyes (xerophthalmia) - persistent for 2 years
- Dry mouth (xerostomia) - difficulty swallowing dry foods
- Parotid gland swelling - bilateral, intermittent
- Joint pain - hands and knees

OBJECTIVE FINDINGS TODAY:
-----------------------------------

1. SCHIRMER TEST (Tear production):
   - Right eye: 3 mm at 5 minutes (ABNORMAL - normal >15mm)
   - Left eye: 2 mm at 5 minutes (ABNORMAL - severe dry eye)

2. SALIVARY FLOW RATE:
   - Unstimulated: 0.08 mL/min (ABNORMAL - normal >0.1 mL/min)
   - Stimulated: 0.5 mL/min (ABNORMAL - normal >1.5 mL/min)

3. ORAL EXAMINATION:
   - Decreased saliva pooling
   - Tongue fissures present
   - Multiple dental caries (8 teeth affected)

LABORATORY RESULTS (Current):
-----------------------------------
- Anti-SSA (Ro): POSITIVE (>240 U/mL) - hallmark of Sjögren's
- Anti-SSB (La): POSITIVE (125 U/mL) - highly specific
- ANA: Positive 1:640 (speckled pattern)
- Rheumatoid Factor: Positive (78 IU/mL)
- ESR: 42 mm/hr (elevated)
- CRP: 8 mg/L (mild elevation)
- IgG: 2100 mg/dL (elevated - hypergammaglobulinemia)

EULAR SJOGREN'S SYNDROME DISEASE ACTIVITY INDEX (ESSDAI):
-----------------------------------
Score: 9 (Moderate activity)

Domain breakdown:
- Constitutional: 0 (no fever/weight loss)
- Lymphadenopathy: 0 (no enlarged lymph nodes)
- Glandular: 3 (moderate parotid swelling)
- Articular: 3 (moderate joint pain/swelling)
- Cutaneous: 0 (no rash)
- Pulmonary: 0 (clear lungs)
- Renal: 0 (normal kidney function)
- Muscular: 0 (no myositis)
- PNS: 0 (no peripheral neuropathy)
- CNS: 0 (no CNS involvement)
- Hematological: 3 (mild leukopenia 3.8 x10^9/L)
- Biological: 0 (normal Ig levels considered)

CURRENT TREATMENT:
-----------------------------------
1. Pilocarpine 5mg QID (salivary stimulant)
2. Artificial tears every 2 hours
3. Hydroxychloroquine 200mg BID
4. Prednisolone 5mg daily

PATIENT-REPORTED OUTCOMES:
- ESSPRI (symptoms): 6.5/10
  - Dryness: 8/10
  - Fatigue: 7/10
  - Pain: 5/10

PLAN:
-----------------------------------
1. Continue current medications
2. Referral to:
   - Ophthalmology for punctal plug insertion (improve dry eyes)
   - Dentist for fluoride treatment (prevent further caries)
3. Consider rituximab if symptoms worsen (ESSDAI >14)
4. Monitor for lymphoma development (annual ultrasound)
5. Dry mouth management:
   - Sugar-free gum/lozenges
   - Frequent water sips
   - Humidifier at night

NEXT VISIT: June 24, 2026 (3 months)

Dr. Zainab Khaled
Consultant Rheumatologist
March 24, 2026
"""

with open(test_dir / "sample_sjogren_note.txt", "w", encoding="utf-8") as f:
    f.write(sjogren_note)

print("✅ Created: sample_sjogren_note.txt")

# ═══════════════════════════════════════════════════════════
#  Instructions for PDF creation
# ═══════════════════════════════════════════════════════════

instructions = """TEST DOCUMENTS CREATED
==================================

Created 3 sample TXT files in ./test_documents/:

1. sample_clinical_note.txt
   - SLE patient with active flare
   - Contains: SLEDAI score, lab results, medications
   - Entities: SLE, Hydroxychloroquine, Anti-dsDNA, etc.

2. sample_lab_report.txt
   - Autoimmune panel results
   - Contains: ANA, Anti-dsDNA, Anti-SSA/SSB, complement levels
   - Entities: Multiple lab tests, numerical values

3. sample_discharge_summary.txt
   - SLE with lupus nephritis Class IV
   - Contains: Hospital course, biopsy results, treatment plan
   - Entities: Cyclophosphamide, Mycophenolate, kidney biopsy

4. sample_sjogren_note.txt
   - Primary Sjögren's Syndrome with ESSDAI scoring
   - Contains: Schirmer test, salivary flow rate, ESSDAI breakdown
   - Entities: Anti-SSA/SSB, Pilocarpine, ESSDAI components

==================================
TO CREATE PDF VERSIONS:
==================================

If you need PDF files for testing OCR, you can:

Option 1: Convert TXT to PDF using LibreOffice (on Linux):
  lowriter --convert-to pdf sample_clinical_note.txt

Option 2: Use online converter (any TXT to PDF tool)

Option 3: Print to PDF from text editor

Option 4: Use Python script with reportlab:
  pip install reportlab
  # Then use reportlab to generate PDFs

For now, test with TXT files first to verify text processing works!

==================================
RUN THE PIPELINE:
==================================

cd /path/to/usm-autoimmune-ml-platform

# Process all sample TXT files
python3 standalone_unstructured_pipeline.py ./test_documents/*.txt

# Or process one by one
python3 standalone_unstructured_pipeline.py ./test_documents/sample_clinical_note.txt

==================================
"""

with open(test_dir / "README.txt", "w", encoding="utf-8") as f:
    f.write(instructions)

print("✅ Created: README.txt (instructions)")

print(f"\n{'='*60}")
print("✅ ALL SAMPLE DOCUMENTS CREATED!")
print(f"{'='*60}")
print(f"📁 Location: {test_dir.absolute()}")
print(f"📄 Files created: 4")
print(f"\n🚀 NEXT STEP:")
print(f"   python3 standalone_unstructured_pipeline.py ./test_documents/*.txt")
print(f"{'='*60}\n")
