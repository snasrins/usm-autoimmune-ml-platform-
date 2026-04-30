#!/usr/bin/env python3
"""
Direct test of extract_entities_from_text() function
Tests NER on extracted OCR text
"""

import sys
import json
from pathlib import Path

# Sample from actual OCR output
TEST_TEXT = """Premier Integrated Labs
Branch : PIL PHA

Lab No         : RLL25428006
MRN            : PIL250585899

HAEMATOLOGY
Full Blood Count
Haemoglobin 血红蛋白                15.8    g/dL        (13.0 - 18.0)
Red Blood Cell 红细胞              5.64    x10^12/L    (4.50 - 6.50)
White Blood Cell 白血细胞          6.3     x10^9/L     (4.0 - 11.0)

BIOCHEMISTRY
Liver Function Test
Alanine Transaminase 丙氨酸转胺酶 * 67 U/L (10 - 49)
Albumin 白蛋白                     43      g/L         (34 - 50)

IMMUNOLOGY & SEROLOGY
hsCRP          高敏感度C-反应蛋白        0.2    mg/L    (<3.1)
Rheumatoid Factor  类风湿关节炎因子    <3.5    IU/mL    (<14.0)
"""

print("\n" + "="*80)
print(" DIRECT NER TEST - Testing extract_entities_from_text()")
print("="*80)

try:
    # Import the NER engine
    from standalone_unstructured_pipeline import Qwen3VLEngine
    
    print("\n✅ Imports successful")
    print(f"📝 Loading Qwen3-VL model with use_model_ner=True...")
    
    # Initialize engine with NER enabled
    engine = Qwen3VLEngine(use_model_ner=True)
    
    print(f"\n🧠 Running extract_entities_from_text() on test sample...")
    print(f"   Text length: {len(TEST_TEXT)} chars")
    print(f"   Expected entities: ~8-10 (Haemoglobin, RBC, WBC, ALT, Albumin, hsCRP, RF, etc.)")
    
    # Run NER
    entities = engine.extract_entities_from_text(TEST_TEXT)
    
    print(f"\n📊 RESULTS:")
    print(f"   Total entities extracted: {len(entities)}")
    
    if len(entities) == 0:
        print("\n❌ ZERO ENTITIES EXTRACTED!")
        print("   This indicates model-based NER is completely failing")
    elif len(entities) < 5:
        print(f"\n⚠️ LOW ENTITY COUNT: {len(entities)}")
        print("   Expected 8-10, got very few")
    else:
        print(f"\n✅ GOOD ENTITY COUNT: {len(entities)}")
    
    # Show all entities
    for i, entity in enumerate(entities, 1):
        print(f"\n   Entity {i}:")
        print(f"      Type: {entity.get('type')}")
        print(f"      Value: {entity.get('value')}")
        print(f"      Confidence: {entity.get('confidence')}")
        
        # Check for template placeholders
        if entity.get('value') in ['...', 'Test: Value Unit', 'Name', 'Disease Name']:
            print(f"      ⚠️ WARNING: Template placeholder detected!")
    
    # Check for specific entities we expect
    expected_terms = ['Haemoglobin', '血红蛋白', 'ALT', 'Alanine', 'hsCRP', 'Rheumatoid']
    found_terms = [term for term in expected_terms if any(term in e.get('value', '') for e in entities)]
    missing_terms = [term for term in expected_terms if term not in found_terms]
    
    print(f"\n📈 Entity Coverage:")
    print(f"   Found terms: {found_terms}")
    print(f"   Missing terms: {missing_terms}")
    
    if missing_terms:
        print(f"\n⚠️ Missing {len(missing_terms)}/{len(expected_terms)} expected entities")
    else:
        print(f"\n✅ All expected entities found!")
    
    # Save results
    output_file = Path("pipeline_output") / "test_ner_direct_output.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(entities, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Results saved to: {output_file}")
    
except Exception as e:
    print(f"\n❌ TEST FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
