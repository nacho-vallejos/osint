"""
Test script for SocialProfiler service
Demonstrates username discovery across platforms
"""

import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.social_recon import SocialProfiler, ProfileStatus


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def test_social_profiler():
    """Test SocialProfiler with multiple usernames"""
    
    print("=" * 70)
    print("🔍 SOCIAL PROFILER TEST - Identity Triangulation")
    print("=" * 70)
    
    # Test usernames (mix of likely found and not found)
    test_usernames = [
        "github",      # Likely to exist on many platforms
        "torvalds",    # Linus Torvalds - Linux creator
        "elonmusk",    # Elon Musk
    ]
    
    profiler = SocialProfiler(timeout=10, max_retries=2)
    
    try:
        for username in test_usernames:
            print(f"\n{'=' * 70}")
            print(f"🎯 Target Username: {username}")
            print(f"{'=' * 70}\n")
            
            # Discover all profiles
            profiles = await profiler.discover_profiles(username)
            
            # Separate by status
            found = [p for p in profiles if p.status == ProfileStatus.FOUND]
            not_found = [p for p in profiles if p.status == ProfileStatus.NOT_FOUND]
            errors = [p for p in profiles if p.status == ProfileStatus.ERROR]
            
            # Display statistics
            print(f"📊 RESULTS:")
            print(f"  ✅ Found: {len(found)} profiles")
            print(f"  ❌ Not Found: {len(not_found)} profiles")
            print(f"  ⚠️  Errors: {len(errors)} platforms")
            print(f"  📈 Total Checked: {len(profiles)} platforms")
            
            # Show found profiles
            if found:
                print(f"\n✨ CONFIRMED PROFILES:")
                for profile in found:
                    confidence_bar = "█" * int(profile.confidence * 10)
                    print(f"  • {profile.platform:15} | {profile.url:50} | Confidence: {confidence_bar} {profile.confidence:.2f}")
            
            # Show high-confidence not found
            if not_found:
                high_conf_not_found = [p for p in not_found if p.confidence > 0.8]
                if high_conf_not_found:
                    print(f"\n❌ CONFIRMED NOT FOUND (high confidence):")
                    for profile in high_conf_not_found[:5]:
                        print(f"  • {profile.platform:15} | Not present")
            
            # Show errors
            if errors:
                print(f"\n⚠️  ERRORS:")
                for profile in errors[:3]:
                    error_msg = profile.metadata.get('error', 'Unknown error')
                    print(f"  • {profile.platform:15} | {error_msg}")
            
            # Generate graph data structure
            print(f"\n🔗 GRAPH RELATIONSHIP DATA:")
            print(f"  Person(username='{username}') -[HAS_ACCOUNT]-> SocialProfile")
            for profile in found:
                print(f"    └─> {profile.platform} ({profile.url}) [confidence: {profile.confidence:.2f}]")
        
        # Test context manager
        print(f"\n\n{'=' * 70}")
        print("🧪 Testing Context Manager:")
        print(f"{'=' * 70}\n")
        
        async with SocialProfiler() as profiler2:
            confirmed = await profiler2.get_confirmed_profiles("python")
            print(f"Found {len(confirmed)} confirmed profiles for 'python':")
            for profile in confirmed[:5]:
                print(f"  • {profile.platform}: {profile.url}")
        
        print(f"\n{'=' * 70}")
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print(f"{'=' * 70}\n")
    
    finally:
        await profiler.close()


async def test_platform_filtering():
    """Test targeting specific platforms"""
    
    print("\n" + "=" * 70)
    print("🎯 PLATFORM FILTERING TEST")
    print("=" * 70 + "\n")
    
    async with SocialProfiler() as profiler:
        # Only check GitHub and Twitter
        profiles = await profiler.discover_profiles(
            "github",
            platforms=["GitHub", "Twitter", "LinkedIn"]
        )
        
        print(f"Checked {len(profiles)} platforms (filtered):")
        for profile in profiles:
            status_emoji = "✅" if profile.status == ProfileStatus.FOUND else "❌"
            print(f"  {status_emoji} {profile.platform}: {profile.status.value}")


async def benchmark_performance():
    """Benchmark profiler performance"""
    import time
    
    print("\n" + "=" * 70)
    print("⚡ PERFORMANCE BENCHMARK")
    print("=" * 70 + "\n")
    
    username = "test_user"
    
    async with SocialProfiler() as profiler:
        start_time = time.time()
        profiles = await profiler.discover_profiles(username)
        end_time = time.time()
        
        elapsed = end_time - start_time
        platforms_checked = len(profiles)
        avg_time_per_platform = elapsed / platforms_checked if platforms_checked > 0 else 0
        
        print(f"⏱️  Performance Metrics:")
        print(f"  • Total Time: {elapsed:.2f}s")
        print(f"  • Platforms Checked: {platforms_checked}")
        print(f"  • Avg Time/Platform: {avg_time_per_platform:.3f}s")
        print(f"  • Parallel Execution: YES (asyncio.gather)")


if __name__ == "__main__":
    print("\n🚀 Starting SocialProfiler Tests\n")
    
    try:
        # Run main test
        asyncio.run(test_social_profiler())
        
        # Run additional tests
        asyncio.run(test_platform_filtering())
        asyncio.run(benchmark_performance())
        
        print("\n🎉 All tests passed!\n")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
