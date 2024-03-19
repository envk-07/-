import telebot
import stegano
import base64
from telebot import types
from tempfile import TemporaryFile

TOKEN = '6397793894:AAGQOmxusygHd_t6Nalh2_n4eDlRIDUW-0E'
bot = telebot.TeleBot(TOKEN)



@bot.message_handler(content_types=['text', 'document', 'photo'], func=lambda msg: msg.text is None or '/' not in msg.text)
def command(message):
    bot.send_message(message.chat.id,text="Отправьте команду /start чтобы начать пользоваться ботом")


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("/encode")
    btn2 = types.KeyboardButton("/decode")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id,
                     text="Привет, я - бот для шифрования сообщений в картинках. С помощью меня ты "
                     "можешь раскодировать зашифрованное сообщение в картинке, или наоборот - "
                     "закодировать любое сообщение в желаемую картинку. Для того чтобы зашифровать "
                     "изображение нажимите  '/encode', а чтобы расшифровать уже имеющееся изображение "
                     "нажмите '/decode'".format(message.from_user), reply_markup=markup)


@bot.message_handler(content_types=['text'], func=lambda msg: msg.text is not None and '/' in msg.text)
def command(message):
    if (message.text == "/encode"):
        bot.send_message(message.chat.id,"Отправь текст, который хочешь закодировать:")
        bot.register_next_step_handler(message, encode_txt)
    elif (message.text == "/decode"):
        bot.send_message(message.chat.id, "Отправь картинку, которую хочешь раскодировать в текст. Она должна быть отправлена без сжатия в формате PNG!")
        bot.register_next_step_handler(message, decode_pic)
    else:
        bot.send_message(message.chat.id, text="Такой команды не существует :(")

def encode_txt(message2):
    text = message2.text
    bot.send_message(message2.chat.id, "Отправь картинку, в который хочешь закодировать данный текст. ВАЖНО! Она должна быть отправлена без сжатия для того, чтобы при дальнейшей пересылке сообщения изображение не искажалось. Формат картинки не важен")
    bot.register_next_step_handler(message2, lambda message: handle_photo(message, text))

def handle_photo(message, text):
    # так можно посмотреть какие есть поля в объекте
    # print(dir(message))

    photo = message.document
    file_info = bot.get_file(photo.file_id)
    image_data = bot.download_file(file_info.file_path)
    downloaded_file = bot.download_file(file_info.file_path)

    # открываем все файлы в бинарном(то есть в не изменяемом виде)
    with TemporaryFile(mode='w+b') as source_photo, TemporaryFile(mode='w+b') as encoded_photo:
        source_photo.write(downloaded_file)
        # перемотаем текущую позицию на начало фала
        source_photo.seek(0)

        bot.reply_to(message, 'Изображение принято и находится в обработке. Пожалуйста, подождите!')

        # шифрование текста в картинку:
        # переводим текст в кодировку base64 чтобы решить проблему русских букв
        b64_text = base64.encodebytes(text.encode('utf-8')).decode()
        image = stegano.lsb.hide(source_photo, b64_text)
        image.save(encoded_photo, format='png')

        # перемотаем позицию на начало
        encoded_photo.seek(0)
        bot.send_document(message.chat.id, encoded_photo, visible_file_name='encoded_photo.png')


def decode_pic(message):
    photo = message.document
    text = message.caption
    file_info = bot.get_file(photo.file_id)
    image_data = bot.download_file(file_info.file_path)
    downloaded_file = bot.download_file(file_info.file_path)

    with TemporaryFile(mode='w+b') as encoded_photo:
        encoded_photo.write(downloaded_file)
        # перемотаем текущую позицию на начало
        encoded_photo.seek(0)

        bot.reply_to(message, 'Изображение принято и находится в обработке. Пожалуйста, подождите!')

        # расшифровка картинки
        try:
            b64_text = stegano.lsb.reveal(encoded_photo)
            # переводим текст обратно из кодировки base64
            text = base64.decodebytes(b64_text.encode()).decode('utf-8')
            bot.reply_to(message, text)
        except Exception as v:
            print(v)
            bot.send_message(message.chat.id, text="Не удалось раскодировать сообщение. Изображение должно быть в формате png")


bot.polling()
# while True:
#     try:
#         bot.polling()
#     except Exception as v:
#         print(v)
