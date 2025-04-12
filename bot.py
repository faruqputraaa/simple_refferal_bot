from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from db import Database
import asyncio
import os
import time
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "@testerantony"

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
db = Database()

# Fungsi bantu: generate kode referral unik (user_id saja, tanpa timestamp)
def generate_ref_code(user_id: int) -> str:
    return f"ref_{user_id}"

# Tombol Dashboard
def dashboard_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="📋 Dashboard", callback_data="dashboard")]]
    )

# Tampilkan Dashboard
async def show_dashboard(user_id, username, target):
    score = await db.get_score(user_id)
    ref_code = generate_ref_code(user_id)
    link = f"https://t.me/{(await bot.get_me()).username}?start={ref_code}"

    text = (
        f"🎉 <b>Selamat datang di Referral Bot!</b>\n\n"
        f"👤 <b>Username:</b> @{username}\n"
        f"🔗 <b>Link referral kamu:</b>\n{link}\n\n"
        f"🏅 <b>Poin kamu:</b> <b>{score}</b>\n\n"
        "Perintah:\n"
        "🔘 /score - lihat poinmu\n"
        "🔘 /link - link referral\n"
        "🔘 /leaderboard - peringkat\n"
    )
    await target.answer(text, reply_markup=dashboard_button())

# Start command
@dp.message(F.text.startswith("/start"))
async def start(message: Message):
    args = message.text.split(" ")
    ref_code = args[1] if len(args) > 1 else None

    referrer_id = None
    if ref_code and ref_code.startswith("ref_"):
        parts = ref_code.split("_")
        if len(parts) == 2 and parts[1].isdigit():
            referrer_id = int(parts[1])

    user_id = message.from_user.id
    username = message.from_user.username or "unknown"

    # Tambahkan user baru
    await db.add_user(user_id, username, referrer_id)

    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ("member", "administrator", "creator"):
            await show_dashboard(user_id, username, message)
        else:
            await ask_to_join(message)
    except Exception as e:
        await message.answer("⚠️ Gagal mengecek keanggotaan channel.")
        print(e)

# Jika belum join
async def ask_to_join(message: Message):
    join_button = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Saya sudah join channel", callback_data="verify_join")]
        ]
    )
    await message.answer(
        "❗ Silakan join channel terlebih dahulu:\nhttps://t.me/testerantony",
        reply_markup=join_button
    )

# Callback: Verifikasi Join
@dp.callback_query(F.data == "verify_join")
async def verify_join(callback: CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.username or "unknown"
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ("member", "administrator", "creator"):
            await callback.message.answer("✅ Verifikasi berhasil!")
            await show_dashboard(user_id, username, callback.message)
        else:
            await callback.message.answer("❌ Kamu belum join channel.")
    except Exception as e:
        await callback.message.answer("⚠️ Gagal mengecek keanggotaan channel.")
        print(e)

# Tombol dashboard ditekan
@dp.callback_query(F.data == "dashboard")
async def dashboard_btn(callback: CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.username or "unknown"
    await show_dashboard(user_id, username, callback.message)

# /link
@dp.message(F.text == "/link")
async def referral_link(message: Message):
    user_id = message.from_user.id
    ref_code = generate_ref_code(user_id)
    link = f"https://t.me/{(await bot.get_me()).username}?start={ref_code}"
    await message.answer(f"🔗 Link referral kamu:\n{link}")

# /score
@dp.message(F.text == "/score")
async def my_score(message: Message):
    user_id = message.from_user.id
    score = await db.get_score(user_id)
    await message.answer(f"🏅 Poin kamu: <b>{score}</b>")

# /leaderboard
@dp.message(F.text == "/leaderboard")
async def leaderboard(message: Message):
    top_users = await db.get_leaderboard()
    text = "🏆 <b>Leaderboard</b> 🏆\n\n"
    for i, (username, score) in enumerate(top_users, start=1):
        text += f"{i}. @{username} - {score} poin\n"
    await message.answer(text)

# Start polling
async def main():
    await db.connect()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
