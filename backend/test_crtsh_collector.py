"""
Test script for Certificate Transparency Collector
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from app.collectors.crtsh_collector import CrtshCollector


async def test_crtsh_collector():
    """Test the CrtshCollector with a well-known domain"""
    print("="*80)
    print("Testing Certificate Transparency Collector (crt.sh)")
    print("="*80)
    
    collector = CrtshCollector()
    
    # Test with a known domain that should have subdomains
    test_domains = [
        "google.com",
        "github.com",
        "example.com"
    ]
    
    for domain in test_domains:
        print(f"\n🔍 Searching subdomains for: {domain}")
        print("-" * 60)
        
        result = await collector.collect(domain)
        
        if result.success:
            subdomains = result.data.get("subdomains", [])
            total = result.data.get("total_count", 0)
            
            print(f"✅ Success!")
            print(f"📊 Total unique subdomains found: {total}")
            
            if total > 0:
                print(f"\n📋 First 10 subdomains:")
                for subdomain in subdomains[:10]:
                    print(f"  • {subdomain}")
                
                if total > 10:
                    print(f"  ... and {total - 10} more")
            
            # Metadata
            if result.metadata:
                print(f"\n📈 Metadata:")
                print(f"  • Source: {result.metadata.get('source')}")
                print(f"  • Certificates found: {result.metadata.get('certificates_found')}")
                print(f"  • Unique subdomains: {result.metadata.get('unique_subdomains')}")
        else:
            print(f"❌ Error: {result.error}")
        
        print()


if __name__ == "__main__":
    asyncio.run(test_crtsh_collector())
