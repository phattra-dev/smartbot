# Telegram URL Monitor Bot

A simple bot that monitors group chats for URLs, counts them, and saves them to `note.txt`.

## Features

- Detects all http/https URLs in group messages
- Persistent URL count across restarts
- Saves URLs with timestamp and username
- Handles multiple URLs per message
- Crash-resistant with error handling
- Commands: `/start`, `/stats`

## Setup Instructions

### Step 1: Create Your Bot with BotFather

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow prompts to name your bot
4. Copy the **API token** (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Step 2: Disable Privacy Mode (IMPORTANT!)

By default, bots can only see commands in groups. To see all messages:

1. In BotFather, send `/mybots`
2. Select your bot
3. Click **Bot Settings** → **Group Privacy**
4. Click **Turn off**

### Step 3: Install Dependencies

```bash
cd telegram_url_bot
pip install -r requirements.txt
```

### Step 4: Set Your Bot Token

**Windows (CMD):**
```cmd
set TELEGRAM_BOT_TOKEN=your_token_here
```

**Windows (PowerShell):**
```powershell
$env:TELEGRAM_BOT_TOKEN="your_token_here"
```

**Linux/Mac:**
```bash
export TELEGRAM_BOT_TOKEN=your_token_here
```

### Step 5: Run the Bot

```bash
python bot.py
```

### Step 6: Add Bot to Group

1. Open your Telegram group
2. Click group name → Add Members
3. Search for your bot's username
4. Add it to the group

## Files Created

- `note.txt` - All collected URLs with timestamps
- `url_count.txt` - Persistent URL counter

## 24/7 Deployment Options

### Option 1: Run with nohup (Linux)
```bash
nohup python bot.py > bot.log 2>&1 &
```

### Option 2: Use systemd service (Linux)
Create `/etc/systemd/system/urlbot.service`:
```ini
[Unit]
Description=Telegram URL Bot
After=network.target

[Service]
User=youruser
WorkingDirectory=/path/to/telegram_url_bot
Environment=TELEGRAM_BOT_TOKEN=your_token_here
ExecStart=/usr/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable urlbot
sudo systemctl start urlbot
```

### Option 3: Docker
Create a `Dockerfile` and run in a container.

## Silent Mode

To disable reply messages, comment out these lines in `bot.py`:
```python
# await update.message.reply_text(
#     f"✅ Detected {len(urls)} URL(s)\n📊 Total URLs saved: {new_count}"
# )
```

## Troubleshooting

- **Bot not responding?** Check privacy mode is disabled
- **Token error?** Verify TELEGRAM_BOT_TOKEN is set correctly
- **No URLs detected?** Bot only works in group/supergroup chats
