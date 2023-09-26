# -*- coding: utf-8 -*-
"""
Created on Wed Jul 12 17:38:52 2023

@author: 1
"""
import telebot
from telebot import types
from telebot.types import CallbackQuery, ReplyKeyboardRemove
import sqlite3
import ast
import matplotlib.pyplot as plt
from random import randint
import os
import traceback
import matplotlib
import datetime
import threading


matplotlib.use('agg')

abandoned = []
token = '6108209005:AAEmhjLXyzgw8KsaBTb0LSkaEPKpzBY6LHA'
bot = telebot.TeleBot(token)

def starting_point(message): #рост
    bot.send_message(message.chat.id,
                        '✍️ Введите ваш рост (в сантиметрах):')   
    
    bot.register_next_step_handler(message, get_height, 'height')

def add_starting_points(message, col, next_func, prev_func):
    conn = sqlite3.connect('db/docdb.db', check_same_thread=False, timeout=3)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE user_id = ?",
                   (str(message.chat.id),))
    
    res = cursor.fetchone()

    try:
        d = message.text
        d = d.replace(',', '.')
        d = d.replace(' ', '') 
        d = float(d)
        if col == 'height':
            index = 4
            txt = '(рост)'
        if col == 'weight':
            index = 2
            txt = '(вес)'
        if col == 'length_bedr':
            index = 6
            txt = '(обхват бедра)'
        
        if col == 'length_tal':
            index = 3
            txt = '(обхват талии)'
        
        if col == 'length_stom':
            index = 5
            txt = '(обхват живота)'

        if res == None or res[index] == None:
            data = [message.text]
            cursor.execute(f'UPDATE users SET {col} = ? WHERE user_id = ?',
                               (str(data), message.chat.id, ))
                
            conn.commit()
           
        else:
            data = ast.literal_eval(str(res[index]))
            data.append(message.text)
            cursor.execute(f'UPDATE users SET {col} = ? WHERE user_id = ?',
                               (str(data), message.chat.id, ))
            conn.commit()
        
        
        cursor.execute("SELECT * FROM administrators")
        
        resadm = cursor.fetchall()
        for i in resadm[0]:
            try:
                bot.send_message(i,
                                f'🆕 Пациент {res[1]} отправил данные {txt}')
            except:
                bot.send_message(i,
                                f'🆕 Новый пользователь отправил данные {txt}')
            
        conn.close()
        buildmenu(message) if next_func == None else bot.register_next_step_handler(message, next_func, None)
        
        
        
    except telebot.apihelper.ApiTelegramException:
        traceback.print_exc()

    except:
        traceback.print_exc()
        bot.send_message(message.chat.id,
                        'Пожалуйста, введите число, например: 51.4')
        
        bot.register_next_step_handler(message, prev_func, col)


def get_stom(message, col):
    bot.send_message(message.chat.id,
                        '✅ Стартовая точка записана!')
    add_starting_points(message, 'length_stom', None, get_tal)


def get_tal(message, col):
    bot.send_message(message.chat.id,
                        '✍️ Введите свой обхват живота (на уровне пупка, в см):')
    add_starting_points(message, 'length_tal', get_stom, get_tal)


def get_bedr(message, col):
    bot.send_message(message.chat.id,
                        '✍️ Введите свой обхват талии (самая тонкая часть, в см):')
    add_starting_points(message, 'length_bedr', get_tal, get_weight)


def get_weight(message, col):
    bot.send_message(message.chat.id,
                        '✍️ Введите свой обхват бедра (в см):')
    add_starting_points(message, 'weight', get_bedr, get_height)

def get_height(message, col):
    add_starting_points(message, 'height', get_weight, None)
    bot.send_message(message.chat.id,
                        '✍️ Введите свой вес (в кг):')


def add_table_values(message):
    name = message.text
    user_id = message.chat.id
    endtime = datetime.datetime.now() + datetime.timedelta(days=30)
    delta = endtime - datetime.datetime.now()
    reminder_timer = threading.Timer(delta.total_seconds(), send_reminder, [user_id])
    reminder_timer.start()
    conn = sqlite3.connect('db/docdb.db', check_same_thread=False, timeout=15)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id, ))

    res = cursor.fetchall()

    cursor.execute('INSERT INTO users (user_id, name, end_time) VALUES (?, ?, ?)', (user_id, name, endtime))
    conn.commit()

    conn.close()

    if len(res) != 0:
        buildmenu(message)
    else:

        starting_point(message)
    

def send_reminder(chat_id):
    conn = sqlite3.connect('db/docdb.db', check_same_thread=False, timeout=3)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM administrators")
    
    resadm = cursor.fetchall()

    cursor.execute("SELECT name FROM users WHERE user_id = ?", (chat_id,))
    name = cursor.fetchone()
    conn.close()

    markup = types.InlineKeyboardMarkup(row_width=1)
    usr = types.InlineKeyboardButton(text=f'Да', callback_data=f'kill|{chat_id}')
    markup.row(usr)
    usr = types.InlineKeyboardButton(text=f'Нет', callback_data=f'menu')
    markup.row(usr)
    
    for i in resadm[0]:        
        bot.send_message(i, f'У пациента {name} закончился курс в 30 дней, удалить его?', reply_markup=markup)


    

def get_login(message):
    conn = sqlite3.connect('db/docdb.db', check_same_thread=False, timeout=15)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?',
                   (message.chat.id,))
    res = cursor.fetchall()
    conn.close()
    if len(res):
        buildmenu(message)
    else:
        bot.send_message(message.chat.id,
                        'Введите имя и фамилию:')
        bot.register_next_step_handler(message, add_table_values)
    

def build_admin_menu(message):
    conn = sqlite3.connect('db/docdb.db', check_same_thread=False, timeout=3)
    cursor = conn.cursor()
    
    
    
    cursor.execute("SELECT * FROM users")
    
    users = cursor.fetchall()
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    usr = types.InlineKeyboardButton(text=f'Общая рассылка', callback_data=f'rassilka')
    markup.row(usr)
    usr = types.InlineKeyboardButton(text=f'Удалить пациента', callback_data=f'ban_hammer')
    markup.row(usr)
    for u in users:
        usr = types.InlineKeyboardButton(text=f'{u[1]}', callback_data=f'check|{u[0]}')
        markup.row(usr)
        
    
    try:
        bot.edit_message_text('Выберите пользователя для проверки:', message.chat.id, message.message_id,
                         reply_markup=markup)
    except:
        bot.send_message(message.chat.id, 'Выберите пользователя для проверки:',
                         reply_markup=markup)
        

    
    conn.close()


@bot.message_handler(commands=['start'])
def start_message(message):
    conn = sqlite3.connect('db/docdb.db', check_same_thread=False, timeout=3)
    cursor = conn.cursor()
    
    
    
    cursor.execute("SELECT id FROM administrators WHERE id = ?", (message.chat.id,))
    
    name = cursor.fetchone()
    
    conn.close()
    if name != None:
        build_admin_menu(message)
    else:
        msg = bot.send_message(message.chat.id, 'Здравствуйте... (описание)')
        get_login(msg)
    
    

def buildmenu(message):

    conn = sqlite3.connect('db/docdb.db', check_same_thread=False, timeout=3)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM administrators")
    
    resadm = cursor.fetchall()
    
    conn.close() 

    flg = False
    for user in resadm:
        if str(user[0]) == str(message.chat.id):
            flg = True
            break

    if not flg:

        markup = types.InlineKeyboardMarkup(row_width=1)
        stats = types.InlineKeyboardButton(text='📊 Получить статистику', callback_data='show_stats')
        markup.row(stats)
        data = types.InlineKeyboardButton(text='✍️ Добавить данные', callback_data='add_stats')
        markup.row(data)
        tips = types.InlineKeyboardButton(text='❌ Удалить данные', callback_data='delete_stats')
        markup.row(tips)
        tips = types.InlineKeyboardButton(text='📝 Написать доктору', callback_data='tip')
        markup.row(tips)
        
        conn = sqlite3.connect('db/docdb.db', check_same_thread=False, timeout=3)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM users WHERE user_id = ?",
                    (str(message.chat.id),))
        
        res = cursor.fetchone()
        conn.close()

        try:
            bot.edit_message_text(f'🏛 Рады видеть вас, {res[0]}!\nВыберите действие:', message.chat.id, message.message_id, protect_content=True, 
                            reply_markup=markup)
        except:
            bot.send_message(message.chat.id, f'🏛 Рады видеть вас, {res[0]}!\nВыберите действие:', protect_content=True,
                            reply_markup=markup)
        
    else:
        build_admin_menu(message)


def build_stats_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    data = types.InlineKeyboardButton(text='🍬 Вес', callback_data=f'get|weight')
    markup.row(data)

    stats = types.InlineKeyboardButton(text='🍬 Окружность бедер', callback_data=f'get|length_bedr')
    markup.row(stats)

    stats = types.InlineKeyboardButton(text='🍬 Окружность талии (самая тонкая часть)', callback_data=f'get|length_tal')
    markup.row(stats)
    
    stats = types.InlineKeyboardButton(text='🍬 Окружность живота (на уровне пупка)', callback_data=f'get|length_stom')
    markup.row(stats)

    stats = types.InlineKeyboardButton(text='↩️ Назад', callback_data='menu')
    markup.row(stats)
    
    try:
        bot.edit_message_text('🏛 Выберите статистику:', message.chat.id, message.message_id,
                             reply_markup=markup)
    except:
        bot.send_message(message.chat.id, '🏛 Выберете статистику:',
                            reply_markup=markup)



def build_stats_menu_for_user(message, user_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    data = types.InlineKeyboardButton(text='🍬 Вес', callback_data=f'data|weight|{user_id}')
    markup.row(data)

    stats = types.InlineKeyboardButton(text='🍬 Окружность бедер', callback_data=f'data|length_bedr|{user_id}')
    markup.row(stats)

    stats = types.InlineKeyboardButton(text='🍬 Окружность талии (самая тонкая часть)', callback_data=f'data|length_tal|{user_id}')
    markup.row(stats)
    
    stats = types.InlineKeyboardButton(text='🍬 Окружность живота (на уровне пупка)', callback_data=f'data|length_stom|{user_id}')
    markup.row(stats)

    
    
    stats = types.InlineKeyboardButton(text='↩️ Назад', callback_data='menu')
    markup.row(stats)
    
    try:
        bot.edit_message_text('🏛 Выберите статистику:', message.chat.id, message.message_id,
                             reply_markup=markup)
    except:
        bot.send_message(message.chat.id, '🏛 Выберете статистику:',
                            reply_markup=markup)


def build_sending_options_to_delete(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    data = types.InlineKeyboardButton(text='🍬 Вес', callback_data=f'del1|weight')
    markup.row(data)

    stats = types.InlineKeyboardButton(text='🍬 Окружность бедер', callback_data=f'del1|length_bedr')
    markup.row(stats)

    stats = types.InlineKeyboardButton(text='🍬 Окружность талии (самая тонкая часть)', callback_data=f'del1|length_tal')
    markup.row(stats)
    
    stats = types.InlineKeyboardButton(text='🍬 Окружность живота (на уровне пупка)', callback_data=f'del1|length_stom')
    markup.row(stats)

    
    
    stats = types.InlineKeyboardButton(text='↩️ Назад', callback_data='menu')
    markup.row(stats)
    
    try:
        bot.edit_message_text('Выберите категорию для удаления:', message.chat.id, message.message_id,
                         reply_markup=markup)
    except:
        bot.send_message(message.chat.id, 'Выберите категорию для удаления:',
                         reply_markup=markup)
        

def build_sending_options(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    data = types.InlineKeyboardButton(text='🍬 Вес', callback_data=f'add|weight')
    markup.row(data)

    stats = types.InlineKeyboardButton(text='🍬 Окружность бедер', callback_data=f'add|length_bedr')
    markup.row(stats)

    stats = types.InlineKeyboardButton(text='🍬 Окружность талии (самая тонкая часть)', callback_data=f'add|length_tal')
    markup.row(stats)
    
    stats = types.InlineKeyboardButton(text='🍬 Окружность живота (на уровне пупка)', callback_data=f'add|length_stom')
    markup.row(stats)

    
    
    stats = types.InlineKeyboardButton(text='↩️ Назад', callback_data='menu')
    markup.row(stats)
    
    try:
        bot.edit_message_text('Выберите данные для отправки:', message.chat.id, message.message_id,
                         reply_markup=markup)
    except:
        bot.send_message(message.chat.id, 'Выберите данные для отправки:',
                         reply_markup=markup)


def add_table_data(message, col):
    conn = sqlite3.connect('db/docdb.db', check_same_thread=False, timeout=3)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE user_id = ?",
                   (str(message.chat.id),))
    
    res = cursor.fetchone()

    try:    
        d = message.text
        d = d.replace(',', '.')
        d = d.replace(' ', '') 
        d = float(d)
        if col == 'weight':
            index = 2
            txt = '(вес)'
        if col == 'length_bedr':
            index = 6
            txt = '(обхват бедра)'
        
        if col == 'length_tal':
            index = 3
            txt = '(обхват талии)'
        
        if col == 'length_stom':
            index = 5
            txt = '(обхват живота)'

        if res[index] == None:
            data = [message.text]
            cursor.execute(f'UPDATE users SET {col} = ? WHERE user_id = ?',
                               (str(data), message.chat.id, ))
                
            conn.commit()
           
        else:
            data = ast.literal_eval(str(res[index]))
            data.append(message.text)
            cursor.execute(f'UPDATE users SET {col} = ? WHERE user_id = ?',
                               (str(data), message.chat.id, ))
            conn.commit()
        
        
        cursor.execute("SELECT * FROM administrators")
        
        resadm = cursor.fetchall()
        for i in resadm[0]:
            bot.send_message(i,
                            f'Пользователь ')
        conn.close()
        
        buildmenu(message)
    except:
        traceback.print_exc()
        bot.send_message(message.chat.id,
                        '🛑 Пожалуйста, введите число, например: 51.4')
        
        bot.register_next_step_handler(message, add_table_data, col)


def apply_data(message, col):
    x = 'кг' if col == 'weight' else 'см'
    bot.send_message(message.chat.id,
                    f'✍️ Введите данные (в {x}):')
    bot.register_next_step_handler(message, add_table_data, col)


def dellcur(message, col, ind=[]):
    conn = sqlite3.connect('db/docdb.db', check_same_thread=False, timeout=3)
    cursor = conn.cursor()
    cursor.execute(f'SELECT {col}  FROM users WHERE user_id = ?', (message.chat.id,))
    
    res = cursor.fetchone()
    
    
    
    data = ast.literal_eval(str(res[0]))
    markup = types.InlineKeyboardMarkup(row_width=1)
    if data != None:
        for i in range(len(data)):
            text = data[i] if i not in ind else f'{data[i]} ❌ '
            stats = types.InlineKeyboardButton(text=text, callback_data=f'derlind|{i}|{ind}|{col}')
            markup.row(stats)
        
        stats = types.InlineKeyboardButton(text='Применить', callback_data=f'apld|{ind}|{col}')
        markup.row(stats)
        
        stats = types.InlineKeyboardButton(text='Назад', callback_data='menu')
        markup.row(stats)
        
        try:
            bot.edit_message_text('Последние 5 записей (нажмите, чтобы выбрать):', message.chat.id, message.message_id,
                             reply_markup=markup)
        except:
            bot.send_message(message.chat.id, 'Последние 5 записей (нажмите, чтобы выбрать):',
                             reply_markup=markup)
    else:
        markup = types.InlineKeyboardMarkup(row_width=1)
        stats = types.InlineKeyboardButton(text='Назад', callback_data='menu')
        markup.row(stats)
        bot.send_message(message.chat.id, 'Кажется, у вас нет записей',
                         reply_markup=markup)
    conn.close()


def send_to_doctor(message):
    bot.send_message(message.chat.id, 'Введите текст:')
    bot.register_next_step_handler(message, send_doctor)


def send_doctor(message):
    conn = sqlite3.connect('db/docdb.db', check_same_thread=False, timeout=3)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM administrators")
    
    resadm = cursor.fetchall()
    
    cursor.execute("SELECT name FROM users WHERE user_id = ?", (message.chat.id,))
    name = cursor.fetchone()
    conn.close()
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    stats = types.InlineKeyboardButton(text='Ответить', callback_data=f'rep|{message.chat.id}')
    markup.row(stats)
    
    for i in resadm[0]:
        
        bot.send_message(i,
                        f'📰 Пациент {name[0]} написал обращение: \n{message.text}',
                        reply_markup=markup)

    buildmenu(message)


def reply_to_user(message, rep_id):
    bot.send_message(rep_id, f'📰 Ответ доктора: \n{message.text}')

def take_cur(message, ind=[]):
    conn = sqlite3.connect('db/docdb.db', check_same_thread=False, timeout=3)
    cursor = conn.cursor()
    cursor.execute(f'SELECT *  FROM users')
    
    res = cursor.fetchall()
    
    
    
    data = res
    markup = types.InlineKeyboardMarkup(row_width=1)
    if data != None:
        
        for i in range(len(data)):
            text = data[i][1] if str(data[i][-1]) not in ind else f'❌ {data[i][1]}'
            text = text.replace('\n', ' ')
            stats = types.InlineKeyboardButton(text=text, callback_data=f'passed|{ind}|{data[i][-1]}')
            markup.row(stats)
        
        stats = types.InlineKeyboardButton(text='Применить', callback_data=f'applied|{ind}')
        markup.row(stats)
        
        stats = types.InlineKeyboardButton(text='Назад', callback_data='menu')
        markup.row(stats)
        
        try:
            bot.edit_message_text('Выберите пользователей для рассылки:', message.chat.id, message.message_id,
                             reply_markup=markup)
        except:
            bot.send_message(message.chat.id, 'Выберите пользователей для рассылки:',
                             reply_markup=markup)
    else:
        markup = types.InlineKeyboardMarkup(row_width=1)
        stats = types.InlineKeyboardButton(text='Назад', callback_data='menu')
        markup.row(stats)
        bot.send_message(message.chat.id, 'Кажется, у вас нет пациентов',
                         reply_markup=markup)
    conn.close()


def get_text_to_send(message, users, texting='', img_paths=[]):
    texting = message.text if texting == '' else texting
    markup = types.InlineKeyboardMarkup(row_width=1)
    stats = types.InlineKeyboardButton(text='Назад', callback_data='menu')
    markup.row(stats)
    bot.send_message(message.chat.id, 'Отправьте картинку или напишите "+", чтобы продолжить',
                         reply_markup=markup)
        
    bot.register_next_step_handler(message, get_image_to_send, users, texting, img_paths)

def get_image_to_send(message, users, texting, img_paths):
    print(img_paths)
    markup = types.InlineKeyboardMarkup(row_width=1)
    stats = types.InlineKeyboardButton(text='Назад', callback_data='menu')
    markup.row(stats)
    try:
        users = ast.literal_eval(users)
    except:
        pass


    conn = sqlite3.connect('db/docdb.db', check_same_thread=False, timeout=3)
    cursor = conn.cursor()
    
    if message.text == '+':
        images = []
        img_paths = img_paths[::-1]
        for path in range(len(img_paths)):
            if img_paths[path] not in abandoned:
                images.append(telebot.types.InputMediaPhoto(open(f'{img_paths[path]}', 'rb'), 
                                                                                caption='📨 Рассылка от доктора: \n' + texting if path == 0 else ''))
                abandoned.append(img_paths[path])
            else:
                pass
        for id in users:
            cursor.execute(f'SELECT user_id FROM users WHERE id = ?', (id, ))       
            snd = cursor.fetchone()
            try:
                
                bot.send_media_group(snd[0], images, protect_content=True)
            
            except:
                traceback.print_exc()
                
                bot.send_message(snd[0], text='📨 Рассылка от доктора: \n' + texting)
        try:
            for i in img_paths:
                os.remove(i)
        except:
            traceback.print_exc()
        
        build_admin_menu(message) 
        
    else:
        photo = message.photo[-1]
        file_info = bot.get_file(photo.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        fm = f'{randint(1, 100000)}.jpg'
        save_path = f'{fm}'
        img_paths.append(save_path)
        with open(save_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        bot.send_message(message.chat.id, 'Отправьте ещё картинку или напишите "+", чтобы закончить',
                         reply_markup=markup)
        
        bot.register_next_step_handler(message, get_image_to_send, users, texting, img_paths)
    
    conn.close()


def users_to_delete(message):
    conn = sqlite3.connect('db/docdb.db', check_same_thread=False, timeout=3)
    cursor = conn.cursor()
    cursor.execute(f'SELECT *  FROM users')
    
    res = cursor.fetchall()
    
    conn.close()
    
    data = res
    markup = types.InlineKeyboardMarkup(row_width=1)
    if data != None:
        
        for i in range(len(data)):
            stats = types.InlineKeyboardButton(text=text, callback_data=f'kill|{data[i][-1]}')
            markup.row(stats)
        
    
        
        stats = types.InlineKeyboardButton(text='Назад', callback_data='menu')
        markup.row(stats)
        
        try:
            bot.edit_message_text('Выберите пользователя для удаления', message.chat.id, message.message_id,
                             reply_markup=markup)
        except:
            bot.send_message(message.chat.id, 'Выберите пользователя для удаления',
                             reply_markup=markup)
    else:
        markup = types.InlineKeyboardMarkup(row_width=1)
        stats = types.InlineKeyboardButton(text='Назад', callback_data='menu')
        markup.row(stats)
        bot.send_message(message.chat.id, 'Кажется, у вас нет пациентов',
                         reply_markup=markup)
    conn.close()


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == 'ban_hammer':
        users_to_delete(call.message)

    if 'kill|' in call.data:
        conn = sqlite3.connect('db/docdb.db', check_same_thread=False, timeout=3)
        cursor = conn.cursor()
        cursor.execute(f'DELETE FROM users WHERE user=?', (call.data.split('|')[1],))
        conn.close()
        build_admin_menu(call.message)

    if 'applied|' in call.data:
        users_to_send = call.data.split('|')[1]
        markup = types.InlineKeyboardMarkup(row_width=1)
        stats = types.InlineKeyboardButton(text='Назад', callback_data='menu')
        markup.row(stats)
        bot.send_message(call.message.chat.id, 'Введите текст для отправки одним сообщением:',
                         reply_markup=markup)
        
        bot.register_next_step_handler(call.message, get_text_to_send, users_to_send)
        

    if 'data|' in call.data:
        user_id = call.data.split('|')[2]
        stat = call.data.split('|')[1]

        conn = sqlite3.connect('db/docdb.db', check_same_thread=False, timeout=3)
        cursor = conn.cursor()
                    
                    
        cursor.execute(f'SELECT name  FROM users WHERE user_id = ?', (user_id, ))       
        name = cursor.fetchone()
        conn.close()
        
        try:
            text = f'✅ Cтатистика пациента {name[0]} '
            if stat == "length_bedr":
                text += 'по окружности бёдер'

            if stat == "length_tal":
                text += 'по окружности талии'

            if stat == "length_stom":
                text += 'по окружности живота'

            if stat == "weight":
                text += 'по весу'

            label = 'кг' if stat == "weight" else 'см'
            

            options = types.InlineKeyboardMarkup(row_width=1)
            back = types.InlineKeyboardButton(text='↩️ Назад', callback_data='menu')
            options.row(back)
            
            index = call.data.split("|")[1]
            
            conn = sqlite3.connect('db/docdb.db', check_same_thread=False, timeout=3)
            cursor = conn.cursor()
                    
                    
            cursor.execute(f'SELECT {index}  FROM users WHERE user_id = ?', (user_id, ))
                    
            res = cursor.fetchone()
            

            cursor.execute(f'SELECT height  FROM users WHERE user_id = ?', (user_id, ))
                    
            height = cursor.fetchone()
            height = ast.literal_eval(str(res[0]))

            
            res = ast.literal_eval(str(res[0]))
            res = [float(i) for i in res]
            x = [i for i in range(1, len(res) + 1)]

            index = x
            values = res
            
            cursor.execute(f'SELECT height  FROM users WHERE user_id = ?', (user_id, ))
                    
            
            wght = int(res[-1])

            imt = round(wght / (int(height[0]) / 100), 2)
            text += f', ИМТ составляет {imt}'
            plt.clf()
                    
            plt.bar(index,values)
                    
            ax = plt.gca()
            plt.bar_label(ax.containers[0])
                    
            plt.xlabel("Порядок измерений")
            plt.ylabel(label)

            flname = str(randint(100000, 1000000))
                    
            plt.savefig(f'{flname}.png')
                    

                    
            if x != None and len(x) != 0:
                bot.send_photo(call.message.chat.id, open(f'{flname}.png', 'rb'),
                                caption=f'{text}', reply_markup=options)
            else:   
                try:
                    bot.edit_message_text('Кажется, у пациента нет записей', call.message.chat.id, call.message.message_id,
                                            reply_markup=options)
                    os.remove(f'{flname}.png')

                except:
                    bot.send_message(call.message.chat.id, 'Кажется, у пациента нет записей',
                                            reply_markup=options)
                      
                    os.remove(f'{flname}.png')
            
            conn.close()
            
        except:
            traceback.print_exc()
            try:
                bot.edit_message_text('Кажется, у пациента нет записей', call.message.chat.id, call.message.message_id,
                                     reply_markup=options)
            except:
                bot.send_message(call.message.chat.id, 'Кажется, у пациента нет записей',
                                     reply_markup=options)
    

    if call.data == 'rassilka':
        take_cur(call.message)

    if 'passed|' in call.data:
        res = call.data.split("|")
        ind = ast.literal_eval(str(res[1]))
        i = str(res[2])
        if i not in ind:
            ind.append(i)
        else:
            del ind[ind.index(i)]
        take_cur(call.message, ind)

    if 'check' in call.data:
        user_id = call.data.split('|')[1]
        build_stats_menu_for_user(call.message, int(user_id))
        
    if 'rep|' in call.data:
        rep_id = call.data.split('|')[1]
        bot.send_message(call.message.chat.id, '✍️ Введите ответ пользователю:')
        bot.register_next_step_handler(call.message, reply_to_user, rep_id)

    if call.data == 'tip':
        send_to_doctor(call.message)

    if 'del1' in call.data:
        col = call.data.split('|')[1]
        dellcur(call.message, col)
        
    if 'derlind' in call.data:
        res = call.data.split("|")
        col = res[3]
        ind = ast.literal_eval(str(res[2]))
        i = int(res[1])
        if i not in ind:
            ind.append(i)
        else:
            del ind[ind.index(i)]
        dellcur(call.message, col, ind)

    if call.data == "show_stats":
        build_stats_menu(call.message)
    
    if call.data == "menu":
        buildmenu(call.message)

    if call.data == 'delete_stats':
        build_sending_options_to_delete(call.message)

    if call.data == 'add_stats':
        build_sending_options(call.message)
    
    if 'apld' in call.data:
        res = call.data.split("|")
        col = res[2]
        ind = ast.literal_eval(str(res[1]))
        
        conn = sqlite3.connect('db/docdb.db', check_same_thread=False, timeout=3)
        cursor = conn.cursor()
        cursor.execute(f'SELECT {col}  FROM users WHERE user_id = ?', (call.message.chat.id,))
        
        res = cursor.fetchone()
        res = ast.literal_eval(str(res[0]))
        data = []
        for i in range(len(res[0])):
            if i not in ind:
                try:
                    data.append(res[i])
                except:
                    pass
        
        cursor.execute(f'UPDATE users SET {col} = ? WHERE user_id = ?',
                           (str(data), call.message.chat.id, ))
        conn.commit()
        
        conn.close()
        
        
        buildmenu(call.message)


    
    if 'add|' in call.data:
        index = call.data.split('|')[1]
        apply_data(call.message, index)

    if 'get|' in call.data:
        try:
            text = '✅ Ваша статистика по '
            if call.data == "get|length_bedr":
                text += 'окружности бёдер'

            if call.data == "get|length_tal":
                text += 'окружности талии'

            if call.data == "get|length_stom":
                text += 'окружности живота'

            if call.data == "get|weight":
                text += 'весу'

            label = 'кг' if call.data == "get|weight" else 'см'
            

            options = types.InlineKeyboardMarkup(row_width=1)
            back = types.InlineKeyboardButton(text='↩️ Назад', callback_data='menu')
            options.row(back)
            
            index = call.data.split("|")[1]
            
            conn = sqlite3.connect('db/docdb.db', check_same_thread=False, timeout=3)
            cursor = conn.cursor()
                    
                    
            cursor.execute(f'SELECT {index}  FROM users WHERE user_id = ?', (call.message.chat.id,))
                    
            res = cursor.fetchone()
                    
            conn.close()
            res = ast.literal_eval(str(res[0]))
            res = [float(i) for i in res]
            x = [i for i in range(1, len(res) + 1)]

            index = x
            values = res
            wght = int(res[-1])
            
            cursor.execute(f'SELECT height  FROM users WHERE user_id = ?', (call.message.chat.id, ))
                    
            
            wght = int(res[-1])

            imt = round(wght / (int(height[0]) / 100), 2)
            text += f', ИМТ составляет {imt}'

            plt.clf()
                    
            plt.bar(index,values)
                    
            ax = plt.gca()
            plt.bar_label(ax.containers[0])
                    
            plt.xlabel("Порядок измерений")
            plt.ylabel(label)

            flname = str(randint(100000, 1000000))
                    
            plt.savefig(f'{flname}.png')
                    

                    
            if x != None and len(x) != 0:
                bot.send_photo(call.message.chat.id, open(f'{flname}.png', 'rb'),
                                caption=f'{text}', reply_markup=options)
            else:   
                try:
                    bot.edit_message_text('Кажется, у вас нет записей', call.message.chat.id, call.message.message_id,
                                            reply_markup=options)
                    os.remove(f'{flname}.png')

                except:
                    bot.send_message(call.message.chat.id, 'Кажется, у вас нет записей',
                                            reply_markup=options)
                      
                    os.remove(f'{flname}.png')
            
            
        except:
            try:
                bot.edit_message_text('Кажется, у вас нет записей', call.message.chat.id, call.message.message_id,
                                     reply_markup=options)
            except:
                bot.send_message(call.message.chat.id, 'Кажется, у вас нет записей',
                                     reply_markup=options)
        
if __name__ == '__main__':
    bot.infinity_polling() 