#!/usr/bin/env python3
"""
Client Custom Entity Detection Demo

This script demonstrates how the Private AI system handles custom client-specific
entity detection and redaction using pattern matching and domain blocklists.
"""

import json
from pii_transform import detect_and_transform, restore_original_values

def test_client_entity_detection():
    """Test detection of client-specific entities using custom patterns"""
    
    # Example client text with sensitive information
    test_text = """
    CONFIDENTIAL - Internal Use Only
    
    Project status update for PROJECT APOLLO and PROJECT ZEUS:
    
    Team Alpha has completed the integration with SecureShield and is now 
    working on PrivacyDefender implementation. The development environment 
    at dev.client-domain.com shows all systems operational.
    
    SENTINEL-12345 alert has been resolved. SEC-MONITOR-XYZ shows no issues 
    with the ADMIN-CONSOLE-123 deployment.
    
    Please check the documentation at confluence.client-domain.com/projects/apollo
    and contact Team Omega for any questions about client-resources.azurewebsites.net.
    
    Partner integration with partner-alpha.com is scheduled for next week.
    """
    
    print("Original Text:")
    print(test_text)
    print("\n" + "-"*50 + "\n")
    
    # Transform the text using our custom patterns and domain blocklist
    transformed, transformation_logs = detect_and_transform(test_text)
    
    print("Transformed Text:")
    print(transformed)
    print("\n" + "-"*50 + "\n")
    
    # Display what entities were detected
    print("Detected Entities:")
    for log in transformation_logs:
        entity_type = log.get('entity_type', 'Unknown')
        entity = log.get('entity', 'Unknown')
        score = log.get('score', 0)
        replacement = log.get('replacement', 'Not replaced')
        
        # Print in a more readable format
        print(f"- Type: {entity_type}")
        print(f"  Original: {log.get('word', 'Unknown')}")
        print(f"  Replacement: {replacement}")
        print(f"  Confidence: {score}")
        print()
    
    # Now restore the original values
    restored = restore_original_values(transformed)
    
    print("Restored Text:")
    print(restored)
    print("\n" + "-"*50 + "\n")
    
    # Verify restoration
    if restored == test_text:
        print("✅ Restoration successful - all original values recovered correctly")
    else:
        print("⚠️ Restoration incomplete - some values could not be restored")

if __name__ == "__main__":
    print("="*80)
    print("CLIENT CUSTOM ENTITY DETECTION DEMO")
    print("="*80)
    print("\nThis demo shows how to protect client-specific sensitive information\n")
    
    test_client_entity_detection()