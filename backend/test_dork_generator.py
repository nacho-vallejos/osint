"""
Test script for Passive Dorking functionality
Demonstrates dork generation for various target types
"""

import sys
from app.utils.dork_generator import generate_dorks, generate_dork_for_email


def test_person_dorks():
    """Test dork generation for person/username targets"""
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║           Person Dorks - Username/Name Search                ║")
    print("╚═══════════════════════════════════════════════════════════════╝\n")
    
    target = "octocat"
    dorks = generate_dorks(target, "person")
    
    print(f"Target: {target}")
    print(f"Type: Person/Username")
    print(f"Dorks Generated: {len(dorks)}\n")
    
    for dork in dorks:
        print(f"{dork['icon']} {dork['platform']}")
        print(f"   Description: {dork['description']}")
        print(f"   URL: {dork['url']}\n")


def test_domain_dorks():
    """Test dork generation for domain/infrastructure targets"""
    print("\n╔═══════════════════════════════════════════════════════════════╗")
    print("║         Domain Dorks - Infrastructure Search                 ║")
    print("╚═══════════════════════════════════════════════════════════════╝\n")
    
    target = "example.com"
    dorks = generate_dorks(target, "domain")
    
    print(f"Target: {target}")
    print(f"Type: Domain/Infrastructure")
    print(f"Dorks Generated: {len(dorks)}\n")
    
    for dork in dorks:
        print(f"{dork['icon']} {dork['platform']}")
        print(f"   Description: {dork['description']}")
        print(f"   URL: {dork['url']}\n")


def test_email_dorks():
    """Test dork generation for email addresses"""
    print("\n╔═══════════════════════════════════════════════════════════════╗")
    print("║            Email Dorks - Email Address Search                ║")
    print("╚═══════════════════════════════════════════════════════════════╝\n")
    
    target = "test@example.com"
    dorks = generate_dork_for_email(target)
    
    print(f"Target: {target}")
    print(f"Type: Email Address")
    print(f"Dorks Generated: {len(dorks)}\n")
    
    # Show first 5 dorks
    for dork in dorks[:5]:
        print(f"{dork['icon']} {dork['platform']}")
        print(f"   Description: {dork['description']}")
        print(f"   URL: {dork['url']}\n")


def test_custom_target():
    """Test with custom target from command line"""
    if len(sys.argv) > 1:
        target = sys.argv[1]
        target_type = sys.argv[2] if len(sys.argv) > 2 else "person"
        
        print("\n╔═══════════════════════════════════════════════════════════════╗")
        print("║                Custom Target Dork Generation                 ║")
        print("╚═══════════════════════════════════════════════════════════════╝\n")
        
        if '@' in target:
            print(f"Detected email address, using email-specific dorks...\n")
            dorks = generate_dork_for_email(target)
        else:
            dorks = generate_dorks(target, target_type)
        
        print(f"Target: {target}")
        print(f"Type: {target_type}")
        print(f"Dorks Generated: {len(dorks)}\n")
        
        for dork in dorks[:8]:  # Show first 8
            print(f"{dork['icon']} {dork['platform']}")
            print(f"   {dork['description']}")
            print(f"   {dork['url']}\n")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        test_custom_target()
    else:
        test_person_dorks()
        test_domain_dorks()
        test_email_dorks()
        
        print("\n" + "="*65)
        print("✓ All dork generation tests completed successfully!")
        print("="*65)
        print("\nUsage: python3 test_dork_generator.py [target] [type]")
        print("Example: python3 test_dork_generator.py elonmusk person")
        print("Example: python3 test_dork_generator.py google.com domain")
        print("Example: python3 test_dork_generator.py admin@company.com")
