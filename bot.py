# imports
import random
import threading
from telebot import types
# bot initial configuration
from config import *


# handling database
def add_audio(message):
    conn = sqlite3.connect('database.db')
    try:
        conn.execute("INSERT INTO MUSIC (CHAT_ID, MUSIC_NAME, MUSIC_FILE_ID , PERFORMER) VALUES (?, ?, ? , ?)",
                     (channel_id_number, message.audio.title, message.audio.file_id, message.audio.performer))
        conn.commit()
    except Exception as e:
        pass
    conn.close()


def get_audios():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM MUSIC")
    result = cursor.fetchall()
    conn.close()
    return result


def have_audio(message):
    audios = get_audios()
    for audio in audios:
        if audio[1] == message.audio.title and audio[3] == message.audio.performer:
            return True
    return False


# bot menu
def menu(message):
    if message.chat.type == "private" and sign_key_creator(message.chat) in get_admins():
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        itembtn1 = types.KeyboardButton('اضافه کردن امضا')
        itembtn2 = types.KeyboardButton('حذف امضا')
        itembtn3 = types.KeyboardButton('مشاهده امضا')
        # itembtn4 = types.KeyboardButton('فعال / غیر فعال کردن نمایش فرستنده')
        itembtn5 = types.KeyboardButton('سرچ در بین آهنگ ها')
        itembtn6 = types.KeyboardButton('پلی لیست تصادفی')
        itembtn7 = types.KeyboardButton('اطلاعات آرشیو')
        itembtn8 = types.KeyboardButton('راهنما')
        itembtn9 = types.KeyboardButton('ارسال انتقاد / پیشنهاد به ادمین')
        markup.row(itembtn1, itembtn2)
        markup.row(itembtn3)
        markup.row(itembtn5, itembtn6)
        markup.row(itembtn7, itembtn8)
        markup.row(itembtn9)
        bot.send_message(message.chat.id, "دستور خود را وارد کنید", reply_markup=markup)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        itembtn5 = types.KeyboardButton('سرچ در بین آهنگ ها')
        itembtn6 = types.KeyboardButton('پلی لیست تصادفی')
        itembtn7 = types.KeyboardButton('اطلاعات آرشیو')
        itembtn8 = types.KeyboardButton('راهنما')
        itembtn9 = types.KeyboardButton('ارسال انتقاد / پیشنهاد به ادمین')
        markup.row(itembtn5, itembtn6)
        markup.row(itembtn7, itembtn8)
        markup.row(itembtn9)
        bot.send_message(message.chat.id, "دستور خود را وارد کنید", reply_markup=markup)


def audio_menu(message):
    custom_sign_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    custom_sign_keyboard.row(types.KeyboardButton('اضافه کردن کپشن'), types.KeyboardButton('اضافه کردن lyrics'))
    custom_sign_keyboard.row(types.KeyboardButton('برگشت'))
    custom_sign_keyboard.row(types.KeyboardButton('ارسال'))
    bot.send_message(message.chat.id, "لطفا دستور مورد نظر خود را وارد نمایید", reply_markup=custom_sign_keyboard)
    reply_mode[message.chat.id] = "audio"


# Handling functions

def handle_caption_exception(message):
    caption = "None"
    try:
        caption = message.caption
    except:
        pass
    logging.warning(f" prev caption : {caption}")


def get_admins():
    result = []
    for admin in bot.get_chat_administrators(channel_id_number):
        if admin.user.last_name is not None:
            result.append(admin.user.first_name + " " + admin.user.last_name)
        else:
            result.append(admin.user.first_name)
    return result


def sign_key_creator(user):
    if user.last_name is not None:
        return user.first_name + " " + user.last_name
    else:
        return user.first_name


def get_admin_id(admin_sign):
    for admin in bot.get_chat_administrators(channel_id_number):
        if admin.user.last_name is not None:
            if admin.user.first_name + " " + admin.user.last_name == admin_sign:
                return admin.user.id
        else:
            if admin.user.first_name == admin_sign:
                return admin.user.id
    return None


def admin_show_help(message):
    help_text = "راهنما" + '\n' + """میتوانید امضای شخصی خود را اضافه کنید تا در همه آهنگ های ارسالی خودتان اضافه شود
آهنگ خود را ارسال کنید تا از طریق بات با متنی دلخواه در کانال ارسال شود
می توانید از آرشیو کانال در بات استفاده کنید و از امکاناتی مانند سرچ و پلی لیست تصادفی استفاده کنید  
"""
    bot.send_message(message.chat.id, help_text)


def user_show_help(message):
    help_text = "راهنما" + '\n' + """
می توانید از آرشیو کانال در بات استفاده کنید و از امکاناتی مانند سرچ و پلی لیست تصادفی استفاده کنید  
"""
    bot.send_message(message.chat.id, help_text)


def get_sign(admin_name):
    if signs != {} and signs is not None:
        if admin_name in signs.keys():
            return signs[admin_name]
    return None


def add_sign(admin_name, sign):
    global signs
    if signs == {} or signs is None:
        signs = {}
    signs[admin_name] = sign
    signs_file = open(signs_file_name, 'wb')
    pickle.dump(signs, signs_file)
    signs_file.close()


def change_sign_mode(admin_id, mode):
    global sign_mode
    if sign_mode == {} or sign_mode is None:
        sign_mode = {}
    sign_mode[admin_id] = mode
    sign_mode_file = open(sign_mode_file_name, 'wb')
    pickle.dump(sign_mode, sign_mode_file)
    sign_mode_file.close()


def add_group(group_id):
    global groups
    if groups is None:
        groups = []
    if group_id not in groups:
        groups.append(group_id)
        groups_file = open(groups_file_name, 'wb')
        pickle.dump(groups, groups_file)
        groups_file.close()


# handling start of the bot in private mode
@bot.message_handler(commands=['start'])
def greet(message):
    greet_text = "\nبه بخش بات  خوش اومدی"
    if message.chat.type == "private":
        if sign_key_creator(message.chat) in get_admins():
            bot.send_message(message.chat.id, "سلام " + message.chat.first_name + greet_text)
            menu(message)
        else:
            bot.send_message(message.chat.id, "سلام " + message.chat.first_name + greet_text)
            menu(message)


# managing commands
@bot.message_handler(commands=['archive'])
def archive(message):
    if sign_key_creator(message.chat) in get_admins():
        handle_caption_exception(message)
        # bot.send_audio(channel_id_number , message.audio.file_id , caption = "sender: " + sign_key_creator(message.chat) + "\n")
        conn = sqlite3.connect('database.db')
        cursor = conn.execute("SELECT * FROM MUSIC")
        count = 0
        for row in cursor:
            count += 1
        bot.send_message(message.chat.id, str(len(get_audios())))
        conn.close()
    else:
        bot.send_message(message.chat.id, "شما ادمین نیستید")
        menu(message)


def artists_file(message):
    if sign_key_creator(message.chat) in get_admins():
        songs = get_audios()
        artists = []
        for song in songs:
            if song is None:
                continue
            if song[3] is None:
                continue
            if song[3] not in artists:
                artists.append(song[3])
        artists_text = ""
        i = 1
        for artist in artists:
            artists_text += str(i) + " " + artist + "\n"
            i += 1
        with open("artists.txt", "w") as text_file:
            text_file.write(artists_text)
        bot.send_document(message.chat.id, document=open("artists.txt", "rb"))
    else:
        bot.send_message(message.chat.id, "شما ادمین نیستید")
        menu(message)


@bot.message_handler(commands=['artists'])
def archive(message):
    if message.chat.type == "private":
        threading.Thread(target=artists_file, args=(message,)).start()


# handiling audio in private mode
@bot.message_handler(content_types=['audio'])
def handle_audio(message):
    if message.chat.type == "private":
        if sign_key_creator(message.chat) in get_admins():
            handle_caption_exception(message)
            if have_audio(message):
                bot.send_message(message.chat.id, """به نظر میاد آهنگ تو آرشیو کانال موجوده!
بعد از ارسال آهنگ با هشتک #repost ارسال میشه
اگر آهنگ از کانال پاک شده باشه هم تو آرشیو نشون داده میشه پس حواست باشه
                """)
            audio_pv_forward[message.chat.id] = {
                "file_id": message.audio.file_id,
                "caption": "",
                "lyrics": "",
                "repost": have_audio(message),
            }
            audio_database[message.chat.id] = message
            audio_menu(message)
        else:
            bot.send_message(message.chat.id, "شما ادمین نیستید")
            menu(message)


# handling menu
@bot.message_handler(regexp="اضافه کردن امضا")
def handle_message(message):
    if message.chat.type == "private":
        if sign_key_creator(message.chat) in get_admins():
            reply_mode[message.chat.id] = "add_sign"
            custom_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            custom_keyboard.row(types.KeyboardButton('برگشت'))
            bot.send_message(message.chat.id, "لطفا امضای شخصی خود را وارد کنید", reply_markup=custom_keyboard)


@bot.message_handler(regexp="اضافه کردن lyrics")
def handle_message(message):
    if message.chat.type == "private":
        if sign_key_creator(message.chat) in get_admins():
            reply_mode[message.chat.id] = "add_lyrics"
            custom_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            custom_keyboard.row(types.KeyboardButton('برگشت به منوی آهنگ'))
            bot.send_message(message.chat.id, "لطفا lyrics خود را وارد کنید", reply_markup=custom_keyboard)


@bot.message_handler(regexp="ارسال انتقاد / پیشنهاد به ادمین")
def handle_message(message):
    if message.chat.type == "private":
        reply_mode[message.chat.id] = "send_suggestion"
        custom_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        custom_keyboard.row(types.KeyboardButton('برگشت'))
        bot.send_message(message.chat.id, "لطفا نظر خود را ارسال نمایید", reply_markup=custom_keyboard)


@bot.message_handler(regexp="اضافه کردن کپشن")
def handle_message(message):
    if message.chat.type == "private":
        if sign_key_creator(message.chat) in get_admins():
            reply_mode[message.chat.id] = "add_caption_to_audio"
            custom_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            custom_keyboard.row(types.KeyboardButton('برگشت به منوی آهنگ'))
            bot.send_message(message.chat.id, "لطفا کپشن را وارد کنید", reply_markup=custom_keyboard)


@bot.message_handler(regexp="سرچ در بین آهنگ ها")
def handle_message(message):
    if message.chat.type == "private":
        reply_mode[message.chat.id] = "search"
        custom_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        custom_keyboard.row(types.KeyboardButton('برگشت'))
        bot.send_message(message.chat.id, "لطفا محتوای سرچ خود را وارد کنید", reply_markup=custom_keyboard)


@bot.message_handler(regexp="مشاهده امضا")
def handle_message(message):
    if message.chat.type == "private":
        if sign_key_creator(message.chat) in get_admins():
            sign = get_sign(sign_key_creator(message.chat))
            if sign == None:
                bot.send_message(message.chat.id, "شما امضایی ندارید")
            else:
                bot.send_message(message.chat.id, sign)


@bot.message_handler(regexp="پلی لیست تصادفی")
def handle_message(message):
    if message.chat.type == "private":
        reply_mode[message.chat.id] = "random_playlist"
        custom_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        custom_keyboard.row(types.KeyboardButton('برگشت'))
        bot.send_message(message.chat.id, "لطفا تعداد آهنگ های تصادفی خودتو بگو (بین ۱ تا ۱۰)",
                         reply_markup=custom_keyboard)


@bot.message_handler(regexp="حذف امضا")
def handle_message(message):
    if message.chat.type == "private":
        if sign_key_creator(message.chat) in get_admins():
            sign = get_sign(sign_key_creator(message.chat))
            if sign == None:
                bot.send_message(message.chat.id, "شما امضایی ندارید")
            else:
                # add_sign(sign_key_creator(message.chat), None)
                custom_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                custom_keyboard.row(types.KeyboardButton('آره امضا رو حذف کن'))
                custom_keyboard.row(types.KeyboardButton('برگشت'))
                bot.send_message(message.chat.id, "آیا از حذف امضا مطمئنی؟", reply_markup=custom_keyboard)


@bot.message_handler(regexp="آره امضا رو حذف کن")
def handle_message(message):
    if message.chat.type == "private":
        if sign_key_creator(message.chat) in get_admins():
            add_sign(sign_key_creator(message.chat), None)
            bot.send_message(message.chat.id, "امضا حذف شد")
            menu(message)


@bot.message_handler(regexp="راهنما")
def handle_message(message):
    if message.chat.type == "private":
        if sign_key_creator(message.chat) in get_admins():
            admin_show_help(message)
            menu(message)
        else:
            user_show_help(message)
            menu(message)


@bot.message_handler(regexp="ارسال")
def handle_message(message):
    if message.chat.type == "private":
        if sign_key_creator(message.chat) in get_admins() and message.chat.id in audio_pv_forward.keys():
            user_sign = ""
            if get_sign(sign_key_creator(message.chat)) is not None:
                user_sign = f"\n{get_sign(sign_key_creator(message.chat))}"
            if audio_pv_forward[message.chat.id]['repost']:
                user_sign = f"\n#repost"
            if audio_pv_forward[message.chat.id]["caption"] == "":

                if message.from_user.id in sign_mode.keys() and sign_mode[message.from_user.id] is False:
                    bot.send_audio(channel_id_number, audio_pv_forward[message.chat.id]["file_id"],
                                   caption=f"{user_sign}\n{channel_id}")
                    if audio_pv_forward[message.chat.id]['lyrics'] != "":
                        bot.send_message(channel_id_number, audio_pv_forward[message.chat.id]['lyrics'])
                    logging.info("forwarded audio from pv")
                    add_audio(audio_database[message.chat.id])
                    bot.send_message(message.chat.id, "آهنگ با موفقیت ارسال شد")
                    menu(message)
                    for group_id in groups:
                        bot.send_audio(group_id, audio_pv_forward[message.chat.id]["file_id"],
                                       caption=f"{user_sign}\n{channel_id}")
                        logging.info("forwarded message")
                    audio_pv_forward.pop(message.chat.id)

                else:

                    bot.send_audio(channel_id_number, audio_pv_forward[message.chat.id]["file_id"],
                                   caption=f"🎼 {sign_key_creator(message.chat)}{user_sign}\n{channel_id}")
                    if audio_pv_forward[message.chat.id]['lyrics'] != "":
                        bot.send_message(channel_id_number, audio_pv_forward[message.chat.id]['lyrics'])
                    logging.info("forwarded audio from pv")
                    add_audio(audio_database[message.chat.id])
                    bot.send_message(message.chat.id, "آهنگ با موفقیت ارسال شد")
                    menu(message)
                    for group_id in groups:
                        bot.send_audio(group_id, audio_pv_forward[message.chat.id]["file_id"],
                                       caption=f"🎼 {sign_key_creator(message.chat)}{user_sign}\n{channel_id}")
                        logging.info("forwarded message")
                    audio_pv_forward.pop(message.chat.id)
            else:
                if message.from_user.id in sign_mode.keys() and sign_mode[message.from_user.id] is False:

                    bot.send_audio(channel_id_number, audio_pv_forward[message.chat.id]["file_id"],
                                   caption=f"{user_sign}\n{audio_pv_forward[message.chat.id]['caption']}\n{channel_id}")
                    if audio_pv_forward[message.chat.id]['lyrics'] != "":
                        bot.send_message(channel_id_number, audio_pv_forward[message.chat.id]['lyrics'])
                    add_audio(audio_database[message.chat.id])
                    bot.send_message(message.chat.id, "آهنگ با موفقیت ارسال شد")
                    menu(message)
                    for group_id in groups:
                        bot.send_audio(group_id, audio_pv_forward[message.chat.id]["file_id"],
                                       caption=f"{user_sign}\n{audio_pv_forward[message.chat.id]['caption']}\n{channel_id}")
                        logging.info("forwarded message")
                    audio_pv_forward.pop(message.chat.id)

                else:
                    bot.send_audio(channel_id_number, audio_pv_forward[message.chat.id]["file_id"],
                                   caption=f"🎼 {sign_key_creator(message.chat)}\n{audio_pv_forward[message.chat.id]['caption']}{user_sign}\n{channel_id}")
                    if audio_pv_forward[message.chat.id]['lyrics'] != "":
                        bot.send_message(channel_id_number, audio_pv_forward[message.chat.id]['lyrics'])
                    add_audio(audio_database[message.chat.id])
                    bot.send_message(message.chat.id, "آهنگ با موفقیت ارسال شد")
                    menu(message)
                    for group_id in groups:
                        bot.send_audio(group_id, audio_pv_forward[message.chat.id]["file_id"],
                                       caption=f"🎼 {sign_key_creator(message.chat)}\n{audio_pv_forward[message.chat.id]['caption']}{user_sign}\n{channel_id}")
                        logging.info("forwarded message")
                    audio_pv_forward.pop(message.chat.id)


@bot.message_handler(regexp="اطلاعات آرشیو")
def handle_message(message):
    if message.chat.type == "private":
        songs = get_audios()
        artists = []
        artist_count = 0
        for song in songs:
            if song[3] is not None and song[3] not in artists:
                artists.append(song[3])
                artist_count += 1
        bot.send_message(message.chat.id,
                         "تعداد آهنگ ها: " + str(len(songs)) + "\nتعداد آرتیست ها: " + str(artist_count))


# handling replies
@bot.message_handler()
def message_handler(message):
    if message.chat.type == "private" and message.text == "برگشت":
        menu(message)
        return

    if message.chat.type == "private" and message.text == "برگشت به منوی آهنگ":
        audio_menu(message)
        return


    elif (message.chat.type == "group" or message.chat.type == "supergroup") and sign_key_creator(
            message.from_user) in get_admins():
        if message.text == "/addbot":
            # remember that bot should be admin in the group
            add_group(message.chat.id)
            bot.send_message(message.chat.id, "آهنگ ها از کانال به گروه فوروارد خواهند شد")

        if message.text == "/removebot":
            # remember that bot should be admin in the group
            if message.chat.id in groups:
                groups.remove(message.chat.id)
                groups_file = open(groups_file_name, 'wb')
                pickle.dump(groups, groups_file)
                groups_file.close()
                bot.send_message(message.chat.id, "بات از لیست گروه ها حذف شد")
            else:
                bot.send_message(message.chat.id, "این گروه در لیست گروه های بات نیست")
    if message.chat.type == "private" and message.chat.id in reply_mode.keys():
        if reply_mode[message.chat.id] == "add_sign":
            key = sign_key_creator(message.chat)
            add_sign(key, message.text)
            reply_mode.pop(message.chat.id)
            bot.send_message(message.chat.id, "امضای مورد نظر با موفقیت اضافه شد")
            menu(message)
    if message.chat.type == "private" and message.chat.id in reply_mode.keys():
        if reply_mode[message.chat.id] == "send_suggestion":
            bot.send_message(suggestion_channel_id,
                             f"پیشنهاد جدید از طرف {message.chat.first_name} {message.chat.last_name}:\n@{message.chat.username}\n{message.text}")
            bot.reply_to(message, "پیشنهاد شما با موفقیت ارسال شد")
            menu(message)
    if message.chat.type == "private" and message.chat.id in reply_mode.keys():
        if reply_mode[message.chat.id] == "add_caption_to_audio":
            audio_pv_forward[message.chat.id]["caption"] = message.text
            bot.send_message(message.chat.id, "کپشن با موفقیت اضافه شد")
            audio_menu(message)
    if message.chat.type == "private" and message.chat.id in reply_mode.keys():
        if reply_mode[message.chat.id] == "add_lyrics":
            audio_pv_forward[message.chat.id]["lyrics"] = message.text
            bot.send_message(message.chat.id, "lyrics با موفقیت اضافه شد")
            audio_menu(message)
    if message.chat.type == "private" and message.chat.id in reply_mode.keys():
        if reply_mode[message.chat.id] == "search":
            songs = get_audios()
            is_found = False
            for song in songs:
                if song is None:
                    continue
                if song[3] is None or song[1] is None:
                    continue
                if message.text.lower() in song[1].lower() or message.text.lower() in song[3].lower():
                    bot.send_audio(message.chat.id, song[2], caption=channel_id)
                    is_found = True
            if not is_found:
                bot.send_message(message.chat.id, "موردی یافت نشد")
            menu(message)
    if message.chat.type == "private" and message.chat.id in reply_mode.keys():
        if reply_mode[message.chat.id] == "random_playlist":
            songs = get_audios()
            random_number = 0
            try:
                random_number = int(message.text)
            except Exception:
                bot.send_message(message.chat.id, "لطفا یک عدد وارد کنید")
                return
            if random_number > len(songs):
                bot.send_message(message.chat.id, "تعداد آهنگ درخواستی بیشتر از آرشیو کانال است دوباره تلاش کنید")
                return
            if random_number > 10:
                bot.send_message(message.chat.id, "حداکثر تعداد آهنگ 10 میباشد")
                return

            random_songs = random.sample(songs, random_number)
            for song in random_songs:
                bot.send_audio(message.chat.id, song[2], caption=channel_id)
            menu(message)
    if message.chat.type == "private" and message.chat.id in reply_mode.keys():
        reply_mode.pop(message.chat.id)


# handling channel
@bot.channel_post_handler(content_types=['audio'])
def edit_message(message):
    # debug
    if message.author_signature is not None and message.author_signature in get_admins():
        user_sign = ""
        if get_sign(message.author_signature) is not None:
            user_sign = f"\n{get_sign(message.author_signature)}"
        if message.caption is None:
            message.caption = ""
        if get_admin_id(message.author_signature) in sign_mode.keys() and sign_mode[
            get_admin_id(message.author_signature)] is False:
            bot.send_audio(channel_id_number, message.audio.file_id, caption=f"{user_sign}\n{channel_id}")
            for group_id in groups:
                bot.send_audio(group_id, message.audio.file_id, caption=f"{user_sign}\n{channel_id}")
                logging.info("forwarded message")
            bot.delete_message(channel_id_number, message.message_id)
            add_audio(message)
        else:
            bot.send_audio(channel_id_number, message.audio.file_id,
                           caption=f"🎼 {message.author_signature}{user_sign}\n{channel_id}")
            for group_id in groups:
                bot.send_audio(group_id, message.audio.file_id,
                               caption=f"🎼 {message.author_signature}{user_sign}\n{channel_id}")
                logging.info("forwarded message")
            bot.delete_message(channel_id_number, message.message_id)
            add_audio(message)
        return


bot.infinity_polling()
