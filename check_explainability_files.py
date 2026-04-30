"""
Quick diagnostic to check if explainability files exist and can import
Run on server: python3 check_explainability_files.py
"""
import os
import sys

print("="*60)
print("🔍 Checking Explainability Files")
print("="*60)
print()

# Check if files exist
files_to_check = [
    "app/api/endpoints/explainability.py",
    "app/services/shap_explainer_service.py", 
    "app/services/gemma_conversational_service.py"
]

print("1. File existence check:")
print()
all_exist = True
for filepath in files_to_check:
    exists = os.path.exists(filepath)
    symbol = "✅" if exists else "❌"
    print(f"   {symbol} {filepath}")
    if exists:
        size = os.path.getsize(filepath)
        print(f"      Size: {size:,} bytes")
    else:
        all_exist = False

print()

if not all_exist:
    print("❌ Some files are missing! Transfer them via WinSCP first.")
    sys.exit(1)

print("2. Import test:")
print()

# Test imports
try:
    from app.api.endpoints import explainability
    print("   ✅ explainability module imports successfully")
    print(f"      Router routes: {len(explainability.router.routes)}")
    for route in explainability.router.routes:
        print(f"         {list(route.methods)} {route.path}")
except Exception as e:
    print(f"   ❌ explainability import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from app.services.shap_explainer_service import SHAPExplainerService
    print("   ✅ SHAPExplainerService imports successfully")
except Exception as e:
    print(f"   ❌ SHAP service import failed: {e}")
    import traceback
    traceback.print_exc()

try:
    from app.services.gemma_conversational_service import GemmaConversationalService
    print("   ✅ GemmaConversationalService imports successfully")
except Exception as e:
    print(f"   ❌ Gemma service import failed: {e}")
    import traceback
    traceback.print_exc()

print()
print("3. Check if router is registered in main.py:")
print()

try:
    from app.main import app
    ml_routes = [r for r in app.routes if hasattr(r, 'path') and '/ml/' in r.path]
    explainability_routes = [r for r in ml_routes if 'explain' in r.path or 'chat' in r.path]
    
    if explainability_routes:
        print(f"   ✅ Found {len(explainability_routes)} explainability routes:")
        for route in explainability_routes:
            methods = list(getattr(route, 'methods', []))
            print(f"      {methods} {route.path}")
    else:
        print("   ❌ No explainability routes found in app!")
        print("      This means the router wasn't included in main.py")
        
except Exception as e:
    print(f"   ❌ Error checking routes: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*60)
print("✅ Diagnostic complete!")
print("="*60)
