import telebot
from config import TOKEN, USERS, ADMIN_USER
from telebot import types

bot = telebot.TeleBot(TOKEN)

new_name_queue = False
queue_name = ""
queue = []


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    username = message.from_user.username
    chat_id = message.chat.id

    sti = open("sticker.webp", "rb")

    if username in ADMIN_USER:

        bot.send_message(chat_id, "Привет, admin!")
        bot.send_sticker(chat_id, sti)

        # keyboard

        markup = types.ReplyKeyboardMarkup(row_width=2)
        item1 = types.KeyboardButton("Показать последнию очередь:")
        item2 = types.KeyboardButton("Добавить новую очередь")

        markup.add(item1, item2)

        bot.send_message(chat_id, "Выбeрите функцию:", reply_markup=markup)

    elif USERS.get(username) is not None:

        bot.send_message(chat_id, "Привет, " + USERS[username] + "!")
        bot.send_sticker(chat_id, sti)

        # keyboard

        markup = types.ReplyKeyboardMarkup(row_width=2)
        item1 = types.KeyboardButton("Показать последнию очередь:")
        item2 = types.KeyboardButton("Встать в очередь")

        markup.add(item1, item2)

        bot.send_message(chat_id, "Выбeрите функцию:", reply_markup=markup)
    else:

        bot.send_message(chat_id, "Привет, я тебя не знаю!")


ok = False


@bot.message_handler(content_types=["text"])
def processing_test(message):
    global new_name_queue, queue_name, queue, ok
    username = message.from_user.username
    chat_id = message.chat.id

    if username in ADMIN_USER:
        if message.text == "Показать последнию очередь:":
            bot.send_message(chat_id, queue_name + ":")
            for i in range(len(queue)):
                string = str(i + 1) + ". " + queue[i][2] + " (@" + queue[i][3] + ")" 
                string1 = " сдает лабу: " + str(queue[i][0]) 
                string2 = " имеет место: " + str(queue[i][1])
                bot.send_message(chat_id, string + string1 + string2)
        elif message.text == "Добавить новую очередь":
            bot.send_message(chat_id, "Введите название очереди:")
            queue = []
            new_name_queue = True
        elif new_name_queue:
            queue_name = message.text
            new_name_queue = False
        else:
            bot.send_message(chat_id, "Error")
    elif USERS.get(username) is not None:
        if message.text == "Показать последнию очередь:":
            bot.send_message(chat_id, queue_name + ":")
            for i in range(len(queue)):
                string = str(i + 1) + ". " + queue[i][2] + " (@" + queue[i][3] + ")" 
                string1 = " сдает лабу: " + str(queue[i][0]) 
                string2 = " имеет место: " + str(queue[i][1])
                bot.send_message(chat_id, string + string1 + string2)
        elif message.text == "Встать в очередь":
            bot.send_message(chat_id, "Введите через пробел: номер лабы и ваше место в рейтинге этой лабы")
            ok = True
        elif ok:
            number_labs, rating = map(int, message.text.split())
            pair = [number_labs, rating, USERS[username], username]
            if pair not in queue:
                queue.append(pair)
                queue = sorted(queue)
            else:
                bot.send_message(chat_id, "Ты уже есть в очереди!")
        elif ok:
            ok = False
        else:
            bot.send_message(chat_id, "Error")


bot.polling()
