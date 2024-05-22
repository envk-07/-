import sys
import os
import telebot
import stegano
import base64
import subprocess
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from telebot import types
from tempfile import TemporaryFile, NamedTemporaryFile, TemporaryDirectory

TOKEN = '6397793894:AAGQOmxusygHd_t6Nalh2_n4eDlRIDUW-0E'
bot = telebot.TeleBot(TOKEN)

session_store = {}

def report_errors(f):
    def _f(message, *args): #
        try:
            return f(message, *args)
        except Exception as v:
            _start(message, "Произошла ошибка: %s %s\nПроверьте загружаемые данные и попробуйте еще раз." % (v.__class__.__name__, v))
    return _f


def key_from_password(password):
    kdf = PBKDF2HMAC(algorithm = hashes.SHA256(), length = 32, salt = b'salt', iterations = 100000)
    return Fernet(base64.urlsafe_b64encode(kdf.derive(bytearray(password, "utf-8"))))


def _start(message, text=None):
    text = text or "Привет, я - бот для сокрытия данных в тексте, картинках или аудио. С помощью меня ты " \
                   "можешь спрятать сообщение в файле, или наоборот - " \
                   "восстановить сообщение из файла. Для того чтобы работать с ботом нужно использовать встроенные кнопки"

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("/Фото")
    btn2 = types.KeyboardButton("/Аудио")
    btn3 = types.KeyboardButton("/Видео")
    btn4 = types.KeyboardButton("/Текст")
    btn5 = types.KeyboardButton("/pdf")

    if message.from_user.id not in session_store:
        btn6 = types.KeyboardButton("/Установить_пароль")
    else:
        btn6 = types.KeyboardButton("/Сбросить_пароль")

    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)

    bot.send_message(message.chat.id, text=text, reply_markup=markup)

@bot.message_handler(commands=['start']) #регистрирование в структуре телеграм бота
@report_errors
def start(message):
    return _start(message)

@report_errors
def photo_menu(message):
    # выключаем меню
    markup = types.ReplyKeyboardRemove()

    if (message.text == '/Закoдировать'):
        bot.send_message(message.chat.id, "Отправь текстовое сообщение, которое ты хочешь спрятать:", reply_markup=markup)
        bot.register_next_step_handler(message, encode_pic_txt)

    elif (message.text == '/Декoдировать'):
        bot.send_message(message.chat.id, "Отправь картинку, в которой было спрятано сообщение. Она должна быть отправлена без сжатия в формате PNG!", reply_markup=markup)
        bot.register_next_step_handler(message, decode_pic)

    else:
        _start(message, "Такой команды не существует :(")


@report_errors
def audio_menu(message):
    # выключаем меню
    markup = types.ReplyKeyboardRemove()

    if (message.text == "/Спрятать"):
    	bot.send_message(message.chat.id, "Отправь текстовое сообщение, которое ты хочешь спрятать:", reply_markup=markup)
    	bot.register_next_step_handler(message, encode_audio_txt)

    elif (message.text == "/Извлечь"):
        bot.send_message(message.chat.id, "Отправь аудио, в котором было спрятано сообщение, в формате ogg", reply_markup=markup)
        bot.register_next_step_handler(message, decode_audio)

    else:
        _start(message, "Такой команды не существует :(")

@report_errors
def video_menu(message):
    # выключаем меню
    markup = types.ReplyKeyboardRemove()

    if (message.text == "/Спрятать"):
        bot.send_message(message.chat.id, "Отправь текстовое сообщение, которое ты хочешь спрятать:", reply_markup=markup)
        bot.register_next_step_handler(message, encode_video_txt)

    elif (message.text == "/Извлечь"):
        bot.send_message(message.chat.id, "Отправь видео, в котором было спрятано сообщение, в формате mov", reply_markup=markup)
        bot.register_next_step_handler(message, decode_video)

    else:
        _start(message, "Такой команды не существует :(")

@report_errors
def text_menu(message):
    # выключаем меню
    markup = types.ReplyKeyboardRemove()

    if (message.text == "/Спрятать"):
    	bot.send_message(message.chat.id, "Отправь текстовое сообщение, которое ты хочешь спрятать:", reply_markup=markup)
    	bot.register_next_step_handler(message, encode_text_txt)

    elif (message.text == "/Извлечь"):
        bot.send_message(message.chat.id, "Отправь текст, в котором было спрятано сообщение, в формате .TXT", reply_markup=markup)
        bot.register_next_step_handler(message, decode_text_file)

    else:
        _start(message, "Такой команды не существует :(")

@report_errors
def pdf_menu(message):
    # выключаем меню
    markup = types.ReplyKeyboardRemove()

    if (message.text == "/Спрятать"):
        bot.send_message(message.chat.id, "Отправь текстовое сообщение, которое ты хочешь спрятать:", reply_markup=markup)
        bot.register_next_step_handler(message, encode_pdf_txt)

    elif (message.text == "/Извлечь"):
        bot.send_message(message.chat.id, "Отправь pdf, в котором было спрятано сообщение, в формате .pdf", reply_markup=markup)
        bot.register_next_step_handler(message, decode_pdf_file)

    else:
        _start(message, "Такой команды не существует :(")


@bot.message_handler(content_types=['text'], func=lambda msg: msg.text is not None and '/' in msg.text)
@report_errors
def command(message):
    if (message.text == "/Фото"):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("/Закoдировать")
        btn2 = types.KeyboardButton("/Декoдировать")
        markup.add(btn1, btn2)
        bot.register_next_step_handler(message, photo_menu)
        bot.send_message(message.chat.id, text="Выбери операцию для фото", reply_markup=markup)

    elif (message.text == "/Аудио"):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("/Спрятать")
        btn2 = types.KeyboardButton("/Извлечь")
        markup.add(btn1, btn2)
        bot.register_next_step_handler(message, audio_menu)
        bot.send_message(message.chat.id, text="Выбери операцию для аудио", reply_markup=markup)

    elif (message.text == "/Видео"):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("/Спрятать")
        btn2 = types.KeyboardButton("/Извлечь")
        markup.add(btn1, btn2)
        bot.register_next_step_handler(message, video_menu)
        bot.send_message(message.chat.id, text="Выбери операцию для видео", reply_markup=markup)

    elif (message.text == "/Текст"):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("/Спрятать")
        btn2 = types.KeyboardButton("/Извлечь")
        markup.add(btn1, btn2)
        bot.register_next_step_handler(message, text_menu)
        bot.send_message(message.chat.id, text="Выбери операцию для текста", reply_markup=markup)

    elif (message.text == "/pdf"):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("/Спрятать")
        btn2 = types.KeyboardButton("/Извлечь")
        markup.add(btn1, btn2)
        bot.register_next_step_handler(message, pdf_menu)
        bot.send_message(message.chat.id, text="Выбери операцию для pdf", reply_markup=markup)

    elif (message.text == '/Установить_пароль'):
        # выключаем меню
        markup = types.ReplyKeyboardRemove()
        bot.register_next_step_handler(message, set_password)
        bot.send_message(message.chat.id, text="Введите пароль:", reply_markup=markup)

    elif (message.text == '/Сбросить_пароль'):
        if message.from_user.id in session_store:
            del session_store[message.from_user.id]

        _start(message, "Пароль выключен")
    else:
        _start(message, "Такой команды не существует :(")


@report_errors
def set_password(message):
    session_store[message.from_user.id] = message.text.strip()
    _start(message, "Пароль установлен")


@report_errors
def encode_pic_txt(message2):
    text = message2.text
    bot.send_message(message2.chat.id, "Отправь картинку, в который хочешь спрятать данный текст. ВАЖНО! Она должна быть отправлена без сжатия для того, чтобы при дальнейшей пересылке сообщения изображение не искажалось. Формат картинки не важен")
    bot.register_next_step_handler(message2, lambda message: handle_photo(message, text))

@report_errors
def encode_audio_txt(message2):
    text = message2.text
    bot.send_message(message2.chat.id, "Отправь аудиосообщение, в котором ты хочешь спрятать данный текст. ВАЖНО! Оно должно быть по длительности больше 30 секунд")
    bot.register_next_step_handler(message2, lambda message: handle_audio(message, text))

@report_errors
def encode_video_txt(message2):
    text = message2.text
    bot.send_message(message2.chat.id, "Отправь видео, в котором ты хочешь спрятать данный текст")
    bot.register_next_step_handler(message2, lambda message: handle_video(message, text))

@report_errors
def encode_text_txt(message2):
    text = message2.text
    bot.send_message(message2.chat.id, "Отправь текстовый файл, в котором ты хочешь спрятать данный текст. ВАЖНО! Он должен быть в формате .TXT")
    bot.register_next_step_handler(message2, lambda message: handle_text_file(message, text))

@report_errors
def encode_pdf_txt(message2):
    text = message2.text
    bot.send_message(message2.chat.id, "Отправь текстовый файл, в котором ты хочешь спрятать данный текст. ВАЖНО! Он должен быть в формате .pdf")
    bot.register_next_step_handler(message2, lambda message: handle_pdf_file(message, text))

@report_errors
def handle_audio(message, text):
    password = session_store.get(message.from_user.id)
    print('encode audio with password:', password)

    file_info = bot.get_file(message.voice.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    with NamedTemporaryFile(mode='w+b', suffix='.ogg',) as audio_file, \
         NamedTemporaryFile(mode='w+', suffix='.txt') as message_file, \
         NamedTemporaryFile(mode='w+b', suffix='.ogg') as stego_file:

         audio_file.write(downloaded_file)
         audio_file.flush()
         message_file.write(text)
         message_file.flush()

         bot.reply_to(message, 'Запись принята и находится в обработке. Пожалуйста, подождите!')

         subprocess.check_call([sys.executable,
                                os.path.join(os.path.dirname(__file__), 'as4pgc.py'),
                                '-w', message_file.name, audio_file.name,
                                '-f', stego_file.name,
                                '-P', password or '123456'])

         stego_file.seek(0)
         bot.send_audio(message.chat.id, stego_file)
         _start(message, "операция успешно завершена")


# порезать строку на куски длинной b
def batch(s, b):
    i = 0
    res = []

    while i < len(s):
        res.append(s[i: i + b])
        i += b

    return res

@report_errors
def handle_video(message, text):
    password = session_store.get(message.from_user.id)
    print('encode video with password:', password)

    file_info = bot.get_file(message.video.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # шифрование текста
    msg_bin = key_from_password(password or '123456').encrypt(text.encode('utf-8'))

    # переводим текст в кодировку base64 чтобы решить проблему русских букв
    b64_text = base64.encodebytes(msg_bin).decode()

    with TemporaryDirectory() as tmp, \
         NamedTemporaryFile(mode='w+b', suffix='.mov',) as video_file, \
         NamedTemporaryFile(mode='w+b', suffix='.mov') as stego_file:

        video_file.write(downloaded_file)
        video_file.flush()

        bot.reply_to(message, 'Запись принята и находится в обработке. Пожалуйста, подождите!')

        # разборка видео на кадры
        subprocess.check_call(["ffmpeg", "-i", video_file.name, "{}/%d.png".format(tmp), "-y"], stdout=open(os.devnull, "w"), stderr=subprocess.STDOUT)

        # извлечение аудио дорожки
        subprocess.check_call(["ffmpeg", "-i", video_file.name, "-q:a", "0", "-map", "a", "{}/audio.mp3".format(tmp), "-y"], stdout=open(os.devnull, "w"), stderr=subprocess.STDOUT)

        # 20 байт зашифрованного текста на кадр
        for i, s in enumerate(batch(b64_text, 20)):
            f_name = "{}/{}.png".format(tmp, i + 1)
            secret_enc = stegano.lsb.hide(f_name, s)
            secret_enc.save(f_name)

        # сборка видео дорожки из кадров
        subprocess.check_call(["ffmpeg", "-i", "{}/%d.png".format(tmp) , "-vcodec", "png", "{}/video.mov".format(tmp), "-y"], stdout=open(os.devnull, "w"), stderr=subprocess.STDOUT)

        # сборка видео из видео + аудио дорожек
        subprocess.check_call(["ffmpeg", "-i", "{}/video.mov".format(tmp), "-i", "{}/audio.mp3".format(tmp), "-codec", "copy", stego_file.name, "-y"], stdout=open(os.devnull, "w"), stderr=subprocess.STDOUT)

        stego_file.seek(0)
        bot.send_document(message.chat.id, stego_file, visible_file_name='video.mov')
        _start(message, "операция успешно завершена")


@report_errors
def handle_photo(message, text):
    password = session_store.get(message.from_user.id)
    print('Encode photo with password:', password)

    # так можно посмотреть какие есть поля в объекте
    # print(dir(message))

    photo = message.document
    file_info = bot.get_file(photo.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # открываем все файлы в бинарном(то есть в не изменяемом виде)
    with TemporaryFile(mode='w+b') as source_photo, TemporaryFile(mode='w+b') as encoded_photo:
        source_photo.write(downloaded_file)
        # перемотаем текущую позицию на начало фала
        source_photo.seek(0)

        bot.reply_to(message, 'Изображение принято и находится в обработке. Пожалуйста, подождите!')

        # шифрование текста
        msg_bin = key_from_password(password or '123456').encrypt(text.encode('utf-8'))

        # переводим текст в кодировку base64 чтобы решить проблему русских букв
        b64_text = base64.encodebytes(msg_bin).decode()

        # кодирование текста в картинку:
        image = stegano.lsb.hide(source_photo, b64_text)
        image.save(encoded_photo, format='png')

        # перемотаем позицию на начало
        encoded_photo.seek(0)
        bot.send_document(message.chat.id, encoded_photo, visible_file_name='encoded_photo.png')
        _start(message, "операция успешно завершена")


@report_errors
def decode_pic(message):
    password = session_store.get(message.from_user.id)
    print('Decode photo with password:', password)

    photo = message.document
    text = message.caption
    file_info = bot.get_file(photo.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    with TemporaryFile(mode='w+b') as encoded_photo:
        encoded_photo.write(downloaded_file)
        # перемотаем текущую позицию на начало
        encoded_photo.seek(0)

        bot.reply_to(message, 'Изображение принято и находится в обработке. Пожалуйста, подождите!')

        # декодирование картинки
        b64_text = stegano.lsb.reveal(encoded_photo)

        # переводим текст обратно из кодировки base64
        text_bin = base64.decodebytes(b64_text.encode())

        # расшифровка текста
        try:
            text = key_from_password(password or '123456').decrypt(text_bin).decode('utf-8')
        except InvalidToken as v:
            raise Exception('Неверный пароль!')

        _start(message, 'secret message: ' + text)

@report_errors
def decode_video(message):
    password = session_store.get(message.from_user.id)
    print('Decode video with password:', password)

    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    with TemporaryDirectory() as tmp, \
         NamedTemporaryFile(mode='w+b', suffix='.mov') as stego_file:

         stego_file.write(downloaded_file)
         stego_file.flush()

         bot.reply_to(message, 'Запись декодируется. Пожалуйста, подождите!')

         # разборка видео на кадры
         subprocess.check_call(["ffmpeg", "-i", stego_file.name, "{}/%d.png".format(tmp), "-y"], stdout=open(os.devnull, "w"), stderr=subprocess.STDOUT)

         secret=[]
         for i in range(0, len(os.listdir(tmp))):
             f_name = "{}/{}.png".format(tmp, i + 1)

             try:
                 secret_dec = stegano.lsb.reveal(f_name)
             except IndexError:
                 break

             secret.append(secret_dec)

         b64_text = ''.join([i for i in secret])

         # переводим текст обратно из кодировки base64
         text_bin = base64.decodebytes(b64_text.encode())

         # расшифровка текста
         try:
             text = key_from_password(password or '123456').decrypt(text_bin).decode('utf-8')
         except InvalidToken as v:
             raise Exception('Неверный пароль!')

         _start(message, 'secret message: ' + text)


@report_errors
def decode_audio(message):
    password = session_store.get(message.from_user.id)
    print('Decode audio with password:', password)

    file_info = bot.get_file(message.voice.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    with NamedTemporaryFile(mode='r+', suffix='.txt') as message_file, \
         NamedTemporaryFile(mode='w+b', suffix='.ogg') as stego_file:

         stego_file.write(downloaded_file)
         stego_file.flush()

         bot.reply_to(message, 'Запись декодируется. Пожалуйста, подождите!')

         subprocess.check_call([sys.executable,
                                os.path.join(os.path.dirname(__file__), 'as4pgc.py'),
                                '-r', stego_file.name,
                                '-f', os.path.basename(message_file.name),
                                '-P', password or '123456'])

         _start(message, 'secret message: ' + open(message_file.name).read())


@report_errors
def handle_text_file(message, text):
    password = session_store.get(message.from_user.id)
    print('encode text file with password:', password)

    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    with NamedTemporaryFile(mode='w+b', suffix='.txt',) as text_file, \
         NamedTemporaryFile(mode='w+', suffix='.txt') as message_file, \
         NamedTemporaryFile(mode='w+b', suffix='.txt') as stego_file:

         text_file.write(downloaded_file)
         text_file.flush()
         message_file.write(text)
         message_file.flush()

         subprocess.check_call(['stegsnow',
                                '-C',
                                '-f', message_file.name,
                                '-p', password or '123456',
                                text_file.name,
                                stego_file.name
                                ])

         stego_file.seek(0)
         bot.send_document(message.chat.id, stego_file, visible_file_name='encoded_text.txt')
         _start(message, "операция успешно завершена")


@report_errors
def decode_text_file(message):
    password = session_store.get(message.from_user.id)
    print('Decode text with password:', password)

    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    with NamedTemporaryFile(mode='r+', suffix='.txt') as message_file, \
         NamedTemporaryFile(mode='w+b', suffix='.txt') as stego_file:

         stego_file.write(downloaded_file)
         stego_file.flush()

         bot.reply_to(message, 'Запись декодируется. Пожалуйста, подождите!')

         subprocess.check_call(['stegsnow',
                                '-C',
                                '-p', password or '123456',
                                stego_file.name,
                                message_file.name,
                                ])

         _start(message, 'secret message: ' + open(message_file.name).read())

@report_errors
def handle_pdf_file(message, text):
    password = session_store.get(message.from_user.id)
    print('encode pdf file with password:', password)

    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    with NamedTemporaryFile(mode='w+b', suffix='.pdf',) as pdf_file, \
         NamedTemporaryFile(mode='w+', suffix='.txt') as message_file, \
         NamedTemporaryFile(mode='w+b', suffix='.txt') as stego_file:

         pdf_file.write(downloaded_file)
         pdf_file.flush()
         message_file.write(text)
         message_file.flush()

         subprocess.check_call(['./pdf_hide',
                                '-o', stego_file.name,
                                '-k', password or '123456',
                                'embed',
                                message_file.name,
                                pdf_file.name
                                ])

         stego_file.seek(0)
         bot.send_document(message.chat.id, stego_file, visible_file_name='encoded_pdf.pdf')
         _start(message, "операция успешно завершена")

@report_errors
def decode_pdf_file(message):
    password = session_store.get(message.from_user.id)
    print('Decode pdf with password:', password)

    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    with NamedTemporaryFile(mode='r+', suffix='.txt') as message_file, \
         NamedTemporaryFile(mode='w+b', suffix='.pdf') as stego_file:

         stego_file.write(downloaded_file)
         stego_file.flush()

         bot.reply_to(message, 'Запись декодируется. Пожалуйста, подождите!')

         subprocess.check_call(['./pdf_hide',
                                '-o', message_file.name,
                                '-k', password or '123456',
                                'extract',
                                stego_file.name,
                                ])

         _start(message, 'secret message: ' + open(message_file.name).read())

while True:
        try:
            bot.polling()
            break
        except Exception as v:
            print('Unhandled error:', v)
