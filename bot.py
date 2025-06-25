import json
import logging
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler

CONFIG_FILE = "config.json"
BOT_TOKEN = "8103884844:AAE-67rbwRIjVu98GCg4TWPuxq2Yz9JdvrY"

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error("Error loading config: %s", e)
        return {"source_channels": [], "target_channels": [], "replacements": {}}

def save_config(data):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error("Error saving config: %s", e)

def replace_content(text, replacements):
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def forward_message(update: Update, context: CallbackContext):
    data = load_config()
    msg = update.effective_message

    if update.effective_chat.username not in [ch.replace("@", "") for ch in data["source_channels"]]:
        return

    try:
        for target in data["target_channels"]:
            if msg.text:
                new_text = replace_content(msg.text, data["replacements"])
                context.bot.send_message(chat_id=target, text=new_text)
            elif msg.caption:
                new_caption = replace_content(msg.caption, data["replacements"])
                context.bot.copy_message(chat_id=target, from_chat_id=msg.chat_id, message_id=msg.message_id, caption=new_caption)
            else:
                context.bot.copy_message(chat_id=target, from_chat_id=msg.chat_id, message_id=msg.message_id)
    except Exception as e:
        logger.error("Error forwarding: %s", e)

# ---------------- COMMANDS ----------------

def add_channel(update: Update, context: CallbackContext):
    data = load_config()
    if len(context.args) != 2:
        update.message.reply_text("Usage: /add [source|target] @channel")
        return

    kind, channel = context.args
    if kind not in ["source", "target"]:
        update.message.reply_text("First argument must be 'source' or 'target'")
        return

    key = f"{kind}_channels"
    if channel not in data[key]:
        data[key].append(channel)
        save_config(data)
        update.message.reply_text(f"Added {channel} to {key}")
    else:
        update.message.reply_text(f"{channel} already in {key}")

def remove_channel(update: Update, context: CallbackContext):
    data = load_config()
    if len(context.args) != 2:
        update.message.reply_text("Usage: /remove [source|target] @channel")
        return

    kind, channel = context.args
    if kind not in ["source", "target"]:
        update.message.reply_text("First argument must be 'source' or 'target'")
        return

    key = f"{kind}_channels"
    if channel in data[key]:
        data[key].remove(channel)
        save_config(data)
        update.message.reply_text(f"Removed {channel} from {key}")
    else:
        update.message.reply_text(f"{channel} not found in {key}")

def add_replace(update: Update, context: CallbackContext):
    data = load_config()
    if len(context.args) < 2:
        update.message.reply_text("Usage: /addreplace old new")
        return
    old = context.args[0]
    new = " ".join(context.args[1:])
    data["replacements"][old] = new
    save_config(data)
    update.message.reply_text(f"Added replacement: {old} → {new}")

def remove_replace(update: Update, context: CallbackContext):
    data = load_config()
    if len(context.args) != 1:
        update.message.reply_text("Usage: /removereplace old")
        return
    old = context.args[0]
    if old in data["replacements"]:
        del data["replacements"][old]
        save_config(data)
        update.message.reply_text(f"Removed replacement: {old}")
    else:
        update.message.reply_text(f"No replacement found for {old}")

# ---------------- MAIN ----------------

def main():
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Message handler for source channels
    dp.add_handler(MessageHandler(Filters.chat_type.channel, forward_message))

    # Commands
    dp.add_handler(CommandHandler("add", add_channel))
    dp.add_handler(CommandHandler("remove", remove_channel))
    dp.add_handler(CommandHandler("addreplace", add_replace))
    dp.add_handler(CommandHandler("removereplace", remove_replace))

    logger.info("Bot started...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
