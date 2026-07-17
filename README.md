# 📥 Universal Downloader Bot

[![Deploy on Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

A powerful Telegram bot to download content from multiple platforms - YouTube, Instagram, TikTok, Twitter, Facebook, Pinterest, Reddit, and more.

## 🌟 Features

- 📹 **YouTube** - Download videos, audio, thumbnails
- 📸 **Instagram** - Download posts, videos, images
- 🎵 **TikTok** - Download videos (No watermark option)
- 🐦 **Twitter/X** - Download videos and media
- 📘 **Facebook** - Download videos and images
- 📌 **Pinterest** - Download images
- 🎥 **Reddit** - Download videos and media
- 🔗 **Any URL** - Direct file download
- 📊 **User Statistics** - Track your downloads
- 📢 **Channel Logging** - Monitor user activity

## 🚀 Quick Start

1. **Get Bot Token** from @BotFather
2. **Get Channel ID** by adding bot to channel
3. **Deploy on Render** (click the button above)
4. **Start using** the bot with `/start`

## 🛠️ Local Development

```bash
# Clone repository
git clone https://github.com/yourusername/universal-downloader-bot.git
cd universal-downloader-bot

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your credentials

# Run bot
python bot.py