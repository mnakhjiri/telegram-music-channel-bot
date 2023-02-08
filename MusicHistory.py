import asyncio
from pyrogram import Client
import uvloop
import configparser
import time

configparser = configparser.ConfigParser()
configparser.read("config.ini")
api_id = configparser['Telegram']['api_id']
api_hash = configparser['Telegram']['api_hash']
channel_id = configparser['bot']['CHANNEL_USERNAME_SIMPLE']
HISTORY_HANDLER = configparser['bot']['HISTORY_HANDLER']


async def main():
    async with Client("my_account", api_id, api_hash) as app:
        await app.send_message("me", "Updating Database for music channel")
        async for message in app.get_chat_history(channel_id):
            try:
                await message.forward(HISTORY_HANDLER)
                time.sleep(1)
            except Exception as e:
                pass


uvloop.install()
asyncio.run(main())
