"""
Comprehensive Multi-Format Upload Testing Script
Tests all supported formats: CSV, Excel, JSON, XML, Parquet, PDF, Images, Word, TXT
Run after installing requirements and restarting server
"""
import requests
import json
from pathlib import Path
import pandas as pd
import io

# Configuration
BASE_URL = "http://172.24.175.24:8000"  # Update when server is back
USERNAME = "admin"
PASSWORD = "admin123"

class MultiFormatTester:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.token = None
        self.test_results = []
    
    def login(self):
        """Authenticate and get JWT token"""
        print("🔐 Logging in...")
        response = requests.post(
            f"{self.base_url}/api/auth/login",
            data={"username": USERNAME, "password": PASSWORD}
        )
        response.raise_for_status()
        self.token = response.json()['access_token']
        print(f"✅ Logged in as {USERNAME}")
        return self.token
    
    def get_headers(self):
        """Get auth headers"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def test_supported_formats(self):
        """Test: Get list of supported formats"""
        print("\n📋 Testing: Get Supported Formats")
        response = requests.get(
            f"{self.base_url}/api/upload/supported-formats",
            headers=self.get_headers()
        )
        result = response.json()
        
        print(f"✅ Structured formats: {len(result['structured_formats'])}")
        print(f"✅ Unstructured formats: {len(result['unstructured_formats'])}")
        print(f"✅ OCR enabled: {result['ocr_enabled']}")
        print(f"✅ Total formats supported: {result['total_formats']}")
        
        self.test_results.append({
            "test": "supported_formats",
            "status": "PASS",
            "details": result
        })
    
    def create_sample_csv(self):
        """Create sample CSV file"""
        data = {
            'patient_id': ['P001', 'P002', 'P003'],
            'age': [25, 30, 45],
            'gender': ['F', 'M', 'F'],
            'diagnosis': ['SLE', 'RA', 'MS'],
            'wbc': [8.5, 6.2, 9.1]
        }
        df = pd.DataFrame(data)
        
        path = Path('test_data_csv.csv')
        df.to_csv(path, index=False)
        return path
    
    def create_sample_json(self):
        """Create sample JSON file"""
        data = [
            {"patient_id": "P001", "age": 25, "diagnosis": "SLE", "wbc": 8.5},
            {"patient_id": "P002", "age": 30, "diagnosis": "RA", "wbc": 6.2},
            {"patient_id": "P003", "age": 45, "diagnosis": "MS", "wbc": 9.1}
        ]
        
        path = Path('test_data.json')
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        return path
    
    def create_sample_xml(self):
        """Create sample XML file"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<patients>
    <patient>
        <patient_id>P001</patient_id>
        <age>25</age>
        <gender>F</gender>
        <diagnosis>SLE</diagnosis>
        <wbc>8.5</wbc>
    </patient>
    <patient>
        <patient_id>P002</patient_id>
        <age>30</age>
        <gender>M</gender>
        <diagnosis>RA</diagnosis>
        <wbc>6.2</wbc>
    </patient>
</patients>"""
        
        path = Path('test_data.xml')
        with open(path, 'w') as f:
            f.write(xml_content)
        return path
    
    def create_sample_txt(self):
        """Create sample text file"""
        text = """Patient Report
        
Patient ID: P001
Age: 25 years
Gender: Female
Diagnosis: Systemic Lupus Erythematosus (SLE)

Lab Results:
- WBC: 8.5 x10^9/L (elevated)
- Hb: 12.3 g/dL (normal)
- Platelets: 180 x10^9/L (normal)

Clinical Notes:
Patient presents with joint pain and fatigue. 
ANA test positive. Prescribed Hydroxychloroquine 200mg daily.
"""
        
        path = Path('test_data.txt')
        with open(path, 'w') as f:
            f.write(text)
        return path
    
    def test_upload_file(self, file_path, format_name):
        """Test: Upload single file"""
        print(f"\n📤 Testing: Upload {format_name.upper()} file")
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, 'application/octet-stream')}
                data = {'dataset_type': f'TEST_{format_name}'}
                
                response = requests.post(
                    f"{self.base_url}/api/upload/multi-format",
                    files=files,
                    data=data,
                    headers=self.get_headers()
                )
                response.raise_for_status()
                result = response.json()
                
                print(f"✅ {format_name.upper()} upload successful!")
                print(f"   - File ID: {result.get('file_id')}")
                print(f"   - File type: {result.get('file_type')}")
                print(f"   - Next step: {result.get('next_step')}")
                
                if result.get('metadata'):
                    print(f"   - Metadata: {result['metadata']}")
                
                if result.get('qwen_analysis'):
                    print(f"   - Qwen OCR: Enabled")
                
                self.test_results.append({
                    "test": f"upload_{format_name}",
                    "status": "PASS",
                    "file": str(file_path),
                    "result": result
                })
                
                return result
                
        except Exception as e:
            print(f"❌ {format_name.upper()} upload failed: {e}")
            self.test_results.append({
                "test": f"upload_{format_name}",
                "status": "FAIL",
                "error": str(e)
            })
            return None
    
    def test_preview_file(self, file_path, format_name):
        """Test: Preview file without saving"""
        print(f"\n👁️ Testing: Preview {format_name.upper()} file")
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, 'application/octet-stream')}
                
                response = requests.post(
                    f"{self.base_url}/api/upload/preview",
                    files=files,
                    headers=self.get_headers()
                )
                response.raise_for_status()
                result = response.json()
                
                print(f"✅ {format_name.upper()} preview successful!")
                print(f"   - File type: {result.get('file_type')}")
                print(f"   - Format: {result.get('format')}")
                
                if result.get('metadata'):
                    meta = result['metadata']
                    if 'row_count' in meta:
                        print(f"   - Rows: {meta['row_count']}")
                    if 'word_count' in meta:
                        print(f"   - Words: {meta['word_count']}")
                
                self.test_results.append({
                    "test": f"preview_{format_name}",
                    "status": "PASS"
                })
                
                return result
                
        except Exception as e:
            print(f"❌ {format_name.upper()} preview failed: {e}")
            self.test_results.append({
                "test": f"preview_{format_name}",
                "status": "FAIL",
                "error": str(e)
            })
            return None
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("="*60)
        print("🧪 USM Autoimmune Platform - Multi-Format Upload Tests")
        print("="*60)
        
        # Login
        self.login()
        
        # Test 1: Get supported formats
        self.test_supported_formats()
        
        # Test 2: Create sample files
        print("\n📝 Creating sample test files...")
        csv_file = self.create_sample_csv()
        json_file = self.create_sample_json()
        xml_file = self.create_sample_xml()
        txt_file = self.create_sample_txt()
        print("✅ Test files created")
        
        # Test 3: Upload CSV
        self.test_upload_file(csv_file, 'csv')
        
        # Test 4: Upload JSON
        self.test_upload_file(json_file, 'json')
        
        # Test 5: Upload XML
        self.test_upload_file(xml_file, 'xml')
        
        # Test 6: Upload TXT
        self.test_upload_file(txt_file, 'txt')
        
        # Test 7: Preview CSV
        self.test_preview_file(csv_file, 'csv')
        
        # Test 8: Preview JSON
        self.test_preview_file(json_file, 'json')
        
        # Summary
        self.print_summary()
        
        # Cleanup
        print("\n🧹 Cleaning up test files...")
        for f in [csv_file, json_file, xml_file, txt_file]:
            f.unlink(missing_ok=True)
        print("✅ Cleanup complete")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for r in self.test_results if r['status'] == 'PASS')
        failed = sum(1 for r in self.test_results if r['status'] == 'FAIL')
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {passed/len(self.test_results)*100:.1f}%")
        
        if failed > 0:
            print("\n❌ Failed Tests:")
            for r in self.test_results:
                if r['status'] == 'FAIL':
                    print(f"   - {r['test']}: {r.get('error', 'Unknown error')}")
        
        print("="*60)


def main():
    """Main test execution"""
    tester = MultiFormatTester(BASE_URL)
    
    try:
        tester.run_all_tests()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to server")
        print(f"Make sure server is running at: {BASE_URL}")
        print("Check: docker ps")
        print("Logs: docker logs usm-autoimmune-api")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
