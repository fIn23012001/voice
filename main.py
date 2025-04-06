import os
from moviepy.editor import VideoFileClip
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest
import subprocess
from flask import Flask
from threading import Thread

# Flask-сервер для UptimeRobot
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    flask_app.run(host='0.0.0.0', port=8080)

Thread(target=run_flask).start()

# Telegram Bot
TOKEN = os.getenv("TOKEN")

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    file = message.video or message.audio or message.voice or message.document

    if not file:
        return

    file_id = file.file_id
    original = await context.bot.get_file(file_id)

    input_path = f"input_{file_id}"
    output_path = f"output_{file_id}.ogg"

    await original.download_to_drive(input_path)

    try:
        if message.video or (message.document and message.document.mime_type.startswith("video")):
            clip = VideoFileClip(input_path)
            clip.audio.write_audiofile("temp_audio.wav")
            input_path = "temp_audio.wav"

        # Качественная конвертация в формат voice (libopus)
        subprocess.run([
            "ffmpeg", "-i", input_path,
            "-ac", "1",          # моно
            "-ar", "48000",      # частота 48kHz (Telegram стандарт)
            "-b:a", "64k",       # битрейт
            "-c:a", "libopus",   # кодек Opus
            "-vn", output_path
        ], check=True)

        with open(output_path, "rb") as f:
            await message.reply_voice(f)

    except Exception as e:
        print(f"Error: {e}")
        await message.reply_text("Произошла ошибка при обработке файла.")
    finally:
        for path in [input_path, output_path, "temp_audio.wav"]:
            if os.path.exists(path):
                os.remove(path)

if __name__ == '__main__':
    request = HTTPXRequest(connect_timeout=20, read_timeout=20)
    app = ApplicationBuilder().token(TOKEN).request(request).build()
    handler = MessageHandler(filters.ALL, handle_media)
    app.add_handler(handler)
    app.run_polling()
