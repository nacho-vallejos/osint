"""
Test script for SocialCollector
Run this to test the social media username search functionality
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.collectors.social_collector import SocialCollector


async def test_social_collector():
    """Test the SocialCollector with a sample username"""
    
    collector = SocialCollector()
    
    # Test with a common username (likely to exist on multiple platforms)
    test_username = "github"
    
    print(f"🔍 Searching for username: {test_username}")
    print(f"📊 Checking {len(collector.PLATFORMS)} platforms...\n")
    
    # Run the collector
    result = await collector.collect(test_username)
    
    # Display results
    print("=" * 60)
    print(f"✅ Search completed for: {result.target}")
    print("=" * 60)
    
    stats = result.data.get("statistics", {})
    print(f"\n📈 Statistics:")
    print(f"  • Total platforms checked: {stats.get('total_checked', 0)}")
    print(f"  • Profiles found: {stats.get('found', 0)}")
    print(f"  • Not found: {stats.get('not_found', 0)}")
    print(f"  • Errors: {stats.get('errors', 0)}")
    
    print(f"\n✓ Found profiles:")
    found_profiles = result.data.get("found_profiles", [])
    if found_profiles:
        for profile in found_profiles:
            print(f"  • {profile['platform']}: {profile['url']}")
    else:
        print("  (None)")
    
    print(f"\n✗ Not found on:")
    not_found = result.data.get("checked_but_not_found", [])
    if not_found:
        for profile in not_found[:5]:  # Show first 5
            status = f"[{profile.get('status_code', 'N/A')}]"
            error = f" - {profile.get('error', '')}" if 'error' in profile else ""
            print(f"  • {profile['platform']} {status}{error}")
        if len(not_found) > 5:
            print(f"  ... and {len(not_found) - 5} more")
    else:
        print("  (None)")
    
    print("\n" + "=" * 60)
    print("✨ Test completed successfully!")
    
    return result


if __name__ == "__main__":
    print("🚀 Starting SocialCollector Test\n")
    
    try:
        result = asyncio.run(test_social_collector())
        print(f"\n📝 Full result available in 'result' variable")
        print(f"   Entity type: {result.entity_type}")
        print(f"   Collector: {result.collector}")
        print(f"   Success: {result.success}")
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
