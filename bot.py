import telebot
import user_queue
import lab_table_loader
from config import TOKEN, USERS, ADMIN_USER, LAB_COUNT
from user_queue import Queue, QueueElement
from telebot import types
from enum import Enum
from copy import deepcopy
#from handing_stats_manager import handing_stats 
from lab_table_loader import init_leaderboard, leaderboard, LeaderboardLoadError, LeaderboardLabError, LeaderboardUserError
import atexit

err_msg_ps = "Пингуйте Никиту (@nikita01)"

class BotState(Enum):
    READING_COMMAND = 0
    READING_LAB_APPEND_DATA = 1
    READING_QUEUE_NAME = 2
    READING_LAB_REMOVE_DATA = 3
    READING_FREE_INSTRUCTION = 4

bot = telebot.TeleBot(TOKEN)

state_table = {}
queue_name = ""
Q = Queue()
backup_Q = Queue()

create_new_queue_cmd = "Добавить новую очередь"
show_current_queue_cmd = "Показать текущую очередь"
add_to_queue_cmd = "Встать в очередь"
leave_queue_cmd = "Удалиться из очереди"
display_first_cmd = "Показать первого"
free_record_cmd = "Отметить сдачу"
show_handing_stats = "Список лаб"
show_position = "Узнать свой номер"

def shutdown():
    global backup_Q
    print("Saving queue backup")
    dump_backup()

def update_backup():
    global Q, backup_Q
    backup_Q = deepcopy(Q)

def dump_backup():
    global backup_Q
    f = open("queue_dump.dmp", "w")
    backup_Q.dump(f)
    f.close()

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    username = message.from_user.username
    chat_id = message.chat.id

    sti = open("graphics/sticker.webp", "rb")

    if username in ADMIN_USER:

        bot.send_message(chat_id, "Привет, admin!")
        bot.send_sticker(chat_id, sti)

        # keyboard

        markup = types.ReplyKeyboardMarkup(row_width=1)
        item1 = types.KeyboardButton(create_new_queue_cmd)
        item2 = types.KeyboardButton(show_current_queue_cmd)

        markup.add(item1, item2, item3, item4)

        bot.send_message(chat_id, "Выбeрите функцию:", reply_markup=markup)

    elif USERS.get(username) is not None:

        bot.send_message(chat_id, "Привет, " + USERS[username] + "!")
        bot.send_sticker(chat_id, sti)

        # keyboard

        markup = types.ReplyKeyboardMarkup(row_width=1)
        item1 = types.KeyboardButton(show_current_queue_cmd)
        item2 = types.KeyboardButton(add_to_queue_cmd)
        item3 = types.KeyboardButton(leave_queue_cmd)
        item4 = types.KeyboardButton(show_position)

        markup.add(item1, item2, item3, item4)

        bot.send_message(chat_id, "Выбeрите функцию:", reply_markup=markup)
    else:
        bot.send_message(chat_id, "Привет, я тебя не знаю!\nЯ не умею работать с пользователей, которых не знаю!\nНапиши Никите Пологову, возможно это какая-то ошибка")

def log_queue(chat_id):
    global Q, bot, queue_name

    bot.send_message(chat_id, queue_name + ":")
    for (i, s) in enumerate(map(str, iter(Q))):
        msg = "Запись номер " + str(i + 1) + "\n" + s
        #print(msg)
        bot.send_message(chat_id, msg, parse_mode = "HTML")


@bot.message_handler(func = lambda msg: msg.from_user.username not in state_table)
def process_command(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Привет, я тебя не знаю!\nЯ не умею работать с пользователей, которых не знаю!\nНапиши Никите Пологову, возможно это какая-то ошибка")

@bot.message_handler(content_types=["text"], func = lambda msg: msg.from_user.username in state_table and state_table[msg.from_user.username] == BotState.READING_COMMAND)
def process_command(message):
    global Q, queue_name, bot, state_table, handing_stats
    username = message.from_user.username
    chat_id = message.chat.id

    is_admin = username in ADMIN_USER
    is_student = USERS.get(username) is not None
    is_teacher = False

    if message.text == create_new_queue_cmd and is_admin:
        bot.send_message(chat_id, "Введите название очереди:")
        state_table[username] = BotState.READING_QUEUE_NAME
    elif message.text == show_current_queue_cmd and (is_admin or is_student):
        log_queue(chat_id)
    elif message.text == add_to_queue_cmd and is_student:
        bot.send_message(chat_id, "Введите номер лабы, на которую хотите записаться")
        state_table[username] = BotState.READING_LAB_APPEND_DATA
    elif message.text == leave_queue_cmd and is_student:
        bot.send_message(chat_id, "Введите номер лабы, запись которой надо убрать")
        state_table[username] = BotState.READING_LAB_REMOVE_DATA
    elif message.text == show_position and is_student:
        query = Q.record_present(username, None)
        if query is None:
            bot.send_message(chat_id, "Тебя нет в очереди")
        else:
            bot.send_message(chat_id, "Ваша позиция в очереди: " + str(query.index + 1) + "!\nЭто Ваша БЛИЖАЙШАЯ позиция в очереди") 
    elif message.text == display_first_cmd and is_teacher:
        pass
    elif message.text == show_handing_stats:
        msg = "Таблица сдачи лаб\n"
        for (i, b) in enumerate(iter(handing_stats[username])):
            labN = i + 1
            if b: st = "*сдана*"
            else: st = "*не сдана*"
            msg += ("Лаба №" + str(labN) + " " + st + "\n")
        bot.send_message(chat_id, msg, parse_mode = "MarkdownV2")
    else:
        bot.send_message(chat_id, "Неопознанная команда или у Вас нет прав на такую команду")

@bot.message_handler(content_types=["text"], func = lambda msg: msg.from_user.username in state_table and state_table[msg.from_user.username] == BotState.READING_LAB_APPEND_DATA)
def process_lab_append_info(message):
    global Q, queue_name, bot, state_table
    username = message.from_user.username
    chat_id = message.chat.id

    is_admin = username in ADMIN_USER
    is_student = USERS.get(username) is not None

    lab, rating = None, None

    try:
        lab = int(message.text.strip())
        if lab <= 0:
            lab = None
            raise ValueError("Lab number must be greater than 0")
    except ValueError:
        bot.send_message(chat_id, "Неправильный формат ввода.")

    if lab is not None:
        query = Q.record_present(username, lab)
        if query is not None: 
            bot.send_message(chat_id, "Ты уже есть в очереди!")
        else:
            try:
                Q.push(QueueElement(username, lab))
                update_backup()
                bot.send_message(chat_id, "Поздравляю. Ты записан в очередь.")
            except LeaderboardLabError as err:
                print("@" + username + "has caused the following error:\n" + str(err))
                err_msg = "Приносим свои извинения, но у нас пока не загружена таблица лабы №" + str(lab) + ".\n" + err_msg_ps
                bot.send_message(chat_id, err_msg)
            except LeaderboardUserError as err:
                print("@" + username + "has caused the following error:\n" + str(err))
                err_msg = "Приносим свои извинения, но мы не нашли Вас в таблице лабы №" + str(lab) + ".\nВозможно наши данные устарели.\n" + err_msg_ps
                bot.send_message(chat_id, err_msg)

    state_table[username] = BotState.READING_COMMAND

@bot.message_handler(content_types=["text"], func = lambda msg: msg.from_user.username in state_table and state_table[msg.from_user.username] == BotState.READING_QUEUE_NAME)
def process_new_queue_name(message):
    global Q, queue_name, bot, state_table
    username = message.from_user.username
    chat_id = message.chat.id

    is_admin = username in ADMIN_USER
    is_student = USERS.get(username) is not None

    Q = Queue()
    update_backup()
    queue_name = message.text

    bot.send_message(chat_id, "Название очереди изменено на `" + queue_name + "`")

    state_table[username] = BotState.READING_COMMAND

@bot.message_handler(content_types=["text"], func = lambda msg: msg.from_user.username in state_table and state_table[msg.from_user.username] == BotState.READING_LAB_REMOVE_DATA)
def process_lab_remove_info(message):
    global Q, queue_name, bot, state_table
    username = message.from_user.username
    chat_id = message.chat.id

    is_admin = username in ADMIN_USER
    is_student = USERS.get(username) is not None

    lab = None

    try:
        lab = int(message.text.strip())
        if lab <= 0:
            lab = None
            raise ValueError("Lab number must be greater than 0")
    except ValueError:
        bot.send_message(chat_id, "Неправильный формат ввода.")

    if lab is not None:
        query = Q.record_present(username, lab)
        if query is not None:
            Q.remove(username, lab)
            update_backup()
            bot.send_message(chat_id, "Ваша запись удалена. Теперь вы не сдаёте лабу номер " + str(lab))
        else:
            bot.send_message(chat_id, "Ты эту лабу и так не сдаёшь!")

    state_table[username] = BotState.READING_COMMAND

for user in USERS: state_table[user] = BotState.READING_COMMAND
for user in ADMIN_USER: state_table[user] = BotState.READING_COMMAND

try:
    init_leaderboard(LAB_COUNT)
except LeaderboardLoadError as err:
    print(str(err))
    exit()

print("leadeboard loaded")
print("loading backup")

try:
    f = open("queue_dump.dmp", "r")
    Q.load(f)
    f.close()
    update_backup()
    print("backup loaded")
except:
    print("failed to load backup, switching back to empty queue")
    Q = Queue()

try:
    bot.polling(none_stop=True)
except:
    dump_backup()
    print("Backup dumped")

atexit.register(shutdown)
