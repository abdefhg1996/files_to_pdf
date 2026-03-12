import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Konvertatsiya kutubxonalari
from docx2pdf import convert as docx_to_pdf
from PIL import Image

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
CHANNELS = os.getenv("CHANNELS") # Kanalingiz @yuzeri

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- MAJBURIY OBUNA TEKSHIRUVCHISI ---
async def check_sub(user_id):
    try:
        # Bot kanalda admin bo'lishi shart!
        member = await bot.get_chat_member(chat_id=CHANNELS, user_id=user_id)
        if member.status != 'left':
            return True
        return False
    except Exception:
        return False

# Obuna bo'lish tugmasini yaratish
def get_sub_keyboard():
    builder = InlineKeyboardBuilder()
    # IZOH: Kanal linkini o'zgartirishni unutmang
    builder.row(InlineKeyboardButton(text="Kanalga a'zo bo'lish 📢", url=f"https://t.me{CHANNELS.replace('@', '')}"))
    builder.row(InlineKeyboardButton(text="Tekshirish ✅", callback_data="check_subscription"))
    return builder.as_markup()

# --- HANDLERLAR ---

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    if await check_sub(message.from_user.id):
        await message.answer("Xush kelibsiz! Menga fayl yuboring, PDF qilib beraman.")
    else:
        await message.answer(
            f"Botdan foydalanish uchun {CHANNELS} kanaliga obuna bo'lishingiz kerak!",
            reply_markup=get_sub_keyboard()
        )

# Tekshirish tugmasi bosilganda
@dp.callback_query(F.data == "check_subscription")
async def check_callback(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.message.edit_text("Rahmat! Endi botdan foydalanishingiz mumkin. Fayl yuboring:")
    else:
        await call.answer("Siz hali a'zo bo'lmadingiz! ❌", show_alert=True)

# Fayllarni qabul qilish (Tekshiruv bilan)
@dp.message(F.document | F.photo)
async def handle_files(message: types.Message):
    # Obunani tekshiramiz
    if not await check_sub(message.from_user.id):
        await message.answer(
            f"Kechirasiz, avval kanalga obuna bo'ling!",
            reply_markup=get_sub_keyboard()
        )
        return

    # Fayl turi va yo'llarini aniqlash
    if message.photo:
        file_id = message.photo[-1].file_id
        file_name = f"img_{message.from_user.id}.jpg"
    else:
        file_id = message.document.file_id
        file_name = message.document.file_name

    # Faylni yuklab olish va PDF qilish (Oldingi kod kabi davom etadi)
    input_path = os.path.join("downloads", file_name)
    # .pdf kengaytmasini to'g'ri yasash
    output_name = file_name.rsplit('.', 1)[0] + ".pdf"
    output_path = os.path.join("downloads", output_name)
    
    status_msg = await message.answer("Fayl ishlov berilmoqda... ⏳")
    
    try:
        file = await bot.get_file(file_id)
        await bot.download_file(file.file_path, input_path)

        if file_name.endswith(('.docx', '.doc')):
            docx_to_pdf(input_path, output_path)
        elif file_name.endswith(('.jpg', '.jpeg', '.png')):
            Image.open(input_path).convert('RGB').save(output_path)
        
        await message.answer_document(FSInputFile(output_path), caption="Tayyor! ✅")
        await status_msg.delete()
    except Exception as e:
        await message.answer(f"Xato: {e}")
    finally:
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)

async def main():
    if not os.path.exists("downloads"): os.makedirs("downloads")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
