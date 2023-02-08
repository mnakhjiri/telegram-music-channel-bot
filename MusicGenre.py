import asyncio

from pyrogram import Client
import uvloop
import configparser

configparser = configparser.ConfigParser()
configparser.read("config.ini")
api_id = configparser['Telegram']['api_id']
api_hash = configparser['Telegram']['api_hash']
music_api = configparser['MUSIC']['api']


def get_genres(track_name, artist):
    from musixmatch import Musixmatch
    musixmatch = Musixmatch(music_api)
    try:
        x = musixmatch.track_search(q_track=track_name, q_artist=artist, page_size=10, page=1, s_track_rating='desc')
        genre_list = x["message"]["body"]["track_list"][0]["track"]["primary_genres"]["music_genre_list"]
    except Exception as e:
        return []
    if len(genre_list) == 0:
        return []

    result = []
    for i in genre_list:
        result.append(i["music_genre"]["music_genre_name"])
    return result


async def main():
    async with Client("my_account", api_id, api_hash) as app:

        async for message in app.get_chat_history("cultmusicbar"):
            result = ""
            try:
                genres = get_genres(message.audio.title, message.audio.performer)
                if genres == []:
                    continue
                for i in genres:
                    i = i.replace(" ", "_")
                    i = i.replace("-", "_")
                    if "/" in i:
                        result += f"#{i.split('/')[0]} "
                        result += f"#{i.split('/')[1]} "
                    else:
                        result += f"#{i} "
            except:
                continue
            try:
                await app.edit_message_caption(message.chat.id, message.id, message.caption + "\n" + result)
            except Exception as e:
                print(str(e))


uvloop.install()
asyncio.run(main())
