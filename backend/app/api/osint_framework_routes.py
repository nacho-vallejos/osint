"""
OSINT Framework API Routes
Serves the categorized tool hierarchy from the imported framework data
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional

router = APIRouter()

# Sample data structure - In production, this would come from a database
# This represents the OSINT Framework tree structure
FRAMEWORK_DATA = {
    "categories": [
        {
            "id": "username",
            "name": "Username",
            "description": "Search for information about a specific username",
            "parent_id": None,
            "children": [
                {
                    "id": "username-social",
                    "name": "Social Networks",
                    "description": "Find username across social media platforms",
                    "parent_id": "username",
                    "children": [],
                    "tools": [
                        {
                            "id": "username-collector-internal",
                            "name": "Platform Username Search",
                            "description": "Search username across Twitter, Instagram, GitHub, Reddit, TikTok, and LinkedIn",
                            "url": None,
                            "is_internal": True,
                            "category_path": ["username", "username-social"]
                        },
                        {
                            "id": "knowem",
                            "name": "KnowEm",
                            "description": "Check username availability across 500+ social networks",
                            "url": "https://knowem.com/",
                            "is_internal": False,
                            "category_path": ["username", "username-social"]
                        },
                        {
                            "id": "namechk",
                            "name": "NameChk",
                            "description": "Username search across multiple platforms",
                            "url": "https://namechk.com/",
                            "is_internal": False,
                            "category_path": ["username", "username-social"]
                        }
                    ]
                },
                {
                    "id": "username-gaming",
                    "name": "Gaming",
                    "description": "Search gaming profiles and accounts",
                    "parent_id": "username",
                    "children": [],
                    "tools": [
                        {
                            "id": "steamid",
                            "name": "SteamID",
                            "description": "Find Steam profiles and gaming history",
                            "url": "https://steamid.io/",
                            "is_internal": False,
                            "category_path": ["username", "username-gaming"]
                        }
                    ]
                }
            ],
            "tools": []
        },
        {
            "id": "email",
            "name": "Email Address",
            "description": "Gather information about an email address",
            "parent_id": None,
            "children": [
                {
                    "id": "email-verification",
                    "name": "Verification",
                    "description": "Verify email address validity",
                    "parent_id": "email",
                    "children": [],
                    "tools": [
                        {
                            "id": "hunter",
                            "name": "Hunter.io",
                            "description": "Find and verify professional email addresses",
                            "url": "https://hunter.io/",
                            "is_internal": False,
                            "category_path": ["email", "email-verification"]
                        },
                        {
                            "id": "emailrep",
                            "name": "EmailRep",
                            "description": "Email reputation and security analysis",
                            "url": "https://emailrep.io/",
                            "is_internal": False,
                            "category_path": ["email", "email-verification"]
                        }
                    ]
                },
                {
                    "id": "email-breach",
                    "name": "Data Breaches",
                    "description": "Check if email appears in breaches",
                    "parent_id": "email",
                    "children": [],
                    "tools": [
                        {
                            "id": "haveibeenpwned-internal",
                            "name": "Have I Been Pwned Checker",
                            "description": "Check email against known data breaches (internal collector)",
                            "url": None,
                            "is_internal": True,
                            "category_path": ["email", "email-breach"]
                        },
                        {
                            "id": "dehashed",
                            "name": "Dehashed",
                            "description": "Search leaked database records",
                            "url": "https://dehashed.com/",
                            "is_internal": False,
                            "category_path": ["email", "email-breach"]
                        }
                    ]
                }
            ],
            "tools": []
        },
        {
            "id": "domain",
            "name": "Domain Name",
            "description": "Research domain names and DNS records",
            "parent_id": None,
            "children": [
                {
                    "id": "domain-dns",
                    "name": "DNS Records",
                    "description": "Query DNS records and infrastructure",
                    "parent_id": "domain",
                    "children": [],
                    "tools": [
                        {
                            "id": "dns-collector-internal",
                            "name": "DNS Lookup",
                            "description": "Comprehensive DNS record lookup (A, AAAA, MX, NS, TXT, SOA, CNAME)",
                            "url": None,
                            "is_internal": True,
                            "category_path": ["domain", "domain-dns"]
                        },
                        {
                            "id": "mxtoolbox",
                            "name": "MXToolbox",
                            "description": "DNS, SMTP, and blacklist checking",
                            "url": "https://mxtoolbox.com/",
                            "is_internal": False,
                            "category_path": ["domain", "domain-dns"]
                        }
                    ]
                },
                {
                    "id": "domain-whois",
                    "name": "WHOIS Lookup",
                    "description": "Domain registration information",
                    "parent_id": "domain",
                    "children": [],
                    "tools": [
                        {
                            "id": "whois-internal",
                            "name": "WHOIS Checker",
                            "description": "Domain registration and ownership lookup",
                            "url": None,
                            "is_internal": True,
                            "category_path": ["domain", "domain-whois"]
                        },
                        {
                            "id": "who-is",
                            "name": "Who.is",
                            "description": "WHOIS lookup with historical data",
                            "url": "https://who.is/",
                            "is_internal": False,
                            "category_path": ["domain", "domain-whois"]
                        }
                    ]
                }
            ],
            "tools": []
        },
        {
            "id": "ip-address",
            "name": "IP Address",
            "description": "Investigate IP addresses and geolocation",
            "parent_id": None,
            "children": [
                {
                    "id": "ip-geolocation",
                    "name": "Geolocation",
                    "description": "Find geographic location of IP addresses",
                    "parent_id": "ip-address",
                    "children": [],
                    "tools": [
                        {
                            "id": "ipinfo",
                            "name": "IPInfo.io",
                            "description": "IP geolocation and ASN data",
                            "url": "https://ipinfo.io/",
                            "is_internal": False,
                            "category_path": ["ip-address", "ip-geolocation"]
                        }
                    ]
                },
                {
                    "id": "ip-reputation",
                    "name": "Reputation & Security",
                    "description": "Check IP reputation and threat intelligence",
                    "parent_id": "ip-address",
                    "children": [],
                    "tools": [
                        {
                            "id": "virustotal-internal",
                            "name": "VirusTotal Scanner",
                            "description": "Check IP/domain against 70+ antivirus engines",
                            "url": None,
                            "is_internal": True,
                            "category_path": ["ip-address", "ip-reputation"]
                        },
                        {
                            "id": "shodan-internal",
                            "name": "Shodan Search",
                            "description": "Search for internet-connected devices and services",
                            "url": None,
                            "is_internal": True,
                            "category_path": ["ip-address", "ip-reputation"]
                        },
                        {
                            "id": "abuseipdb",
                            "name": "AbuseIPDB",
                            "description": "IP address abuse reports database",
                            "url": "https://www.abuseipdb.com/",
                            "is_internal": False,
                            "category_path": ["ip-address", "ip-reputation"]
                        }
                    ]
                }
            ],
            "tools": []
        },
        {
            "id": "phone",
            "name": "Phone Number",
            "description": "Look up phone number information",
            "parent_id": None,
            "children": [
                {
                    "id": "phone-lookup",
                    "name": "Reverse Lookup",
                    "description": "Find owner and carrier information",
                    "parent_id": "phone",
                    "children": [],
                    "tools": [
                        {
                            "id": "truecaller",
                            "name": "Truecaller",
                            "description": "Phone number lookup and spam identification",
                            "url": "https://www.truecaller.com/",
                            "is_internal": False,
                            "category_path": ["phone", "phone-lookup"]
                        }
                    ]
                }
            ],
            "tools": []
        },
        {
            "id": "metadata",
            "name": "File Metadata",
            "description": "Extract metadata from files and images",
            "parent_id": None,
            "children": [
                {
                    "id": "metadata-images",
                    "name": "Image Metadata",
                    "description": "Extract EXIF and GPS data from images",
                    "parent_id": "metadata",
                    "children": [],
                    "tools": [
                        {
                            "id": "metadata-extractor-internal",
                            "name": "Metadata Extractor",
                            "description": "Extract GPS, EXIF from images and metadata from PDF/DOCX",
                            "url": None,
                            "is_internal": True,
                            "category_path": ["metadata", "metadata-images"]
                        },
                        {
                            "id": "exiftool-online",
                            "name": "ExifTool Online",
                            "description": "Online EXIF data viewer",
                            "url": "https://exifdata.com/",
                            "is_internal": False,
                            "category_path": ["metadata", "metadata-images"]
                        }
                    ]
                }
            ],
            "tools": []
        },
        {
            "id": "social-media",
            "name": "Social Media",
            "description": "Analyze social media profiles and content",
            "parent_id": None,
            "children": [
                {
                    "id": "social-twitter",
                    "name": "Twitter/X",
                    "description": "Twitter/X OSINT tools",
                    "parent_id": "social-media",
                    "children": [],
                    "tools": [
                        {
                            "id": "tweetdeck",
                            "name": "TweetDeck",
                            "description": "Advanced Twitter monitoring",
                            "url": "https://tweetdeck.twitter.com/",
                            "is_internal": False,
                            "category_path": ["social-media", "social-twitter"]
                        }
                    ]
                }
            ],
            "tools": []
        }
    ]
}


@router.get("/categories/tree")
async def get_categories_tree():
    """
    Get the complete OSINT Framework category tree with tools
    
    Returns a hierarchical structure of categories and their associated tools.
    Internal tools (is_internal: true) should be executed via the platform.
    External tools should open in a new tab.
    """
    try:
        return {
            "success": True,
            "data": FRAMEWORK_DATA["categories"],
            "message": "OSINT Framework categories retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories/flat")
async def get_categories_flat():
    """
    Get a flat list of all categories (useful for search/filtering)
    """
    try:
        def flatten_categories(categories: List[Dict], result: List[Dict] = None) -> List[Dict]:
            if result is None:
                result = []
            
            for cat in categories:
                cat_info = {
                    "id": cat["id"],
                    "name": cat["name"],
                    "description": cat.get("description"),
                    "parent_id": cat.get("parent_id"),
                    "tool_count": len(cat.get("tools", []))
                }
                result.append(cat_info)
                
                if cat.get("children"):
                    flatten_categories(cat["children"], result)
            
            return result
        
        flat_list = flatten_categories(FRAMEWORK_DATA["categories"])
        
        return {
            "success": True,
            "data": flat_list,
            "total": len(flat_list)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools")
async def get_all_tools():
    """
    Get a flat list of all tools across all categories
    """
    try:
        def extract_tools(categories: List[Dict], result: List[Dict] = None) -> List[Dict]:
            if result is None:
                result = []
            
            for cat in categories:
                result.extend(cat.get("tools", []))
                
                if cat.get("children"):
                    extract_tools(cat["children"], result)
            
            return result
        
        all_tools = extract_tools(FRAMEWORK_DATA["categories"])
        
        internal_count = sum(1 for tool in all_tools if tool.get("is_internal"))
        external_count = len(all_tools) - internal_count
        
        return {
            "success": True,
            "data": all_tools,
            "stats": {
                "total": len(all_tools),
                "internal": internal_count,
                "external": external_count
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_tools(q: str):
    """
    Search for tools and categories by keyword
    """
    try:
        query = q.lower()
        results = {
            "categories": [],
            "tools": []
        }
        
        def search_recursive(categories: List[Dict]):
            for cat in categories:
                # Search category
                if query in cat["name"].lower() or (cat.get("description") and query in cat["description"].lower()):
                    results["categories"].append({
                        "id": cat["id"],
                        "name": cat["name"],
                        "description": cat.get("description"),
                        "type": "category"
                    })
                
                # Search tools
                for tool in cat.get("tools", []):
                    if (query in tool["name"].lower() or 
                        (tool.get("description") and query in tool["description"].lower())):
                        results["tools"].append(tool)
                
                # Recurse into children
                if cat.get("children"):
                    search_recursive(cat["children"])
        
        search_recursive(FRAMEWORK_DATA["categories"])
        
        return {
            "success": True,
            "query": q,
            "results": results,
            "total": len(results["categories"]) + len(results["tools"])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
