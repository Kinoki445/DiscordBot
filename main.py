import discord
import asyncio
import os
from asyncio import sleep
from discord.ext import commands
from youtube_dl import YoutubeDL
from discord import FFmpegPCMAudio

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

# Инициализация бота
bot = commands.Bot(command_prefix='$',
                   intents=discord.Intents.all(), case_insensitive=True)
# Удаление базовой команды help
bot.remove_command('help')

# Сообщение что бот запустился


@bot.event
async def on_ready():
    print(f'Logged on as {bot.user}!')

    await bot.change_presence(status=discord.Status.online, activity=discord.Game('Пытается превзойти создателя'))

# Реализация команды $clear


@bot.command()
async def clear(ctx, count: int):
    # Удаляет сообщения количество указывается в limit
    await ctx.channel.purge(limit=count+1)
    await ctx.send(f'**Было удалено {count} сообщений**')

# Реализация команды $ban


@bot.command()
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


@bot.command()
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


@bot.command()
async def play(ctx, *args):

    # Глобальные переменные для управления музыкой
    global vc, path

    url = ' '.join(args)

    try:
        voice_channel = ctx.message.author.voice.channel
        vc = await voice_channel.connect()
        path = []
    except:
        pass

    if vc.is_playing():
        path.append(url)
        list_music = ''
        for i in path:
            list_music += f'\n{i}'
        # Создаем вложенный объект discord.Embed с информацией о заказанных треках
        embed = discord.Embed(
            title='Плейлист', description=f'{ctx.message.author.mention}, я добавил в плейлист.\n\n**Текущий плейлист:**\n{list_music}', color=0x00ff00
        )

        # Отправляем сообщение с использованием embed
        await ctx.send(embed=embed)

    else:
        with YoutubeDL(YDL_OPTIONS) as ydl:
            if 'https://' in url:
                info = ydl.extract_info(url, download=False)
            else:
                info = ydl.extract_info(f'ytsearch:{url}', download=False)[
                    'entries'][0]

            link = info['formats'][0]['url']
            # Создаем вложенный объект discord.Embed с информацией о заказанном треке
            embed = discord.Embed(
                description=f"{ctx.message.author.mention} запросил **{info['title']}**\n[Ссылка на трек]({info['webpage_url']}).",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)

            vc.play(FFmpegPCMAudio(executable="ffmpeg\\ffmpeg.exe",
                    source=link, **FFMPEG_OPTIONS))

            while vc.is_playing():
                await sleep(10)
            if not vc.is_paused():
                ctx.voice_client.stop()
                if len(path) == 0:
                    # Сообщение о завершении треков
                    await ctx.send(embed=discord.Embed(description="Треки закончились. Спасибо за прослушивание!"))
                else:
                    music = path.pop(0)
                    list_music = ''
                    for i in path:
                        list_music += f'\n-{i}'
                    # Создаем вложенный объект discord.Embed с информацией о заказанных треках
                    embed = discord.Embed(
                        title='Плейлист',
                        description=f'{ctx.message.author.mention}, Я пропустил трек.\n\n**Текущий плейлист:**\n{list_music}',
                        # Зеленый цвет (можно изменить на другой по желанию)
                        color=0x00ff00)
                    
                    await ctx.send(embed=embed)
                    await play(ctx, music)

# Реализация команды $stop остановки плейлиста


@bot.command()
async def stop(ctx):
    ctx.voice_client.stop()
    path = []
    # Сообщение о завершении треков
    await ctx.send(embed=discord.Embed(description="Я очистил плейлист. Спасибо за прослушивание!"))

# Реализация команды $skip пропуска треков


@bot.command()
async def skip(ctx):
    ctx.voice_client.stop()
    if len(path) == 0:
        # Сообщение о завершении треков
        await ctx.send(embed=discord.Embed(description="Треки закончились. Спасибо за прослушивание!"))
    else:
        music = path.pop(0)
        list_music = ''
        for i in path:
            list_music += f'\n{i}'
        # Создаем вложенный объект discord.Embed с информацией о заказанных треках
        embed = discord.Embed(
            title='Плейлист',
            description=f'{ctx.message.author.mention}, я пропустил трек.\n\n**Текущий плейлист:**\n{list_music}',
            color=0x00ff00)
        
        await ctx.send(embed=embed)
        await play(ctx, music)

# Реализация команды $help


@bot.command()
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
        name='$about', value='Информация о боте и его разработчике. Пример: `$about`', inline=False)

    await ctx.send(embed=embed)


# Реализация команды $about
@bot.command()
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

try:
    bot.run(os.getenv('TOKEN'))
except discord.errors.ConnectionClosed as e:
    print(f"Произошла ошибка: {e}")
