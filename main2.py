from dotenv import dotenv_values
import random
import sqlite3
import telebot
from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
)
from requests.exceptions import ReadTimeout
import json
from urllib.parse import urlparse
import yt_dlp
import datetime
import re
import os
import requests
import hashlib


env = {
    **dotenv_values("/home/justsave_spotify_bot/.env.prod"),
    **dotenv_values(".env.prod"),
    **dotenv_values(".env.dev"),  # override
}

bot = telebot.TeleBot(env["TG_BOT_TOKEN"])
db_link = env["DB_LINK"]
max_filesize = int(env["max_filesize"])
MY_ID = int(env["MY_ID"])
last_edited = {}

REKLAMA_MSG = [
    "🔥 Валютный вклад для россиян (до 12% годовых) <a href='https://crypto-fans.club'>crypto-fans.club</a>",
    "🔥 Если думаешь купить или продать криптовалюту, рекомендую <a href='https://cutt.ly/D7rsbVG'>Bybit</a>",
    "🔥 Если думаешь купить или продать криптовалюту, рекомендую <a href='https://cutt.ly/87rsjAV'>Binance</a>",
]

# Для подключения бота к локальному серверу
# bot.log_out()
# telebot.apihelper.API_URL = "http://localhost:4200/bot{0}/{1}"
telebot.apihelper.READ_TIMEOUT = 5 * 60

inline_btn_1 = InlineKeyboardButton(
    text="Скачать Видео", callback_data="video"
)
inline_btn_2 = InlineKeyboardButton(
    text="Скачать Аудио", callback_data="audio"
)
keyboard = InlineKeyboardMarkup(
    keyboard=[
        [inline_btn_1, inline_btn_2],
    ],
    row_width=1,
)


def write_to_db(message):
    create_table()
    conn = sqlite3.connect(db_link)
    cursor = conn.cursor()
    select_id = cursor.execute(
        "SELECT id FROM user WHERE chat_id = ?", (str(message.chat.id),)
    )
    select_id = select_id.fetchone()
    if select_id:
        try:
            cursor.execute(
                "UPDATE user SET last_msg=?, last_login=? WHERE chat_id=?",
                (
                    message.text,
                    str(message.date),
                    str(message.chat.id),
                ),
            )
        except:
            conn.commit()
            conn.close()
            bot.send_message(
                MY_ID,
                f"Ошибка при добавлении (INSERT) данных в базе Пользователь: {message.chat.id}",
            )
    else:
        try:
            cursor.execute(
                "INSERT INTO user (chat_id, last_login, username, first_name, last_name, last_msg) VALUES (?,?,?,?,?,?)",
                (
                    str(message.chat.id),
                    str(message.date),
                    message.chat.username if message.chat.username else "-",
                    message.chat.first_name
                    if message.chat.first_name
                    else "-",
                    message.chat.last_name if message.chat.last_name else "-",
                    message.text,
                ),
            )
        except:
            conn.commit()
            conn.close()
            bot.send_message(
                MY_ID,
                f"Ошибка при добавлении (INSERT) данных в базе Пользователь: {message.chat.id}",
            )
    conn.commit()
    conn.close()


def create_table():
    """Create table if not exists."""

    conn = sqlite3.connect(db_link)
    cursor = conn.cursor()
    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS user(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT,
            last_login TEXT,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            last_msg TEXT
        );

        CREATE TABLE IF NOT EXISTS donate(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount TEXT,
            date TEXT,
            FOREIGN KEY(user_id) REFERENCES user(id)
        );

        CREATE TABLE IF NOT EXISTS premium(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount TEXT,
            date TEXT,
            FOREIGN KEY(user_id) REFERENCES user(id)
        );
        """
    )
    conn.commit()
    conn.close()


def insta_url_validation(url):
    insta_regex = (
        r"(https?://)?(www\.)?"
        "(open.spotify)\.(com)/"
        "([^&=%\?]{11})"
    )

    insta_regex_match = re.match(insta_regex, url)
    if insta_regex_match:
        return insta_regex_match

    return insta_regex_match


def download_video(message, url, audio=False):
    def progress(d):
        if d["status"] == "downloading":
            try:
                update = False

                if last_edited.get(f"{message.chat.id}-{msg.message_id}"):
                    if (
                        datetime.datetime.now()
                        - last_edited[f"{message.chat.id}-{msg.message_id}"]
                    ).total_seconds() >= 3:
                        update = True
                else:
                    update = True

                if update:
                    perc = round(
                        d["downloaded_bytes"] * 100 / d["total_bytes"]
                    )
                    bot.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=msg.message_id,
                        text=f"Скачивание {d['info_dict']['title']}\n\n{perc}%",
                    )
                    last_edited[
                        f"{message.chat.id}-{msg.message_id}"
                    ] = datetime.datetime.now()
            except Exception as e:
                print(e)

    msg = bot.reply_to(message, "Скачивание...")
    with yt_dlp.YoutubeDL(
        {
            # "format": "mp4",
            "outtmpl": "outputs/%(title)s.%(ext)s",
            "progress_hooks": [progress],
            'cookiefile': 'cookies.txt',
            "postprocessors": [
                {  # Extract audio using ffmpeg
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                }
            ]
            if audio
            else [],
            "max_filesize": max_filesize,
        }
    ) as ydl:
        try:
            info = ydl.extract_info(url, download=True)

            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=msg.message_id,
                text="Отправка файла в Telegram...",
            )
            try:
                if audio:
                    bot.send_audio(
                        message.chat.id,
                        open(
                            info["requested_downloads"][0]["filepath"],
                            "rb",
                        ),
                        timeout=60,
                    )
                else:
                    bot.send_video(
                        message.chat.id,
                        open(
                            info["requested_downloads"][0]["filepath"],
                            "rb",
                        ),
                        timeout=60,
                        supports_streaming=True,
                    )
                bot.delete_message(message.chat.id, msg.message_id)
            except Exception as e:
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=msg.message_id,
                    text=f"Не удалось отправить файл, удостоверьтесь что файл поддерживается Telegram и не превышает *{round(max_filesize / 1000000)}МБ*",
                    parse_mode="MARKDOWN",
                )
            else:
                for file in info["requested_downloads"]:
                    os.remove(file["filepath"])
        except Exception as e:
            bot.send_message(MY_ID, e)
            if isinstance(e, yt_dlp.utils.DownloadError):
                bot.edit_message_text(
                    "Неверный URL", message.chat.id, msg.message_id
                )
            else:
                bot.edit_message_text(
                    "Произошла ошибка при скачивании Вашего видео",
                    message.chat.id,
                    msg.message_id,
                )


@bot.message_handler(commands=["start", "help"])
def send_start(message):
    if message.text == "/start":
        text = """🤖 This bot can download videos and audios from Spotify.
Send the link, choose the format and get your file.

🤖 Этот бот может скачивать видео и аудио из ВК.
Отправь ссылку, выбери формат и получи свой файл.

/help - О боте

👇Отправь ссылку и получи свой файл👇
"""
    elif message.text == "/help":
        text = """🔥 JustSaveIt_Spotify может скачать для вас видео ролики и аудио из Spotify.

Как пользоваться:
  1. Зайдите в Spotify.
  2. Выберите интересное для вас видео.
  3. Скопируйте ссылку на видео.
  4. Отправьте нашему боту и получите ваш файл!
"""
    write_to_db(message)
    bot.send_message(message.chat.id, text)


@bot.callback_query_handler(func=lambda call: call.data == "video")
def download_video_command(call: CallbackQuery):
    text = call.message.reply_to_message.html_text
    if not text:
        bot.reply_to(
            call.message,
            "Invalid usage, use `/download url`",
            parse_mode="MARKDOWN",
        )
        return

    download_video(call.message.reply_to_message, text)


@bot.callback_query_handler(func=lambda call: call.data == "audio")
def download_audio_command(call: CallbackQuery):
    text = call.message.reply_to_message.html_text
    if not text:
        bot.reply_to(
            call.message,
            "Invalid usage, use `/audio url`",
            parse_mode="MARKDOWN",
        )
        return

    download_video(call.message.reply_to_message, text, True)


def md5sign(m, oa, secretWord1, currency, o):
    string = m + ':' + str(oa) + ':' + secretWord1 + ':' + currency + ':' + o
    return hashlib.md5(string.encode("utf-8")).hexdigest()



@bot.callback_query_handler(func=lambda call: call.data == "senddonate")
def download_audio_command(call: CallbackQuery):
    secretWord1 = "Jou^VC4buX_[1x?"
    url = "https://pay.freekassa.ru/"

    # m - ID Вашего магазина merchantId
    m = "32133"
    # Сумма платежа
    oa = "200"
    # Валюта платежа
    currency = "RUB"
    # Номер заказа
    o = str(call.message.id)
    # Подпись
    s = md5sign(m, oa, secretWord1, currency, o)
    lang = "ru"
    userid = str(call.from_user.id)
    type = "donate"

    params = {
        "m": m,
        "oa": oa,
        "currency": currency,
        "o": o,
        "s": s,
        "lang": lang,
        "userid": userid,
    }
    requests.get(url, params=params)


@bot.message_handler(commands=["donate"])
def send_donate(message):
    secretWord1 = "Jou^VC4buX_[1x?"
    url = "https://pay.freekassa.ru/?"

    # m - ID Вашего магазина merchantId
    m = "32133"
    # Сумма платежа
    oa = "200"
    # Валюта платежа
    currency = "RUB"
    # Номер заказа
    o = str(message.id)
    # Подпись
    s = md5sign(m, oa, secretWord1, currency, o)
    lang = "ru"
    userid = str(message.from_user.id)
    type = "donate"
    params = f"m={m}&oa={oa}&currency={currency}&o={o}&s={s}&lang={lang}&userid={userid}&type={type}"

    inline_btn_1 = InlineKeyboardButton(
    text="Угостить ☕️", url=url + params
    )
    keyboard = InlineKeyboardMarkup(
        keyboard=[
            [inline_btn_1],
        ],
        row_width=1,
    )
    text = """Бот ChatGPT работает бесплатно, но Вы всегда можете угостить чашечкой кофе ☕️ разработчиков - глядишь чего полезного изобретут🙏

ChatGPT bot is free, but you can always buy a cup of coffee ☕️ developers - see what they invent🙏
    """
    bot.reply_to(
                message,
                text,
                reply_markup=keyboard,
            )


@bot.message_handler(content_types=["text"])
def download_command(message):
    write_to_db(message)
    if not message.text:
        bot.reply_to(
            message, "Неверный текст, отправь ссылку", parse_mode="MARKDOWN"
        )
        return
    url = (
        message.text
        if message.text
        else message.caption
        if message.caption
        else None
    )
    url_info = urlparse(url)
    if url_info.scheme:
        if url_info.netloc in [
            "www.spotify.com",
            "spotify.com",
            "open.spotify.com",
        ]:
            if not insta_url_validation(url):
                bot.reply_to(message, "Некорректная ссылка")
                return

            bot.reply_to(
                message,
                "Выберите формат",
                reply_markup=keyboard,
            )
        else:
            bot.reply_to(message, "Неверный URL")
    else:
        bot.reply_to(message, "Неверный URL")


if __name__ == "__main__":
    target = bot.infinity_polling()
