import re
import validators
from datetime import datetime

def get_platform_from_url(url: str) -> str:
    """Detect platform from URL"""
    url_lower = url.lower()
    
    if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'youtube'
    elif 'instagram.com' in url_lower:
        return 'instagram'
    elif 'tiktok.com' in url_lower:
        return 'tiktok'
    elif 'twitter.com' in url_lower or 'x.com' in url_lower:
        return 'twitter'
    elif 'facebook.com' in url_lower or 'fb.watch' in url_lower:
        return 'facebook'
    elif 'pinterest.com' in url_lower or 'pin.it' in url_lower:
        return 'pinterest'
    elif 'reddit.com' in url_lower or 'redd.it' in url_lower:
        return 'reddit'
    else:
        return 'unknown'

def get_example_url(platform: str) -> str:
    """Get example URL for a platform"""
    examples = {
        'youtube': 'https://youtube.com/watch?v=abc123',
        'instagram': 'https://instagram.com/p/ABC123/',
        'tiktok': 'https://tiktok.com/@user/video/123456789',
        'twitter': 'https://twitter.com/user/status/123456789',
        'facebook': 'https://facebook.com/watch?v=123456789',
        'pinterest': 'https://pinterest.com/pin/123456789',
        'reddit': 'https://reddit.com/r/subreddit/comments/abc123/'
    }
    return examples.get(platform, 'https://example.com')

def get_user_info(update):
    """Extract user information from update"""
    user = update.effective_user
    return {
        'id': user.id,
        'username': user.username or 'N/A',
        'first_name': user.first_name or 'N/A',
        'last_name': user.last_name or 'N/A',
        'mention': f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
    }

def format_size(bytes_size: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"

def extract_video_id(url: str, platform: str) -> str:
    """Extract video ID from URL"""
    if platform == 'youtube':
        pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11})(?:[?&]|$)'
        match = re.search(pattern, url)
        return match.group(1) if match else None
    elif platform == 'instagram':
        pattern = r'\/p\/([A-Za-z0-9_-]+)'
        match = re.search(pattern, url)
        return match.group(1) if match else None
    return None