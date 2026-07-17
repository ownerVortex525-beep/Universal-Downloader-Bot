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
    """Get download options based on platform.
    
    URL is stored in user_data, callback data only contains short action keys.
    """
    keyboard = []

    if platform == "youtube":
        keyboard = [
            [InlineKeyboardButton("📹 Best Quality", callback_data="dl_video_best")],
            [InlineKeyboardButton("📹 1080p", callback_data="dl_video_1080")],
            [InlineKeyboardButton("📹 720p", callback_data="dl_video_720")],
            [InlineKeyboardButton("📹 480p", callback_data="dl_video_480")],
            [InlineKeyboardButton("🎵 Audio (MP3)", callback_data="dl_audio_best")],
            [InlineKeyboardButton("🖼️ Thumbnail", callback_data="dl_thumbnail_best")]
        ]
    elif platform == "instagram":
        keyboard = [
            [InlineKeyboardButton("📹 Video", callback_data="dl_video_best")],
            [InlineKeyboardButton("🖼️ Image", callback_data="dl_image_best")],
            [InlineKeyboardButton("📂 All Content", callback_data="dl_all_best")]
        ]
    elif platform == "tiktok":
        keyboard = [
            [InlineKeyboardButton("📹 No Watermark", callback_data="dl_video_nwm")],
            [InlineKeyboardButton("📹 Original", callback_data="dl_video_orig")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("📥 Download", callback_data="dl_any_best")]
        ]

    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")])
    return InlineKeyboardMarkup(keyboard)
