import discord, random, asyncio, os, requests
from asyncio import sleep
from discord.ext import commands
from youtube_dl import YoutubeDL
from discord import FFmpegPCMAudio
from googletrans import Translator
from bs4 import BeautifulSoup 
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials

from dotenv import load_dotenv

# Настройки youtube-dl для парсинга музыки
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

# Настройки FFmpegPCMAudio для проигрования audio
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

load_dotenv()

# Авторизация Spotify
sp = Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv('SPOTIPY_CLIENT_ID'), client_secret=os.getenv('SPOTIPY_CLIENT_SECRET')))

# Инициализация бота
bot = commands.Bot(command_prefix='$',
                intents=discord.Intents.all(), case_insensitive=True)
# Удаление базовой команды help
bot.remove_command('help')

#Class Callback button
class MyButton(discord.ui.Button):
    def __init__(self, label, custom_id, callback_function):
        super().__init__(label=label, custom_id=custom_id)
        self.callback_function = callback_function

    async def callback(self, interaction: discord.Interaction):
        await self.callback_function(interaction)

async def skip_callback(interaction):
    try:
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            await interaction.response.send_message(embed=discord.Embed(description=f'Я пропустил трек.'))
            return
        else:
            await interaction.response.send_message("Нет активного воспроизведения.", ephemeral=True)
    except discord.errors.HTTPException:
        pass

async def stop_callback(interaction):
    try:
        voice_client = interaction.guild.voice_client
        if voice_client:
            voice_client.stop()
            path.clear()
            await interaction.response.send_message(embed=discord.Embed(description=f'Я удалил плейлист.'))
            return
        else:
            await interaction.response.send_message("Нет активного воспроизведения.", ephemeral=True)
    except discord.errors.HTTPException:
        pass

async def random_callback(interaction):
    try:
        # Перемешиваем список
        random.shuffle(path)
        await interaction.response.send_message(embed=discord.Embed(
                    title='Рандом', description=f'Треки перемешаны'))
        return
    except discord.errors.HTTPException:
        pass

@bot.event
async def on_button_click(interaction):
    if interaction.custom_id == 'skip_button':
        await skip_callback(interaction)
    elif interaction.custom_id == 'stop_button':
        await stop_callback(interaction)
    elif interaction.custom_id == 'random_button':
        await random_callback(interaction)

# Сообщение что бот запустился

@bot.event
async def on_ready():
    print(f'Logged on as {bot.user}!')

    await bot.change_presence(status=discord.Status.online, activity=discord.Game('Пытается превзойти создателя'))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('Такой команды не существует.')
    else:
        # Другие обработчики ошибок, если необходимо
        print(f'Произошла ошибка: {error}')

# Реализация команды $clear

@bot.command(name='clear', help='Очистить чат.')
async def clear(ctx, count: int):
    # Удаляет сообщения количество указывается в limit
    await ctx.channel.purge(limit=count+1)
    await ctx.send(f'**Было удалено {count} сообщений**')

# Реализация команды $ban


@bot.command(name='ban', help='Забанить пользователяю.')
async def ban(ctx, member: discord.Member = None, time=None, reason: str = None):
    async def un_ban(member):
        async for ban_user in ctx.guild.bans():
            if ban_user.user == member:
                await ctx.guild.unban(ban_user.user)
                embed = discord.Embed(
                    description=f'Пользователь @{ban_user.user} разбанен', color=discord.Color.green())
                await ctx.send(embed=embed)

    async def check_command(reason, time_letter, time_numbers):
        await member.ban(reason=reason)
        await ctx.send(embed=discord.Embed(description=f'Пользователь {member.mention} был забанен \nВремя: {time} Причина: {reason}'))
        await asyncio.sleep(time_numbers)
        await un_ban(member)

    # Проверка на указание пользователя
    if member:
        # Проверка на указание времени
        if time:
            time_letter = time[-1:]
            time_numbers = int(time[:-1])

            if time_letter == 's':
                time_numbers *= 1
            elif time_letter == 'm':
                time_numbers *= 60
            elif time_letter == 'h':
                time_numbers *= 120
            elif time_letter == 'd':
                time_numbers *= 120*24

            # Проверка на указание причины
            if reason:
                await check_command(reason, time_letter, time_numbers)
            else:
                await check_command(reason, time_letter, time_numbers)

        # Если не указанно время
        else:
            await member.ban(reason=None)
            await ctx.send(embed=discord.Embed(description=f'Пользователь {member.mention} был забанен'))

    # Если не указан пользователь
    else:
        embed = discord.Embed(title='Введите имя пользователя:',
                            description='Пример: @kinoki.', color=discord.Color.red())
        await ctx.send(embed=embed)

# Реализация команды $unban


@bot.command(name='unban', help='Разбанить пользователяю.')
async def unban(ctx, id_: int = None):
    if id_:
        async for ban_user in ctx.guild.bans():
            if (ban_user.user.id) == id_:
                await ctx.guild.unban(ban_user.user)
                await ctx.send(f'Пользователь @{ban_user.user.name} разбанен')
    else:
        embed = discord.Embed(title='Введите id пользователя:',
                            description='Пример: 225635556594417665.', color=discord.Color.red())
        await ctx.send(embed=embed)

# Реализация команды $play включение музыки в боте


@bot.command(name='play', help='Воспроизвести музыку. Пример: `$play название_трека_или_ссылка`')
async def play(ctx, *args):
    global vc, path

    url = ' '.join(args)
    list_music = ''

    # инициальзиация функций
    view = discord.ui.View()

    # Кнопка "random" с соответствующим callback
    random_button = MyButton(label='Перемешать плейлист', custom_id='random_button', callback_function=lambda i: random_callback(i))
    view.add_item(random_button)

    # Кнопка "skip" с соответствующим callback
    skip_button = MyButton(label='Пропустить', custom_id='skip_button', callback_function=lambda i: skip_callback(i))
    view.add_item(skip_button)

    # Кнопка "stop" с соответствующим callback
    stop_button = MyButton(label='Остановить', custom_id='stop_button', callback_function=lambda i: stop_callback(i))
    view.add_item(stop_button)

    # Проверяем, находится ли автор сообщения в голосовом канале

    try:
        try:
            voice_channel = ctx.message.author.voice.channel
            vc = await voice_channel.connect()
            path = []
        except:
            print('Я уже в чате')
            pass

        #Если музыка проигрывается
        if vc.is_playing():
            #Если Вк делает из него плейлист
            if 'https://vk.com/music/' in url:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0'}
                # Отправляем GET-запрос к указанному URL
                response = requests.get(url, headers=headers)

                if response.status_code == 200:
                    # Если запрос успешен, парсим содержимое страницы
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Найдите все элементы плейлиста
                    listen = soup.find_all("div", class_="audio_row__performer_title")

                    await ctx.send(embed=discord.Embed(description=f'Начинаю парсить плейлист'))

                    for item in listen:
                        title_element = item.find("a", class_="audio_row__title_inner _audio_row__title_inner")
                        artist_element = item.find("div", class_="audio_row__performers")

                        if title_element and artist_element:
                            title = title_element.getText()
                            artist = artist_element.getText()
                            path.append(f"{artist} - {title}")

                    # Отправляем сообщение о добавлении в плейлист
                    try:
                        await ctx.edit(embed=discord.Embed(description=f'{ctx.author.mention}, я добавил в плейлист \n[{title}]({url})'), view=view)
                    except:
                        await ctx.send(embed=discord.Embed(description=f'{ctx.author.mention}, я добавил в плейлист \n[{title}]({url})'), view=view)
                else:
                    print(f"Ошибка {response.status_code} при получении данных.")
                    
            elif 'https://open.spotify.com/playlist/' in url:
                # Получаем информацию о плейлисте из Spotify API
                playlist_info = sp.playlist(url)

                # Перебираем треки в плейлисте и проигрываем их
                for track in playlist_info['tracks']['items']:
                    song = track['track']['name']
                    artist = track['track']['artists'][0]['name']
                    path.append(f'{artist} - {song}')

            #если обычная ссылка ютуб или название
            else:
                with YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(url, download=False) if 'https://' in url else ydl.extract_info(f'ytsearch:{url}', download=False)['entries'][0]
                    link = info['formats'][0]['url']

                    title = info['title']
                    music_url = info['webpage_url']
                    path.append(music_url)

                    # Отправляем сообщение о добавлении в плейлист
                    try:
                        await ctx.edit(embed=discord.Embed(description=f'{ctx.author.mention}, я добавил в плейлист \n[{title}]({music_url})'), view=view)
                    except:
                        await ctx.send(embed=discord.Embed(description=f'{ctx.author.mention}, я добавил в плейлист \n[{title}]({music_url})'), view=view)

        #Если не играет музыка
        elif not vc.is_paused():
            #Если ВК
            if 'https://vk.com/music/' in url:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0'}
                # Отправляем GET-запрос к указанному URL
                response = requests.get(url, headers=headers)

                if response.status_code == 200:
                    # Если запрос успешен, парсим содержимое страницы
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Найдите все элементы плейлиста
                    listen = soup.find_all("div", class_="audio_row__performer_title")

                    await ctx.send(embed=discord.Embed(description=f'Начинаю парсить плейлист'))

                    for item in listen:
                        title_element = item.find("a", class_="audio_row__title_inner _audio_row__title_inner")
                        artist_element = item.find("div", class_="audio_row__performers")

                        if title_element and artist_element:
                            title = title_element.getText()
                            artist = artist_element.getText()
                            path.append(f"{artist} - {title}")

                    with YoutubeDL(YDL_OPTIONS) as ydl:
                        info = ydl.extract_info(f'ytsearch:{path.pop(0)}', download=False)['entries'][0]
                        link = info['formats'][0]['url']

                        # Формируем информацию о текущем треке и плейлисте
                        for i in path:
                            list_music = ' '.join(f'\n- {i}' for i in path[:5])

                        if list_music == '':
                            embed = discord.Embed(
                                description=f"{ctx.author.mention}, сейчас будет играть: \n[{info['title']}]({info['webpage_url']})",
                                color=0x00ff00)

                            try:
                                await ctx.edit(embed=discord.Embed(description=f'{ctx.author.mention}, я добавил в плейлист \n[{title}]({music_url})'), view=view)
                            except:
                                await ctx.send(embed=embed, view=view)
                        else:
                            embed = discord.Embed(
                                title='Плейлист',
                                description=f"{ctx.author.mention}, сейчас будет играть [{info['title']}]({info['webpage_url']}).\n\n**Текущий плейлист:**\n{list_music}",
                                color=0x00ff00)
                            
                            try:
                                await ctx.edit(embed=embed, view=view)
                            except:
                                await ctx.send(embed=embed, view=view)

                        # Воспроизводим трек
                        vc.play(FFmpegPCMAudio(executable="ffmpeg\\ffmpeg.exe",
                                source=link, **FFMPEG_OPTIONS))

                        # Ждем, пока текущий трек воспроизводится
                        while vc.is_playing():
                            await asyncio.sleep(1)

                        try:
                            await play(ctx, path.pop(0))
                        except:
                            await ctx.send(embed=discord.Embed(
                                title='Конец', description=f'{ctx.author.mention}, Треки закончились спасибо за прослушивание!'), view=view)
                else:
                    print(f"Ошибка {response.status_code} при получении данных.")

            elif 'https://open.spotify.com/playlist/' in url:
                # Получаем информацию о плейлисте из Spotify API
                playlist_info = sp.playlist(url)

                # Перебираем треки в плейлисте и проигрываем их
                for track in playlist_info['tracks']['items']:
                    song = track['track']['name']
                    artist = track['track']['artists'][0]['name']
                    path.append(f'{artist} - {song}')

                with YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(f'ytsearch:{path.pop(0)}', download=False)['entries'][0]
                    link = info['formats'][0]['url']

                    # Формируем информацию о текущем треке и плейлисте
                    for i in path:
                        list_music = ' '.join(f'\n- {i}' for i in path[:5])

                    if list_music == '':
                        embed = discord.Embed(
                            description=f"{ctx.author.mention}, сейчас будет играть: \n[{info['title']}]({info['webpage_url']})",
                            color=0x00ff00)

                        try:
                            await ctx.edit(embed=embed, view=view)
                        except:
                            await ctx.send(embed=embed, view=view)
                    else:
                        embed = discord.Embed(
                            title='Плейлист',
                            description=f"{ctx.author.mention}, сейчас будет играть [{info['title']}]({info['webpage_url']}).\n\n**Текущий плейлист:**\n{list_music}",
                            color=0x00ff00)

                        try:
                            await ctx.edit(embed=embed, view=view)
                        except:
                            await ctx.send(embed=embed, view=view)

                    # Воспроизводим трек
                    vc.play(FFmpegPCMAudio(executable="ffmpeg\\ffmpeg.exe",
                            source=link, **FFMPEG_OPTIONS))

                    # Ждем, пока текущий трек воспроизводится
                    while vc.is_playing():
                        await asyncio.sleep(1)

                    try:
                        await play(ctx, path.pop(0))
                    except:
                        try:
                            await ctx.edit(embed=discord.Embed(
                                title='Конец', description=f'{ctx.author.mention}, Треки закончились спасибо за прослушивание!'))
                        except:
                            await ctx.send(embed=discord.Embed(
                                title='Конец', description=f'{ctx.author.mention}, Треки закончились спасибо за прослушивание!'))

            # Добавляем трек в плейлист
            else:
                with YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(url, download=False) if 'https://' in url else ydl.extract_info(f'ytsearch:{url}', download=False)['entries'][0]
                    link = info['formats'][0]['url']

                # Формируем информацию о текущем треке и плейлисте
                for i in path:
                    list_music = ' '.join(f'\n- {i}' for i in path[:5])

                if list_music == '':
                    embed = discord.Embed(
                        description=f"{ctx.author.mention}, сейчас будет играть: \n[{info['title']}]({info['webpage_url']})",
                        color=0x00ff00)

                    try:
                        await ctx.edit(embed=embed, view=view)
                    except:
                        await ctx.send(embed=embed, view=view)
                else:
                    embed = discord.Embed(
                        title='Плейлист',
                        description=f"{ctx.author.mention}, сейчас будет играть [{info['title']}]({info['webpage_url']}).\n\n**Текущий плейлист:**\n{list_music}",
                        color=0x00ff00)

                    try:
                        await message.edit(embed=embed, view=view)
                    except:
                        message = await ctx.send(embed=embed, view=view)

                # Воспроизводим трек
                vc.play(FFmpegPCMAudio(executable="ffmpeg\\ffmpeg.exe",
                        source=link, **FFMPEG_OPTIONS))

                # Ждем, пока текущий трек воспроизводится
                while vc.is_playing():
                    await asyncio.sleep(1)

                try:
                    await play(ctx, path.pop(0))
                except:
                    await ctx.send(embed=discord.Embed(
                        title='Конец', description=f'{ctx.author.mention}, Треки закончились спасибо за прослушивание!'))

    except Exception as e:
        print(f"Произошла ошибка: {e}")
        await ctx.send("Произошла ошибка при попытке воспроизведения трека.")
        try:
            await play(ctx, path.pop(0))
        except:
            await ctx.send(embed=discord.Embed(
                title='Конец', description=f'{ctx.author.mention}, Треки закончились спасибо за прослушивание!'))

# Реализация команды $stop остановки плейлиста

@bot.command(name='stop', help='Выключить воспроизведение.')
async def stop(ctx):
    ctx.voice_client.stop()
    path.clear()

# Реализация команды $skip пропуска треков

@bot.command(name='skip', help='Пропустить текущий трек.')
async def skip(ctx):
    ctx.voice_client.stop()

@bot.command(name='play_random', help='Сделайть плейлист рандомным ')
async def play_random(ctx):
    # Перемешиваем список
    random.shuffle(path)
    await ctx.send(embed=discord.Embed(
                title='Рандом', description=f'Треки перемешаны'))

# Реализация команды $help

@bot.command(name='help', help='Узнать команды бота')

async def help(ctx):
    embed = discord.Embed(
        title='Команды бота',
        description='Префикс команды: $',
        color=discord.Color.blue()
    )

    embed.add_field(
        name='$play', value='Воспроизвести музыку. Пример: `$play название_трека_или_ссылка`', inline=False)
    embed.add_field(
        name='$skip', value='Пропустить текущий трек. Пример: `$skip`', inline=False)
    embed.add_field(
        name='$stop', value='Выключить воспроизведение. Пример: `$stop`', inline=False)
    embed.add_field(
        name='$ban', value='Забанить пользователя. Пример: `$ban @kinoki445 12s` (время в s/m/h/d)', inline=False)
    embed.add_field(
        name='$unban', value='Разбанить пользователя по id. Пример: `$unban id_пользователя`', inline=False)
    embed.add_field(
        name='$clear', value='Отчистить чат указанное количество сообщений. Пример: `$clear 100`', inline=False)
    embed.add_field(
        name='$joke', value='Получить случайный анекдот. Пример: `$joke`', inline=False)
    embed.add_field(
        name='$anime_img', value='Получить случайное аниме изображение. Пример: `$anime_img` \n\n`type`(sfw/nsfw) \n\n`category-sfw` (waifu/neko/shinobu/megumin/bully/cuddle/cry/hug/awoo/kiss/\nlick/pat/smug/bonk/yeet/blush/smile/wave/highfive/handhold/nom/bite/glomp\n/slap/kill/kick/happy/wink/poke/dance/cringe) \n\n`category-nsfw` (waifu/neko/trap/blowjob)', inline=False)
    embed.add_field(
        name='$about', value='Информация о боте и его разработчике. Пример: `$about`', inline=False)

    await ctx.send(embed=embed)


# Реализация команды $about
@bot.command(name='about', help='Информация о боте и его разработчике. Пример: `$about`')
async def about(ctx):
    embed = discord.Embed(
        title='О боте',
        description='Этот бот был создан и разработан пользователем @kinoki_\nБот будет дорабатываться и улучшаться в будущем.',
        color=discord.Color.green()
    )

    embed.add_field(name='Ссылка на VK',
                    value='[VK Mem445](https://vk.com/mem445)', inline=False)
    embed.add_field(name='Ссылка на Telegram',
                    value='[Telegram Kinoki445](https://t.me/Kinoki445)', inline=False)
    embed.add_field(name='Ссылка на Портфолио',
                    value='[Kinoki445](https://kinoki.vercel.app/)', inline=False)

    await ctx.send(embed=embed)


@bot.command(name='joke', help='Получить случайный анекдот.')
async def joke(ctx):
    url = "https://v2.jokeapi.dev/joke/Any?blacklistFlags=nsfw,religious,political,racist,sexist,explicit&type=single"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        tr = Translator()
        a = tr.translate(data['joke'], dest='ru')
        await ctx.send(embed=discord.Embed(description=f"{a.text}"))


@bot.command(name='anime_img', help='Получить случайное аниме изображение. Пример: `$anime_img')
async def anime_img(ctx, *args):
    try:
        response = requests.get(f"https://api.waifu.pics/{args[0]}/{args[1]}")
    except:
        response = requests.get("https://api.waifu.pics/sfw/smile")

    if response.status_code == 200:
        data = response.json()
        image_url = data["url"]
        await ctx.send(image_url)
    else:
        await ctx.send(embed=discord.Embed(description=f"Error {response.status_code}: Не удалось получить изображение."))
        return None

try:
    bot.run(os.getenv('TOKEN'))
except discord.errors.ConnectionClosed as e:
    print(f"Произошла ошибка: {e}")
