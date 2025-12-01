"""
Test script for IdentityCollector - Person & Digital Identity Discovery
"""

import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.collectors.identity_collector import IdentityCollector


async def test_identity_collector():
    """Test the IdentityCollector with various targets"""
    
    collector = IdentityCollector()
    
    # Test cases: mix of emails and usernames
    test_targets = [
        "octocat",  # Famous GitHub username
        "test@example.com",  # Email (unlikely to have Gravatar)
        "elonmusk",  # High-profile username
    ]
    
    for target in test_targets:
        print(f"\n{'='*70}")
        print(f"Testing Identity Collector for: {target}")
        print(f"{'='*70}")
        
        result = await collector.collect(target)
        
        print(f"\n✓ Success: {result.success}")
        
        if result.error:
            print(f"✗ Error: {result.error}")
            continue
        
        if result.data:
            data = result.data
            print(f"\n📊 Identity Analysis:")
            print(f"  Target: {data.get('target')}")
            print(f"  Type: {data.get('target_type')}")
            print(f"  Signals Found: {data.get('found_signals')}")
            
            # Gravatar info
            gravatar = data.get('gravatar')
            if gravatar:
                print(f"\n🖼️  Gravatar Profile:")
                print(f"    Exists: {gravatar.get('exists')}")
                print(f"    Avatar URL: {gravatar.get('avatar_url')}")
                print(f"    Profile: {gravatar.get('profile_url')}")
            else:
                print(f"\n🖼️  Gravatar: Not found")
            
            # Social accounts
            social_accounts = data.get('social_accounts', [])
            if social_accounts:
                print(f"\n👥 Social Accounts Found ({len(social_accounts)}):")
                for account in social_accounts:
                    icon = account.get('icon', '•')
                    platform = account.get('platform')
                    url = account.get('url')
                    print(f"    {icon} {platform}: {url}")
            else:
                print(f"\n👥 Social Accounts: None found")
            
            # Summary
            summary = data.get('summary')
            if summary:
                print(f"\n📈 Identity Strength: {summary.get('identity_strength', 'unknown').upper()}")
                platforms = summary.get('platforms_with_presence', [])
                if platforms:
                    print(f"   Platforms: {', '.join(platforms)}")
        
        if result.metadata:
            print(f"\n🔍 Metadata:")
            print(f"  Platforms Checked: {result.metadata.get('platforms_checked')}")
            print(f"  Gravatar Checked: {result.metadata.get('gravatar_checked')}")
            print(f"  Username Used: {result.metadata.get('username_used')}")


async def test_with_custom_target():
    """Test with a custom target provided via command line"""
    
    if len(sys.argv) > 1:
        custom_target = sys.argv[1]
        print(f"\n{'='*70}")
        print(f"Custom Identity Search: {custom_target}")
        print(f"{'='*70}")
        
        collector = IdentityCollector()
        result = await collector.collect(custom_target)
        
        # Pretty print the full result
        print("\nFull JSON Result:")
        print(json.dumps({
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "metadata": result.metadata
        }, indent=2, default=str))


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════╗
║           IdentityCollector Test Suite                          ║
║     Person Discovery & Digital Identity Footprint Analysis      ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Run tests
    if len(sys.argv) > 1:
        asyncio.run(test_with_custom_target())
    else:
        asyncio.run(test_identity_collector())
    
    print("\n✓ Test completed")
