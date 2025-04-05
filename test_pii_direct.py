#!/usr/bin/env python3
"""
Direct PII Transformation Test

This script directly tests the PII transformation functionality without going through the proxy.
"""

from pii_transform import PIITransformer

# Sample PII for testing
SAMPLE_TEXT = """
My name is John Smith and my email is john.smith@example.com.
My phone number is (555) 123-4567 and I live at 123 Main St, Anytown, CA 12345.
My social security number is 123-45-6789 and my credit card is 4111-1111-1111-1111.
My date of birth is 01/01/1980.

Please help me write a Python function to calculate the factorial of a number.
"""

def main():
    """Main function"""
    print("🔒 Direct PII Transformation Test")
    print("\n📝 Original text:")
    print(SAMPLE_TEXT)
    
    # Initialize the PII transformer
    transformer = PIITransformer()
    
    # Transform the text
    result = transformer.transform_text(SAMPLE_TEXT)
    
    # The result is a tuple with the transformed text and metadata
    if isinstance(result, tuple) and len(result) > 0:
        transformed_text = result[0]
        metadata = result[1] if len(result) > 1 else []
    else:
        transformed_text = result
        metadata = []
    
    print("\n🔄 Transformed text:")
    print(transformed_text)
    
    if metadata:
        print("\n📊 Transformation metadata:")
        for item in metadata:
            print(f"  - {item['entity_type']}: {item.get('start', 'N/A')}-{item.get('end', 'N/A')}")
    
    # Check if PII was transformed
    pii_items = [
        "John Smith",
        "john.smith@example.com",
        "(555) 123-4567",
        "123 Main St, Anytown, CA 12345",
        "123-45-6789",
        "4111-1111-1111-1111",
        "01/01/1980"
    ]
    
    print("\n🔍 Checking for PII in transformed text:")
    for item in pii_items:
        if item in transformed_text:
            print(f"❌ Found: {item}")
        else:
            print(f"✅ Not found: {item}")
    
    # Summary of what was transformed and what wasn't
    print("\n📋 Summary:")
    transformed_types = set(item['entity_type'] for item in metadata) if metadata else set()
    
    if "EMAIL" in transformed_types:
        print("✅ Emails are being transformed")
    else:
        print("❌ Emails are NOT being transformed")
        
    if "CREDIT_CARD" in transformed_types:
        print("✅ Credit cards are being transformed")
    else:
        print("❌ Credit cards are NOT being transformed")
        
    if "PHONE_NUMBER" in transformed_types:
        print("✅ Phone numbers are being transformed")
    else:
        print("❌ Phone numbers are NOT being transformed")
        
    if "PERSON" in transformed_types or "NAME" in transformed_types:
        print("✅ Names are being transformed")
    else:
        print("❌ Names are NOT being transformed")
        
    if "ADDRESS" in transformed_types or "LOCATION" in transformed_types:
        print("✅ Addresses are being transformed")
    else:
        print("❌ Addresses are NOT being transformed")
        
    if "US_SSN" in transformed_types or "SSN" in transformed_types:
        print("✅ Social Security Numbers are being transformed")
    else:
        print("❌ Social Security Numbers are NOT being transformed")
        
    if "DATE_TIME" in transformed_types or "DATE" in transformed_types:
        print("✅ Dates are being transformed")
    else:
        print("❌ Dates are NOT being transformed")
    
    print("\n⚠️ Note: The proxy is currently using regex-only transformations due to NER model loading issues.")
    print("This means that some types of PII may not be detected and transformed.")

if __name__ == "__main__":
    main()