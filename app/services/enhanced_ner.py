"""
Enhanced NER Module - Ported from Tested Standalone Pipeline
=============================================================
Comprehensive medical entity extraction with:
- Multi-pattern lab test detection (handles Premier Labs, hospital formats)
- Flexible metadata parsing (lab_no, MRN, dates, facility)
- Entity component parsing (test name, value, unit, ref range, flags)
- Section structure detection
- Chinese + English support

Author: Syarifah Fajriyah
Date: April 7, 2026
Ported from: standalone_unstructured_pipeline.py (TESTED & PROVEN)
"""

import re
from typing import Dict, List, Any, Optional


def clean_ocr_text(text: str) -> str:
    """
    Clean OCR artifacts from text (chat template tokens, etc.)
    """
    # Remove chat template markers
    text = re.sub(r'\b(system|user|assistant)\b\s*\n*', '', text, flags=re.IGNORECASE)
    
    # Remove multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def extract_medical_entities_comprehensive(text: str) -> List[Dict[str, Any]]:
    """
    COMPREHENSIVE NER from tested standalone pipeline
    Extracts lab tests from multiple formats with high accuracy
    
    Returns: [{"type": "lab_test", "value": "Haemoglobin: 15.8 g/dL (13.0 - 18.0)", "confidence": 0.90}]
    """
    # Clean OCR artifacts
    text = clean_ocr_text(text)
    
    entities = []
    
    # PRIORITY 1: Extract lab tests from structured format (Premier Labs, hospital reports)
    # Pattern: [Test Name] [Chinese] [Value] [Unit] ([Ref Range])
    lab_test_pattern = re.compile(
        r'^([A-Z][A-Za-z ,\-/()#]+?(?:\s+[\u4e00-\u9fff]+)?)'  # Test name + Chinese
        r'\s{2,}'  # 2+ whitespace chars
        r'([*])?\s*'  # Optional asterisk flag
        r'([<>≤≥]?\s*\d+\.?\d*)\s+'  # Value with optional operator
        r'([a-zA-Z/%^0-9\-\.]+)\s*'  # Unit
        r'\(\s*([^\)\n]+?)\s*\)',  # Reference range
        re.MULTILINE | re.UNICODE
    )
    
    for match in lab_test_pattern.finditer(text):
        test_name = match.group(1).strip()
        flag = match.group(2)
        value = match.group(3).strip()
        unit = match.group(4).strip()
        ref_range = match.group(5).strip()
        
        # Skip if test_name is too short or contains issues
        if len(test_name) < 3 or '\n' in test_name or test_name.isupper():
            continue
        
        # Skip if unit is suspiciously long
        if len(unit) > 20:
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
    
    # PRIORITY 1B: Extract qualitative test results (Positive/Negative/Reactive)
    qualitative_pattern = re.compile(
        r'^([A-Z][A-Za-z ,\-/()#]+?(?:  +[\u4e00-\u9fff]+)?)'  # Test name + Chinese
        r'\s{2,}'  # Multiple spaces
        r'(Positive|Negative|Reactive|Non-Reactive|Non Reactive|Detected|Not Detected|Clear|Nil)',
        re.MULTILINE | re.IGNORECASE | re.UNICODE
    )
    
    for match in qualitative_pattern.finditer(text):
        test_name = match.group(1).strip()
        result = match.group(2).strip()
        
        # STRICT validation
        if (len(test_name) < 8 or 
            test_name.lower() == result.lower() or
            '\n' in test_name or 
            test_name.isupper() or 
            test_name.startswith('Category')):
            continue
        
        entities.append({
            'type': 'lab_test',
            'value': f"{test_name}: {result}",
            'confidence': 0.90
        })
    
    # PRIORITY 1C: Compact format with minimal whitespace
    compact_pattern = re.compile(
        r'([A-Z][A-Za-z ,\-/()#]+?[\u4e00-\u9fff]+?)\s+'  # Test name MUST have Chinese
        r'([*])?\s*'  # Optional asterisk flag
        r'([<>≤≥]?\s*\d+\.?\d*)\s+'  # Value
        r'([a-zA-Z/%^0-9\-\.]+)\s*'  # Unit
        r'\(\s*([^\)\n]+?)\s*\)',  # Reference range
        re.MULTILINE | re.UNICODE
    )
    
    for match in compact_pattern.finditer(text):
        test_name = match.group(1).strip()
        flag = match.group(2)
        value = match.group(3).strip()
        unit = match.group(4).strip()
        ref_range = match.group(5).strip()
        
        # Skip if issues detected
        if len(test_name) < 3 or '\n' in test_name or test_name.isupper() or len(unit) > 20:
            continue
        
        # Build entity
        entity_value = f"{test_name}: {value} {unit} ({ref_range})"
        if flag:
            entity_value = f"{test_name}: {flag} {value} {unit} ({ref_range})"
        
        # Avoid duplicates from wide-whitespace pattern
        if not any(e.get('value', '').startswith(test_name) for e in entities):
            entities.append({
                'type': 'lab_test',
                'value': entity_value,
                'confidence': 0.90
            })
    
    # PRIORITY 1D: Chinese-only test names (no English prefix)
    chinese_only_pattern = re.compile(
        r'^([\u4e00-\u9fff]{2,})\s+'  # Chinese test name (2+ chars)
        r'([*])?\s*'  # Optional asterisk
        r'([<>≤≥]?\s*\d+\.?\d*)\s+'  # Value
        r'([a-zA-Z/%^0-9\-\.]+)\s*'  # Unit
        r'\(\s*([^\)\n]+?)\s*\)',  # Reference range
        re.MULTILINE | re.UNICODE
    )
    
    for match in chinese_only_pattern.finditer(text):
        test_name = match.group(1).strip()
        flag = match.group(2)
        value = match.group(3).strip()
        unit = match.group(4).strip()
        ref_range = match.group(5).strip()
        
        # Skip if unit is too long
        if len(unit) > 20:
            continue
        
        # Build entity
        entity_value = f"{test_name}: {value} {unit} ({ref_range})"
        if flag:
            entity_value = f"{test_name}: {flag} {value} {unit} ({ref_range})"
        
        # Avoid duplicates
        if not any(e.get('value', '').startswith(test_name) for e in entities):
            entities.append({
                'type': 'lab_test',
                'value': entity_value,
                'confidence': 0.90
            })
    
    # ✅ DEDUPLICATION: Remove duplicate entities by value
    seen_values = set()
    unique_entities = []
    for entity in entities:
        entity_key = f"{entity['type']}:{entity['value']}"
        if entity_key not in seen_values:
            seen_values.add(entity_key)
            unique_entities.append(entity)
    
    return unique_entities


def parse_metadata_from_text(text: str) -> Dict[str, Any]:
    """
    GENERIC metadata extraction from ANY medical document
    Extracts: Lab No, MRN, Dates, Facility, Patient info
    """
    # Clean OCR artifacts
    text = clean_ocr_text(text)
    
    metadata = {}
    
    # === IDENTIFIERS ===
    # Lab No / Lab Number / Lab ID / Reference No
    lab_patterns = [
        r'Lab\s*(?:No|Number|ID|Ref)[\s:：]+([A-Z0-9-]+)',
        r'Reference\s*(?:No|Number)[\s:：]+([A-Z0-9-]+)',
        r'Lab\s*#[\s:：]*([A-Z0-9-]+)'
    ]
    for pattern in lab_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            metadata['lab_no'] = match.group(1).strip()
            break
    
    # MRN / Patient ID
    mrn_patterns = [
        r'MRN[\s:：]+([A-Z0-9-]+)',
        r'Patient\s*(?:ID|No)[\s:：]+([A-Z0-9-]+)',
    ]
    for pattern in mrn_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            metadata['mrn'] = match.group(1).strip()
            break
    
    # === DATES ===
    collected_patterns = [
        r'Collected[\s:：]+(\d{2}[\./-]\d{2}[\./-]\d{4}(?:\s+\d{2}:\d{2}(?::\d{2})?)?)',
    ]
    for pattern in collected_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            metadata['collected_date'] = match.group(1).strip()
            break
    
    received_match = re.search(r'Received[\s:：]+(\d{2}[\./-]\d{2}[\./-]\d{4}(?:\s+\d{2}:\d{2}(?::\d{2})?)?)', text, re.IGNORECASE)
    if received_match:
        metadata['received_date'] = received_match.group(1).strip()
    
    reported_match = re.search(r'Reported[\s:：]+(\d{2}[\./-]\d{2}[\./-]\d{4}(?:\s+\d{2}:\d{2}(?::\d{2})?)?)', text, re.IGNORECASE)
    if reported_match:
        metadata['reported_date'] = reported_match.group(1).strip()
    
    # === FACILITY ===
    facility_patterns = [
        r'^([A-Z][A-Za-z\s&]+(?:Labs?|Hospital|Clinic|Centre|Center))',
    ]
    for pattern in facility_patterns:
        match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
        if match:
            metadata['facility'] = match.group(1).strip()
            break
    
    branch_match = re.search(r'Branch[\s:：]+([A-Z0-9\s]{3,20})(?:\s+(?:Collected|Received|Reference|Page|Lab)|$)', text, re.IGNORECASE)
    if branch_match:
        metadata['branch'] = branch_match.group(1).strip()
    
    location_match = re.search(r'Location[\s:：]+([A-Za-z\s]{3,30})(?:\s+(?:Reference|Branch|Collected|Page|Lab)|$)', text, re.IGNORECASE)
    if location_match:
        metadata['location'] = location_match.group(1).strip()
    
    return metadata


def extract_section_structure(text: str) -> List[Dict[str, Any]]:
    """
    GENERIC section detection - finds ALL-CAPS headers
    Returns: [{"section_name": "HAEMATOLOGY", "start_char": 150, "end_char": 890}]
    """
    # Clean OCR artifacts
    text = clean_ocr_text(text)
    
    sections = []
    lines = text.split('\n')
    current_pos = 0
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # Section header: ALL CAPS, 3+ chars, no numbers/special chars
        if (line_stripped.isupper() and 
            len(line_stripped) >= 3 and 
            not re.search(r'\d', line_stripped) and
            re.match(r'^[A-Z\s&-]+$', line_stripped)):
            
            sections.append({
                'section_name': line_stripped,
                'start_char': current_pos,
                'end_char': current_pos  # Will be updated
            })
        
        current_pos += len(line) + 1
    
    # Calculate end positions
    for i in range(len(sections)):
        if i < len(sections) - 1:
            sections[i]['end_char'] = sections[i + 1]['start_char']
        else:
            sections[i]['end_char'] = len(text)
    
    return sections


def parse_table_structure_from_text(text: str) -> Dict[str, Any]:
    """
    STAGE 2: Parse OCR text into structured table format
    Converts flat entity list to proper test rows with preserved table structure
    
    Input: Raw OCR text from Qwen-VL
    Output: {
        "metadata": {"lab_no": "...", "mrn": "...", ...},
        "tests": [
            {
                "test_name": "Haemoglobin",
                "test_name_cn": "血红蛋白",
                "result": "15.8",
                "unit": "g/dL",
                "ref_range_low": 13.0,
                "ref_range_high": 18.0,
                "flag": "",
                "section": "HAEMATOLOGY"
            },
            ...
        ]
    }
    
    This preserves the table structure: one row per test instead of one row with entity_0...entity_N
    """
    # Clean OCR artifacts
    text = clean_ocr_text(text)
    
    # Parse metadata
    metadata = parse_metadata_from_text(text)
    
    # Parse sections for context
    sections = extract_section_structure(text)
    section_map = {}  # Map character positions to section names
    for section in sections:
        section_map[section['start_char']] = section['section_name']
    
    # Extract tests using the same comprehensive patterns
    tests = []
    current_section = "GENERAL"  # Default section
    
    # Track processed line positions to avoid duplicates
    processed_positions = set()
    
    # Pattern 1: Wide-whitespace format (Premier Labs)
    lab_test_pattern = re.compile(
        r'^([A-Z][A-Za-z ,\-/()#]+?)(?:\s+([\u4e00-\u9fff]+))?'  # Name + optional Chinese
        r'\s{2,}'  # Multiple spaces
        r'([*])?\s*'  # Optional flag
        r'([<>≤≥]?\s*\d+\.?\d*)\s+'  # Value
        r'([a-zA-Z/%^0-9\-\.]+)\s*'  # Unit
        r'\(\s*([^\)\n]+?)\s*\)',  # Reference range
        re.MULTILINE | re.UNICODE
    )
    
    for match in lab_test_pattern.finditer(text):
        # Check if this line was already processed
        start_pos = match.start()
        if start_pos in processed_positions:
            continue
        processed_positions.add(start_pos)
        
        test_name = match.group(1).strip()
        test_name_cn = match.group(2).strip() if match.group(2) else ""
        flag = match.group(3) if match.group(3) else ""
        result = match.group(4).strip()
        unit = match.group(5).strip()
        ref_range = match.group(6).strip()
        
        # Skip invalid extractions
        if len(test_name) < 3 or '\n' in test_name or test_name.isupper() or len(unit) > 20:
            continue
        
        # Find current section
        for section in sections:
            if section['start_char'] <= start_pos < section['end_char']:
                current_section = section['section_name']
                break
        
        # Parse reference range
        ref_low, ref_high = _parse_reference_range(ref_range)
        
        # Parse result value (handle <, >, etc.)
        result_numeric, result_operator = _parse_result_value(result)
        
        tests.append({
            "test_name": test_name,
            "test_name_cn": test_name_cn,
            "result": result_numeric,
            "result_operator": result_operator,
            "unit": unit,
            "ref_range_low": ref_low,
            "ref_range_high": ref_high,
            "ref_range_text": ref_range,
            "flag": flag,
            "section": current_section,
            "is_abnormal": flag == "*"
        })
    
    # Pattern 2: Qualitative results (Positive/Negative)
    qualitative_pattern = re.compile(
        r'^([A-Z][A-Za-z ,\-/()#]+?)(?:\s{2,}([\u4e00-\u9fff]+))?'
        r'\s{2,}'
        r'(Positive|Negative|Reactive|Non-Reactive|Non Reactive|Detected|Not Detected|Clear|Nil)',
        re.MULTILINE | re.IGNORECASE | re.UNICODE
    )
    
    for match in qualitative_pattern.finditer(text):
        start_pos = match.start()
        if start_pos in processed_positions:
            continue
        processed_positions.add(start_pos)
        
        test_name = match.group(1).strip()
        test_name_cn = match.group(2).strip() if match.group(2) else ""
        result = match.group(3).strip()
        
        # Validation
        if len(test_name) < 8 or test_name.lower() == result.lower() or '\n' in test_name or test_name.isupper():
            continue
        
        # Find section
        for section in sections:
            if section['start_char'] <= start_pos < section['end_char']:
                current_section = section['section_name']
                break
        
        tests.append({
            "test_name": test_name,
            "test_name_cn": test_name_cn,
            "result": result,
            "result_operator": "",
            "unit": "",
            "ref_range_low": None,
            "ref_range_high": None,
            "ref_range_text": "",
            "flag": "",
            "section": current_section,
            "is_abnormal": result.lower() in ["positive", "reactive", "detected"]
        })
    
    # Pattern 3: Compact format (single space)
    compact_pattern = re.compile(
        r'([A-Z][A-Za-z ,\-/()#]+?[\u4e00-\u9fff]+?)\s+'
        r'([*])?\s*'
        r'([<>≤≥]?\s*\d+\.?\d*)\s+'
        r'([a-zA-Z/%^0-9\-\.]+)\s*'
        r'\(\s*([^\)\n]+?)\s*\)',
        re.MULTILINE | re.UNICODE
    )
    
    for match in compact_pattern.finditer(text):
        start_pos = match.start()
        if start_pos in processed_positions:
            continue
        processed_positions.add(start_pos)
        
        test_name = match.group(1).strip()
        flag = match.group(2) if match.group(2) else ""
        result = match.group(3).strip()
        unit = match.group(4).strip()
        ref_range = match.group(5).strip()
        
        if len(test_name) < 3 or '\n' in test_name or len(unit) > 20:
            continue
        
        # Extract Chinese and English parts
        chinese_match = re.search(r'[\u4e00-\u9fff]+', test_name)
        test_name_cn = chinese_match.group(0) if chinese_match else ""
        test_name_en = re.sub(r'[\u4e00-\u9fff]+', '', test_name).strip()
        
        # Find section
        for section in sections:
            if section['start_char'] <= start_pos < section['end_char']:
                current_section = section['section_name']
                break
        
        ref_low, ref_high = _parse_reference_range(ref_range)
        result_numeric, result_operator = _parse_result_value(result)
        
        tests.append({
            "test_name": test_name_en or test_name,
            "test_name_cn": test_name_cn,
            "result": result_numeric,
            "result_operator": result_operator,
            "unit": unit,
            "ref_range_low": ref_low,
            "ref_range_high": ref_high,
            "ref_range_text": ref_range,
            "flag": flag,
            "section": current_section,
            "is_abnormal": flag == "*"
        })
    
    # Pattern 4: Chinese-only test names
    chinese_only_pattern = re.compile(
        r'^([\u4e00-\u9fff]{2,})\s+'
        r'([*])?\s*'
        r'([<>≤≥]?\s*\d+\.?\d*)\s+'
        r'([a-zA-Z/%^0-9\-\.]+)\s*'
        r'\(\s*([^\)\n]+?)\s*\)',
        re.MULTILINE | re.UNICODE
    )
    
    for match in chinese_only_pattern.finditer(text):
        start_pos = match.start()
        if start_pos in processed_positions:
            continue
        processed_positions.add(start_pos)
        
        test_name_cn = match.group(1).strip()
        flag = match.group(2) if match.group(2) else ""
        result = match.group(3).strip()
        unit = match.group(4).strip()
        ref_range = match.group(5).strip()
        
        if len(unit) > 20:
            continue
        
        # Find section
        for section in sections:
            if section['start_char'] <= start_pos < section['end_char']:
                current_section = section['section_name']
                break
        
        ref_low, ref_high = _parse_reference_range(ref_range)
        result_numeric, result_operator = _parse_result_value(result)
        
        tests.append({
            "test_name": test_name_cn,  # Use Chinese as primary name
            "test_name_cn": test_name_cn,
            "result": result_numeric,
            "result_operator": result_operator,
            "unit": unit,
            "ref_range_low": ref_low,
            "ref_range_high": ref_high,
            "ref_range_text": ref_range,
            "flag": flag,
            "section": current_section,
            "is_abnormal": flag == "*"
        })
    
    return {
        "metadata": metadata,
        "tests": tests,
        "sections": sections
    }


def _parse_reference_range(ref_range_text: str) -> tuple:
    """
    Parse reference range text to low/high values
    Examples: "13.0 - 18.0" → (13.0, 18.0)
              "<3.1" → (None, 3.1)
              ">=10" → (10.0, None)
    """
    ref_low, ref_high = None, None
    
    # Format 1: Range (13.0 - 18.0)
    range_match = re.search(r'([<>]?\d+\.?\d*)\s*-\s*(\d+\.?\d*)', ref_range_text)
    if range_match:
        ref_low = float(range_match.group(1).lstrip('<>'))
        ref_high = float(range_match.group(2))
    else:
        # Format 2: Single threshold (<3.1, >=10)
        single_match = re.search(r'([<>≤≥]+)(\d+\.?\d*)', ref_range_text)
        if single_match:
            operator = single_match.group(1)
            value = float(single_match.group(2))
            if '<' in operator or '≤' in operator:
                ref_high = value
            elif '>' in operator or '≥' in operator:
                ref_low = value
    
    return ref_low, ref_high


def _parse_result_value(result_text: str) -> tuple:
    """
    Parse result value with operator
    Examples: "15.8" → (15.8, "")
              "<3.5" → (3.5, "<")
              ">90" → (90.0, ">")
    """
    match = re.match(r'([<>≤≥]?)\s*(\d+\.?\d*)', result_text)
    if match:
        operator = match.group(1)
        value = float(match.group(2))
        return value, operator
    
    # If not numeric, return as-is
    return result_text, ""
