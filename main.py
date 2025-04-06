import os
from moviepy.editor import VideoFileClip
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest
import subprocess

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
            clip.audio.write_audiofile(output_path, codec='libvorbis')
        else:
            subprocess.run([
                "ffmpeg", "-i", input_path,
                "-c:a", "libvorbis", "-vn", output_path
            ], check=True)

        with open(output_path, "rb") as f:
            await message.reply_voice(f)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        for path in [input_path, output_path]:
            if os.path.exists(path):
                os.remove(path)

if __name__ == '__main__':
    request = HTTPXRequest(connect_timeout=20, read_timeout=20)
    app = ApplicationBuilder().token(TOKEN).request(request).build()
    handler = MessageHandler(filters.ALL, handle_media)
    app.add_handler(handler)
    app.run_polling()