import asyncio
import os
from aiogram import Bot
from aiogram.types import FSInputFile
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import aiohttp
from posts import POSTS
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot is running!'

# ===== ТВОИ ДАННЫЕ =====
BOT_TOKEN = "8760752864:AAEkawGTRxWfMF8rSOq1E5t8Wyy8kF3DYlE"
...
CHANNEL_ID = "@prestige_social_work"

STATE_FILE = "state.txt"

class SmartBot:
    def __init__(self):
        self.bot = Bot(token=BOT_TOKEN)
        self.scheduler = AsyncIOScheduler()  # ← один раз
        
        from aiogram import Dispatcher, types
        self.dp = Dispatcher()
        
        @self.dp.message(commands=['start'])
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
        """Генерация картинки через API"""
        print(f"🎨 Создаю картинку...")
        
        encoded_prompt = prompt.replace(" ", "%20")
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=512&nologo=true"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status == 200:
                    img_path = f"images/{filename}"
                    with open(img_path, 'wb') as f:
                        f.write(await response.read())
                    print(f"✅ Картинка сохранена")
                    return img_path
                else:
                    print(f"⚠️ Ошибка API")
                    return None
        
    async def publish_post(self):
        """Публикуем пост"""
        post_index = self.load_state()
        
        if post_index >= len(POSTS):
            print("🎉 Все посты уже опубликованы!")
            return
            
        post = POSTS[post_index]
        print(f"\n📤 Публикация поста #{post_index + 1}")
        print(f"📝 {post['text'][:50]}...")
        
        img_filename = f"post_{post_index}.png"
        img_path = await self.make_image(post["image"], img_filename)
        
        if img_path:
            photo = FSInputFile(img_path)
            await self.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=photo,
                caption=post["text"]
            )
        else:
            await self.bot.send_message(
                chat_id=CHANNEL_ID,
                text=post["text"]
            )
            
        # Сохраняем, что пост опубликован
        self.save_state(post_index + 1)
        print(f"✅ Пост #{post_index + 1} опубликован! Всего: {post_index + 1}/{len(POSTS)}")
        
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
    
    # Запускаем бота в фоновой задаче asyncio
    asyncio.create_task(bot.run())
    
    # Запускаем Flask (держит порт открытым)
    app.run(host='0.0.0.0', port=10000)
