#!/usr/bin/env python3
"""
Test parsing functions with sample medical report text
Validates JSON structure without requiring GPU
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import parsing functions directly
try:
    from standalone_unstructured_pipeline import (
        parse_metadata_from_text,
        parse_entity_components,
        extract_section_structure,
        ProcessingResult
    )
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nTrying relative import...")
    # Define minimal versions for testing if imports fail
    def parse_metadata_from_text(text): return {}
    def parse_entity_components(value, type): return {}
    def extract_section_structure(text): return []

# Sample medical report text (from previous OCR test)
SAMPLE_TEXT = """
Premier Integrated Labs
Branch : PIL PHA

Lab No         : RLL25428006
MRN            : PIL250585899
Name           : [REDACTED]
DOB / Age      : [REDACTED]
Gender         : Male
Collected      : 23.11.2025 10:28:52
Received       : 23.11.2025 11:14:05
Reported       : 23.11.2025 14:37:22
Specimen       : EDTA whole blood
Fasting        : No
Page No        : 1 / 7

HAEMATOLOGY
Full Blood Count
Hemoglobin 血红蛋白                15.8    g/dL        (13.0 - 18.0)
Red Blood Cell 红细胞              5.64    x10^12/L    (4.50 - 6.50)
White Blood Cell 白血细胞          6.3     x10^9/L     (4.0 - 11.0)
Platelet 血小板                    314     x10^9/L     (150 - 400)

--- PAGE BREAK ---

Premier Integrated Labs
Page No        : 2 / 7

BIOCHEMISTRY
Liver Function Test
Total Protein 蛋白质总计           73      g/L         (57 - 82)
Albumin 白蛋白                     43      g/L         (34 - 50)
ALT 谷丙转氨酶                   * 68      U/L         (<41)

--- PAGE BREAK ---

Premier Integrated Labs
Page No        : 3 / 7

IMMUNOLOGY & SEROLOGY
Rheumatoid Factor 类风湿关节炎因子  1.9     IU/mL       (<15)
hs-CRP 高敏感度C-反应蛋白          0.2     mg/L        (<3.1)

HEPATITIS SCREENING
Hepatitis B Surface Antigen        Negative
Anti-Hepatitis C Virus             Negative
Anti-Hepatitis A Virus IgM         Non-Reactive
"""

# Sample entities (what NER should extract)
SAMPLE_ENTITIES = [
    {"type": "lab_test", "value": "Hemoglobin 血红蛋白: 15.8 g/dL (13.0 - 18.0)", "confidence": 0.95},
    {"type": "lab_test", "value": "ALT 谷丙转氨酶: * 68 U/L (<41)", "confidence": 0.93},
    {"type": "lab_test", "value": "Rheumatoid Factor 类风湿关节炎因子: 1.9 IU/mL (<15)", "confidence": 0.96},
    {"type": "lab_test", "value": "hs-CRP 高敏感度C-反应蛋白: 0.2 mg/L (<3.1)", "confidence": 0.94},
    {"type": "disease", "value": "Hepatitis B", "confidence": 0.89},
    {"type": "disease", "value": "Hepatitis C", "confidence": 0.88}
]

def test_metadata_parsing():
    """Test metadata extraction"""
    print("\n" + "="*80)
    print("TEST 1: METADATA PARSING")
    print("="*80)
    
    metadata = parse_metadata_from_text(SAMPLE_TEXT)
    
    print(f"\n✅ Extracted {len(metadata)} metadata fields:")
    for key, value in metadata.items():
        if value:
            print(f"   {key:20s}: {value}")
    
    # Validate critical fields
    assert metadata.get('lab_no') == 'RLL25428006', "Lab No not parsed correctly"
    assert metadata.get('mrn') == 'PIL250585899', "MRN not parsed correctly"
    assert metadata.get('collected_date') == '23.11.2025 10:28:52', "Collected date not parsed correctly"
    assert metadata.get('facility'), "Facility name not parsed"
    assert metadata.get('gender') == 'Male', "Gender not parsed correctly"
    
    print("\n✅ All metadata assertions passed!")
    return metadata

def test_section_structure():
    """Test section detection"""
    print("\n" + "="*80)
    print("TEST 2: SECTION STRUCTURE DETECTION")
    print("="*80)
    
    sections = extract_section_structure(SAMPLE_TEXT)
    
    print(f"\n✅ Detected {len(sections)} sections:")
    for sec in sections:
        print(f"   {sec['section_name']:30s} (lines {sec['start_line']}-{sec['end_line']})")
    
    # Validate section names
    section_names = [s['section_name'] for s in sections]
    assert 'HAEMATOLOGY' in section_names, "HAEMATOLOGY section not detected"
    assert 'BIOCHEMISTRY' in section_names, "BIOCHEMISTRY section not detected"
    assert 'IMMUNOLOGY & SEROLOGY' in section_names or 'IMMUNOLOGY' in section_names, "IMMUNOLOGY section not detected"
    
    print("\n✅ All section assertions passed!")
    return sections

def test_entity_parsing():
    """Test entity component parsing"""
    print("\n" + "="*80)
    print("TEST 3: ENTITY COMPONENT PARSING")
    print("="*80)
    
    enhanced_entities = []
    
    for entity in SAMPLE_ENTITIES:
        entity_copy = entity.copy()
        
        if entity.get('type') == 'lab_test':
            parsed = parse_entity_components(entity.get('value', ''), entity.get('type', ''))
            entity_copy.update(parsed)
        
        enhanced_entities.append(entity_copy)
    
    print(f"\n✅ Enhanced {len(enhanced_entities)} entities:")
    
    for entity in enhanced_entities:
        if entity.get('test_name'):
            print(f"\n   Test: {entity['test_name']}")
            print(f"      Value: {entity.get('value_numeric')} {entity.get('unit')}")
            print(f"      Ref Range: {entity.get('ref_range_low')} - {entity.get('ref_range_high')}")
            print(f"      Abnormal: {entity.get('is_abnormal')}")
            print(f"      Flag: {entity.get('flag')}")
    
    # Validate specific entities
    hemoglobin = next((e for e in enhanced_entities if 'Hemoglobin' in e.get('value', '')), None)
    assert hemoglobin, "Hemoglobin entity not found"
    assert hemoglobin.get('test_name') == 'Hemoglobin 血红蛋白', "Hemoglobin test name not parsed (multilingual)"
    assert hemoglobin.get('value_numeric') == 15.8, "Hemoglobin value not parsed"
    assert hemoglobin.get('unit') == 'g/dL', "Hemoglobin unit not parsed"
    assert hemoglobin.get('ref_range_low') == 13.0, "Hemoglobin ref_range_low not parsed"
    assert hemoglobin.get('ref_range_high') == 18.0, "Hemoglobin ref_range_high not parsed"
    assert hemoglobin.get('is_abnormal') == False, "Hemoglobin abnormal flag incorrect"
    
    alt = next((e for e in enhanced_entities if 'ALT' in e.get('value', '')), None)
    assert alt, "ALT entity not found"
    assert alt.get('value_numeric') == 68.0, "ALT value not parsed"
    assert alt.get('flag') == '*', "ALT flag not detected"
    assert alt.get('is_abnormal') == True, "ALT abnormal flag incorrect (should be True)"
    
    print("\n✅ All entity parsing assertions passed!")
    return enhanced_entities

def test_full_json_structure():
    """Test complete PostgreSQL JSON structure"""
    print("\n" + "="*80)
    print("TEST 4: FULL PostgreSQL JSON STRUCTURE")
    print("="*80)
    
    # Create ProcessingResult with all parsed data
    metadata = parse_metadata_from_text(SAMPLE_TEXT)
    sections = extract_section_structure(SAMPLE_TEXT)
    
    # Parse entities
    enhanced_entities = []
    for entity in SAMPLE_ENTITIES:
        entity_copy = entity.copy()
        if entity.get('type') == 'lab_test':
            parsed = parse_entity_components(entity.get('value', ''), entity.get('type', ''))
            entity_copy.update(parsed)
        enhanced_entities.append(entity_copy)
    
    # Create ProcessingResult (mimicking process_pdf output)
    result = ProcessingResult(
        filename="Sample Medical Report.pdf",
        file_type="pdf",
        status="success",
        extracted_text=SAMPLE_TEXT,
        confidence=0.85,
        page_count=3,
        medical_entities=enhanced_entities,
        metadata=metadata,
        sections=sections,
        source_path="usm-raw-unstructured/2026/03/24/Sample_Medical_Report.pdf",
        file_hash="sha256:abc123def456...",
        processing_time=416.0,
        vram_used_mb=11220.0
    )
    
    # Generate PostgreSQL JSON
    postgres_json = result.to_postgres_json()
    
    print("\n✅ Generated PostgreSQL JSON:")
    print(json.dumps(postgres_json, indent=2, ensure_ascii=False))
    
    # Validate structure
    assert 'document' in postgres_json, "Missing 'document' key"
    assert 'metadata' in postgres_json, "Missing 'metadata' key"
    assert 'extracted_text' in postgres_json, "Missing 'extracted_text' key"
    assert 'medical_entities' in postgres_json, "Missing 'medical_entities' key"
    assert 'sections' in postgres_json, "Missing 'sections' key"
    assert 'processing_metadata' in postgres_json, "Missing 'processing_metadata' key"
    
    # Validate document section
    doc = postgres_json['document']
    assert doc['filename'] == "Sample Medical Report.pdf", "Document filename missing"
    assert doc['ocr_engine'] == "Qwen3-VL-4B-Thinking", "OCR engine not recorded"
    assert doc['page_count'] == 3, "Page count incorrect"
    assert doc['confidence_score'] == 0.85, "Confidence score missing"
    
    # Validate metadata section
    meta = postgres_json['metadata']
    assert meta['lab_no'] == 'RLL25428006', "Lab No not in PostgreSQL JSON"
    assert meta['mrn'] == 'PIL250585899', "MRN not in PostgreSQL JSON"
    assert meta['facility'], "Facility not in PostgreSQL JSON"
    
    # Validate entities
    entities = postgres_json['medical_entities']
    assert len(entities) > 0, "No entities in PostgreSQL JSON"
    
    # Check first lab test entity has parsed components
    lab_tests = [e for e in entities if e.get('test_name')]
    assert len(lab_tests) > 0, "No lab tests with parsed components"
    
    first_test = lab_tests[0]
    assert 'test_name' in first_test, "test_name missing from entity"
    assert 'value_numeric' in first_test, "value_numeric missing from entity"
    assert 'unit' in first_test, "unit missing from entity"
    assert 'is_abnormal' in first_test, "is_abnormal missing from entity"
    
    # Validate sections
    secs = postgres_json['sections']
    assert len(secs) >= 3, f"Expected at least 3 sections, got {len(secs)}"
    
    print("\n✅ All JSON structure assertions passed!")
    print(f"\n📊 JSON Statistics:")
    print(f"   Total size: {len(json.dumps(postgres_json))} bytes")
    print(f"   Metadata fields: {len([k for k,v in meta.items() if v])}")
    print(f"   Entities: {len(entities)}")
    print(f"   Sections: {len(secs)}")
    print(f"   Lab tests with parsed components: {len(lab_tests)}")
    
    return postgres_json

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print(" TESTING PARSING INTEGRATION (NO GPU REQUIRED)")
    print("="*80)
    print("\nThis test validates the parsing functions and JSON structure")
    print("without requiring GPU access. It uses sample medical report text.")
    
    try:
        # Run tests
        metadata = test_metadata_parsing()
        sections = test_section_structure()
        entities = test_entity_parsing()
        postgres_json = test_full_json_structure()
        
        # Save sample output
        output_file = Path("pipeline_output") / "test_parsing_output.json"
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(postgres_json, f, indent=2, ensure_ascii=False)
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED!")
        print("="*80)
        print(f"\nSample PostgreSQL JSON saved to: {output_file}")
        print("\nReady for GPU test with:")
        print("   python3 standalone_unstructured_pipeline.py \"Sample Medical Report.pdf\"")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
