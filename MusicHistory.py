import asyncio
import sqlite3
from config import *

from pyrogram import Client
import uvloop
import configparser
import socks
configparser = configparser.ConfigParser()
configparser.read("config.ini")

api_id = configparser['Telegram']['api_id']
api_hash = configparser['Telegram']['api_hash']
import socks
# proxy = [socks.SOCKS5, '127.0.0.1', 1080]
proxy = {
     "scheme": "socks5",  # "socks4", "socks5" and "http" are supported
     "hostname": '127.0.0.1',
     "port": 1080,
     # "username": "username",
     # "password": "password"
 }
async def main():
    async with Client("my_account", api_id, api_hash,proxy=proxy) as app:
        await app.send_message("me", "Updating Database for music channel")
        conn = sqlite3.connect('database.db')
        async for message in app.get_chat_history("cultmusicbar"):
            try:
                conn.execute("INSERT INTO MUSIC (CHAT_ID, MUSIC_NAME, MUSIC_FILE_ID , PERFORMER) VALUES (?, ?, ? , ?)",
                             (channel_id_number, message.audio.title, message.audio.file_id, message.audio.performer))
                conn.commit()
            except Exception as e:
                pass
            conn.close()



uvloop.install()
asyncio.run(main())
