import requests
from bs4 import BeautifulSoup
from youtube_dl import YoutubeDL

YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegVideoConvertor',
        'preferedformat': 'mp4',
    }],
    'age_limit': 18,  # Указываем возрастной лимит
    'source_address': '0.0.0.0',  # Указываем исходный IP-адрес, чтобы избежать блокировки
    'noplaylist': 'True',
}


def vk_music(url):
    with YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(url, download=False) if 'https://' in url else ydl.extract_info(
            f'ytsearch:{url}', download=False)['entries'][0]
        link = info['formats'][0]['url']

        title = info['title']
        music_url = info['webpage_url']
    return (music_url, title)


print(vk_music('12 morgen')[0])
