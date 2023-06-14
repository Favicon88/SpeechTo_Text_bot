# ChatGPT_telegram_bot

Telegram bot with ChatGPT model by OpenAI (Example running here https://t.me/ChatGPT_ForTelegramBot)

How to run:

Clone repository:

```
git clone git@github.com:ViktorAllayarov/ChatGPT_telegram_bot.git
cd ChatGPT_telegram_bot
```

Create and activate environment:

```
python3 -m venv env
or
py -3.10 -m venv env
```

If you have Linux/macOS

```
source env/bin/activate
```

If you have windows

```
source env/scripts/activate
python -m pip install --upgrade pip
```

Install requirements in requirements.txt:

```
pip install -r requirements.txt
```

Create file '.env.prod' in main repository then provide API_KEY_CHATGPT and TG_BOT_TOKEN:

```
# in .env.prod file
API_KEY_CHATGPT=
TG_BOT_TOKEN=
DB_LINK=db.db
```

Run project:

```
python main.py
```

команды для сервера

```
systemctl status speech_to_text
systemctl restart speech_to_text
```
