from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_menu():
    """Main menu keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("📹 YouTube", callback_data="platform_youtube"),
            InlineKeyboardButton("📸 Instagram", callback_data="platform_instagram"),
            InlineKeyboardButton("🎵 TikTok", callback_data="platform_tiktok")
        ],
        [
            InlineKeyboardButton("🐦 Twitter/X", callback_data="platform_twitter"),
            InlineKeyboardButton("📘 Facebook", callback_data="platform_facebook"),
            InlineKeyboardButton("📌 Pinterest", callback_data="platform_pinterest")
        ],
        [
            InlineKeyboardButton("🎥 Reddit", callback_data="platform_reddit"),
            InlineKeyboardButton("🔗 Any URL", callback_data="platform_any"),
            InlineKeyboardButton("📄 Extract Text", callback_data="platform_text")
        ],
        [
            InlineKeyboardButton("📊 My Stats", callback_data="stats"),
            InlineKeyboardButton("❓ Help", callback_data="help"),
            InlineKeyboardButton("📢 Channel", url="https://t.me/yourchannel")
        ],
        [
            InlineKeyboardButton("⚠️ Report", callback_data="report"),
            InlineKeyboardButton("🎁 Donate", callback_data="donate")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_download_options(url: str, platform: str):
    """Get download options based on platform"""
    keyboard = []
    
    if platform == "youtube":
        keyboard = [
            [InlineKeyboardButton("📹 Best Quality", callback_data=f"dl_{platform}_video_best_{url}")],
            [InlineKeyboardButton("📹 1080p", callback_data=f"dl_{platform}_video_1080_{url}")],
            [InlineKeyboardButton("📹 720p", callback_data=f"dl_{platform}_video_720_{url}")],
            [InlineKeyboardButton("📹 480p", callback_data=f"dl_{platform}_video_480_{url}")],
            [InlineKeyboardButton("🎵 Audio (MP3)", callback_data=f"dl_{platform}_audio_best_{url}")],
            [InlineKeyboardButton("🖼️ Thumbnail", callback_data=f"dl_{platform}_thumbnail_{url}")]
        ]
    elif platform == "instagram":
        keyboard = [
            [InlineKeyboardButton("📹 Video", callback_data=f"dl_{platform}_video_{url}")],
            [InlineKeyboardButton("🖼️ Image", callback_data=f"dl_{platform}_image_{url}")],
            [InlineKeyboardButton("📂 All Content", callback_data=f"dl_{platform}_all_{url}")]
        ]
    elif platform == "tiktok":
        keyboard = [
            [InlineKeyboardButton("📹 No Watermark", callback_data=f"dl_{platform}_video_nwm_{url}")],
            [InlineKeyboardButton("📹 Original", callback_data=f"dl_{platform}_video_orig_{url}")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("📥 Download", callback_data=f"dl_{platform}_any_{url}")]
        ]
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")])
    return InlineKeyboardMarkup(keyboard)