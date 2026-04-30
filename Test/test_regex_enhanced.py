#!/usr/bin/env python3
"""Test enhanced regex entity extraction"""

import re
import json
from typing import List, Dict, Any

TEST_TEXT = """Premier Integrated Labs
Branch : PIL PHA

Lab No         : RLL25428006
MRN            : PIL250585899

HAEMATOLOGY
Full Blood Count
Haemoglobin 血红蛋白                15.8    g/dL        (13.0 - 18.0)
Red Blood Cell 红细胞              5.64    x10^12/L    (4.50 - 6.50)
White Blood Cell 白血细胞          6.3     x10^9/L     (4.0 - 11.0)
Platelet 血小板                    314     x10^9/L     (150 - 400)

BIOCHEMISTRY
Liver Function Test
Total Protein 蛋白质总计 73 g/L (57 - 82)
Albumin 白蛋白 43 g/L (34 - 50)
Alanine Transaminase 丙氨酸转胺酶 * 67 U/L (10 - 49)

IMMUNOLOGY & SEROLOGY
hsCRP          高敏感度C-反应蛋白        0.2    mg/L    (<3.1)
Rheumatoid Factor  类风湿关节炎因子    <3.5    IU/mL    (<14.0)
"""

print("\n" + "="*80)
print(" TESTING ENHANCED REGEX PATTERN")
print("="*80)

# Enhanced pattern for Premier Labs format
lab_test_pattern = re.compile(
    r'([A-Z][A-Za-z\s,\-/()]+?(?:\s+[\u4e00-\u9fff]+)?)\s+'  # Test name + Chinese
    r'(\*|H|L)?\s*'  # Optional flag
    r'([<>≤≥]?\s*\d+\.?\d*)\s+'  # Value with optional operator
    r'([a-zA-Z/%^0-9\s\-\.]+?)\s+'  # Unit (g/dL, x10^9/L, etc.)
    r'\(([^\)]+)\)',  # Reference range
    re.UNICODE
)

entities = []
for match in lab_test_pattern.finditer(TEST_TEXT):
    test_name = match.group(1).strip()
    flag = match.group(2)
    value = match.group(3).strip()
    unit = match.group(4).strip()
    ref_range = match.group(5).strip()
    
    # Skip if test_name is too short (likely noise)
    if len(test_name) < 3:
        continue
    
    # Build entity value string
    entity_value = f"{test_name}: {value} {unit} ({ref_range})"
    if flag:
        entity_value = f"{test_name}: {flag} {value} {unit} ({ref_range})"
    
    entities.append({
        'type': 'lab_test',
        'value': entity_value,
        'confidence': 0.90
    })

print(f"\n✅ Extracted {len(entities)} entities:")
for i, entity in enumerate(entities, 1):
    print(f"\n{i}. {entity['value']}")

# Save results
import sys
from pathlib import Path
output_file = Path("pipeline_output") / "test_regex_enhanced_output.json"
output_file.parent.mkdir(exist_ok=True)

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(entities, f, indent=2, ensure_ascii=False)

print(f"\n✅ Results saved to: {output_file}")

if len(entities) >= 8:
    print("\n✅ SUCCESS: Enhanced regex extracts entities from Premier Labs format!")
    sys.exit(0)
else:
    print(f"\n⚠️ Only {len(entities)} entities extracted (expected 8+)")
    sys.exit(1)
