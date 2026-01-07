"""
Telegram URL Counter Bot
- Collects URLs with @profile
- Every 10 URLs: sends 10link.txt file to group
- Reply 'delete' to remove a URL
"""

import re
import os
import json
import logging
from telegram import Update, ReactionTypeEmoji
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

PENDING_FILE = "pending_urls.json"
COUNT_FILE = "url_counts.json"
BATCH_SIZE = 30

URL_PATTERN = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')
PROFILE_IN_URL_PATTERN = re.compile(r'/@([a-zA-Z0-9_.]+)')


def extract_profile_from_url(url: str) -> str | None:
    match = PROFILE_IN_URL_PATTERN.search(url)
    return f"@{match.group(1)}" if match else None


def load_pending_urls() -> list:
    try:
        if os.path.exists(PENDING_FILE):
            with open(PENDING_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return []


def save_pending_urls(urls: list) -> None:
    with open(PENDING_FILE, 'w', encoding='utf-8') as f:
        json.dump(urls, f, indent=2)


def load_counts() -> dict:
    try:
        if os.path.exists(COUNT_FILE):
            with open(COUNT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}


def save_counts(counts: dict) -> None:
    with open(COUNT_FILE, 'w', encoding='utf-8') as f:
        json.dump(counts, f, indent=2)


def create_batch_file(urls: list) -> str:
    filename = "30link.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        for entry in urls:
            f.write(f"{entry['url']}\n")
    return filename


async def handle_reply_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle when user replies 'delete' to remove their URL."""
    try:
        user = update.message.from_user
        sender = user.username or user.first_name or "Unknown"
        
        replied_msg = update.message.reply_to_message
        replied_text = replied_msg.text or ""
        
        urls_in_reply = URL_PATTERN.findall(replied_text)
        if not urls_in_reply:
            await update.message.reply_text("That message doesn't contain a URL!")
            return
        
        original_sender = replied_msg.from_user
        original_username = original_sender.username or original_sender.first_name or "Unknown"
        
        if original_username != sender:
            await update.message.reply_text("You can only delete your own URLs!")
            return
        
        pending = load_pending_urls()
        url_to_remove = urls_in_reply[0]
        
        removed = None
        for i, entry in enumerate(pending):
            if entry['url'] == url_to_remove and entry['sender'] == sender:
                removed = pending.pop(i)
                break
        
        if removed:
            save_pending_urls(pending)
            counts = load_counts()
            if sender in counts and counts[sender] > 0:
                counts[sender] -= 1
                save_counts(counts)
            
            await update.message.reply_text(
                f"URL removed!\nProfile: {removed['profile']}\nProgress: {len(pending)}/{BATCH_SIZE} URLs"
            )
            logger.info(f"@{sender} removed URL. Pending: {len(pending)}")
        else:
            await update.message.reply_text("URL not found in pending list")
            
    except Exception as e:
        logger.error(f"Error in reply delete: {e}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if not update.message or not update.message.text:
            return
        
        text_lower = update.message.text.lower().strip()
        
        # Check if user is replying "delete" to remove their URL
        if text_lower in ['delete', 'remove', 'del', 'rm']:
            if update.message.reply_to_message:
                await handle_reply_delete(update, context)
            return
        
        text = update.message.text
        urls = URL_PATTERN.findall(text)
        
        if not urls:
            return
        
        user = update.message.from_user
        sender = user.username or user.first_name or "Unknown"
        
        valid_urls = []
        for url in urls:
            profile = extract_profile_from_url(url)
            # Accept all URLs, profile is optional
            valid_urls.append({'url': url, 'profile': profile or 'N/A', 'sender': sender})
        
        # React with praying hands emoji
        try:
            await update.message.set_reaction([ReactionTypeEmoji(emoji="\U0001F64F")])
        except Exception as e:
            logger.warning(f"Could not set reaction: {e}")
        
        pending = load_pending_urls()
        pending.extend(valid_urls)
        
        counts = load_counts()
        if sender not in counts:
            counts[sender] = 0
        counts[sender] += len(valid_urls)
        save_counts(counts)
        
        current_count = len(pending)
        previous_count = current_count - len(valid_urls)
        logger.info(f"@{sender} added {len(valid_urls)} URL(s). Total: {current_count}")
        
        save_pending_urls(pending)
        
        # Send progress message at milestones: 10, 20, 30, 40, etc.
        for milestone in range(10, current_count + 1, 10):
            if previous_count < milestone <= current_count:
                await update.message.reply_text(f"Progress: {current_count} URLs")
                break
        
    except Exception as e:
        logger.error(f"Error: {e}")


async def remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user = update.message.from_user
        sender = user.username or user.first_name or "Unknown"
        
        pending = load_pending_urls()
        
        removed = None
        for i in range(len(pending) - 1, -1, -1):
            if pending[i]['sender'] == sender:
                removed = pending.pop(i)
                break
        
        if removed:
            save_pending_urls(pending)
            counts = load_counts()
            if sender in counts and counts[sender] > 0:
                counts[sender] -= 1
                save_counts(counts)
            
            await update.message.reply_text(
                f"Removed your URL!\nProfile: {removed['profile']}\nProgress: {len(pending)}/{BATCH_SIZE} URLs"
            )
        else:
            await update.message.reply_text("You have no URLs to remove!")
            
    except Exception as e:
        logger.error(f"Error: {e}")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        counts = load_counts()
        pending = load_pending_urls()
        total = sum(counts.values())
        
        if not counts:
            await update.message.reply_text(f"No URLs yet!\nPending: {len(pending)}/{BATCH_SIZE}")
            return
        
        sorted_users = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        leaderboard = "\n".join([f"  @{user}: {count}" for user, count in sorted_users[:10]])
        
        await update.message.reply_text(
            f"URL Statistics\n\nTotal URLs: {total}\nPending: {len(pending)}/{BATCH_SIZE}\n"
            f"Contributors: {len(counts)}\n\nTop contributors:\n{leaderboard}"
        )
    except Exception as e:
        logger.error(f"Error: {e}")


async def get_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send file with all collected URLs and reset the list."""
    try:
        pending = load_pending_urls()
        
        if not pending:
            await update.message.reply_text("No URLs collected yet!")
            return
        
        filename = create_batch_file(pending)
        with open(filename, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=f"{len(pending)}link.txt",
                caption=f"{len(pending)} URLs collected! Thank you contributors!"
            )
        os.remove(filename)
        
        # Reset pending URLs
        save_pending_urls([])
        logger.info(f"File sent with {len(pending)} URLs. List reset.")
    except Exception as e:
        logger.error(f"Error in get command: {e}")


async def total_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show total URLs collected."""
    try:
        pending = load_pending_urls()
        await update.message.reply_text(f"Total URLs: {len(pending)}")
    except Exception as e:
        logger.error(f"Error: {e}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pending = load_pending_urls()
    await update.message.reply_text(
        "Hello! I'm the URL Counter Bot.\n\n"
        "Send any URL (TikTok, Facebook, etc.)\n\n"
        f"Progress: {len(pending)}/{BATCH_SIZE}\n\n"
        "Commands:\n"
        "/get - Download all URLs as file\n"
        "/remove - Remove your last URL\n"
        "/stats - Show statistics"
    )


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        return
    
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("remove", remove_command))
    app.add_handler(CommandHandler("get", get_command))
    app.add_handler(CommandHandler("total", total_command))
    app.add_handler(MessageHandler(
        filters.TEXT & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP),
        handle_message
    ))
    
    logger.info("Bot started! Collecting URLs...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
