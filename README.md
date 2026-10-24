# ShahSAT Telegram bot

aiogram 3 + SQLite. Foydalanuvchi menyusi, kursga yozilish (FSM), mini-CRM admin panel (`/admin`).

## Lokal ishga tushirish (Windows)

1. `.env` faylini to'ldiring: `BOT_TOKEN` (@BotFather) va `ADMIN_IDS` (o'z Telegram ID'ingiz — @userinfobot).
2. Ishga tushirish:
   ```
   .venv\Scripts\python.exe bot.py
   ```
   (venv yo'q bo'lsa: Python 3.12 bilan `python -m venv .venv` va `.venv\Scripts\pip install -r requirements.txt`.
   Python 3.15 hozircha aiogram bilan ishlamaydi.)

Logda `Bot ishga tushdi: @...` chiqsa — tayyor. Botga `/start`, admin panel — `/admin`.

## Railway'ga joylash

1. Kodni GitHub'ga yuklang (`.env` va `*.db` `.gitignore`da).
2. Railway → New Project → Deploy from GitHub repo.
3. Servisga Volume qo'shing, mount path: `/data`.
4. Variables: `BOT_TOKEN`, `ADMIN_IDS`, `ADMIN_CHAT_ID` (ixtiyoriy), `DB_PATH=/data/bot.db`, `TZ=Asia/Tashkent`.
5. Start buyrug'i `railway.json`da (`python bot.py`, restart: ON_FAILURE).

## Birinchi sozlash (bot ichida, /admin)

- 🏫 Markaz ma'lumotlari — salomlashish, manzil, lokatsiya, aloqa, ish vaqti, markaz haqida.
- 📚 Kurslar / 👨‍🏫 Mentorlar / ❓ FAQ — qo'shish, tahrirlash, faol/nofaol.
- 🔗 Manbalar — har bir reklama joyi uchun `t.me/<bot>?start=<kod>` havolasi.

Ariza kelganda kartochka adminlarga (yoki `ADMIN_CHAT_ID` guruhiga) status tugmalari bilan keladi.
Har kuni 03:00 (Toshkent) da baza zaxirasi bosh adminga yuboriladi; xatolar ham bosh adminga boradi.
