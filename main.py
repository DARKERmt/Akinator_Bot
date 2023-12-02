import telebot
from akinator import Akinator
import requests
from googlesearch import search
from icrawler.builtin import GoogleImageCrawler
import os


# Replace 'YOUR_TELEGRAM_BOT_TOKEN' with your actual Telegram bot token
TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'

bot = telebot.TeleBot(TOKEN)
akinator_game = Akinator()

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Welcome to Akinator! Think of a character, and I'll try to guess it. "
                                      "Type /play to start the game.")

@bot.message_handler(commands=['play'])
def play(message):
    global akinator_game
    akinator_game = Akinator()
    akinator_game.start_game()
    send_question_with_options(message.chat.id, akinator_game.question)

def send_question_with_options(chat_id, question):
    possible_answers = ['Yes', 'No', "I don't know", 'Probably', 'Probably not']
    markup = generate_markup(possible_answers)
    bot.send_message(chat_id, question, reply_markup=markup)

def generate_markup(options):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    buttons = [telebot.types.InlineKeyboardButton(text=option, callback_data=option) for option in options]
    markup.add(*buttons)
    return markup

def send_image(word):

    google_crawler = GoogleImageCrawler(
        feeder_threads=1,
        parser_threads=1,
        downloader_threads=1,
        storage={'root_dir': 'img'}
    )
    filters = dict(type='photo')  # You can add more filters as needed

    google_crawler.crawl(keyword=word, filters=filters, max_num=1)

    # Get the downloaded image path
    image_path = google_crawler.storage.root_dir

    return image_path  # Return the path of the downloaded image


@bot.callback_query_handler(func=lambda call: True)
def handle_answer(call):
    global akinator_game
    if akinator_game is None:
        bot.answer_callback_query(call.id, text="Please start the game first using /play.")
    else:
        if akinator_game.progression is None:
            bot.answer_callback_query(call.id, text="Please continue the game by answering questions.")
        else:
            if akinator_game.progression <= 80:
                answer = call.data.lower()
                akinator_game.answer(answer)
                if akinator_game.progression <= 80:
                    send_question_with_options(call.message.chat.id, akinator_game.question)
                else:
                    akinator_game.win()
                    bot.send_message(call.message.chat.id, "I think...")
                    result = akinator_game.first_guess['name']
                    image_path = send_image(result)
                    if image_path:
                        image_files = os.listdir(image_path)
                        if image_files:
                            image_file = os.path.join(image_path, image_files[0])
                            with open(image_file, 'rb') as img:
                                bot.send_photo(call.message.chat.id, photo=img, caption=f"I'm guessing your character is: {result}")
                            os.remove(image_file)
                            bot.delete_message(call.message.chat.id, call.message.message_id)  # Delete "Thinking..." message
                        else:
                            bot.send_message(call.message.chat.id, f"I'm guessing your character is: {result}")
                            bot.delete_message(call.message.chat.id, call.message.message_id)  # Delete "Thinking..." message
                    else:
                        bot.send_message(call.message.chat.id, f"I'm guessing your character is: {result}")
                        bot.delete_message(call.message.chat.id, call.message.message_id)  # Delete "Thinking..." message
                    bot.send_message(call.message.chat.id, "Click /play to play again.")
                    akinator_game = None  # Reset the game instance after finishing
            else:
                bot.answer_callback_query(call.id, text="The game has ended. Click /play to start a new game.")



if __name__ == "__main__":
    print("Bot is working..")
    bot.polling()