import os
import tempfile
import subprocess
import yt_dlp
import instaloader
import requests
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

async def download_youtube(url: str, format_type: str = 'video', quality: str = 'best') -> Tuple[Optional[str], str]:
    """Download YouTube content"""
    try:
        temp_dir = tempfile.mkdtemp()
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
                'extract_flat': False
            }
        elif format_type == 'thumbnail':
            ydl_opts = {
                'skip_download': True,
                'writethumbnail': True,
                'outtmpl': output_template,
                'quiet': True,
                'no_warnings': True
            }
        else:  # video
            quality_map = {
                'best': 'best[ext=mp4]',
                '1080': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]',
                '720': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]',
                '480': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]',
            }
            ydl_opts = {
                'format': quality_map.get(quality, quality_map['best']),
                'merge_output_format': 'mp4',
                'outtmpl': output_template,
                'quiet': True,
                'no_warnings': True
            }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_files = [f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))]
            
            if downloaded_files:
                file_path = os.path.join(temp_dir, downloaded_files[0])
                return file_path, info.get('title', 'Unknown')
            return None, "No file downloaded"
            
    except Exception as e:
        logger.error(f"YouTube download error: {e}")
        return None, str(e)

async def download_instagram(url: str, content_type: str = 'all') -> Tuple[Optional[str], str]:
    """Download Instagram content"""
    try:
        temp_dir = tempfile.mkdtemp()
        loader = instaloader.Instaloader(
            download_pictures=True,
            download_videos=True,
            compress_json=False,
            save_metadata=False,
            post_metadata_txt_pattern=''
        )
        
        shortcode = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
        post = instaloader.Post.from_shortcode(loader.context, shortcode)
        loader.download_post(post, target=temp_dir)
        
        downloaded_files = [f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))]
        media_files = [f for f in downloaded_files if not f.endswith('.json')]
        
        if media_files:
            file_path = os.path.join(temp_dir, media_files[0])
            return file_path, post.title or 'Instagram Post'
        return None, "No media found"
            
    except Exception as e:
        logger.error(f"Instagram download error: {e}")
        return None, str(e)

async def download_tiktok(url: str, no_watermark: bool = True) -> Tuple[Optional[str], str]:
    """Download TikTok video"""
    try:
        temp_dir = tempfile.mkdtemp()
        output_template = f"{temp_dir}/%(title)s.%(ext)s"
        
        ydl_opts = {
            'format': 'best',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_files = [f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))]
            
            if downloaded_files:
                file_path = os.path.join(temp_dir, downloaded_files[0])
                return file_path, info.get('title', 'TikTok Video')
            return None, "No video downloaded"
            
    except Exception as e:
        logger.error(f"TikTok download error: {e}")
        return None, str(e)

async def download_generic(url: str) -> Tuple[Optional[str], str]:
    """Download any URL content"""
    try:
        response = requests.get(url, timeout=30, stream=True)
        if response.status_code == 200:
            temp_dir = tempfile.mkdtemp()
            filename = url.split('/')[-1] or 'download'
            file_path = os.path.join(temp_dir, filename)
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return file_path, filename
        return None, f"HTTP {response.status_code}"
            
    except Exception as e:
        logger.error(f"Generic download error: {e}")
        return None, str(e)