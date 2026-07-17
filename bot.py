import os
import sys
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

async def log_to_channel(context: ContextTypes.DEFAULT_TYPE, user_info: Dict, action: str, details: str = ""):
    """Send user activity to destination channel"""
    if not CHANNEL_ID:
        return
    
    try:
        message = f"""
╔══════════════════════════════════════════════════╗
║           👤 USER ACTIVITY LOG                    ║
╠══════════════════════════════════════════════════╣
║                                                   ║
║  🆔 User ID: {user_info['id']}                   ║
║  👤 Username: @{user_info['username']}           ║
║  📛 Name: {user_info['first_name']}              ║
║  ⚡ Action: {action}                              ║
║  📝 Details: {details}                           ║
║  🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}║
║                                                   ║
╚══════════════════════════════════════════════════╝
"""
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=message,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Failed to log to channel: {e}")

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
        "NEW USER 🎉", 
        f"User @{user_info['username']} started the bot"
    )
    
    welcome = f"""
╔══════════════════════════════════════════════════╗
║         📥 UNIVERSAL DOWNLOADER BOT              ║
╠══════════════════════════════════════════════════╣
║                                                   ║
║  👋 Hello {user_info['first_name']}!              ║
║                                                   ║
║  📌 Download from ANY platform:                   ║
║  📹 YouTube    📸 Instagram    🎵 TikTok        ║
║  🐦 Twitter    📘 Facebook     📌 Pinterest     ║
║  🎥 Reddit     🔗 Any URL      📄 Text          ║
║                                                   ║
║  🚀 How to use:                                   ║
║  1️⃣ Send me a URL                                ║
║  2️⃣ Choose format                                ║
║  3️⃣ Download instantly!                          ║
║                                                   ║
║  ⭐ Features:                                     ║
║  ✅ No watermark downloads                        ║
║  ✅ Multiple quality options                      ║
║  ✅ Fast & reliable                              ║
║                                                   ║
║  🔥 Send any link to get started!                 ║
║                                                   ║
╚══════════════════════════════════════════════════╝
"""
    await update.message.reply_text(
        welcome,
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
📖 **UNIVERSAL DOWNLOADER - HELP**

**📥 How to Use:**
1. Send a URL from any supported platform
2. Select your preferred format/quality
3. Wait for download to complete

**🎯 Supported Platforms:**
• YouTube - Video/Audio/Thumbnail
• Instagram - Video/Image/All content
• TikTok - Video (No watermark available)
• Twitter/X - Videos & Media
• Facebook - Videos & Images
• Pinterest - Images
• Reddit - Videos & Media
• Any URL - Direct download

**⚡ Commands:**
/start - Show main menu
/help - Show this help
/stats - View your download statistics

**⚠️ Limits:**
• Max file: 50MB
• Rate limit: 10 downloads/minute
• Files auto-delete after sending

**💡 Tips:**
• For YouTube, choose lower quality for faster downloads
• TikTok downloads are watermark-free
• Use "Any URL" for direct file downloads
"""
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
        
        stats = f"""
📊 **YOUR STATISTICS**

👤 User: {user_info['first_name']}
🆔 ID: {user_info['id']}
📥 Total Downloads: {downloads}
📅 Joined: {user.joined_date.strftime('%Y-%m-%d') if user else 'N/A'}
🔄 Last Active: {user.last_active.strftime('%Y-%m-%d %H:%M') if user else 'N/A'}

💡 More downloads = More features unlocked!
"""
        await update.message.reply_text(
            stats,
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu()
        )
    except Exception as e:
        logger.error(f"Stats error: {e}")
        await update.message.reply_text("❌ Error fetching stats")
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
            "❌ **Invalid URL!**\n\n"
            "Please send a valid URL starting with http:// or https://\n\n"
            "📌 Example: https://youtube.com/watch?v=abc123",
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu()
        )
        return
    
    # Detect platform
    platform = get_platform_from_url(url)
    
    if platform == 'unknown':
        keyboard = [
            [InlineKeyboardButton("📹 YouTube", callback_data=f"platform_youtube_{url}")],
            [InlineKeyboardButton("📸 Instagram", callback_data=f"platform_instagram_{url}")],
            [InlineKeyboardButton("🎵 TikTok", callback_data=f"platform_tiktok_{url}")],
            [InlineKeyboardButton("🐦 Twitter/X", callback_data=f"platform_twitter_{url}")],
            [InlineKeyboardButton("🔗 Any URL", callback_data=f"platform_any_{url}")],
            [InlineKeyboardButton("🔙 Back", callback_data="menu")]
        ]
        await update.message.reply_text(
            "🤔 **Platform Not Detected**\n\n"
            "Please select the platform of your URL:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Log to channel
    await log_to_channel(
        context,
        user_info,
        "DOWNLOAD REQUEST 📥",
        f"Platform: {platform.upper()}\nURL: {url[:100]}..."
    )
    
    # Show download options
    await update.message.reply_text(
        f"✅ **Platform Detected:** {platform.upper()}\n\n"
        f"🔗 URL: {url[:100]}{'...' if len(url) > 100 else ''}\n\n"
        f"⬇️ **Select download option:**",
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
        await query.edit_message_text(
            "📥 **Universal Downloader**\n\n"
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
            
            stats_text = f"""
📊 **YOUR STATISTICS**

👤 User: {user_info['first_name']}
🆔 ID: {user_info['id']}
📥 Total Downloads: {downloads}
📅 Joined: {user.joined_date.strftime('%Y-%m-%d') if user else 'N/A'}
🔄 Last Active: {user.last_active.strftime('%Y-%m-%d %H:%M') if user else 'N/A'}

💡 Tip: More downloads = More features soon!
"""
            await query.edit_message_text(
                stats_text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="menu")]
                ])
            )
        except Exception as e:
            await query.edit_message_text("❌ Error fetching stats")
            logger.error(f"Stats error: {e}")
        finally:
            session.close()
        return
    
    if data == "help":
        help_text = """
📖 **HOW TO USE**

1️⃣ Send a URL from any platform
2️⃣ Choose your download format
3️⃣ Download instantly!

**Commands:**
/start - Main menu
/help - This help
/stats - Your stats

**Support:** @YourSupportBot
"""
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
            "🐛 **Report Issue**\n\n"
            "Please describe the issue:\n\n"
            "Send your report to: @YourSupportBot\n\n"
            "Include:\n"
            "• URL you tried to download\n"
            "• What happened\n"
            "• Expected behavior",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="menu")]
            ])
        )
        return
    
    if data == "donate":
        await query.edit_message_text(
            "🎁 **Support Development**\n\n"
            "If you find this bot useful, consider supporting:\n\n"
            "💰 UPI: your-upi@okhdfc\n"
            "💳 PayPal: your-paypal@email.com\n"
            "☕ Buy Me Coffee: buymeacoffee.com/yourname\n\n"
            "Your support keeps this bot running! 🚀",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="menu")]
            ])
        )
        return
    
    # ===== PLATFORM SELECTION =====
    if data.startswith("platform_"):
        parts = data.split("_")
        platform = parts[1]
        url = parts[2] if len(parts) > 2 else None
        
        if url:
            await query.edit_message_text(
                f"📥 **{platform.upper()} Download**\n\n"
                f"🔗 {url[:100]}{'...' if len(url) > 100 else ''}\n\n"
                f"⬇️ **Select option:**",
                parse_mode=ParseMode.HTML,
                reply_markup=get_download_options(url, platform)
            )
        else:
            await query.edit_message_text(
                f"📥 **{platform.upper()} Download**\n\n"
                f"Please send me the {platform.title()} URL.\n\n"
                f"Example: {get_example_url(platform)}",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="menu")]
                ])
            )
            context.user_data['pending_platform'] = platform
        return
    
    # ===== DOWNLOAD HANDLER =====
    if data.startswith("dl_"):
        parts = data.split("_")
        platform = parts[1]
        format_type = parts[2]
        quality = parts[3] if len(parts) > 4 else 'best'
        url = "_".join(parts[4:]) if len(parts) > 4 else "_".join(parts[3:])
        
        # Send processing message
        processing_msg = await query.edit_message_text(
            f"⏳ **Processing...**\n\n"
            f"📥 Downloading from {platform.upper()}\n"
            f"🔗 {url[:50]}...\n\n"
            f"Please wait, this may take a moment... ⏱️",
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
            elif platform == "any":
                file_path, filename = await download_generic(url)
            else:
                file_path, filename = await download_generic(url)
            
            if file_path and os.path.exists(file_path):
                # Check file size
                file_size = os.path.getsize(file_path) / (1024 * 1024)
                max_size = int(os.getenv('MAX_FILE_SIZE', 50))
                
                if file_size > max_size:
                    await processing_msg.edit_text(
                        f"❌ **File too large!**\n\n"
                        f"File size: {file_size:.1f}MB\n"
                        f"Max allowed: {max_size}MB\n\n"
                        f"Try downloading in lower quality."
                    )
                    os.remove(file_path)
                    return
                
                # Send the file
                with open(file_path, 'rb') as f:
                    if format_type == 'audio':
                        await context.bot.send_audio(
                            chat_id=update.effective_chat.id,
                            audio=f,
                            caption=f"🎵 **{filename}**\n\nDownloaded from {platform.upper()}"
                        )
                    elif platform == "instagram" and format_type == "image":
                        await context.bot.send_photo(
                            chat_id=update.effective_chat.id,
                            photo=f,
                            caption=f"🖼️ **{filename}**\n\nDownloaded from Instagram"
                        )
                    else:
                        try:
                            await context.bot.send_video(
                                chat_id=update.effective_chat.id,
                                video=f,
                                caption=f"📹 **{filename}**\n\nDownloaded from {platform.upper()}"
                            )
                        except:
                            # Fallback to document if video fails
                            await context.bot.send_document(
                                chat_id=update.effective_chat.id,
                                document=f,
                                caption=f"📁 **{filename}**\n\nDownloaded from {platform.upper()}"
                            )
                
                # Save to database
                save_download(user_info['id'], url, platform, format_type, 'success')
                
                # Clean up
                os.remove(file_path)
                os.rmdir(os.path.dirname(file_path))
                
                await processing_msg.delete()
                await query.message.reply_text(
                    f"✅ **Download Complete!**\n\n"
                    f"📥 {filename}\n"
                    f"📊 Size: {file_size:.1f}MB\n"
                    f"🔗 From: {platform.upper()}\n\n"
                    f"💡 Send another URL to continue!",
                    parse_mode=ParseMode.HTML
                )
                
                # Log success
                await log_to_channel(
                    context,
                    user_info,
                    "DOWNLOAD SUCCESS ✅",
                    f"Platform: {platform.upper()}\n"
                    f"Type: {format_type}\n"
                    f"Size: {file_size:.1f}MB"
                )
                
            else:
                await processing_msg.edit_text(
                    f"❌ **Download Failed**\n\n"
                    f"Could not download from {platform.upper()}.\n"
                    f"Error: {filename}\n\n"
                    f"Try:\n"
                    f"• Check if URL is valid\n"
                    f"• Try a different platform\n"
                    f"• Contact support if issue persists"
                )
                
                await log_to_channel(
                    context,
                    user_info,
                    "DOWNLOAD FAILED ❌",
                    f"Platform: {platform.upper()}\nError: {filename}"
                )
                
        except Exception as e:
            logger.error(f"Download error: {e}")
            await processing_msg.edit_text(
                f"❌ **Error Occurred**\n\n"
                f"Error: {str(e)[:200]}\n\n"
                f"Please try again or report this issue."
            )

# ============ ERROR HANDLER ============

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error: {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ **Something went wrong!**\n\n"
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
    logger.info("🚀 Universal Downloader Bot is starting...")
    logger.info(f"📢 Channel ID: {CHANNEL_ID}")
    logger.info(f"👑 Admins: {ADMIN_IDS}")
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()