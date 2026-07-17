import os
import sys
import shutil
import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, Tuple

# Configure logging for Render
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import our modules
from config import BOT_TOKEN, CHANNEL_ID, ADMIN_IDS, DATABASE_URL
from database import SessionLocal, User, Download
from keyboards import get_main_menu, get_download_options
from downloader import (
    download_youtube, download_instagram,
    download_tiktok, download_generic
)
from utils import get_user_info, get_platform_from_url, get_example_url

# Telegram imports
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from telegram.constants import ParseMode

# ============ DATABASE FUNCTIONS ============

def save_user(user_id: int, username: str, first_name: str, last_name: str = ""):
    """Save or update user in database"""
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            user = User(
                telegram_id=user_id,
                username=username or "N/A",
                first_name=first_name or "N/A",
                last_name=last_name or ""
            )
            session.add(user)
        else:
            user.last_active = datetime.utcnow()
        session.commit()
        return user
    except Exception as e:
        logger.error(f"Database error: {e}")
        session.rollback()
        return None
    finally:
        session.close()

def save_download(user_id: int, url: str, platform: str, file_type: str, status: str):
    """Save download record"""
    session = SessionLocal()
    try:
        download = Download(
            user_id=user_id,
            url=url,
            platform=platform,
            file_type=file_type,
            status=status
        )
        session.add(download)

        # Update user download count
        user = session.query(User).filter_by(telegram_id=user_id).first()
        if user:
            user.download_count += 1
            user.last_active = datetime.utcnow()

        session.commit()
        return True
    except Exception as e:
        logger.error(f"Database error: {e}")
        session.rollback()
        return False
    finally:
        session.close()

# ============ CHANNEL LOGGING ============

_channel_warning_sent = False

async def log_to_channel(context: ContextTypes.DEFAULT_TYPE, user_info: Dict, action: str, details: str = ""):
    """Send user activity to destination channel"""
    global _channel_warning_sent
    if not CHANNEL_ID:
        return

    try:
        message = (
            f"<b>USER ACTIVITY LOG</b>\n\n"
            f"<b>User ID:</b> <code>{user_info['id']}</code>\n"
            f"<b>Username:</b> @{user_info['username']}\n"
            f"<b>Name:</b> {user_info['first_name']}\n"
            f"<b>Action:</b> {action}\n"
            f"<b>Details:</b> {details}\n"
            f"<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=message,
            parse_mode=ParseMode.HTML
        )
        _channel_warning_sent = False
    except Exception as e:
        if not _channel_warning_sent:
            logger.warning(f"Channel logging failed (check CHANNEL_ID and bot is in channel): {e}")
            _channel_warning_sent = True

# ============ COMMAND HANDLERS ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user_info = get_user_info(update)

    # Save user to database
    save_user(user_info['id'], user_info['username'], user_info['first_name'], user_info['last_name'])

    # Log to channel
    await log_to_channel(
        context,
        user_info,
        "NEW USER",
        f"User @{user_info['username']} started the bot"
    )

    welcome = (
        f"<b>UNIVERSAL DOWNLOADER BOT</b>\n\n"
        f"Hello <b>{user_info['first_name']}</b>!\n\n"
        f"<b>Download from ANY platform:</b>\n"
        f"YouTube | Instagram | TikTok\n"
        f"Twitter | Facebook | Pinterest\n"
        f"Reddit | Any URL | Text\n\n"
        f"<b>How to use:</b>\n"
        f"1. Send me a URL\n"
        f"2. Choose format\n"
        f"3. Download instantly!\n\n"
        f"<b>Features:</b>\n"
        f"No watermark downloads\n"
        f"Multiple quality options\n"
        f"Fast &amp; reliable\n\n"
        f"Send any link to get started!"
    )
    await update.message.reply_text(
        welcome,
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = (
        "<b>UNIVERSAL DOWNLOADER - HELP</b>\n\n"
        "<b>How to Use:</b>\n"
        "1. Send a URL from any supported platform\n"
        "2. Select your preferred format/quality\n"
        "3. Wait for download to complete\n\n"
        "<b>Supported Platforms:</b>\n"
        "YouTube - Video/Audio/Thumbnail\n"
        "Instagram - Video/Image/All content\n"
        "TikTok - Video (No watermark available)\n"
        "Twitter/X - Videos &amp; Media\n"
        "Facebook - Videos &amp; Images\n"
        "Pinterest - Images\n"
        "Reddit - Videos &amp; Media\n"
        "Any URL - Direct download\n\n"
        "<b>Commands:</b>\n"
        "/start - Show main menu\n"
        "/help - Show this help\n"
        "/stats - View your download statistics\n\n"
        "<b>Limits:</b>\n"
        "Max file: 50MB\n"
        "Rate limit: 10 downloads/minute\n"
        "Files auto-delete after sending\n\n"
        "<b>Tips:</b>\n"
        "For YouTube, choose lower quality for faster downloads\n"
        "TikTok downloads are watermark-free\n"
        "Use Any URL for direct file downloads"
    )
    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu()
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command"""
    user_info = get_user_info(update)

    session = SessionLocal()
    try:
        user = session.query(User).filter_by(telegram_id=user_info['id']).first()
        downloads = session.query(Download).filter_by(user_id=user_info['id']).count()

        stats = (
            "<b>YOUR STATISTICS</b>\n\n"
            f"User: {user_info['first_name']}\n"
            f"ID: <code>{user_info['id']}</code>\n"
            f"Total Downloads: {downloads}\n"
            f"Joined: {user.joined_date.strftime('%Y-%m-%d') if user else 'N/A'}\n"
            f"Last Active: {user.last_active.strftime('%Y-%m-%d %H:%M') if user else 'N/A'}\n\n"
            "More downloads = More features unlocked!"
        )
        await update.message.reply_text(
            stats,
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu()
        )
    except Exception as e:
        logger.error(f"Stats error: {e}")
        await update.message.reply_text("Error fetching stats")
    finally:
        session.close()

# ============ MESSAGE HANDLER ============

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle URL messages"""
    url = update.message.text.strip()
    user_info = get_user_info(update)

    # Validate URL
    if not (url.startswith('http://') or url.startswith('https://')):
        await update.message.reply_text(
            "<b>Invalid URL!</b>\n\n"
            "Please send a valid URL starting with http:// or https://\n\n"
            "Example: https://youtube.com/watch?v=abc123",
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu()
        )
        return

    # Detect platform
    platform = get_platform_from_url(url)

    if platform == 'unknown':
        keyboard = [
            [InlineKeyboardButton("📹 YouTube", callback_data="platform_youtube")],
            [InlineKeyboardButton("📸 Instagram", callback_data="platform_instagram")],
            [InlineKeyboardButton("🎵 TikTok", callback_data="platform_tiktok")],
            [InlineKeyboardButton("🐦 Twitter/X", callback_data="platform_twitter")],
            [InlineKeyboardButton("🔗 Any URL", callback_data="platform_any")],
            [InlineKeyboardButton("🔙 Back", callback_data="menu")]
        ]
        # Store URL in user_data for when they pick a platform
        context.user_data['pending_url'] = url
        await update.message.reply_text(
            "<b>Platform Not Detected</b>\n\n"
            "Please select the platform of your URL:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Store URL in user_data (avoids 64-byte callback data limit)
    context.user_data['current_url'] = url
    context.user_data['current_platform'] = platform

    # Log to channel
    await log_to_channel(
        context,
        user_info,
        "DOWNLOAD REQUEST",
        f"Platform: {platform.upper()}\nURL: {url[:100]}"
    )

    # Show download options
    await update.message.reply_text(
        f"<b>Platform Detected:</b> {platform.upper()}\n\n"
        f"<b>URL:</b> <code>{url[:100]}{'...' if len(url) > 100 else ''}</code>\n\n"
        f"<b>Select download option:</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=get_download_options(url, platform)
    )

# ============ CALLBACK HANDLER ============

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries"""
    query = update.callback_query
    await query.answer()

    data = query.data
    user_info = get_user_info(update)

    # ===== MENU NAVIGATION =====
    if data == "menu":
        # Clear stored URL on menu return
        context.user_data.pop('current_url', None)
        context.user_data.pop('current_platform', None)
        context.user_data.pop('pending_url', None)
        await query.edit_message_text(
            "<b>Universal Downloader</b>\n\n"
            "Send me any link or use the buttons below:",
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu()
        )
        return

    if data == "stats":
        session = SessionLocal()
        try:
            user = session.query(User).filter_by(telegram_id=user_info['id']).first()
            downloads = session.query(Download).filter_by(user_id=user_info['id']).count()

            stats_text = (
                "<b>YOUR STATISTICS</b>\n\n"
                f"User: {user_info['first_name']}\n"
                f"ID: <code>{user_info['id']}</code>\n"
                f"Total Downloads: {downloads}\n"
                f"Joined: {user.joined_date.strftime('%Y-%m-%d') if user else 'N/A'}\n"
                f"Last Active: {user.last_active.strftime('%Y-%m-%d %H:%M') if user else 'N/A'}\n\n"
                "Tip: More downloads = More features soon!"
            )
            await query.edit_message_text(
                stats_text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="menu")]
                ])
            )
        except Exception as e:
            await query.edit_message_text("Error fetching stats")
            logger.error(f"Stats error: {e}")
        finally:
            session.close()
        return

    if data == "help":
        help_text = (
            "<b>HOW TO USE</b>\n\n"
            "1. Send a URL from any platform\n"
            "2. Choose your download format\n"
            "3. Download instantly!\n\n"
            "<b>Commands:</b>\n"
            "/start - Main menu\n"
            "/help - This help\n"
            "/stats - Your stats\n\n"
            "<b>Support:</b> @YourSupportBot"
        )
        await query.edit_message_text(
            help_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="menu")]
            ])
        )
        return

    if data == "report":
        await query.edit_message_text(
            "<b>Report Issue</b>\n\n"
            "Please describe the issue:\n\n"
            "Send your report to: @YourSupportBot\n\n"
            "Include:\n"
            "- URL you tried to download\n"
            "- What happened\n"
            "- Expected behavior",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="menu")]
            ])
        )
        return

    if data == "donate":
        await query.edit_message_text(
            "<b>Support Development</b>\n\n"
            "If you find this bot useful, consider supporting:\n\n"
            "UPI: your-upi@okhdfc\n"
            "PayPal: your-paypal@email.com\n"
            "Buy Me Coffee: buymeacoffee.com/yourname\n\n"
            "Your support keeps this bot running!",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="menu")]
            ])
        )
        return

    # ===== PLATFORM SELECTION =====
    if data.startswith("platform_"):
        platform = data.replace("platform_", "", 1)

        # Check if there's a pending URL from an unknown platform
        pending_url = context.user_data.get('pending_url')

        if pending_url:
            # User selected a platform for their unknown URL
            context.user_data['current_url'] = pending_url
            context.user_data['current_platform'] = platform
            context.user_data.pop('pending_url', None)

            await query.edit_message_text(
                f"<b>{platform.upper()} Download</b>\n\n"
                f"<b>URL:</b> <code>{pending_url[:100]}{'...' if len(pending_url) > 100 else ''}</code>\n\n"
                f"<b>Select option:</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=get_download_options(pending_url, platform)
            )
        else:
            # User clicked a platform from main menu - ask for URL
            context.user_data['pending_platform'] = platform
            await query.edit_message_text(
                f"<b>{platform.upper()} Download</b>\n\n"
                f"Please send me the {platform.title()} URL.\n\n"
                f"Example: {get_example_url(platform)}",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="menu")]
                ])
            )
        return

    # ===== DOWNLOAD HANDLER =====
    if data.startswith("dl_"):
        # Parse short callback: dl_{format}_{quality}
        parts = data.split("_")
        format_type = parts[1] if len(parts) > 1 else "video"
        quality = parts[2] if len(parts) > 2 else "best"

        # Retrieve URL and platform from user_data
        url = context.user_data.get('current_url')
        platform = context.user_data.get('current_platform')

        if not url or not platform:
            await query.edit_message_text(
                "<b>Error:</b> No URL found.\n\nPlease send a URL again.",
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_menu()
            )
            return

        # Send processing message
        processing_msg = await query.edit_message_text(
            f"<b>Processing...</b>\n\n"
            f"Downloading from <b>{platform.upper()}</b>\n"
            f"<code>{url[:50]}...</code>\n\n"
            f"Please wait, this may take a moment...",
            parse_mode=ParseMode.HTML
        )

        try:
            # Perform download
            file_path = None
            filename = None

            if platform == "youtube":
                file_path, filename = await download_youtube(url, format_type, quality)
            elif platform == "instagram":
                file_path, filename = await download_instagram(url, format_type)
            elif platform == "tiktok":
                file_path, filename = await download_tiktok(url, quality == "nwm")
            else:
                file_path, filename = await download_generic(url)

            if file_path and os.path.exists(file_path):
                # Check file size
                file_size = os.path.getsize(file_path) / (1024 * 1024)
                max_size = int(os.getenv('MAX_FILE_SIZE', 50))

                if file_size > max_size:
                    await processing_msg.edit_text(
                        f"<b>File too large!</b>\n\n"
                        f"File size: {file_size:.1f}MB\n"
                        f"Max allowed: {max_size}MB\n\n"
                        f"Try downloading in lower quality."
                    )
                    shutil.rmtree(os.path.dirname(file_path), ignore_errors=True)
                    return

                # Send the file
                with open(file_path, 'rb') as f:
                    if format_type == 'audio':
                        await context.bot.send_audio(
                            chat_id=update.effective_chat.id,
                            audio=f,
                            caption=f"{filename}\n\nDownloaded from {platform.upper()}"
                        )
                    elif platform == "instagram" and format_type == "image":
                        await context.bot.send_photo(
                            chat_id=update.effective_chat.id,
                            photo=f,
                            caption=f"{filename}\n\nDownloaded from Instagram"
                        )
                    else:
                        try:
                            await context.bot.send_video(
                                chat_id=update.effective_chat.id,
                                video=f,
                                caption=f"{filename}\n\nDownloaded from {platform.upper()}"
                            )
                        except Exception:
                            # Fallback to document if video fails
                            await context.bot.send_document(
                                chat_id=update.effective_chat.id,
                                document=f,
                                caption=f"{filename}\n\nDownloaded from {platform.upper()}"
                            )

                # Save to database
                save_download(user_info['id'], url, platform, format_type, 'success')

                # Clean up entire temp directory safely
                shutil.rmtree(os.path.dirname(file_path), ignore_errors=True)

                await processing_msg.delete()
                await query.message.reply_text(
                    f"<b>Download Complete!</b>\n\n"
                    f"{filename}\n"
                    f"Size: {file_size:.1f}MB\n"
                    f"From: {platform.upper()}\n\n"
                    f"Send another URL to continue!",
                    parse_mode=ParseMode.HTML
                )

                # Clear stored URL after successful download
                context.user_data.pop('current_url', None)
                context.user_data.pop('current_platform', None)

                # Log success
                await log_to_channel(
                    context,
                    user_info,
                    "DOWNLOAD SUCCESS",
                    f"Platform: {platform.upper()}\n"
                    f"Type: {format_type}\n"
                    f"Size: {file_size:.1f}MB"
                )

            else:
                error_msg = filename if filename else "Unknown error"
                await processing_msg.edit_text(
                    f"<b>Download Failed</b>\n\n"
                    f"Could not download from {platform.upper()}.\n"
                    f"Error: {error_msg}\n\n"
                    f"Try:\n"
                    f"- Check if URL is valid\n"
                    f"- Try a different platform\n"
                    f"- Contact support if issue persists"
                )

                await log_to_channel(
                    context,
                    user_info,
                    "DOWNLOAD FAILED",
                    f"Platform: {platform.upper()}\nError: {error_msg}"
                )

        except Exception as e:
            logger.error(f"Download error: {e}")
            await processing_msg.edit_text(
                f"<b>Error Occurred</b>\n\n"
                f"Error: {str(e)[:200]}\n\n"
                f"Please try again or report this issue."
            )

# ============ ERROR HANDLER ============

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error: {context.error}")

    if update and update.effective_message:
        await update.effective_message.reply_text(
            "<b>Something went wrong!</b>\n\n"
            "Please try again later.\n"
            "If the issue persists, contact support.",
            parse_mode=ParseMode.HTML
        )

# ============ MAIN ============

def main():
    """Start the bot"""
    # Check for required environment variables
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set!")
        sys.exit(1)

    if not CHANNEL_ID:
        logger.warning("CHANNEL_ID not set - channel logging disabled")

    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))

    # Add URL handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))

    # Add callback query handler
    application.add_handler(CallbackQueryHandler(handle_callback))

    # Add error handler
    application.add_error_handler(error_handler)

    # Start bot
    logger.info("Universal Downloader Bot is starting...")
    logger.info(f"Channel ID: {CHANNEL_ID}")
    logger.info(f"Admins: {ADMIN_IDS}")

    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
