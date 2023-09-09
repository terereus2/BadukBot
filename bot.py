import sqlite3
import time
import os
import logging
import telebot
import asyncio
import threading
from telebot import types

with open('token.txt', 'r') as token_file:
    TOKEN = token_file.read().strip()

bot = telebot.TeleBot(TOKEN)


# обработчик команд
@bot.message_handler(commands=['start'])
def all_commands(message):
    list_command = 'List of commands:\n' \
                   '/problem - Daily problem\n'
    bot.send_message(message.chat.id, list_command)


# обработчик команд
@bot.message_handler(commands=['problem'])
def button_daily_problem(message):
    markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_replay = types.KeyboardButton(text='Daily problem')
    markup_replay.add(btn_replay)
    bot.send_message(message.chat.id, 'A new problem every day', reply_markup=markup_replay)


# обработчик входящего сообщения
@bot.message_handler(content_types=['text'])
def daily_problem(message):
    folder_path = 'G:\programming\Bot\problems'
    file_list = sorted(os.listdir(folder_path), key=lambda x: int(x.rstrip('.jpg')))
    current_unix_time = int(time.time())
    five = current_unix_time // 300
    remainder = five % (len(file_list) + 1)

    if message.text == 'Daily problem':
        photo = open(f'problems/{file_list[remainder]}', 'rb')
        bot.send_photo(message.chat.id, photo)

        photo.close()
        markup_replay = types.InlineKeyboardMarkup()
        btn_replay = types.InlineKeyboardButton(text="Solution", callback_data=remainder)
        markup_replay.add(btn_replay)
        bot.send_message(message.chat.id, 'Daily problem', reply_markup=markup_replay)


# ответ на задачу
@bot.callback_query_handler(func=lambda call: call.data)
def answer(call):
    folder_path = 'G:\programming\Bot\solutions'
    file_list = sorted(os.listdir(folder_path), key=lambda x: int(x.rstrip('.jpg')))
    photo = open(f'solutions/{file_list[int(call.data)]}', 'rb')
    bot.send_photo(call.message.chat.id, photo)
    photo.close()




# создание таблицы в базе данных
conn = sqlite3.connect('games.db')
cur = conn.cursor()
cur.execute(""" CREATE TABLE IF NOT EXISTS users (
   user_id INTEGER PRIMARY KEY,
   user_name TEXT,
   chat_id INTEGER,
   message_id INTEGER,
   file       TEXT
);
""")
conn.close()



# получение файла sgf от юзера
@bot.message_handler(content_types=['document'])
def get_file_svg(message):
    if (message.document.mime_type == 'application/x-go-sgf'):
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_name = message.document.file_id[-8:] +'_' + message.document.file_name
        chat_id = message.chat.id


        records_path = f'G:\programming\Bot\GoGameRecords\{file_name}'
        print(message.document)
        print(type(file_name))
        print(file_name)


        # запись полученого файла в папку GoGameRecords
        with open(records_path, 'wb') as new_file:
            new_file.write(downloaded_file)
            bot.reply_to(message, f'файл {file_name} \n <b>успешно отправлен</b>', parse_mode='HTML')


        # сохранение данных в базу данных
        conec = sqlite3.connect('games.db')
        cursor = conec.cursor()

        user_name = message.chat.first_name
        chat_id = message.chat.id
        message_id = message.message_id
        file = file_name
        cursor.execute('INSERT OR IGNORE INTO users(user_name, chat_id, message_id, file) VALUES (?,?,?,?)',
                       (user_name, chat_id, message_id, file))
        conec.commit()
        conec.close()

        '''# получение данных с базы данных
        connection = sqlite3.connect('games.db')
        cur = connection.cursor()
        query = "SELECT * FROM users WHERE file=?"
        print(query)
        cur.execute(query, (file_name,))
        all_records = cur.fetchall()
        print(all_records)'''
        rec_list_path = f'G:\programming\Bot\GoGamesRecords_SendUsers'

        def send_file_to_user():
            while True:
                list_games = os.listdir(rec_list_path)
                if file_name in list_games:
                    rec_path = f'G:\programming\Bot\GoGamesRecords_SendUsers\{file_name}'
                    with open(rec_path, 'rb') as fa:
                        bot.send_document(chat_id, fa)
                    os.remove(rec_path)
                    list_games.clear()
                else:
                    time.sleep(20)

        threading.Thread(target=send_file_to_user).start()

    else:
        bot.reply_to(message, 'файл не доставлен, нужно отправлять в формате sgf')

while True:
    logging.basicConfig(level=logging.INFO, filename="py_log.log", filemode="w",
                        format="%(asctime)s %(levelname)s %(message)s")
    try:

        bot.polling(none_stop=True)

    except Exception as e:
        logging.error(e)


