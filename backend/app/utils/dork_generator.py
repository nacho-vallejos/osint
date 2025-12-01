"""
Passive Dorking - Advanced Search Query Generator
Generates pre-optimized search URLs for external intelligence pivots.
"""

from typing import Literal, TypedDict
from urllib.parse import quote


class DorkLink(TypedDict):
    """Structure for a dork search link."""
    platform: str
    url: str
    description: str
    icon: str


def generate_dorks(
    target: str,
    dork_type: Literal['person', 'domain']
) -> list[DorkLink]:
    """
    Generate Google dork search URLs for passive intelligence gathering.
    
    Args:
        target: The search target (username, email, or domain)
        dork_type: Type of target - 'person' for individuals, 'domain' for infrastructure
        
    Returns:
        List of dork links with platform, URL, description, and icon
        
    Examples:
        >>> dorks = generate_dorks("johndoe", "person")
        >>> dorks = generate_dorks("example.com", "domain")
    """
    
    # Sanitize target for URL encoding
    safe_target = quote(target)
    quoted_target = quote(f'"{target}"')
    
    dorks: list[DorkLink] = []
    
    if dork_type == 'person':
        # Person-focused dorks (username or real name)
        dorks = [
            {
                'platform': 'LinkedIn Profiles',
                'url': f'https://www.google.com/search?q=site:linkedin.com/in/+{quoted_target}',
                'description': 'Search for professional profiles and career history',
                'icon': '💼'
            },
            {
                'platform': 'Pastebin Leaks',
                'url': f'https://www.google.com/search?q=site:pastebin.com+{quoted_target}',
                'description': 'Find text leaks, credentials, or mentions in pastes',
                'icon': '📋'
            },
            {
                'platform': 'Trello Boards',
                'url': f'https://www.google.com/search?q=site:trello.com+{quoted_target}',
                'description': 'Discover public project boards and task management',
                'icon': '📊'
            },
            {
                'platform': 'Document Files',
                'url': f'https://www.google.com/search?q=filetype:pdf+OR+filetype:docx+{quoted_target}',
                'description': 'Find PDF and DOCX documents containing the name',
                'icon': '📄'
            },
            {
                'platform': 'GitHub Code',
                'url': f'https://www.google.com/search?q=site:github.com+{quoted_target}',
                'description': 'Search source code, commits, and repositories',
                'icon': '💻'
            },
            {
                'platform': 'Stack Overflow',
                'url': f'https://www.google.com/search?q=site:stackoverflow.com+{quoted_target}',
                'description': 'Find technical questions and answers',
                'icon': '💬'
            },
            {
                'platform': 'Email Mentions',
                'url': f'https://www.google.com/search?q={safe_target}+%40+OR+email+OR+contact',
                'description': 'Search for email addresses and contact information',
                'icon': '📧'
            },
            {
                'platform': 'Social Media (General)',
                'url': f'https://www.google.com/search?q={quoted_target}+site:twitter.com+OR+site:facebook.com+OR+site:instagram.com',
                'description': 'Search across major social platforms',
                'icon': '👥'
            }
        ]
        
    elif dork_type == 'domain':
        # Domain-focused dorks (infrastructure reconnaissance)
        dorks = [
            {
                'platform': 'Configuration Files',
                'url': f'https://www.google.com/search?q=site:{safe_target}+ext:xml+OR+ext:conf+OR+ext:cnf+OR+ext:reg',
                'description': 'Find exposed configuration and registry files',
                'icon': '⚙️'
            },
            {
                'platform': 'Login Pages',
                'url': f'https://www.google.com/search?q=site:{safe_target}+inurl:login+OR+inurl:admin+OR+inurl:dashboard',
                'description': 'Discover administrative portals and login endpoints',
                'icon': '🔐'
            },
            {
                'platform': 'AWS S3 Buckets',
                'url': f'https://www.google.com/search?q=site:s3.amazonaws.com+{quoted_target}',
                'description': 'Search for open S3 buckets containing domain name',
                'icon': '☁️'
            },
            {
                'platform': 'Database Files',
                'url': f'https://www.google.com/search?q=site:{safe_target}+ext:sql+OR+ext:db+OR+ext:mdb',
                'description': 'Find exposed database files and SQL dumps',
                'icon': '🗄️'
            },
            {
                'platform': 'Backup Files',
                'url': f'https://www.google.com/search?q=site:{safe_target}+ext:bak+OR+ext:backup+OR+ext:old',
                'description': 'Locate backup files and legacy resources',
                'icon': '💾'
            },
            {
                'platform': 'Log Files',
                'url': f'https://www.google.com/search?q=site:{safe_target}+ext:log+OR+intext:"error"+OR+intext:"warning"',
                'description': 'Search for log files with potential error information',
                'icon': '📝'
            },
            {
                'platform': 'Directory Listings',
                'url': f'https://www.google.com/search?q=site:{safe_target}+intitle:"index+of"',
                'description': 'Find open directory listings and file browsers',
                'icon': '📁'
            },
            {
                'platform': 'Subdomain Enumeration',
                'url': f'https://www.google.com/search?q=site:*.{safe_target}+-site:www.{safe_target}',
                'description': 'Discover subdomains indexed by Google',
                'icon': '🌐'
            },
            {
                'platform': 'API Documentation',
                'url': f'https://www.google.com/search?q=site:{safe_target}+inurl:api+OR+inurl:swagger+OR+inurl:docs',
                'description': 'Find API endpoints and documentation pages',
                'icon': '🔌'
            },
            {
                'platform': 'Git Repositories',
                'url': f'https://www.google.com/search?q=site:{safe_target}+inurl:.git+OR+filetype:git',
                'description': 'Search for exposed .git folders and repositories',
                'icon': '🔍'
            }
        ]
    
    return dorks


def generate_dork_for_email(email: str) -> list[DorkLink]:
    """
    Generate person-focused dorks specifically for email addresses.
    Extracts username from email and searches for both.
    
    Args:
        email: Email address to search
        
    Returns:
        List of dork links with combined email and username searches
    """
    
    # Extract username from email
    username = email.split('@')[0] if '@' in email else email
    
    # Generate standard person dorks
    email_dorks = generate_dorks(email, 'person')
    username_dorks = generate_dorks(username, 'person')
    
    # Add email-specific dorks
    safe_email = quote(email)
    quoted_email = quote(f'"{email}"')
    
    email_specific = [
        {
            'platform': 'Data Breach Search',
            'url': f'https://www.google.com/search?q={quoted_email}+leak+OR+breach+OR+database',
            'description': 'Search for data breaches mentioning this email',
            'icon': '💀'
        },
        {
            'platform': 'PGP Key Servers',
            'url': f'https://www.google.com/search?q=site:keys.openpgp.org+OR+site:pgp.mit.edu+{safe_email}',
            'description': 'Find PGP public keys associated with email',
            'icon': '🔑'
        }
    ]
    
    # Combine and deduplicate
    all_dorks = email_dorks + email_specific
    
    return all_dorks


# Example usage and testing
if __name__ == '__main__':
    print("=== Person Dorks (Username) ===")
    person_dorks = generate_dorks("octocat", "person")
    for dork in person_dorks:
        print(f"\n{dork['icon']} {dork['platform']}")
        print(f"   {dork['description']}")
        print(f"   {dork['url']}")
    
    print("\n\n=== Domain Dorks ===")
    domain_dorks = generate_dorks("example.com", "domain")
    for dork in domain_dorks:
        print(f"\n{dork['icon']} {dork['platform']}")
        print(f"   {dork['description']}")
        print(f"   {dork['url']}")
    
    print("\n\n=== Email Dorks ===")
    email_dorks = generate_dork_for_email("test@example.com")
    for dork in email_dorks[:3]:  # Show first 3
        print(f"\n{dork['icon']} {dork['platform']}")
        print(f"   {dork['description']}")
        print(f"   {dork['url']}")
