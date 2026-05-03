import asyncio
from telegram import Bot
from bot_engine.config import TELEGRAM_TOKEN
from bot_engine.config import BASE_DIR

async def download_logo():
    bot = Bot(token=TELEGRAM_TOKEN)
    bot_info = await bot.get_me()
    photos = await bot.get_user_profile_photos(bot_info.id)
    if photos.photos:
        file = await bot.get_file(photos.photos[0][-1].file_id)
        out_path = BASE_DIR / "data" / "nova_logo.png"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        await file.download_to_drive(out_path)
        print(f"Logo descargado en {out_path}")
    else:
        print("El bot no tiene foto de perfil")

if __name__ == "__main__":
    asyncio.run(download_logo())
