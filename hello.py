import asyncio
import logging
import yt_dlp
import psycopg2
import os
import re
from aiogram.types import InputFile
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command

# Bot tokeni
TOKEN = "7471718456:AAEOTwy2eyxVIuaUtrnK9hbGZoFg2aUvQ80"

# PostgreSQL ulanish parametrlari
DB_NAME = "musicbot"
DB_USER = "your_user"
DB_PASS = "your_password"
DB_HOST = "localhost"
DB_PORT = "5432"

# PostgreSQL ulanish
def get_db_connection():
    return psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)

# Bot va Dispatcher
bot = Bot(token=TOKEN)
dp = Dispatcher()

# 🔹 YouTube qo‘shiqlarni yuklash
async def download_audio(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'outtmpl': 'downloads/%(id)s.%(ext)s',  # Fayl nomini ID asosida qilish
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 10,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = f"downloads/{info['id']}.mp3"
            return file_path
    except Exception as e:
        logging.error(f"Yuklashda xatolik: {e}")
        return None

# 🔹 Qo‘shiq qidirish
async def search_song(query):
    search_url = f"ytsearch5:{query}"  # Eng ko‘pi bilan 5 ta natija qaytarish
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(search_url, download=False)
            if 'entries' not in info or not info['entries']:
                return []
            return [(entry['title'], entry['id']) for entry in info['entries']]
    except Exception as e:
        logging.error(f"Qidirishda xatolik: {e}")
        return []

# 🔹 /start komandasi
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("Assalomu alaykum! Menga qo‘shiq nomini yoki ijrochini yozing.")

# 🔹 Qidiruv
@dp.message()
async def song_search(message: types.Message):
    query = message.text.strip()
    results = await search_song(query)
    if not results:
        await message.answer("Hech narsa topilmadi!")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=title, callback_data=video_id)] for title, video_id in results]
    )

    await message.answer("Natijalarni tanlang:", reply_markup=keyboard)

# 🔹 Tanlangan qo‘shiqni yuklash va yuborish
async def download_and_send_audio(call, video_url):
    file_path = await download_audio(video_url)
    if not file_path:
        await call.message.answer("Qo‘shiqni yuklab bo‘lmadi. Keyinroq urinib ko‘ring!")
        return
    try:
        audio = InputFile(file_path)
        await call.message.answer_audio(audio)
    except Exception as e:
        logging.error(f"Fayl yuborishda xatolik: {e}")
        await call.message.answer("Qo‘shiqni yuborishda xatolik yuz berdi!")

# 🔹 Callback uchun asinxron yuklash
@dp.callback_query()
async def send_audio(call: CallbackQuery):
    video_id = call.data
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    await call.message.answer("Qo‘shiq yuklanmoqda... ⏳")
    asyncio.create_task(download_and_send_audio(call, video_url))  # ✅ Asinxron yuklash

# 🔹 Botni ishga tushirish
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

