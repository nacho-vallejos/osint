"""
Test script for UsernameCollector
"""

import asyncio
import sys
import os

# Add backend to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.collectors.username_collector import UsernameCollector


async def test_username_collector():
    """Test the UsernameCollector with various usernames"""
    
    collector = UsernameCollector()
    
    # Test cases
    test_usernames = [
        "octocat",  # Famous GitHub user
        "elonmusk",  # Elon Musk
        "thisuserdoesnotexist123456789",  # Non-existent
    ]
    
    for username in test_usernames:
        print(f"\n{'='*60}")
        print(f"Testing username: {username}")
        print(f"{'='*60}")
        
        result = await collector.collect(username)
        
        print(f"Success: {result.success}")
        if result.data:
            print(f"Username: {result.data.get('username')}")
            print(f"Platforms checked: {result.data.get('total_platforms')}")
            print(f"Profiles found: {result.data.get('found_count')}")
            
            print("\nFound profiles:")
            for profile in result.data.get('found', []):
                print(f"  ✓ {profile['platform']}: {profile['url']}")
            
            print("\nNot found on:")
            for profile in result.data.get('not_found', []):
                print(f"  ✗ {profile['platform']}")
        
        if result.error:
            print(f"Error: {result.error}")


if __name__ == "__main__":
    asyncio.run(test_username_collector())
