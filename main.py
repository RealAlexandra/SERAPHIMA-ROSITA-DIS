import random
import os
from dotenv import load_dotenv
import json
import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions
import asyncio
from discord import Embed
import datetime
import requests
from bs4 import BeautifulSoup

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix='!', intents=intents)

client = commands.Bot(command_prefix='!', help_command=None, intents=intents)

@client.command()
@has_permissions(mute_members=True)
async def mute(ctx, member: discord.Member, timeout, reason=None):
    muted_role = discord.utils.get(ctx.guild.roles, name="Muted")

    if not muted_role:
        muted_role = await ctx.guild.create_role(name="Muted")
        for channel in ctx.guild.channels:
            await channel.set_permissions(muted_role, speak=False, send_messages=False, read_message_history=True, read_messages=False)

    await member.add_roles(muted_role, reason=reason)
    
    # Создаем встроенное сообщение для мьюта
    embed = discord.Embed(title="Участник замьючен", description=f"{member.mention} был замьючен на {timeout} по причине {reason}", color=0xff0000)
    embed.set_thumbnail(url=member.display_avatar.url)  # Используем display_avatar.url
    embed.set_footer(text=f"Команда вызвана {ctx.author}", icon_url=ctx.author.display_avatar.url)  # Используем display_avatar.url
    await ctx.send(embed=embed)
    
    client.loop.create_task(unmute_after_timeout(member, muted_role, int(timeout) * 60, ctx.channel))

async def unmute_after_timeout(member, muted_role, timeout, channel):
    await asyncio.sleep(timeout)
    await member.remove_roles(muted_role, reason="Время мьюта истекло")
    
    # Создаем встроенное сообщение для размьюта
    embed = discord.Embed(title="Участник размьючен", description=f"{member.mention} был размьючен.", color=0x00ff00)
    embed.set_thumbnail(url=member.display_avatar.url)  # Используем display_avatar.url
    await channel.send(embed=embed)

@client.command()
@has_permissions(mute_members=True)
async def unmute(ctx, member: discord.Member, *, reason=None):
    muted_role = discord.utils.get(ctx.guild.roles, name="Muted")

    if not muted_role:
        # Создаем встроенное сообщение для ошибки
        embed = discord.Embed(title="Ошибка", description="Роль 'Muted' не найдена. Убедитесь, что она существует на сервере.", color=0xff0000)
        embed.set_footer(text=f"Команда вызвана {ctx.author}", icon_url=ctx.author.display_avatar.url)  # Используем display_avatar.url
        await ctx.send(embed=embed)
    else:
        await member.remove_roles(muted_role, reason=reason)
        # Создаем встроенное сообщение для размьюта
        embed = discord.Embed(title="Участник размьючен", description=f"{member.mention} был размьючен по причине {reason}", color=0x00ff00)
        embed.set_thumbnail(url=member.display_avatar.url)  # Используем display_avatar.url
        embed.set_footer(text=f"Команда вызвана {ctx.author}", icon_url=ctx.author.display_avatar.url)  # Используем display_avatar.url
        await ctx.send(embed=embed)

@client.command()
@has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, timeout, *, reason=None):
    # Баним участника
    await member.ban(reason=reason)
    
    # Создаем embed сообщение
    embed = discord.Embed(title="Ban Notification", description=f"{member.mention} был забанен на {timeout} по причине {reason}", color=0xFF0000)
    embed.set_thumbnail(url=member.display_avatar.url)  # Используем display_avatar.url
    embed.set_footer(text=f"Команда вызвана {ctx.author}", icon_url=ctx.author.display_avatar.url)  # Используем display_avatar.url
    await ctx.send(embed=embed)
    
    # Создаем задачу для разбана через указанное время
    client.loop.create_task(unban_after_timeout(ctx.guild, member, int(timeout) * 60))

async def unban_after_timeout(guild, member, timeout):
    await asyncio.sleep(timeout)
    
    # Находим запись о бане участника
    ban_entry = await next((ban async for ban in guild.bans() if ban.user.id == member.id), None)
    
    if ban_entry is not None:
        # Разбаниваем участника
        await guild.unban(ban_entry.user, reason="Время бана истекло")
        
        # Создаем embed сообщение
        embed = discord.Embed(title="Unban Notification", description=f"{ban_entry.user.mention} был разбанен.", color=0x00FF00)
        embed.set_thumbnail(url=ban_entry.user.display_avatar.url)  # Используем display_avatar.url
        await guild.system_channel.send(embed=embed)

@client.command()
async def help(ctx):
    embed = discord.Embed(
        title="Серафима",
        description="Серафима - это бот, который помогает вам в различных ситуациях. Он может поддерживать разговор на разные темы и многое другое! Серафима (Розита 2.0) работает на новом движке, который делает его более удобным и мобильным. В связи с переходом на новый движок, некоторые команды бота были отключены или изменены. Это сделано для того, чтобы улучшить качество и скорость работы бота, а также избежать возможных ошибок и конфликтов. Мы надеемся, что вы поймете и примете эти изменения. Если у вас есть вопросы или пожелания по работе бота, вы можете написать нам в канал идей. Спасибо, что пользуетесь ботом Серафима! Мы ценим ваше доверие и стремимся сделать ваше общение с ботом приятным и полезным. Желаем вам хорошего дня! 😊",
        color=discord.Color.blue()
    )

    embed.add_field(name="Команды", value="", inline=False)
    embed.add_field(name="!help", value="Показывает это сообщение", inline=False)
    embed.add_field(name="!ban", value="Банит указанного участника", inline=False)
    embed.add_field(name="!mute", value="Мьютит указанного участника", inline=False)
    embed.add_field(name="!unmute", value="Снимает мьют с указанного участника", inline=False)
    embed.add_field(name="!lvl", value="Показывает уровень участника", inline=False)
    embed.add_field(name="!clear", value="Очищает сообщения в чате, в том количестве в котором вы указали.", inline=False)
    embed.add_field(name="!mylaw", value="Показывает ваш уголовный закон УК РФ.", inline=False)
    embed.add_field(name="!coinflip", value="Орёл или Решка? Рандом на вашей стороне.", inline=False)
    embed.add_field(name="!avatar", value="Выводит аватар указанного пользователя.", inline=False)
    embed.add_field(name="!quote", value="Выводит случайную известную цитату.", inline=False)
    embed.add_field(name="!ping", value="Выводит пинг между участником и ботом.", inline=False)

    embed.set_footer(text=f"Команда вызвана {ctx.author}", icon_url=ctx.author.display_avatar.url)  # Используем display_avatar.url

    await ctx.send(embed=embed)

@client.command()
async def new(ctx):
    embed = discord.Embed(
        title = "Версия бота",
        description="Данная версия: ROSITA RELEASE 2.1 SERAPHIMA",
        color=discord.Color.purple()
    )
    embed.add_field(name="Эта команда - пасхалка, так что не судите строго.", value="Developed by Alexandra", inline=False)
    embed.set_footer(text=f"Команда вызвана {ctx.author}", icon_url=ctx.author.display_avatar.url)  # Используем display_avatar.url

    await ctx.send(embed=embed)

@client.command()
@commands.has_permissions(administrator=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount+1)  # Увеличиваем количество на 1, чтобы удалить саму команду !clear
    embed = discord.Embed(title="Очистка чата", description=f"Удалено {amount} сообщений.", color=0x00ff00)
    embed.set_footer(text=f"Команда вызвана {ctx.author}", icon_url=ctx.author.display_avatar.url)  # Используем display_avatar.url
    await ctx.send(embed=embed, delete_after=15)  # Сообщение автоматически удалится через 5 секунд








levels = {}  # Словарь для хранения уровней и очков пользователей

@client.event
async def on_ready():
    global levels
    try:
        with open('levels.json', 'r') as f:
            levels = json.load(f)
    except FileNotFoundError:
        print("Не удалось загрузить файл levels.json")
        levels = {}

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    user_id = str(message.author.id)  # Ключи в JSON должны быть строками
    if user_id not in levels:
        levels[user_id] = {"level": 1, "points": 0}

    levels[user_id]["points"] += 1
    if levels[user_id]["points"] >= 70:
        levels[user_id]["level"] += 1
        levels[user_id]["points"] = 0
        await message.channel.send(f"{message.author.mention}, поздравляем! Вы достигли уровня {levels[user_id]['level']}!")

    with open('levels.json', 'w') as f:
        json.dump(levels, f)

    await client.process_commands(message)

@client.command()
async def lvl(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    user_id = str(member.id)
    if user_id not in levels:
        embed = discord.Embed(title="Ошибка", description=f"{member.mention}, вы еще не начали набирать очки.", color=0xff0000)
    else:
        embed = discord.Embed(
            title = f"Уровень {member.name}",
            description=f"Уровень: {levels[user_id]['level']}\nОчки: {levels[user_id]['points']}",
            color=discord.Color.pink()
        )

    embed.set_footer(text=f"Команда вызвана {ctx.author}", icon_url=ctx.author.display_avatar.url)  # Используем display_avatar.url
    await ctx.send(embed=embed)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    user_id = str(message.author.id)  # Ключи в JSON должны быть строками
    if user_id not in levels:
        levels[user_id] = {"level": 1, "points": 0}

    levels[user_id]["points"] += 1
    if levels[user_id]["points"] >= 70:
        levels[user_id]["level"] += 1
        levels[user_id]["points"] = 0
        await message.channel.send(f"{message.author.mention}, поздравляем! Вы достигли уровня {levels[user_id]['level']}!")

    with open('levels.json', 'w') as f:
        json.dump(levels, f)

    await client.process_commands(message)

@client.event
async def on_ready():
    global levels
    try:
        with open('levels.json', 'r') as f:
            loaded_levels = json.load(f)
    except FileNotFoundError:
        print("Не удалось загрузить файл levels.json")
        levels = {}
    else:
        # Создаем новый словарь для хранения уровней и очков пользователей
        levels = {}
        for user_id, data in loaded_levels.items():
            if user_id not in levels:
                levels[user_id] = data
            else:
                # Если встречается дубликат, прибавляем его значения к существующей записи
                levels[user_id]['level'] = max(levels[user_id]['level'], data['level'])
                levels[user_id]['points'] += data['points']





@client.command()
async def hackserver(ctx):
    muted_role = discord.utils.get(ctx.guild.roles, name="Muted")

    if not muted_role:
        muted_role = await ctx.guild.create_role(name="Muted")
        for channel in ctx.guild.channels:
            await channel.set_permissions(muted_role, speak=False, send_messages=False, read_message_history=True, read_messages=False)

    await ctx.author.add_roles(muted_role, reason="Вызвана команда !hackserver")
    
    # Создаем встроенное сообщение
    embed = discord.Embed(title="Hack Server", description=f"{ctx.author.mention}, вы были замьючены навсегда!", color=0xFF0000)
    embed.set_thumbnail(url=ctx.author.display_avatar.url)  # Используем display_avatar.url
    embed.set_footer(text=f"Команда вызвана {ctx.author}", icon_url=ctx.author.display_avatar.url)  # Используем display_avatar.url
    await ctx.send(embed=embed)












@client.command()
async def coinflip(ctx):
    # Определение орла или решки
    result = "Орёл" if random.randint(0, 1) == 0 else "Решка"

    # Создание встраиваемого сообщения
    embed = discord.Embed(
        title = f"Орёл или Решка",
        description = f"Вам выпадает {result}!",
        color = discord.Color.blue()
    )

    # Добавление аватарки пользователя
    embed.set_thumbnail(url=ctx.author.avatar.url)

    # Отправка встраиваемого сообщения
    await ctx.send(embed=embed)






# Словарь для хранения выбранной статьи для каждого пользователя
user_articles = {}

def get_articles():
    # URL веб-сайта, с которого вы хотите извлечь статьи
    url = "https://www.consultant.ru/document/cons_doc_LAW_10699/"
    
    # Отправляем HTTP-запрос и получаем ответ
    response = requests.get(url)
    
    # Анализируем HTML-страницу
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Извлекаем статьи (вы должны адаптировать этот код в соответствии со структурой вашего веб-сайта)
    articles = [a.text for a in soup.find_all('a', href=True) if "Статья" in a.text]
    
    return articles

@client.command()
async def mylaw(ctx):
    user_id = str(ctx.author.id)
    current_date = datetime.date.today()

    # Если для пользователя еще не выбрана статья или выбрана статья за другой день
    if user_id not in user_articles or user_articles[user_id]['date'] != current_date:
        # Выбираем случайную статью
        articles = get_articles()
        article = random.choice(articles)
        # Сохраняем выбранную статью и дату ее выбора
        user_articles[user_id] = {'article': article, 'date': current_date}
    else:
        # Используем ранее выбранную статью
        article = user_articles[user_id]['article']

    # Создание встраиваемого сообщения
    embed = discord.Embed(
        title = "Ваша статья УК РФ на сегодня",
        description = article,
        color = discord.Color.blue()
    )

    # Добавление аватарки пользователя
    embed.set_thumbnail(url=ctx.author.avatar.url)

    # Отправка встраиваемого сообщения
    await ctx.send(embed=embed)



@client.command()
async def avatar(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    # Создание встраиваемого сообщения
    embed = discord.Embed(
        title = f"Аватарка {member.name}",
        color = discord.Color.blue()
    )

    # Добавление аватарки пользователя
    embed.set_image(url=member.avatar.url)

    # Отправка встраиваемого сообщения
    await ctx.send(embed=embed)




# Список цитат
quotes = [
    "«Быть или не быть, вот в чем вопрос» - Гамлет, Шекспир",
    "«Я скажу вам, что такое свободу: нет страха!» - Нина Симон",
    "«Я буду назад» - Терминатор",
    "«В конце концов, мы все умираем. Вопрос в том, что мы делаем, пока живем» - Алия из Игры Престолов",
    "«Жизнь - это как коробка шоколадных конфет: никогда не знаешь что тебе попадётся» - Форест Гамп из одноимённого фильма",
    "«Великие умы обсуждают идеи, средние умы обсуждают события, маленькие умы обсуждают людей» - Элеонора Рузвельт, жена президента США Франклина Рузвельта.",
    "«Нет ничего невозможного, пока ты не попробуешь» - Алиса из книги Алиса в стране чудес Льюиса Кэрролла.",
    "«Война. Война никогда не меняется» - Рон Перлман из игры Fallout",
    "«Свобода - это право говорить людям то, что они не хотят слышать» - Джордж Оруэлл, автор книги 1984",
    "«Мысли материальны» - Рене Декарт, французский философ и математик.",
    "«Самое страшное в этом мире - это человеческая глупость» - Альберт Эйнштейн, немецкий физик и нобелевский лауреат.",
    "«Счастье - это не что-то готовое. Это то, что вы создаете сами» - Далай-лама, духовный лидер тибетского буддизма.",
    "«Не ждите идеального момента, возьмите момент и сделайте его идеальным» - Зиг Зиглар, американский мотивационный спикер и писатель.",
    "«Мы не сдаемся без боя! Мы будем жить! Мы будем выживать! Сегодня мы отмечаем наш День независимости!» - Президент Уитмор из фильма «День независимости»",
    "«Все, что мы делаем в жизни, отзывается эхом в вечности» - Максимус из фильма «Гладиатор»",
    "«Все счастливые семьи похожи друг на друга, каждая несчастливая семья несчастлива по-своему» - Лев Толстой, автор книги «Анна Каренина»",
    "«Все, что нужно знать о жизни, можно узнать из садоводства» - Волтер, французский писатель и философ",
    "«Никогда не судите человека по его обуви» - Шерлок Холмс из книги «Знак четырех» Артура Конан Дойла",
    "«Все, что имеет начало, имеет и конец» - Архитектор из фильма «Матрица: Революция»",
    "«Все, что не убивает нас, делает нас сильнее» - Фридрих Ницше, немецкий философ и поэт",
    "«Все, что вы можете себе представить, реально» - Пабло Пикассо, испанский художник и скульптор",
    "«Все, что вы хотите, ждет вас за пределами вашей зоны комфорта» - Роберт Аллен, американский писатель и бизнесмен",
    "«Я не ищу смысла жизни. Я ищу чувство быть живым» - Лара Крофт из игры «Расхитительница гробниц»",
    "«Нет ничего страшнее, чем умереть одному» - Солид Снейк из игры «Metal Gear Solid»",
    "«Все, что мы делаем, оставляет след. Но следы исчезают. И мы с ними» - Элизабет из игры «BioShock Infinite»",
    "«Не бойся темноты. Бойся того, что в ней скрывается» - Кортана из игры «Halo»",
    "«Нет ничего хуже, чем жить в мире, который пытается сделать тебя кем-то другим» - Эвелин из игры «Dragon Age: Inquisition»",
    "«Нет ничего сильнее, чем сердце верного друга» - Йен из игры «The Witcher 3: Wild Hunt»",
    "«Нет ничего сложнее, чем принять себя таким, какой ты есть» - Джоэль из игры «The Last of Us»",
    "«Нет ничего важнее, чем свобода выбора» - Алтаир из игры «Assassin's Creed»",
    "«Нет ничего ценнее, чем время. Оно не возвращается» - Макс Колфилд из игры «Life is Strange»",
    "«Мы не хотим и не будем вмешиваться во внутренние дела других стран. Но мы не будем допускать, чтобы вмешивались в наши» - Владимир Путин, президент России, 2014 год",
    "«Россия - это не страна, а мир. Россия - это не нация, а цивилизация» - Дмитрий Медведев, премьер-министр России, 2016 год",
    "«Нет такого понятия - бывший КГБист. Это на всю жизнь» - Владимир Путин, президент России, 2004 год",
    "«Мы не можем жить в прошлом, но мы не можем забывать прошлое» - Михаил Горбачев, последний лидер СССР, 2011 год",
    "«Мы не хотим новой холодной войны. Мы не хотим новой гонки вооружений. Мы не хотим нового конфликта. Мы хотим нового мира» - Борис Ельцин, первый президент России, 1992 год",
    "«Мы не будем терпеть диктата и ультиматумов. Мы не будем платить за свою свободу и независимость кровью и разрухой» - Александр Лукашенко, президент Беларуси, 2020 год",
    "«Мы не можем жить без своей истории, без своих героев, без своих великих побед и трагических потерь» - Дмитрий Песков, пресс-секретарь президента России, 2015 год",
    "«Мы не будем строить социализм по образцу других стран. Мы будем строить социализм по образцу Китая» - Дэн Сяопин, лидер Китая, 1978 год",
    "«Мы не можем быть друзьями с теми, кто не уважает нас, нашу историю, наши традиции» - Виктор Орбан, премьер-министр Венгрии, 2018 год",
    "«Мы не можем сидеть сложа руки, когда наши граждане убиваются и издеваются над ними» - Сергей Лавров, министр иностранных дел России, 2014 год",
    "«Нет ничего страшнее, чем потерять то, что тебе дорого. Но есть что-то еще хуже: не попытаться его спасти» - Клэр Редфилд из игры «Resident Evil 2»",
    "«Нет ничего лучше, чем хорошая история. Она может изменить мир» - Варрик Тетрас из игры «Dragon Age: Inquisition»",
    "«Нет ничего сладже, чем месть. Особенно, когда она подается холодной» - Кратос из игры «God of War»",
    "«Нет ничего сильнее, чем вера. Она может двигать горы... и разрушать империи» - Алтайр из игры «Assassin's Creed»",
    "«Нет ничего важнее, чем семья. Она - твое прошлое, настоящее и будущее» - Доминик Сантьяго из игры «Gears of War»",
    "«Нет ничего сложнее, чем простить себе свои ошибки. Но это единственный способ идти дальше» - Элли из игры «The Last of Us Part II»",
    "«Нет ничего ценнее, чем свобода. Она - твое право и твоя ответственность» - Командир Шепард из игры «Mass Effect»",
    "«Нет ничего хуже, чем одиночество. Оно может съесть тебя изнутри» - Лара Крофт из игры «Tomb Raider»",
    "«Нет ничего лучше, чем путешествие. Оно открывает тебе новые горизонты и новые возможности» - Натан Дрейк из игры «Uncharted»",
    "«Нет ничего страшнее, чем смерть. Но есть что-то еще страшнее: жизнь без смысла» - Макс Пейн из игры «Max Payne»",
    "«Нет ничего лучше, чем дружба. Она - твоя опора и твой дар» - Соник из игры «Sonic the Hedgehog»",
    "«Нет ничего сильнее, чем любовь. Она может победить все препятствия и преодолеть все расстояния» - Йеннифэр из игры «The Witcher 3: Wild Hunt»",
    "«Нет ничего важнее, чем честь. Она - твой кодекс и твой путь» - Самурай Джек из игры «Samurai Jack: Battle Through Time»",
    "«Нет ничего сложнее, чем выбор. Он может определить твою судьбу и твои последствия» - Корво Аттано из игры «Dishonored»",
    "«Нет ничего ценнее, чем знание. Оно - твой ресурс и твой оружие» - Алой из игры «Horizon Zero Dawn»",
    "«Нет ничего хуже, чем предательство. Оно может разбить твое сердце и твою доверие» - Артур Морган из игры «Red Dead Redemption 2»",
    "«Нет ничего лучше, чем приключение. Оно - твой вызов и твоя награда» - Марио из игры «Super Mario»",
    "«Нет ничего сильнее, чем мечта. Она - твой стимул и твоя цель» - Сора из игры «Kingdom Hearts»",
    "«Нет ничего важнее, чем мир. Он - твоя миссия и твоя цена» - Солид Снейк из игры «Metal Gear Solid»",
    "«Нет ничего хуже, чем жить во лжи. Она - твоя тюрьма и твой палач» - Эдвард Кенуэй из игры «Assassin's Creed IV: Black Flag»",
    "«Нет ничего лучше, чем исследовать мир. Он - твой учитель и твой друг» - Эви Фрай из игры «Assassin's Creed: Syndicate»",
    "«Нет ничего сильнее, чем верность. Она - твоя защита и твой долг» - Шай Патрик Кормак из игры «Assassin's Creed: Rogue»",
    "«Нет ничего важнее, чем справедливость. Она - твоя ценность и твой идеал» - Арно Дориан из игры «Assassin's Creed: Unity»",
    "«Нет ничего сложнее, чем измена. Она - твоя рана и твой урок» - Агилар де Нерха из фильма «Assassin's Creed»",
    "«Нет ничего ценнее, чем память. Она - твоя история и твой наследник» - Дезмонд Майлз из игры «Assassin's Creed III»",
    "«Нет ничего хуже, чем рабство. Оно - твое унижение и твое проклятие» - Адевале из игры «Assassin's Creed IV: Black Flag»",
    "«Нет ничего лучше, чем свет. Он - твой путеводитель и твой символ» - Байек из игры «Assassin's Creed: Origins»",
    "«Нет ничего сильнее, чем сила. Она - твой ресурс и твой аргумент» - Алексиос из игры «Assassin's Creed: Odyssey»",
    "«Нет ничего важнее, чем баланс. Он - твоя гармония и твой порядок» - Юно из игры «Assassin's Creed: Revelations»",
    "«Нет ничего сложнее, чем прощение. Оно - твоя милость и твой выбор» - Людовико Орси из игры «Assassin's Creed II»",
    "«Нет ничего ценнее, чем жизнь. Она - твой дар и твой вызов» - Кассандра из игры «Assassin's Creed: Odyssey»",
    "«Нет ничего хуже, чем страх. Он - твой враг и твой палач» - Якоб Фрай из игры «Assassin's Creed: Syndicate»",
    "«Нет ничего лучше, чем мудрость. Она - твой наставник и твой союзник» - Сократ из игры «Assassin's Creed: Odyssey»",
    "«Нет ничего хуже, чем жить во лжи. Она - твоя тюрьма и твой палач» - Кара, андроид-няня, которая бежит с девочкой-андроидом Алисой от насильственного отца",
    "«Нет ничего лучше, чем исследовать мир. Он - твой учитель и твой друг» - Эви Фрай, андроид-детектив, которая работает вместе с человеческим напарником Коннором",
    "«Нет ничего сильнее, чем верность. Она - твоя защита и твой долг» - Лютер, андроид-телохранитель, который помогает Каре и Алисе в их побеге",
    "«Нет ничего важнее, чем справедливость. Она - твоя ценность и твой идеал» - Арно Дориан, андроид-адвокат, который защищает права андроидов в суде",
    "«Нет ничего сложнее, чем измена. Она - твоя рана и твой урок» - Агилар де Нерха, андроид-шпион, который работает на тайную организацию Ассасины",
    "«Нет ничего ценнее, чем память. Она - твоя история и твой наследник» - Дезмонд Майлз, андроид-исследователь, который использует машину Анимусдля восстановления воспоминаний своих предков",
    "«Нет ничего хуже, чем рабство. Оно - твое унижение и твое проклятие» - Адевале, андроид-пират, который борется за свободу андроидов на Карибах",
    "«Нет ничего лучше, чем свет. Он - твой путеводитель и твой символ» - Байек, андроид-охотник, который помогает Маркусу в его революции",
    "«Нет ничего сильнее, чем сила. Она - твой ресурс и твой аргумент» - Алексиос, андроид-наемник, который работает на разные стороны в войне между андроидами и людьми",
    "«Нет ничего важнее, чем баланс. Он - твоя гармония и твой порядок» - Юно, андроид-ученый, который изобрел машину Анимус и является лидером тайной организации Тамплиеры",
    "«Нельзя вести дурную жизнь и надеяться на счастливый исход» - Артур Морган, главный герой игры",
    "«Мы не можем жить в прошлом, но мы не можем забывать прошлое» - Михаил Горбачев, последний лидер СССР, который появляется в игре в качестве камео",
    "«Мы не будем терпеть диктата и ультиматумов. Мы не будем платить за свою свободу и независимость кровью и разрухой» - Александр Лукашенко, президент Беларуси, который также появляется в игре в качестве камео",
    "«Мы не хотим новой холодной войны. Мы не хотим новой гонки вооружений. Мы не хотим нового конфликта. Мы хотим нового мира» - Борис Ельцин, первый президент России, который умер во время событий игры",
    "«Мы не можем сидеть сложа руки, когда наши граждане убиваются и издеваются над ними» - Сергей Лавров, министр иностранных дел России, который в игре является одним из союзников главного героя",
    "«Мы не будем строить социализм по образцу других стран. Мы будем строить социализм по образцу Китая» - Дэн Сяопин, лидер Китая, который в игре является одним из врагов главного героя",
    "«Мы не можем жить без своей истории, без своих героев, без своих великих побед и трагических потерь» - Дмитрий Песков, пресс-секретарь президента России, который в игре является одним из информаторов главного героя",
    "«Мы не будем терпеть насилия и террора. Мы не будем молчать, когда нас угнетают и унижают. Мы не будем бояться бороться за свои права и свою судьбу» - Маркус, лидер андроидов-повстанцев, который в игре является одним из союзников главного героя",
    "«Мы не можем быть друзьями с теми, кто не уважает нас, нашу историю, наши традиции» - Виктор Орбан, премьер-министр Венгрии, который в игре является одним из врагов главного героя",
    "«Лучше ужасный конец, чем ужас без конца» - Адольф Гитлер, фюрер Третьего рейха",
    "«Кто хочет жить, тот обязан бороться, а кто не захочет сопротивляться в этом мире вечной борьбы, тот не заслуживает права на жизнь» - Адольф Гитлер, фюрер Третьего рейха",
    "«Совести нет. Совесть придумали евреи» - Адольф Гитлер, фюрер Третьего рейха",
    "«Выбрал свой путь — иди по нему до конца» - Адольф Гитлер, фюрер Третьего рейха",
    "«За кем молодежь, за тем и будущее» - Адольф Гитлер, фюрер Третьего рейха",
    "«Перед лицом великой цели никакие жертвы не покажутся слишком большими» - Адольф Гитлер, фюрер Третьего рейха",
    "«Чем грандиознее ложь, тем легче ей готовы поверить» - Адольф Гитлер, фюрер Третьего рейха",
    "«Никого не любить — это величайший дар, делающий тебя непобедимым, т. к. никого не любя, ты лишаешься самой страшной боли» - Адольф Гитлер, фюрер Третьего рейха",
    "«То кем вы стали, вы стали только благодаря мне! И то кем я стал, я стал только благодаря вам» - Адольф Гитлер, фюрер Третьего рейха",
    "«Если мне суждено погибнуть, то пусть погибнет и немецкий народ, потому что он оказался недостойным меня» - Адольф Гитлер, фюрер Третьего рейха",
    "«Судьбу всего сущего я вижу в борьбе. Уклониться от борьбы не может никто, если не хочет погибнуть» - Адольф Гитлер, фюрер Третьего рейха",
    "«Русские получили право напасть на своих священников, но они не имеют права нападать на идею высшей силы. Это факт, что мы ничтожные творения, и что творческая сила существует» - Адольф Гитлер, фюрер Третьего рейха",
    "«Мои христианские чувства указывают мне, что мой Господь и Спаситель — борец. Они указывают на человека, который однажды, будучи одинок и окружён малочисленными последователями, распознал истинную сущность евреев и призвал людей к борьбе против них, и Он (правда Божья!) был величайшим не только в страдании, но и в борьбе» - Адольф Гитлер, фюрер Третьего рейха",
    "«О религии Судьбу всего сущего я вижу в борьбе. Уклониться от борьбы не может никто, если не хочет погибнуть. См. также «Моя борьба», «Застольные беседы Гитлера» Русские получили право напасть на своих священников, но они не имеют права нападать на идею высшей силы. Это факт, что мы ничтожные творения, и что творческая сила существует» - Адольф Гитлер, фюрер Третьего рейха",
    "«Нет такой нации, которая не могла бы возродиться» - Адольф Гитлер, фюрер Третьего рейха",
    "-«Официант, Яйцо! -Вам сварить или пожарить? - Почесать»",
    "«Бип буп биип» -R2D2",
]

@client.command()
async def quote(ctx):
    # Выбираем случайную цитату
    quote = random.choice(quotes)

    # Создание встраиваемого сообщения
    embed = discord.Embed(
        title = "Ваша цитата на сегодня",
        description = quote,
        color = discord.Color.blue()
    )

    # Добавление аватарки пользователя
    embed.set_thumbnail(url=ctx.author.avatar.url)

    # Отправка встраиваемого сообщения
    await ctx.send(embed=embed)


@client.command()
async def ping(ctx):
    # Вычисляем задержку путем вычитания времени отправки сообщения от текущего времени
    latency = round(client.latency * 1000)  # конвертируем в миллисекунды

    # Создание встраиваемого сообщения
    embed = discord.Embed(
        title = "Пинг",
        description = f"Задержка: {latency}ms",
        color = discord.Color.blue()
    )

    # Добавление аватарки пользователя
    embed.set_thumbnail(url=ctx.author.avatar.url)

    # Отправка встраиваемого сообщения
    await ctx.send(embed=embed)


load_dotenv()
token = os.getenv('DISCORD_TOKEN')

client.run(token)