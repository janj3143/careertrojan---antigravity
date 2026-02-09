import sys
import os

# Add local services to path
sys.path.append(r"C:\careertrojan\services")

from shared.registry.registry import registry

def test_registry():
    print("Testing Registry...")
    
    # Test Defaults
    kafka = registry.check_capability("parsing.resume_parsing")
    print(f"parsing.resume_parsing: {kafka} (Expected: True)")
    
    mock = registry.check_capability("parsing.mock_data_fallback")
    print(f"parsing.mock_data_fallback: {mock} (Expected: False)")
    
    # Test Missing
    missing = registry.check_capability("non_existent.capability")
    print(f"non_existent.capability: {missing} (Expected: False)")
    
    print("Registry Test Complete.")

if __name__ == "__main__":
    test_registry()
