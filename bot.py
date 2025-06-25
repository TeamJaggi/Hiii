import json
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

BOT_TOKEN = "8103884844:AAE-67rbwRIjVu98GCg4TWPuxq2Yz9JdvrY"
CONFIG_FILE = "config.json"

logging.basicConfig(level=logging.INFO)


def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {"source_channels": [], "target_channels": [], "replacements": {}}


def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /add source|target @channel")
        return

    mode, channel = context.args[0], context.args[1]
    data = load_config()

    if mode not in ["source", "target"]:
        await update.message.reply_text("Invalid mode. Use source or target.")
        return

    key = f"{mode}_channels"
    if channel not in data[key]:
        data[key].append(channel)
        save_config(data)
        await update.message.reply_text(f"Added {channel} to {mode} channels.")
    else:
        await update.message.reply_text("Already added.")


async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /remove source|target @channel")
        return

    mode, channel = context.args[0], context.args[1]
    data = load_config()
    key = f"{mode}_channels"

    if channel in data[key]:
        data[key].remove(channel)
        save_config(data)
        await update.message.reply_text(f"Removed {channel} from {mode} channels.")
    else:
        await update.message.reply_text("Channel not found.")


async def addreplace(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /addreplace old new")
        return

    old, new = context.args[0], context.args[1]
    data = load_config()
    data["replacements"][old] = new
    save_config(data)
    await update.message.reply_text(f"Replacement rule added: {old} → {new}")


async def removereplace(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /removereplace old")
        return

    old = context.args[0]
    data = load_config()
    if old in data["replacements"]:
        del data["replacements"][old]
        save_config(data)
        await update.message.reply_text(f"Removed replacement: {old}")
    else:
        await update.message.reply_text("Rule not found.")


async def forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_config()

    source_username = update.effective_chat.username
    if not source_username or f"@{source_username}" not in data["source_channels"]:
        return

    msg = update.effective_message
    text = msg.text or msg.caption or ""
    for old, new in data["replacements"].items():
        text = text.replace(old, new)

    for target in data["target_channels"]:
        try:
            if msg.text:
                await context.bot.send_message(chat_id=target, text=text)
            elif msg.photo:
                await context.bot.send_photo(chat_id=target, photo=msg.photo[-1].file_id, caption=text)
            elif msg.video:
                await context.bot.send_video(chat_id=target, video=msg.video.file_id, caption=text)
            elif msg.document:
                await context.bot.send_document(chat_id=target, document=msg.document.file_id, caption=text)
            elif msg.sticker:
                await context.bot.send_sticker(chat_id=target, sticker=msg.sticker.file_id)
            elif msg.audio:
                await context.bot.send_audio(chat_id=target, audio=msg.audio.file_id, caption=text)
            elif msg.voice:
                await context.bot.send_voice(chat_id=target, voice=msg.voice.file_id, caption=text)
            elif msg.video_note:
                await context.bot.send_video_note(chat_id=target, video_note=msg.video_note.file_id)
        except Exception as e:
            logging.error(f"Failed to forward to {target}: {e}")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("addreplace", addreplace))
    app.add_handler(CommandHandler("removereplace", removereplace))
    app.add_handler(MessageHandler(filters.ALL & filters.ChatType.CHANNEL, forward))

    print("Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
