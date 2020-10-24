import telebot
import user_queue
from config import TOKEN, USERS, ADMIN_USER
from user_queue import Queue, QueueElement
from telebot import types

bot = telebot.TeleBot(TOKEN)

# 0 --- reading a command
# 1 --- reading lab data
# 2 --- entering new queue name
state_table = {}
queue_name = ""
Q = Queue()

create_new_queue_cmd = "Добавить новую очередь"
show_current_queue_cmd = "Показать текущую очередь"
add_to_queue_cmd = "Встать в очередь"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    username = message.from_user.username
    chat_id = message.chat.id

    sti = open("sticker.webp", "rb")

    if username in ADMIN_USER:

        bot.send_message(chat_id, "Привет, admin!")
        bot.send_sticker(chat_id, sti)

        # keyboard

        markup = types.ReplyKeyboardMarkup(row_width=1)
        item1 = types.KeyboardButton(create_new_queue_cmd)
        item2 = types.KeyboardButton(show_current_queue_cmd)
        item3 = types.KeyboardButton(add_to_queue_cmd)

        markup.add(item1, item2, item3)

        bot.send_message(chat_id, "Выбeрите функцию:", reply_markup=markup)

    elif USERS.get(username) is not None:

        bot.send_message(chat_id, "Привет, " + USERS[username] + "!")
        bot.send_sticker(chat_id, sti)

        # keyboard

        markup = types.ReplyKeyboardMarkup(row_width=1)
        item1 = types.KeyboardButton(show_current_queue_cmd)
        item2 = types.KeyboardButton(add_to_queue_cmd)

        markup.add(item1, item2)

        bot.send_message(chat_id, "Выбeрите функцию:", reply_markup=markup)
    else:
        bot.send_message(chat_id, "Привет, я тебя не знаю!")

def log_queue(chat_id):
    global Q, bot, queue_name
        
    bot.send_message(chat_id, queue_name + ":") 
    for (i, s) in enumerate(map(str, iter(Q))):
        bot.send_message(chat_id, "Запись №" + str(i + 1) + "\n" + s, parse_mode = "MarkdownV2")

@bot.message_handler(content_types=["text"], func = lambda msg: state_table[msg.from_user.username] == 0)
def process_command(message):
    global Q, queue_name, bot, state_table
    username = message.from_user.username
    chat_id = message.chat.id

    current_state = state_table[username]
    is_admin = username in ADMIN_USER
    is_student = USERS.get(username) is not None 

    if message.text == create_new_queue_cmd and is_admin:
        bot.send_message(chat_id, "Введите название очереди:")
        state_table[username] = 2
    elif message.text == show_current_queue_cmd and (is_admin or is_student):
        log_queue(chat_id)
    elif message.text == add_to_queue_cmd and (is_admin or is_student):
        bot.send_message(chat_id, "Введите через пробел: номер лабы и ваше место в рейтинге этой лабы")
        state_table[username] = 1
    else:
        bot.send_message(chat_id, "Неопознанная команда")

@bot.message_handler(content_types=["text"], func = lambda msg: state_table[msg.from_user.username] == 1)
def process_lab_info(message):
    global Q, queue_name, bot, state_table
    username = message.from_user.username
    chat_id = message.chat.id

    current_state = state_table[username]
    is_admin = username in ADMIN_USER
    is_student = USERS.get(username) is not None 

    lab, rating = None, None

    try:
        lab, rating = map(int, message.text.split())
    except ValueError:
        bot.send_message(chat_id, "Неправильный формат ввода.")
           
    if lab is not None and rating is not None:
        query = Q.record_present(username, lab, rating)
        if query is not None: bot.send_message(chat_id, "Ты уже есть в очереди!")
        else: 
            Q.push(QueueElement(username, lab, rating))
            bot.send_message(chat_id, "Поздравляю. Ты записан в очередь.")

    state_table[username] = 0

@bot.message_handler(content_types=["text"], func = lambda msg: state_table[msg.from_user.username] == 2)
def process_new_queue_name(message):
    global Q, queue_name, bot, state_table
    username = message.from_user.username
    chat_id = message.chat.id

    current_state = state_table[username]
    is_admin = username in ADMIN_USER
    is_student = USERS.get(username) is not None 

    Q = Queue()
    queue_name = message.text
    state_table[username] = 0

for user in USERS: state_table[user] = 0

bot.polling()
