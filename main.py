import asyncio
import hashlib
import os
import random

import aiosqlite
import openai
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from dotenv import dotenv_values
from openai.error import InvalidRequestError, RateLimitError
from pydub import AudioSegment
from requests.exceptions import ReadTimeout

CHECK_KEY = "check_key_lskJHjf32"
GET_ALL_USERS_COUNT = "get_all_users_count_lskJHjf32"

env = {
    **dotenv_values("/home/speech_to_text/.env.prod"),
    **dotenv_values(".env.dev"),  # override
}

API_KEYS_CHATGPT = [
    env["API_KEY_CHATGPT"],
    env["API_KEY_CHATGPT_1"],
    env["API_KEY_CHATGPT_2"],
    env["API_KEY_CHATGPT_3"],
    env["API_KEY_CHATGPT_4"],
    env["API_KEY_CHATGPT_5"],
    env["API_KEY_CHATGPT_6"],
    env["API_KEY_CHATGPT_7"],
    env["API_KEY_CHATGPT_8"],
    env["API_KEY_CHATGPT_9"],
    env["API_KEY_CHATGPT_10"],
    env["API_KEY_CHATGPT_11"],
    env["API_KEY_CHATGPT_12"],
]

bot = Bot(token=env["TG_BOT_TOKEN"])
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
db_link = env["DB_LINK"]

REKLAMA_MSG = [
    "🔥 Выбери валютный вклад под 12% годовых, сохрани и приумножь свой капитал.<a href='https://crypto-fans.club'>crypto-fans.club</a>",
    "🔥 Бот ChatGPT работает бесплатно, но Вы всегда можете <a href='https://pay.freekassa.ru/?m=32133&oa=300&currency=RUB&o=1329664&s=578c86c20802cc09803d7a0e1d97169c&lang=ru&userid=612063160&type=donate'>угостить чашечкой кофе ☕️</a> разработчиков - глядишь чего полезного изобретут🙏",
]


async def write_to_db(message):
    conn = await aiosqlite.connect(db_link)
    cursor = await conn.cursor()
    select_id = await cursor.execute(
        "SELECT id FROM user WHERE chat_id = ?", (str(message.chat.id),)
    )
    select_id = await select_id.fetchone()
    if select_id:
        try:
            await cursor.execute(
                "UPDATE user SET last_msg=?, last_login=? WHERE chat_id=?",
                (
                    message.text,
                    str(message.date),
                    str(message.chat.id),
                ),
            )
        except Exception as e:
            await conn.commit()
            await conn.close()
            await bot.send_message(
                612063160,
                f"Ошибка при добавлении (INSERT) данных в базе Пользователь: {message.chat.id}",
            )
    else:
        try:
            await cursor.execute(
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
        except Exception as e:
            await conn.commit()
            await conn.close()
            await bot.send_message(
                612063160,
                f"Ошибка при добавлении (INSERT) данных в базе Пользователь: {message.chat.id}",
            )
    await conn.commit()
    await conn.close()


def check_length(answer, list_of_answers):
    if len(answer) > 4090 and len(answer) < 409000:
        list_of_answers.append(answer[0:4090] + "...")
        check_length(answer[4091:], list_of_answers)
    else:
        list_of_answers.append(answer[0:])
        return list_of_answers


async def make_request(message, api_key_numb, last_msg):
    chance = random.choices((0, 1, 2, 3, 4))
    await bot.send_chat_action(message.chat.id, "typing")
    try:
        # добавляем сообщение в контекст
        messages = [
            {
                "role": "system",
                "content": "Твое имя Рагнар, ты викинг, ты пришел захватить мир. Тебе будут пистаь разные сообщения, вконце каждого своего ответа тебе нужно добавлять одно словое - апчихиризме!",
            }
        ]
        messages.append({"role": "user", "content": message.text})
        if storage.data.get(str(message.from_id)):
            if not storage.data.get(str(message.from_id)).get("messages"):
                storage.data.get(str(message.from_id))["messages"] = [
                    {
                        "role": "system",
                        "content": "Твое имя Рагнар, ты викинг, ты пришел захватить мир. Тебе будут пистаь разные сообщения, вконце каждого своего ответа тебе нужно добавлять одно словое - апчихиризме!",
                    }
                ]
            storage.data.get(str(message.from_id))["messages"].append(
                messages[0]
            )

        engine = "gpt-3.5-turbo"
        completion = await openai.ChatCompletion.acreate(
            model=engine,
            messages=storage.data.get(str(message.from_id))["messages"],
        )

        list_of_answers = check_length(
            completion.choices[0]["message"]["content"], []
        )
        await bot.send_chat_action(message.chat.id, "typing")
        if list_of_answers:
            for piece_of_answer in list_of_answers:
                await last_msg.edit_text(
                    piece_of_answer,
                )
                storage.data.get(str(message.from_id))["messages"].append(
                    {"role": "assistant", "content": piece_of_answer}
                )
            if chance == [1]:
                await message.answer(
                    random.choices(REKLAMA_MSG)[0],
                    disable_web_page_preview=True,
                    parse_mode="HTML",
                )
        else:
            await make_request(message, api_key_numb, last_msg)
    except RateLimitError:
        if api_key_numb < len(API_KEYS_CHATGPT) - 1:
            api_key_numb += 1
            openai.api_key = API_KEYS_CHATGPT[api_key_numb]
            await make_request(message, api_key_numb)
        else:
            if not key_end:
                await bot.send_message(
                    612063160,
                    f"Ключи закончились!!!",
                )
            key_end = True
            await message.answer(
                "ChatGPT в данный момент перегружен запросами, пожалуйста повторите свой запрос чуть позже.",
            )
    except ReadTimeout:
        await message.answer(
            "ChatGPT в данный момент перегружен запросами, пожалуйста повторите свой запрос чуть позже.",
        )
    except InvalidRequestError:
        await message.answer(
            "Максимальная длина контекста составляет около 3000 слов, ответ превысил длину контекста. Пожалуйста, повторите вопрос, либо перефразируйте его.",
        )


async def create_table():
    """Create table if not exists."""

    conn = await aiosqlite.connect(db_link)
    cursor = await conn.cursor()
    await cursor.executescript(
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
    await conn.commit()
    await conn.close()


@dp.message_handler(commands=["start"])
async def send_start(message: types.Message):
    # await create_table()
    text = """👇 отправь голосовое|send voice 👇"""
    await bot.send_chat_action(message.chat.id, "typing")
    last_msg = await message.answer(
        "<code>Сообщение принято. Ждем ответа...</code>", parse_mode="HTML"
    )
    await write_to_db(message)
    await last_msg.edit_text(text)


@dp.message_handler(commands=["help"])
async def send_start(message: types.Message):
    text = """Приветствую ✌

Скажите голосом свою речь и я переведу ее в текст.

"""
    await bot.send_chat_action(message.chat.id, "typing")
    last_msg = await message.answer(
        "<code>Сообщение принято. Ждем ответа...</code>", parse_mode="HTML"
    )
    await write_to_db(message)
    await last_msg.edit_text(text)


# @dp.message_handler(commands=["new"])
# async def send_start(message: types.Message):
#     text = """Контекст очищен"""
#     await bot.send_chat_action(message.chat.id, "typing")
#     last_msg = await message.answer(
#         "<code>Сообщение принято. Ждем ответа...</code>", parse_mode="HTML"
#     )
#     await write_to_db(message)
#     if not storage.data.get(str(message.from_id)).get("messages"):
#         storage.data.get(str(message.from_id))["messages"] = []
#     storage.data.get(str(message.from_id))["messages"].clear()
#     await last_msg.edit_text(text)


def md5sign(m, oa, secretWord1, currency, o):
    string = m + ":" + str(oa) + ":" + secretWord1 + ":" + currency + ":" + o
    return hashlib.md5(string.encode("utf-8")).hexdigest()


@dp.message_handler(commands=["donate"])
async def send_donate(message: types.Message):
    secretWord1 = env["secretWord1"]
    url = "https://pay.freekassa.ru/?"

    # m - ID Вашего магазина merchantId
    m = "32133"
    # Сумма платежа
    oa = "300"
    # Валюта платежа
    currency = "RUB"
    # Номер заказа
    o = str(message.message_id)
    # Подпись
    s = md5sign(m, oa, secretWord1, currency, o)
    lang = "ru"
    userid = str(message.from_user.id)
    type = "donate"
    params = f"m={m}&oa={oa}&currency={currency}&o={o}&s={s}&lang={lang}&us_userid={userid}&us_type={type}"

    await bot.send_chat_action(message.chat.id, "typing")
    last_msg = await message.answer(
        "<code>Сообщение принято. Ждем ответа...</code>", parse_mode="HTML"
    )

    inline_btn_1 = types.InlineKeyboardButton(
        text="Угостить ☕️", url=url + params
    )
    keyboard = types.InlineKeyboardMarkup(
        row_width=1,
    )
    keyboard.add(inline_btn_1)
    text = """Бот ChatGPT работает бесплатно, но Вы всегда можете угостить чашечкой кофе ☕️ разработчиков - глядишь чего полезного изобретут🙏

ChatGPT bot is free, but you can always buy a cup of coffee ☕️ developers - see what they invent🙏
    """
    await last_msg.edit_text(text=text, reply_markup=keyboard)


async def check_key(message):
    key = message.text[19:]
    openai.api_key = key
    try:
        engine = "gpt-3.5-turbo"
        # engine = "gpt-4"
        await openai.ChatCompletion.acreate(
            model=engine, messages=[{"role": "user", "content": message.text}]
        )
        await message.answer(f"Ключ {key} работает.")
    except:
        await message.answer(f"Ключ {key} НЕ рабочий либо истек.")


async def get_all_users_count(message):   
    conn = await aiosqlite.connect(db_link)
    cursor = await conn.cursor()
    count = await cursor.execute(
       """SELECT COUNT("id") FROM user"""
    )
    count = await cursor.fetchone()
    await conn.commit()
    await conn.close()
    await message.answer(f"Всего пользователей: {count[0]}")


@dp.message_handler(content_types=["text"])
async def send_msg_to_chatgpt(message: types.Message):
    if CHECK_KEY == message.text[:19]:
        await check_key(message)
        return
    if GET_ALL_USERS_COUNT == message.text:
        await get_all_users_count(message)
        return
    api_key_numb = 0
    openai.api_key = random.choice(API_KEYS_CHATGPT)
    last_msg = await message.answer(
        "<code>Я принимаю только голосовые запросы, и перевожу их в текст.</code>", parse_mode="HTML"
    )
    await write_to_db(message)


async def delete_temporary_files(*files):
    # await asyncio.sleep(10)
    loop = asyncio.get_running_loop()
    for file in files:
        try:
            await loop.run_in_executor(None, os.remove, file)
        except Exception as e:
            print(e)


@dp.message_handler(content_types=["voice"])
async def send_transcription(message: types.Message):
    await bot.send_chat_action(message.chat.id, "typing")
    chance = random.choices((0, 1, 2, 3, 4))
    if chance == [1]:
                await message.answer(
                    random.choices(REKLAMA_MSG)[0],
                    disable_web_page_preview=True,
                    parse_mode="HTML",
                )
    last_msg = await message.answer(
        "<code>Сообщение принято. Ждем ответа...</code>", parse_mode="HTML"
    )
    try:
        file_id = message.voice.file_id
        voice_file = await bot.get_file(file_id)
        voice_path = await voice_file.download()

        audio = AudioSegment.from_file(voice_path.name)
        mp3_path = f"voice/voice{message.voice.file_id}.mp3"
        audio.export(mp3_path, format="mp3")

        audio_file = open(mp3_path, "rb")
        transcript = await openai.Audio.atranscribe("whisper-1", audio_file)
        await bot.send_chat_action(message.chat.id, "typing")
        if transcript["text"]:
            await last_msg.edit_text(
                "<code>Вы сказали:</code>", parse_mode="HTML"
            )
            await message.answer(transcript["text"])
        else:
            await last_msg.edit_text("К сожалению, не удалось распознать речь")
    finally:
        audio_file.close()
        voice_path.close()
        await delete_temporary_files(voice_path.name, mp3_path)


if __name__ == "__main__":
    openai.api_key = API_KEYS_CHATGPT[0]
    executor.start_polling(dp, skip_updates=True)
