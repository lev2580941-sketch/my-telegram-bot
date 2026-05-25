import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import aiohttp
from flask import Flask
from posts import POSTS

# ===== ТВОИ ДАННЫЕ =====
BOT_TOKEN = "8760752864:AAEkawGTRxWfMF8rSOq1E5t8Wyy8kF3DYlE"
CHANNEL_ID = "@prestige_social_work"
STATE_FILE = "state.txt"

# Flask приложение (для Render)
app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot is running!'


class SmartBot:
    def __init__(self):
        self.bot = Bot(token=BOT_TOKEN)
        self.scheduler = AsyncIOScheduler()
        self.dp = Dispatcher()
        
        # Обработчик команды /start
        @self.dp.message(Command("start"))
        async def cmd_start(message: types.Message):
            await message.answer("Привет! Я бот для автопостинга. Посты публикуются по расписанию!")
    
    def load_state(self):
        """Читаем, сколько постов уже опубликовано"""
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                return int(f.read().strip())
        return 0
    
    def save_state(self, index):
        """Сохраняем, сколько постов опубликовано"""
        with open(STATE_FILE, 'w') as f:
            f.write(str(index))
    
    async def make_image(self, prompt, filename):
        """Генерация изображения"""
        # Ваш код генерации изображения
        pass
    
    async def publish_post(self):
        """Публикация поста"""
        post_index = self.load_state()
        
        if post_index >= len(POSTS):
            print("✅ Все посты опубликованы!")
            return
        
        post = POSTS[post_index]
        
        try:
            if post.get('image'):
                # Публикуем с изображением
                photo = FSInputFile(post['image'])
                await self.bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=photo,
                    caption=post['text']
                )
            else:
                # Публикуем только текст
                await self.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=post['text']
                )
            
            self.save_state(post_index + 1)
            print(f"✅ Пост #{post_index + 1} опубликован! Всего: {post_index + 1}/{len(POSTS)}")
            
        except Exception as e:
            print(f"❌ Ошибка публикации: {e}")
    
    def start_schedule(self):
        self.scheduler.add_job(
            self.publish_post,
            'cron',
            hour=10,
            minute=0
        )
        self.scheduler.start()
        print("⏰ Планировщик запущен. Посты в 10:00.")
    
    async def run(self):
        print("🤖 Умный бот запущен!")
        print(f"📊 Уже опубликовано: {self.load_state()}/{len(POSTS)}")
        
        # Если сегодня ещё не публиковали — публикуем сразу
        # Если уже публиковали — ждём 10:00
        
        self.start_schedule()
        
        # Запускаем обработчик сообщений в фоне (для команды /start)
        asyncio.create_task(self.dp.start_polling(self.bot))
        
        while True:
            await asyncio.sleep(3600)


if __name__ == "__main__":
    bot = SmartBot()
    
    async def main():
        # Запускаем Flask в фоновом потоке
        from threading import Thread
        flask_thread = Thread(target=lambda: app.run(host='0.0.0.0', port=10000))
        flask_thread.start()
        
        # Запускаем бота
        await bot.run()
    
    asyncio.run(main())
