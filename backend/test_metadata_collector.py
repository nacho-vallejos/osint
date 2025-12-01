"""
Test script for MetadataCollector - Document Metadata Extraction
"""

import asyncio
import sys
import os
import json

# Add backend to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.collectors.metadata_collector import MetadataCollector


async def test_metadata_collector():
    """Test the MetadataCollector with various domains"""
    
    collector = MetadataCollector()
    
    # Test domains (use domains likely to have public documents)
    test_domains = [
        "ieee.org",  # Academic papers
        "python.org",  # Documentation PDFs
        # "example.com",  # Unlikely to have documents
    ]
    
    for domain in test_domains:
        print(f"\n{'='*70}")
        print(f"Testing MetadataCollector for: {domain}")
        print(f"{'='*70}")
        
        result = await collector.collect(domain)
        
        print(f"\n✓ Success: {result.success}")
        
        if result.error:
            print(f"✗ Error: {result.error}")
            continue
        
        if result.data:
            print(f"\n📊 Summary:")
            print(f"  Domain: {result.data.get('domain')}")
            print(f"  Documents Found: {result.data.get('documents_found')}")
            
            # Show potential users
            potential_users = result.data.get('potential_users', [])
            if potential_users:
                print(f"\n👥 Potential Users Identified: {len(potential_users)}")
                for user in potential_users[:10]:  # Show first 10
                    if user:
                        print(f"    - {user}")
            
            # Show document details
            documents = result.data.get('documents', [])
            if documents:
                print(f"\n📄 Documents with Metadata:")
                for idx, doc in enumerate(documents, 1):
                    print(f"\n  Document {idx}:")
                    print(f"    URL: {doc.get('url', 'N/A')}")
                    print(f"    Type: {doc.get('filetype', 'N/A')}")
                    print(f"    Size: {doc.get('size_bytes', 0) / 1024:.1f} KB")
                    
                    if doc.get('author'):
                        print(f"    Author: {doc['author']}")
                    if doc.get('creator'):
                        print(f"    Creator: {doc['creator']}")
                    if doc.get('producer'):
                        print(f"    Producer: {doc['producer']}")
                    if doc.get('creation_date'):
                        print(f"    Created: {doc['creation_date']}")
                    if doc.get('title'):
                        print(f"    Title: {doc['title']}")
                    if doc.get('error'):
                        print(f"    ⚠️  Error: {doc['error']}")
            
            # Show summary statistics
            summary = result.data.get('summary')
            if summary:
                print(f"\n📈 Statistics:")
                print(f"  Total Documents: {summary.get('total_documents')}")
                print(f"  Unique Authors: {summary.get('unique_authors')}")
                print(f"  File Types: {', '.join(summary.get('filetypes_found', []))}")
                
                software = summary.get('software_detected', [])
                if software:
                    print(f"\n💻 Software Detected:")
                    for sw in software[:5]:  # Show first 5
                        if sw:
                            print(f"    - {sw}")
        
        if result.metadata:
            print(f"\n🔍 Search Details:")
            print(f"  Query: {result.metadata.get('search_query')}")
            print(f"  Max Results: {result.metadata.get('max_results')}")


async def test_with_custom_domain():
    """Test with a custom domain provided via command line"""
    
    if len(sys.argv) > 1:
        custom_domain = sys.argv[1]
        print(f"\n{'='*70}")
        print(f"Custom Domain Test: {custom_domain}")
        print(f"{'='*70}")
        
        collector = MetadataCollector()
        result = await collector.collect(custom_domain)
        
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
║              MetadataCollector Test Suite                        ║
║  Forensic Document Metadata Extraction from Public Sources      ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Check if googlesearch-python is available
    try:
        from googlesearch import search
        print("✓ googlesearch-python is installed")
    except ImportError:
        print("✗ googlesearch-python not found!")
        print("  Install with: pip install googlesearch-python")
        sys.exit(1)
    
    # Run tests
    if len(sys.argv) > 1:
        asyncio.run(test_with_custom_domain())
    else:
        asyncio.run(test_metadata_collector())
    
    print("\n✓ Test completed")
