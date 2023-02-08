import logging
import configparser
import telebot
import os
import pickle

# class Config:
config = configparser.ConfigParser()
config.read('config.ini')
logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', filename='bot.log',
                    level=logging.DEBUG)
bot = telebot.TeleBot(config['bot']['API_KEY'])
channel_id_number = config['bot']['CHANNEL_ID']
channel_id = config['bot']['CHANNEL_USERNAME']
music_api = config['MUSIC']['api']
signs = {}
groups = []
reply_mode = {}
delete_mode = {}
current_sessions = {}
sign_mode = {}
audio_pv_forward = {}
audio_database = {}
signs_file_name = "signs.pkl"
groups_file_name = "groups.pkl"
suggestion_channel_id = config['bot']['SUGGESTION_ID']
sign_mode_file_name = "sign_mode.pkl"
# Database config
import sqlite3

conn = sqlite3.connect('database.db')

try:
    conn.execute('''CREATE TABLE MUSIC
         (CHAT_ID INT  KEY     NOT NULL, 
         MUSIC_NAME           TEXT  UNIQUE  NOT NULL,
         MUSIC_FILE_ID     TEXT   UNIQUE   NOT NULL,
         PERFORMER        CHAR(255)
         );''')
except Exception:
    pass
try:
    conn.execute('''CREATE TABLE CHATS
         (CHAT_ID INT  KEY UNIQUE NOT NULL, 
         VIP  INTEGER  DEFAULT 0
         );''')
except Exception as e:
    print(str(e))

try:
    conn.execute('''CREATE TABLE PLAYLISTS
         (CHAT_ID INT  KEY  NOT NULL,
         NAME TEXT NOT NULL
         );''')
except Exception as e:
    print(str(e))

try:
    conn.execute('''CREATE TABLE PLAYLIST_MUSICS
         (MUSIC_FILE_ID TEXT NOT NULL,
         CHAT_ID INT  KEY  NOT NULL,
         PLAYLISTNAME TEXT NOT NULL,
         );''')
except Exception as e:
    print(str(e))

try:
    conn.execute('''ALTER TABLE PLAYLIST_MUSICS add MUSICNAME TEXT''')
    conn.execute('''ALTER TABLE PLAYLIST_MUSICS add PERFORMER TEXT''')
except Exception as e:
    print(str(e))

conn.commit()
conn.close()

# end Database config
if not os.path.exists(groups_file_name):
    groups_file = open(groups_file_name, 'wb')
    groups_file.close()

if not os.path.exists(sign_mode_file_name):
    sign_mode_file = open(sign_mode_file_name, 'wb')
    sign_mode_file.close()

if not os.path.exists(signs_file_name):
    signs_file = open(signs_file_name, 'wb')
    signs_file.close()

signs_file = open(signs_file_name, 'rb')
groups_file = open(groups_file_name, 'rb')
sign_mode_file = open(sign_mode_file_name, 'rb')

try:
    groups = pickle.load(groups_file)
except Exception:
    groups_file = open(groups_file_name, 'wb')
    pickle.dump(groups, groups_file)
groups_file.close()

try:
    signs = pickle.load(signs_file)
except Exception:
    signs_file = open(signs_file_name, 'wb')
    pickle.dump(signs, signs_file)
signs_file.close()

try:
    sign_mode = pickle.load(sign_mode_file)
except Exception:
    sign_mode_file = open(sign_mode_file_name, 'wb')
    pickle.dump(sign_mode, sign_mode_file)
