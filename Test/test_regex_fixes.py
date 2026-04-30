#!/usr/bin/env python3
"""Quick test of regex fixes"""

import re
import json
from typing import List, Dict, Any

# Import from main file
import sys
sys.path.insert(0, '.')
from standalone_unstructured_pipeline import extract_medical_entities_regex, parse_entity_components

TEST_TEXT = """HAEMATOLOGY
Full Blood Count
Haemoglobin 血红蛋白                15.8    g/dL        (13.0 - 18.0)
Red Blood Cell 红细胞              5.64    x10^12/L    (4.50 - 6.50)
White Blood Cell 白血细胞          6.3     x10^9/L     (4.0 - 11.0)

BIOCHEMISTRY
Liver Function Test
Total Protein 蛋白质总计 73 g/L (57 - 82)
Albumin 白蛋白 43 g/L (34 - 50)
Alanine Transaminase 丙氨酸转胺酶 * 67 U/L (10 - 49)

IMMUNOLOGY & SEROLOGY
hsCRP          高敏感度C-反应蛋白        0.2    mg/L    (<3.1)
Hepatitis Bs Antigen  乙型肝炎病毒抗原    Non-Reactive    IU/L
"""

print("\n" + "="*80)
print(" TESTING REGEX FIXES")
print("="*80)

# Extract entities
entities = extract_medical_entities_regex(TEST_TEXT)

print(f"\n✅ Extracted {len(entities)} entities:")

# Check for expected entities
expected = ['Haemoglobin', 'Red Blood Cell', 'White Blood Cell', 'Total Protein', 
            'Albumin', 'Alanine Transaminase', 'hsCRP', 'Hepatitis Bs Antigen']

found_tests = []
for entity in entities:
    # Parse components
    if entity.get('type') == 'lab_test':
        parsed = parse_entity_components(entity.get('value', ''), entity.get('type', ''))
        entity.update(parsed)
        found_tests.append(entity.get('test_name', ''))
        
        print(f"\n  {entity.get('test_name', 'Unknown')}")
        print(f"    Value: {entity.get('value_numeric')} {entity.get('unit', '')}")
        print(f"    Ref Range: {entity.get('ref_range_low')} - {entity.get('ref_range_high')}")
        print(f"    Flag: {entity.get('flag')}")
        print(f"    Abnormal: {entity.get('is_abnormal')}")

# Check coverage
found_count = sum(1 for exp in expected if any(exp in test for test in found_tests))
print(f"\n📊 Coverage: {found_count}/{len(expected)} expected tests found")

# Validate fixes
print(f"\n🔍 Validation:")

# Check 1: Should find Haemoglobin (excessive whitespace)
if any('Haemoglobin' in test or '血红蛋白' in test for test in found_tests):
    print(f"  ✅ Haemoglobin found (whitespace handled)")
else:
    print(f"  ❌ Haemoglobin missing (whitespace issue)")

# Check 2: Should find qualitative test
if any('Hepatitis' in test for test in found_tests):
    print(f"  ✅ Qualitative test found (Hepatitis)")
else:
    print(f"  ❌ Qualitative test missing")

# Check 3: Should NOT have all "L" flags
false_L_flags = [e for e in entities if e.get('flag') == 'L' and '/L' in e.get('value', '')]
if len(false_L_flags) == 0:
    print(f"  ✅ No false 'L' flags from units (g/L, mmol/L)")
else:
    print(f"  ⚠️ {len(false_L_flags)} entities with false 'L' flag from units")

# Check 4: No placeholder entities
placeholders = [e for e in entities if e.get('value') in ['...', 'Test: Value Unit']]
if len(placeholders) == 0:
    print(f"  ✅ No placeholder entities")
else:
    print(f"  ❌ {len(placeholders)} placeholder entities found")

if found_count >= 6:
    print(f"\n✅ REGEX FIXES WORKING - Ready for full pipeline test")
    sys.exit(0)
else:
    print(f"\n⚠️ Only {found_count}/8 entities found - needs more work")
    sys.exit(1)
