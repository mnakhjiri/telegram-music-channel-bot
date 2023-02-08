# imports
import random
import threading
from telebot import types
from config import *
import requests


# handling database


def get_genres(track_name, artist):
    from musixmatch import Musixmatch
    musixmatch = Musixmatch(music_api)
    try:
        x = musixmatch.track_search(q_track=track_name, q_artist=artist, page_size=10, page=1, s_track_rating='desc')
        genre_list = x["message"]["body"]["track_list"][0]["track"]["primary_genres"]["music_genre_list"]
    except Exception as e:
        print(str(e))
        return []
    if len(genre_list) == 0:
        return []

    result = []
    for i in genre_list:
        result.append(i["music_genre"]["music_genre_name"])
    return result


def add_audio(message):
    conn = sqlite3.connect('database.db')
    try:
        conn.execute("INSERT INTO MUSIC (CHAT_ID, MUSIC_NAME, MUSIC_FILE_ID , PERFORMER) VALUES (?, ?, ? , ?)",
                     (channel_id_number, message.audio.title, message.audio.file_id, message.audio.performer))
        conn.commit()
    except Exception as e:
        pass
    conn.close()


def create_or_get_playlist(chat_id, playlist_name):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"SELECT CHAT_ID, NAME FROM PLAYLISTS WHERE CHAT_ID = \"{chat_id}\" AND NAME = \"{playlist_name}\";")
    except:
        conn.execute("INSERT INTO PLAYLISTS (CHAT_ID, NAME) VALUES (?, ?)",
                     (chat_id, playlist_name))
        conn.commit()
        cursor.execute(
            f"SELECT CHAT_ID, NAME FROM PLAYLISTS where CHAT_ID = \"{chat_id}\"  AND NAME = \"{playlist_name}\";")

    result = cursor.fetchall()
    if len(result) != 0:
        for item in result:
            conn.close()
            return item[0]


def add_to_playlist(chat_id, music_id, playlist_name, music_name, performer):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT MUSIC_FILE_ID, CHAT_ID FROM PLAYLIST_MUSICS where CHAT_ID = \"{chat_id}\" AND PLAYLISTNAME = \"{playlist_name}\" and MUSICNAME = \"{music_name}\" and PERFORMER = \"{performer}\"; ")
    result = cursor.fetchall()
    if len(result) == 0:
        conn.execute(
            "INSERT INTO PLAYLIST_MUSICS (CHAT_ID, PLAYLISTNAME, MUSIC_FILE_ID, MUSICNAME, PERFORMER) VALUES (?, ?, ?, ?, ?)",
            (chat_id, playlist_name, music_id, music_name, performer))
        conn.commit()
    conn.close()


def remove_from_playlist(chat_id, music_id, playlist_name, music_name, performer):
    conn = sqlite3.connect('database.db')
    print("hi")
    try:
        conn.execute(
            f"DELETE FROM PLAYLIST_MUSICS where CHAT_ID = \"{chat_id}\" AND PLAYLISTNAME = \"{playlist_name}\" and MUSICNAME = \"{music_name}\" and PERFORMER = \"{performer}\";")
        conn.commit()
    except Exception as e:
        print(str(e))
    conn.close()


def get_from_playlist(chat_id, playlist_name):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT MUSIC_FILE_ID, CHAT_ID FROM PLAYLIST_MUSICS where CHAT_ID = \"{chat_id}\" AND PLAYLISTNAME = \"{playlist_name}\";")
    result = cursor.fetchall()
    conn.close()
    return result


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

def new_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    itembtn1 = types.KeyboardButton('🏠')
    itembtn2 = types.KeyboardButton('🔎')
    itembtn3 = types.KeyboardButton('🔀')
    markup.row(itembtn1, itembtn2, itembtn3)
    return markup


def audio_menu(message):
    custom_sign_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    custom_sign_keyboard.row(types.KeyboardButton('اضافه کردن کپشن'), types.KeyboardButton('اضافه کردن lyrics'))
    custom_sign_keyboard.row(types.KeyboardButton('جست و جوی lyrics'))
    custom_sign_keyboard.row(types.KeyboardButton('ارسال'), types.KeyboardButton('برگشت'))
    bot.send_message(message.chat.id, "لطفا دستور مورد نظر خود را وارد نمایید", reply_markup=custom_sign_keyboard)
    reply_mode[message.chat.id] = "audio"


def add_sign_menu(message):
    if message.chat.type == "private":
        if sign_key_creator(message.chat) in get_admins():
            reply_mode[message.chat.id] = "add_sign"
            custom_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            custom_keyboard.row(types.KeyboardButton('برگشت'))
            bot.send_message(message.chat.id, "لطفا امضای شخصی خود را وارد کنید", reply_markup=custom_keyboard)


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


def get_home_markup():
    buttons = telebot.types.InlineKeyboardMarkup(row_width=1)
    buttons.add(telebot.types.InlineKeyboardButton(text='علاقه مندی ها', callback_data=f'favs'))
    buttons.add(telebot.types.InlineKeyboardButton(text='ارتباط با ادمین', callback_data=f'support'))
    buttons.add(telebot.types.InlineKeyboardButton(text='پروفایل', callback_data=f'profile'))
    return buttons


def get_admin_markup():
    buttons = telebot.types.InlineKeyboardMarkup(row_width=1)
    buttons.add(telebot.types.InlineKeyboardButton(text='مشاهده امضا', callback_data=f'showSign'))
    buttons.add(telebot.types.InlineKeyboardButton(text='اضافه کردن امضا', callback_data=f'addSign'))
    buttons.add(telebot.types.InlineKeyboardButton(text='حذف امضا', callback_data=f'deleteSign'))
    return buttons


def send_lyrics(message):
    result = requests.get(f"https://lyrist.vercel.app/api/:{message.audio.title}/:{message.audio.performer}")
    try:
        bot.send_message(message.chat.id, result.json()['lyrics'])
    except Exception as e:
        bot.send_message(message.chat.id, "متاسفم نتونستم lyrics آهنگتو پیدا کنم")


def send_lyrics_with_title(title, performer, message):
    result = requests.get(f"https://lyrist.vercel.app/api/:{title}/:{performer}")
    try:
        bot.send_message(message.chat.id, result.json()['lyrics'])
    except Exception as e:
        bot.send_message(message.chat.id, "متاسفم نتونستم lyrics آهنگتو پیدا کنم")


def send_sign(message):
    if message.chat.type == "private":
        if sign_key_creator(message.chat) in get_admins():
            sign = get_sign(sign_key_creator(message.chat))
            if sign == None:
                bot.send_message(message.chat.id, "شما امضایی ندارید")
            else:
                bot.send_message(message.chat.id, sign)


def delete_sign(message):
    if message.chat.type == "private":
        if sign_key_creator(message.chat) in get_admins():
            sign = get_sign(sign_key_creator(message.chat))
            if sign is None:
                bot.send_message(message.chat.id, "شما امضایی ندارید")
            else:
                # add_sign(sign_key_creator(message.chat), None)
                reply_mode[message.chat.id] = "delete_sign"
                custom_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                custom_keyboard.row(types.KeyboardButton('آره امضا رو حذف کن'))
                custom_keyboard.row(types.KeyboardButton('برگشت'))
                bot.send_message(message.chat.id, "آیا از حذف امضا مطمئنی؟", reply_markup=custom_keyboard)


# handling start of the bot in private mode
@bot.message_handler(commands=['start'])
def greet(message):
    show_home(message)


def delete_current_sessions(message):
    if message.chat.id in current_sessions:
        for current_session in current_sessions[message.chat.id]:
            try:
                bot.delete_message(message.chat.id, current_session.message_id)
            except Exception as e:
                pass

    if message.chat.type == "private" and message.chat.id in reply_mode.keys():
        reply_mode.pop(message.chat.id)


def create_session(message, messages):
    current_sessions[message.chat.id] = messages


def show_home(message, delete_message=False):
    if message.chat.type == "private":
        if sign_key_creator(message.chat) in get_admins():
            delete_current_sessions(message)
            current_session1 = bot.send_message(message.chat.id, "خانه", reply_markup=new_menu())
            current_session2 = bot.send_message(message.chat.id, "سلام " + message.chat.first_name,
                                                reply_markup=get_home_markup())
            if delete_message:
                try:
                    bot.delete_message(message.chat.id, message.message_id)
                except Exception as e:
                    pass
            current_sessions[message.chat.id] = [current_session1, current_session2]
        else:
            delete_current_sessions(message)
            current_session1 = bot.send_message(message.chat.id, "خانه", reply_markup=new_menu())
            current_session2 = bot.send_message(message.chat.id, "سلام " + message.chat.first_name,
                                                reply_markup=get_home_markup())
            if delete_message:
                try:
                    bot.delete_message(message.chat.id, message.message_id)
                except Exception as e:
                    pass
            current_sessions[message.chat.id] = [current_session1, current_session2]


def show_profile(message, delete_message=False):
    if message.chat.type == "private":
        if sign_key_creator(message.chat) in get_admins():
            delete_current_sessions(message)
            panel_message = "کاربر ادمین"
            fav_count = len(get_from_playlist(message.chat.id, "fav"))
            panel_message += "\n\n" + " تعداد آهنگ ها در لیست علاقه مندی ها : " + str(fav_count)
            current_session1 = bot.send_message(message.chat.id, "پروفایل", reply_markup=new_menu())
            current_session2 = bot.send_message(message.chat.id, panel_message,
                                                reply_markup=get_admin_markup())
            if delete_message:
                try:
                    bot.delete_message(message.chat.id, message.message_id)
                except Exception as e:
                    pass
            current_sessions[message.chat.id] = [current_session1, current_session2]
        else:
            delete_current_sessions(message)
            panel_message = "کاربر عادی"
            fav_count = len(get_from_playlist(message.chat.id, "fav"))
            panel_message += "\n\n" + " تعداد آهنگ ها در لیست علاقه مندی ها : " + str(fav_count)
            current_session1 = bot.send_message(message.chat.id, "پروفایل", reply_markup=new_menu())
            current_session2 = bot.send_message(message.chat.id, panel_message)
            if delete_message:
                try:
                    bot.delete_message(message.chat.id, message.message_id)
                except Exception as e:
                    pass
            current_sessions[message.chat.id] = [current_session1, current_session2]


def show_random(message):
    if message.chat.type == "private":
        delete_current_sessions(message)
        print("hi")
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except Exception as e:
            pass
        reply_mode[message.chat.id] = "random_playlist"
        bot.send_message(message.chat.id, "لطفا تعداد آهنگ های تصادفی خودتو بگو (بین ۱ تا ۱۰)",
                         reply_markup=new_menu())
        create_session(message, [])


def show_support(message):
    if message.chat.type == "private":
        delete_current_sessions(message)
        reply_mode[message.chat.id] = "send_suggestion"
        bot.send_message(message.chat.id, "لطفا نظر خود را ارسال نمایید", reply_markup=new_menu())
        create_session(message, [])


def show_search(message):
    if message.chat.type == "private":
        delete_current_sessions(message)
        reply_mode[message.chat.id] = "search"
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except Exception as e:
            pass
        search_message = bot.send_message(message.chat.id, "لطفا محتوای سرچ خود را وارد کنید")
        create_session(message, [search_message])


# managing commands

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


@bot.message_handler(commands=['artists'])
def archive(message):
    if message.chat.type == "private":
        threading.Thread(target=artists_file, args=(message,)).start()


# handiling audio in private mode
@bot.message_handler(content_types=['audio'])
def handle_audio(message):
    if message.chat.type == "private":
        if message.chat.id in reply_mode and reply_mode[message.chat.id] == "get_lyrics":
            threading.Thread(target=send_lyrics, args=(message,)).start()
            # reply_mode[message.chat.id] = None
            bot.send_message(message.chat.id, "لطفا منتظر بمانید")
            # menu(message)
            return
        if sign_key_creator(message.chat) in get_admins():
            handle_caption_exception(message)
            if have_audio(message):
                bot.send_message(message.chat.id, """به نظر میاد آهنگ تو آرشیو کانال موجوده!
بعد از ارسال آهنگ با هشتک #repost ارسال میشه
اگر آهنگ از کانال پاک شده باشه هم تو آرشیو نشون داده میشه پس حواست باشه
                """)
            result = ""
            try:
                genres = get_genres(message.audio.title, message.audio.performer)
                for i in genres:
                    i = i.replace(" ", "_")
                    i = i.replace("-", "_")
                    if "/" in i:
                        result += f"#{i.split('/')[0]} "
                        result += f"#{i.split('/')[1]} "
                    else:
                        result += f"#{i} "
            except Exception as e:
                print(str(e))
            audio_pv_forward[message.chat.id] = {
                "file_id": message.audio.file_id,
                "caption": "",
                "lyrics": "",
                "repost": have_audio(message),
                "genres": result,
                "title": message.audio.title,
                "performer": message.audio.performer
            }
            audio_database[message.chat.id] = message
            audio_menu(message)


# handling menu
@bot.message_handler(regexp='🏠')
def home(message):
    show_home(message, delete_message=True)


@bot.message_handler(regexp='🔎')
def search_handler(message):
    show_search(message)


@bot.message_handler(regexp='🔀')
def random_handler(message):
    show_random(message)


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


@bot.message_handler(regexp="جست و جوی lyrics")
def handle_message(message):
    if message.chat.type == "private":
        if sign_key_creator(message.chat) in get_admins():
            threading.Thread(target=send_lyrics_with_title, args=(
                audio_pv_forward[message.chat.id]["title"], audio_pv_forward[message.chat.id]["performer"],
                message)).start()


@bot.message_handler(regexp="ارسال انتقاد / پیشنهاد به ادمین")
def handle_message(message):
    if message.chat.type == "private":
        reply_mode[message.chat.id] = "send_suggestion"
        custom_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        custom_keyboard.row(types.KeyboardButton('برگشت'))
        bot.send_message(message.chat.id, "لطفا نظر خود را ارسال نمایید", reply_markup=custom_keyboard)


@bot.message_handler(regexp="دریافت lyrics")
def handle_message(message):
    if message.chat.type == "private":
        reply_mode[message.chat.id] = "get_lyrics"
        custom_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        custom_keyboard.row(types.KeyboardButton('برگشت'))
        bot.send_message(message.chat.id, "لطفا آهنگ مورد نظر خود را فوروارد نمایید.", reply_markup=custom_keyboard)


@bot.message_handler(regexp="اضافه کردن کپشن")
def handle_message(message):
    if message.chat.type == "private":
        if sign_key_creator(message.chat) in get_admins():
            reply_mode[message.chat.id] = "add_caption_to_audio"
            custom_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            custom_keyboard.row(types.KeyboardButton('برگشت به منوی آهنگ'))
            bot.send_message(message.chat.id, "لطفا کپشن را وارد کنید", reply_markup=custom_keyboard)


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


@bot.message_handler(regexp="لیست علاقه مندی ها")
def handle_message(message):
    if message.chat.type == "private":
        songs = get_from_playlist(message.chat.id, "fav")
        if len(songs) == 0:
            bot.send_message(message.chat.id, "شما آهنگی در لیست علاقه مندی ها ندارید")
        else:
            for song in songs:
                buttons = telebot.types.InlineKeyboardMarkup(
                    [[telebot.types.InlineKeyboardButton(text='❌', callback_data=f'dislikeP'),
                      telebot.types.InlineKeyboardButton(text='📃', callback_data=f'lyrics')]], row_width=1)

                # btn_1 = telebot.types.InlineKeyboardButton('❤', callback_data=f'{message.chat.id}-{song[2]}-like')
                # btn_2 = telebot.types.InlineKeyboardButton('❌', callback_data=f'{message.chat.id}-{song[2]}-dislike')
                # btn_1 = telebot.types.InlineKeyboardButton('❤')
                # btn_2 = telebot.types.InlineKeyboardButton('❌')
                # buttons.add(btn_1, btn_2)
                bot.send_audio(message.chat.id, song[0], caption=channel_id, reply_markup=buttons)


def send_favs(message):
    if message.chat.type == "private":
        songs = get_from_playlist(message.chat.id, "fav")
        if len(songs) == 0:
            bot.send_message(message.chat.id, "شما آهنگی در لیست علاقه مندی ها ندارید")
        else:
            for song in songs:
                buttons = telebot.types.InlineKeyboardMarkup(
                    [[telebot.types.InlineKeyboardButton(text='❌', callback_data=f'dislikeP'),
                      telebot.types.InlineKeyboardButton(text='📃', callback_data=f'lyrics')]], row_width=1)

                # btn_1 = telebot.types.InlineKeyboardButton('❤', callback_data=f'{message.chat.id}-{song[2]}-like')
                # btn_2 = telebot.types.InlineKeyboardButton('❌', callback_data=f'{message.chat.id}-{song[2]}-dislike')
                # btn_1 = telebot.types.InlineKeyboardButton('❤')
                # btn_2 = telebot.types.InlineKeyboardButton('❌')
                # buttons.add(btn_1, btn_2)
                bot.send_audio(message.chat.id, song[0], caption=channel_id, reply_markup=buttons)


@bot.message_handler(regexp="حذف امضا")
def handle_message(message):
    if message.chat.type == "private":
        if sign_key_creator(message.chat) in get_admins():
            sign = get_sign(sign_key_creator(message.chat))
            if sign is None:
                bot.send_message(message.chat.id, "شما امضایی ندارید")
            else:
                # add_sign(sign_key_creator(message.chat), None)
                custom_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                custom_keyboard.row(types.KeyboardButton('آره امضا رو حذف کن'))
                custom_keyboard.row(types.KeyboardButton('برگشت به صفحه اصلی'))
                bot.send_message(message.chat.id, "آیا از حذف امضا مطمئنی؟", reply_markup=custom_keyboard)


@bot.message_handler(regexp="آره امضا رو حذف کن")
def handle_message(message):
    if message.chat.type == "private":
        if sign_key_creator(message.chat) in get_admins():
            add_sign(sign_key_creator(message.chat), None)
            bot.send_message(message.chat.id, "امضا حذف شد")
            show_profile(message)


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
                                   caption=f"{user_sign}\n{channel_id}\n{audio_pv_forward[message.chat.id]['genres']}")
                    if audio_pv_forward[message.chat.id]['lyrics'] != "":
                        bot.send_message(channel_id_number, audio_pv_forward[message.chat.id]['lyrics'])
                    logging.info("forwarded audio from pv")
                    add_audio(audio_database[message.chat.id])
                    bot.send_message(message.chat.id, "آهنگ با موفقیت ارسال شد")
                    show_home(message)
                    for group_id in groups:
                        bot.send_audio(group_id, audio_pv_forward[message.chat.id]["file_id"],
                                       caption=f"{user_sign}\n{channel_id}\n{audio_pv_forward[message.chat.id]['genres']}")
                        logging.info("forwarded message")
                    audio_pv_forward.pop(message.chat.id)

                else:

                    bot.send_audio(channel_id_number, audio_pv_forward[message.chat.id]["file_id"],
                                   caption=f"🎼 {sign_key_creator(message.chat)}{user_sign}\n{channel_id}\n{audio_pv_forward[message.chat.id]['genres']}")
                    if audio_pv_forward[message.chat.id]['lyrics'] != "":
                        bot.send_message(channel_id_number, audio_pv_forward[message.chat.id]['lyrics'])
                    logging.info("forwarded audio from pv")
                    add_audio(audio_database[message.chat.id])
                    bot.send_message(message.chat.id, "آهنگ با موفقیت ارسال شد")
                    show_home(message)
                    for group_id in groups:
                        bot.send_audio(group_id, audio_pv_forward[message.chat.id]["file_id"],
                                       caption=f"🎼 {sign_key_creator(message.chat)}{user_sign}\n{channel_id}\n{audio_pv_forward[message.chat.id]['genres']}")
                        logging.info("forwarded message")
                    audio_pv_forward.pop(message.chat.id)
            else:
                if message.from_user.id in sign_mode.keys() and sign_mode[message.from_user.id] is False:

                    bot.send_audio(channel_id_number, audio_pv_forward[message.chat.id]["file_id"],
                                   caption=f"{user_sign}\n{audio_pv_forward[message.chat.id]['caption']}\n{channel_id}\n{audio_pv_forward[message.chat.id]['genres']}")
                    if audio_pv_forward[message.chat.id]['lyrics'] != "":
                        bot.send_message(channel_id_number, audio_pv_forward[message.chat.id]['lyrics'])
                    add_audio(audio_database[message.chat.id])
                    bot.send_message(message.chat.id, "آهنگ با موفقیت ارسال شد")
                    show_home(message)
                    for group_id in groups:
                        bot.send_audio(group_id, audio_pv_forward[message.chat.id]["file_id"],
                                       caption=f"{user_sign}\n{audio_pv_forward[message.chat.id]['caption']}\n{channel_id}\n{audio_pv_forward[message.chat.id]['genres']}")
                        logging.info("forwarded message")
                    audio_pv_forward.pop(message.chat.id)

                else:
                    bot.send_audio(channel_id_number, audio_pv_forward[message.chat.id]["file_id"],
                                   caption=f"🎼 {sign_key_creator(message.chat)}\n{audio_pv_forward[message.chat.id]['caption']}{user_sign}\n{channel_id}\n{audio_pv_forward[message.chat.id]['genres']}")
                    if audio_pv_forward[message.chat.id]['lyrics'] != "":
                        bot.send_message(channel_id_number, audio_pv_forward[message.chat.id]['lyrics'])
                    add_audio(audio_database[message.chat.id])
                    bot.send_message(message.chat.id, "آهنگ با موفقیت ارسال شد")
                    show_home(message)
                    for group_id in groups:
                        bot.send_audio(group_id, audio_pv_forward[message.chat.id]["file_id"],
                                       caption=f"🎼 {sign_key_creator(message.chat)}\n{audio_pv_forward[message.chat.id]['caption']}{user_sign}\n{channel_id}\n{audio_pv_forward[message.chat.id]['genres']}")
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
        if message.chat.id in reply_mode and reply_mode[message.chat.id] == "get_lyrics":
            reply_mode[message.chat.id] = None
        if message.chat.id in reply_mode and (
                reply_mode[message.chat.id] == "delete_sign" or reply_mode[message.chat.id] == "add_sign"):
            show_profile(message)
            return
        show_home(message)
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
            show_profile(message)
    if message.chat.type == "private" and message.chat.id in reply_mode.keys():
        if reply_mode[message.chat.id] == "send_suggestion":
            bot.send_message(suggestion_channel_id,
                             f"پیشنهاد جدید از طرف {message.chat.first_name} {message.chat.last_name}:\n@{message.chat.username}\n{message.text}")
            bot.reply_to(message, "پیشنهاد شما با موفقیت ارسال شد")
            create_session(message, [])
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
            count = 0
            for song in songs:
                if song is None:
                    continue
                if song[3] is None or song[1] is None:
                    continue
                if message.text.lower() in song[1].lower() or message.text.lower() in song[3].lower():
                    buttons = telebot.types.InlineKeyboardMarkup(
                        [[telebot.types.InlineKeyboardButton(text='🗑️', callback_data=f'deleteNow'),
                          telebot.types.InlineKeyboardButton(text='📃', callback_data=f'lyrics'),
                          telebot.types.InlineKeyboardButton(text='❤', callback_data=f'like')]], row_width=2)

                    # btn_1 = telebot.types.InlineKeyboardButton('❤', callback_data=f'{message.chat.id}-{song[2]}-like')
                    # btn_2 = telebot.types.InlineKeyboardButton('❌', callback_data=f'{message.chat.id}-{song[2]}-dislike')
                    # btn_1 = telebot.types.InlineKeyboardButton('❤')
                    # btn_2 = telebot.types.InlineKeyboardButton('❌')
                    # buttons.add(btn_1, btn_2)
                    result_message = bot.send_audio(message.chat.id, song[2], caption=channel_id, reply_markup=buttons)
                    count += 1
                    if count >= 15:
                        break
                    is_found = True
            if not is_found:
                result_message = bot.send_message(message.chat.id, "موردی یافت نشد", reply_markup=new_menu())
            else:
                if count >= 15:
                    bot.send_message(message.chat.id, str(count) + " نتیجه یافت شد(15 نتیجه اول ارسال شد) ",
                                     reply_markup=new_menu())
                else:
                    bot.send_message(message.chat.id, str(count) + " نتیجه یافت شد ", reply_markup=new_menu())
            # menu(message)
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
            if random_number < 1:
                bot.send_message(message.chat.id, "عددی بزرگ تر از 0 وارد کنید")
                return

            random_songs = random.sample(songs, random_number)
            for song in random_songs:
                buttons = telebot.types.InlineKeyboardMarkup(
                    [[telebot.types.InlineKeyboardButton(text='🗑️', callback_data=f'deleteNow'),
                      telebot.types.InlineKeyboardButton(text='📃', callback_data=f'lyrics'),
                      telebot.types.InlineKeyboardButton(text='❤', callback_data=f'like')]], row_width=2)
                # btn_1 = telebot.types.InlineKeyboardButton('❤', callback_data=f'{message.chat.id}-{song[2]}-like')
                # btn_2 = telebot.types.InlineKeyboardButton('❌', callback_data=f'{message.chat.id}-{song[2]}-dislike')
                # btn_1 = telebot.types.InlineKeyboardButton('❤')
                # btn_2 = telebot.types.InlineKeyboardButton('❌')
                # buttons.add(btn_1, btn_2)
                bot.send_audio(message.chat.id, song[2], caption=channel_id, reply_markup=buttons)
                # bot.send_message(message.chat.id, "test", reply_markup=buttons)


# handling channel

@bot.channel_post_handler(content_types=['audio'])
def edit_message(message):
    # uncomment this to fix music Archive
    # add_audio(message)
    get_genres(message.audio.title, message.audio.performer)
    # debug
    if message.author_signature is not None and message.author_signature in get_admins():
        user_sign = ""
        if get_sign(message.author_signature) is not None:
            user_sign = f"\n{get_sign(message.author_signature)}"
        if message.caption is None:
            message.caption = ""

        result = ""
        try:
            genres = get_genres(message.audio.title, message.audio.performer)
            for i in genres:
                i = i.replace(" ", "_")
                i = i.replace("-", "_")
                if "/" in i:
                    result += f"#{i.split('/')[0]} "
                    result += f"#{i.split('/')[1]} "
                else:
                    result += f"#{i} "
        except:
            pass

        if get_admin_id(message.author_signature) in sign_mode.keys() and sign_mode[
            get_admin_id(message.author_signature)] is False:
            bot.send_audio(channel_id_number, message.audio.file_id, caption=f"{user_sign}\n{channel_id}\n{result}")
            for group_id in groups:
                bot.send_audio(group_id, message.audio.file_id, caption=f"{user_sign}\n{channel_id}\n{result}")
                logging.info("forwarded message")
            try:
                bot.delete_message(channel_id_number, message.message_id)
            except Exception as e:
                pass
            add_audio(message)
        else:
            bot.send_audio(channel_id_number, message.audio.file_id,
                           caption=f"🎼 {message.author_signature}{user_sign}\n{channel_id}\n{result}")
            for group_id in groups:
                bot.send_audio(group_id, message.audio.file_id,
                               caption=f"🎼 {message.author_signature}{user_sign}\n{channel_id}\n{result}")
                logging.info("forwarded message")
            try:
                bot.delete_message(channel_id_number, message.message_id)
            except Exception as e:
                pass
            add_audio(message)
        return


# handling callbacks
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    # calls = call.split()
    print(call.json['data'] == 'like')
    if call.json['data'] == 'like':
        create_or_get_playlist(call.json['message']['chat']['id'], "fav")
        add_to_playlist(call.json['message']['chat']['id'], call.json['message']['audio']['file_id'], "fav",
                        call.json['message']['audio']['title'], call.json['message']['audio']['performer'])
        bot.answer_callback_query(call.id, "به لیست علاقه مندی ها افزوده شد")
    elif call.json['data'] == 'dislike':
        remove_from_playlist(call.json['message']['chat']['id'], call.json['message']['audio']['file_id'], "fav",
                             call.json['message']['audio']['title'], call.json['message']['audio']['performer'])
        bot.answer_callback_query(call.id, "از لیست علاقه مندی ها برداشته شد")
    elif call.json['data'] == 'dislikeP':
        remove_from_playlist(call.json['message']['chat']['id'], call.json['message']['audio']['file_id'], "fav",
                             call.json['message']['audio']['title'], call.json['message']['audio']['performer'])
        bot.answer_callback_query(call.id, "آهنگ از لیست علاقه مندی ها حذف شد")
        try:
            bot.delete_message(call.json['message']['chat']['id'], call.json['message']['message_id'])
        except Exception as e:
            pass
    elif call.json['data'] == "lyrics":
        threading.Thread(target=send_lyrics, args=(call.message,)).start()
        bot.answer_callback_query(call.id, "در حال جست و جو برای lyrics")
    elif call.json['data'] == "favs":
        delete_current_sessions(call.message)
        fav_message = bot.send_message(call.json['message']['chat']['id'], "علاقه مندی ها", reply_markup=new_menu())
        current_sessions[call.json['message']['chat']['id']] = [fav_message]
        send_favs(call.message)
    elif call.json['data'] == "support":
        show_support(call.message)
    elif call.json['data'] == "showSign":
        send_sign(call.message)
    elif call.json['data'] == "addSign":
        add_sign_menu(call.message)
    elif call.json['data'] == "deleteSign":
        delete_sign(call.message)
    elif call.json['data'] == "profile":
        show_profile(call.message)
    elif call.json['data'] == "deleteNow":
        bot.delete_message(call.message.chat.id, call.message.message_id)


bot.infinity_polling()
