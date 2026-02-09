"""
Module Import Test for IntelliCV Admin Portal
============================================

This script tests that all 18 admin modules can be imported correctly
and have the required render() function.
"""

import sys
import importlib
from pathlib import Path

# Add the pages directory to Python path
pages_dir = Path(__file__).parent
if str(pages_dir) not in sys.path:
    sys.path.insert(0, str(pages_dir))

# List of all modules to test
MODULES_TO_TEST = [
    "01_User_Management",
    "02_Data_Parsers", 
    "03_System_Monitor",
    "04_AI_Enrichment",
    "05_Analytics",
    "06_Compliance_Audit",
    "07_API_Integration",
    "08_Contact_Communication",
    "09_Batch_Processing",
    "10_Advanced_Logging",
    "11_Advanced_Settings",
    "12_Competitive_Intelligence",
    "13_Enhanced_Glossary",
    "14_System_Snapshot",
    "15_Legacy_Utilities",
    "16_Market_Intelligence_Center",
    "17_AI_Content_Generator",
    "18_Web_Company_Intelligence"
]

def test_module_imports():
    """Test importing all admin modules"""
    print("🧪 Testing IntelliCV Admin Module Imports...")
    print("=" * 50)
    
    results = {
        "success": [],
        "missing_file": [],
        "import_error": [],
        "missing_render": [],
        "other_error": []
    }
    
    for module_name in MODULES_TO_TEST:
        print(f"Testing {module_name}...", end=" ")
        
        try:
            # Check if file exists
            module_file = pages_dir / f"{module_name}.py"
            if not module_file.exists():
                print("❌ FILE NOT FOUND")
                results["missing_file"].append(module_name)
                continue
            
            # Try to import
            module = importlib.import_module(module_name)
            
            # Check for render function
            if hasattr(module, 'render'):
                print("✅ SUCCESS")
                results["success"].append(module_name)
            else:
                print("⚠️  NO RENDER FUNCTION")
                results["missing_render"].append(module_name)
                
        except ImportError as e:
            print(f"❌ IMPORT ERROR: {e}")
            results["import_error"].append((module_name, str(e)))
        except Exception as e:
            print(f"❌ OTHER ERROR: {e}")
            results["other_error"].append((module_name, str(e)))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY:")
    print(f"✅ Successfully imported: {len(results['success'])}")
    print(f"❌ Missing files: {len(results['missing_file'])}")
    print(f"❌ Import errors: {len(results['import_error'])}")
    print(f"⚠️  Missing render function: {len(results['missing_render'])}")
    print(f"❌ Other errors: {len(results['other_error'])}")
    
    # Print details for issues
    if results["missing_file"]:
        print(f"\n📁 Missing files:")
        for module in results["missing_file"]:
            print(f"   - {module}.py")
    
    if results["import_error"]:
        print(f"\n🚫 Import errors:")
        for module, error in results["import_error"]:
            print(f"   - {module}: {error}")
    
    if results["missing_render"]:
        print(f"\n⚠️  Missing render functions:")
        for module in results["missing_render"]:
            print(f"   - {module}")
    
    if results["other_error"]:
        print(f"\n❌ Other errors:")
        for module, error in results["other_error"]:
            print(f"   - {module}: {error}")
    
    # Overall status
    total_modules = len(MODULES_TO_TEST)
    working_modules = len(results["success"])
    
    print(f"\n🎯 OVERALL STATUS: {working_modules}/{total_modules} modules working")
    
    if working_modules == total_modules:
        print("🎉 ALL MODULES READY! The admin portal should work perfectly.")
    else:
        print("⚠️  Some modules need attention before the admin portal will work fully.")
    
    return results

if __name__ == "__main__":
    test_module_imports()