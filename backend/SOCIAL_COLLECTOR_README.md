# Social Media Username Collector

## Overview

The `SocialCollector` is a high-performance OSINT module that searches for usernames across 15 popular social media platforms simultaneously using asynchronous HTTP requests.

## Features

- ✅ **Asynchronous & Fast**: Uses `aiohttp` and `asyncio.gather` for parallel requests
- 🌐 **15 Platforms**: GitHub, Twitter, Instagram, Reddit, Twitch, LinkedIn, Facebook, TikTok, YouTube, Medium, Pinterest, Snapchat, Telegram, Discord, Steam
- 🛡️ **Anti-Blocking**: Generic User-Agent to avoid basic bot detection
- 📊 **Detailed Results**: Separates found/not found profiles with statistics
- ⚡ **10s Timeout**: Per-request timeout to avoid hanging on slow platforms

## Supported Platforms

| Platform | URL Pattern | Detection Method |
|----------|-------------|------------------|
| GitHub | `github.com/{username}` | HTTP 200 = Found |
| Twitter | `twitter.com/{username}` | HTTP 200 = Found |
| Instagram | `instagram.com/{username}` | HTTP 200 = Found |
| Reddit | `reddit.com/user/{username}` | HTTP 200 = Found |
| Twitch | `twitch.tv/{username}` | HTTP 200 = Found |
| LinkedIn | `linkedin.com/in/{username}` | HTTP 200 = Found |
| Facebook | `facebook.com/{username}` | HTTP 200 = Found |
| TikTok | `tiktok.com/@{username}` | HTTP 200 = Found |
| YouTube | `youtube.com/@{username}` | HTTP 200 = Found |
| Medium | `medium.com/@{username}` | HTTP 200 = Found |
| Pinterest | `pinterest.com/{username}` | HTTP 200 = Found |
| Snapchat | `snapchat.com/add/{username}` | HTTP 200 = Found |
| Telegram | `t.me/{username}` | HTTP 200 = Found |
| Discord | `discord.com/users/{username}` | HTTP 200 = Found |
| Steam | `steamcommunity.com/id/{username}` | HTTP 200 = Found |

## Usage

### API Endpoint

```bash
POST /api/v1/collectors/execute
Content-Type: application/json

{
  "collector_name": "SocialCollector",
  "target": "username_to_search"
}
```

### Python Example

```python
import asyncio
from app.collectors.social_collector import SocialCollector

async def search_username():
    collector = SocialCollector()
    result = await collector.collect("john_doe")
    
    print(f"Found on {len(result.data['found_profiles'])} platforms")
    for profile in result.data['found_profiles']:
        print(f"  • {profile['platform']}: {profile['url']}")

asyncio.run(search_username())
```

### cURL Example

```bash
curl -X POST http://localhost:8000/api/v1/collectors/execute \
  -H "Content-Type: application/json" \
  -d '{
    "collector_name": "SocialCollector",
    "target": "github"
  }'
```

## Response Format

```json
{
  "collector": "social",
  "target": "github",
  "entity_type": "person",
  "data": {
    "username": "github",
    "found_profiles": [
      {
        "platform": "GitHub",
        "url": "https://github.com/github",
        "found": true,
        "status_code": 200
      },
      {
        "platform": "Twitter",
        "url": "https://twitter.com/github",
        "found": true,
        "status_code": 200
      }
    ],
    "checked_but_not_found": [
      {
        "platform": "Snapchat",
        "url": "https://snapchat.com/add/github",
        "found": false,
        "status_code": 404
      }
    ],
    "statistics": {
      "total_checked": 15,
      "found": 8,
      "not_found": 7,
      "errors": 0
    }
  },
  "success": true,
  "metadata": {
    "platforms_checked": ["GitHub", "Twitter", "Instagram", ...]
  }
}
```

## Performance

- **Average execution time**: 2-5 seconds for 15 platforms
- **Concurrent requests**: All platforms checked simultaneously
- **Timeout per platform**: 10 seconds
- **Memory footprint**: ~5-10 MB during execution

## Testing

Run the included test script:

```bash
cd backend
python test_social_collector.py
```

Expected output:
```
🔍 Searching for username: github
📊 Checking 15 platforms...

============================================================
✅ Search completed for: github
============================================================

📈 Statistics:
  • Total platforms checked: 15
  • Profiles found: 8
  • Not found: 7
  • Errors: 0
```

## Limitations & Future Improvements

### Current Limitations (v1)
- **Simple Detection**: Only uses HTTP status codes (200 = found, 404 = not found)
- **False Positives**: Some platforms return 200 even for non-existent profiles
- **No Rate Limiting**: Could be blocked by platforms with aggressive rate limiting
- **No Authentication**: Cannot check private profiles or authenticated content

### Planned Improvements (v2)
1. **Content-Based Detection**: Parse HTML to verify actual profile existence
2. **Rate Limiting**: Implement delays and respect `Retry-After` headers
3. **Proxy Support**: Rotate IPs to avoid blocking
4. **Additional Platforms**: Add 20+ more platforms (Mastodon, Keybase, etc.)
5. **Profile Metadata**: Extract follower counts, bio, profile pictures when available
6. **Caching**: Cache results for 24h to avoid redundant checks

## Error Handling

The collector handles various error scenarios:

- **Timeout**: 10s timeout per request (returns `found: false`)
- **Connection Errors**: Network issues (returns `found: false` with error message)
- **HTTP Errors**: 5xx errors treated as "not found" (could be temporary)
- **Exceptions**: Caught and logged without crashing the entire search

## Security & Privacy

- **No Data Storage**: Results are not stored by default
- **Generic User-Agent**: Mimics a real browser to avoid detection
- **HTTPS Only**: All platforms use secure connections
- **No Credentials**: Does not require or handle user credentials

## Integration with OSINT Graph Viewer

Results can be visualized in the frontend Graph Viewer:

```javascript
// Example: Convert SocialCollector results to graph nodes
const socialData = await fetch('/api/v1/collectors/execute', {
  method: 'POST',
  body: JSON.stringify({
    collector_name: 'SocialCollector',
    target: 'username'
  })
});

const nodes = socialData.data.found_profiles.map(profile => ({
  id: profile.platform,
  type: 'custom',
  data: {
    label: profile.platform,
    type: 'person',
    info: profile.url
  }
}));
```

## Contributing

To add a new platform:

1. Add URL pattern to `PLATFORMS` dict in `social_collector.py`
2. Test with known usernames
3. Update this documentation
4. Submit PR with test results

Example:
```python
PLATFORMS = {
    # ... existing platforms
    "Mastodon": "https://mastodon.social/@{}",
    "Keybase": "https://keybase.io/{}",
}
```

## License

Part of the OSINT Platform - Same license as parent project.

## Support

For issues or questions:
- Check the test script output for debugging
- Review API logs for HTTP errors
- Verify username format (no special characters)
- Test with known usernames first (e.g., "github", "twitter")
