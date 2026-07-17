import os
import tempfile
import yt_dlp
import requests
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def _get_temp_dir():
    return tempfile.mkdtemp()

# ============ INSTAGRAM SESSION ============

_ig_client = None

def get_instagram_client():
    """Get or create Instagram client with login"""
    global _ig_client
    if _ig_client:
        return _ig_client

    ig_user = os.getenv('INSTAGRAM_USERNAME', '')
    ig_pass = os.getenv('INSTAGRAM_PASSWORD', '')

    if not ig_user or not ig_pass:
        return None

    try:
        from instagrapi import Client
        cl = Client()
        cl.login(ig_user, ig_pass)
        _ig_client = cl
        logger.info("Instagram login successful")
        return cl
    except Exception as e:
        logger.error(f"Instagram login failed: {e}")
        return None

# ============ DOWNLOADERS ============

async def download_youtube(url: str, format_type: str = 'video', quality: str = 'best') -> Tuple[Optional[str], str]:
    """Download YouTube content using yt-dlp"""
    try:
        temp_dir = _get_temp_dir()
        output_template = f"{temp_dir}/%(title)s.%(ext)s"

        if format_type == 'audio':
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': output_template,
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'socket_timeout': 30,
            }
        elif format_type == 'thumbnail':
            ydl_opts = {
                'skip_download': True,
                'writethumbnail': True,
                'outtmpl': output_template,
                'quiet': True,
                'no_warnings': True,
                'socket_timeout': 30,
            }
        else:
            quality_map = {
                'best': 'best[ext=mp4]/best',
                '1080': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]',
                '720': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]',
                '480': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]',
            }
            ydl_opts = {
                'format': quality_map.get(quality, quality_map['best']),
                'merge_output_format': 'mp4',
                'outtmpl': output_template,
                'quiet': True,
                'no_warnings': True,
                'socket_timeout': 30,
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_files = [f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))]

            if downloaded_files:
                file_path = os.path.join(temp_dir, downloaded_files[0])
                title = info.get('title', 'Unknown')
                return file_path, title
            return None, "No file downloaded"

    except Exception as e:
        logger.error(f"YouTube download error: {e}")
        return None, str(e)

async def download_instagram(url: str, content_type: str = 'all') -> Tuple[Optional[str], str]:
    """Download Instagram content using instagrapi (with login) or yt-dlp fallback"""
    cl = get_instagram_client()

    if cl:
        try:
            temp_dir = _get_temp_dir()
            media_pk = cl.media_pk_from_url(url)
            media = cl.media_info(media_pk)

            if media.media_type == 1:
                file_path = cl.photo_download(media_pk, folder=temp_dir)
                return str(file_path), media.caption_text or "Instagram Photo"

            elif media.media_type == 2:
                file_path = cl.video_download(media_pk, folder=temp_dir)
                return str(file_path), media.caption_text or "Instagram Video"

            elif media.media_type == 8:
                files = cl.album_download(media_pk, folder=temp_dir)
                if files:
                    file_path = files[0] if isinstance(files, list) else files
                    return str(file_path), media.caption_text or "Instagram Post"

            return None, "Unsupported Instagram content type"

        except Exception as e:
            logger.error(f"instagrapi download error: {e}")

    # Fallback to yt-dlp
    try:
        temp_dir = _get_temp_dir()
        output_template = f"{temp_dir}/%(title)s.%(ext)s"

        ydl_opts = {
            'format': 'best',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 30,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.instagram.com/',
            },
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_files = [f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))]

            if downloaded_files:
                file_path = os.path.join(temp_dir, downloaded_files[0])
                title = info.get('title', 'Instagram Post')
                return file_path, title
            return None, "No media found"

    except Exception as e:
        error_str = str(e).lower()
        if '401' in error_str or 'login' in error_str:
            return None, "Instagram login required. Admin must set INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD."
        return None, f"Instagram download failed: {str(e)[:100]}"

async def download_tiktok(url: str, no_watermark: bool = True) -> Tuple[Optional[str], str]:
    """Download TikTok video"""
    try:
        temp_dir = _get_temp_dir()
        output_template = f"{temp_dir}/%(title)s.%(ext)s"

        ydl_opts = {
            'format': 'best',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 30,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            },
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_files = [f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))]

            if downloaded_files:
                file_path = os.path.join(temp_dir, downloaded_files[0])
                title = info.get('title', 'TikTok Video')
                return file_path, title
            return None, "No video downloaded"

    except Exception as e:
        logger.error(f"TikTok download error: {e}")
        return None, str(e)

async def download_generic(url: str) -> Tuple[Optional[str], str]:
    """Download any URL content"""
    try:
        temp_dir = _get_temp_dir()
        output_template = f"{temp_dir}/%(title)s.%(ext)s"

        ydl_opts = {
            'format': 'best',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 30,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            },
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_files = [f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))]

            if downloaded_files:
                file_path = os.path.join(temp_dir, downloaded_files[0])
                title = info.get('title', os.path.basename(file_path))
                return file_path, title

    except Exception:
        pass

    try:
        response = requests.get(url, timeout=30, stream=True, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        if response.status_code == 200:
            temp_dir = _get_temp_dir()
            content_type = response.headers.get('content-type', '')
            content_disp = response.headers.get('content-disposition', '')

            if 'filename=' in content_disp:
                filename = content_disp.split('filename=')[-1].strip('"')
            elif '/' in url:
                filename = url.split('/')[-1].split('?')[0]
            else:
                filename = 'download'

            if '.' not in filename:
                if 'video' in content_type:
                    filename += '.mp4'
                elif 'image' in content_type:
                    filename += '.jpg'
                elif 'audio' in content_type:
                    filename += '.mp3'
                else:
                    filename += '.bin'

            file_path = os.path.join(temp_dir, filename)

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return file_path, filename
        return None, f"HTTP {response.status_code}"

    except Exception as e:
        logger.error(f"Generic download error: {e}")
        return None, str(e)
