import random
import sqlite3
import discord
from discord.ext import tasks
from discord import app_commands
from datetime import datetime, timedelta, timezone

# 連接 SQLite 資料庫
connection_db_gacha_record = sqlite3.connect("data/gacha_record.db")
cursor_gacha_record = connection_db_gacha_record.cursor()

connection_db_patrol_record = sqlite3.connect("data/patrol_record.db")
cursor_patrol_record = connection_db_patrol_record.cursor()

# 建立抽卡紀錄表
cursor_gacha_record.execute("""
    CREATE TABLE IF NOT EXISTS 抽卡紀錄 (
        伺服器_id INTEGER,
        使用者_id INTEGER,
        總計出金數量 INTEGER DEFAULT 0,
        總計常駐數量 INTEGER DEFAULT 0,
        總計限定數量 INTEGER DEFAULT 0,
        總計出紫數量 INTEGER DEFAULT 0,
        總計出藍數量 INTEGER DEFAULT 0,
        上一次出金 TEXT DEFAULT NULL,
        出金計數 INTEGER DEFAULT 0,
        出紫計數 INTEGER DEFAULT 0,
        PRIMARY KEY (伺服器_id, 使用者_id)
    )
""")
connection_db_gacha_record.commit()

cursor_patrol_record.execute("""
    CREATE TABLE IF NOT EXISTS 巡視紀錄 (
        伺服器_id INTEGER,
        頻道_id INTEGER,
        使用者_id INTEGER,
        總計出金數量 INTEGER DEFAULT 0,
        總計出紫數量 INTEGER DEFAULT 0,
        總計出藍數量 INTEGER DEFAULT 0,
        目前巡視裝備 TEXT DEFAULT NULL,
        目前巡視等級 TEXT DEFAULT NULL,
        目前巡視時間 TEXT DEFAULT NULL,
        巡視完成時間 TEXT DEFAULT NULL,
        PRIMARY KEY (伺服器_id, 使用者_id)
    )
""")
connection_db_patrol_record.commit()

bot = discord.Client(intents=discord.Intents.default())

gacha_group = app_commands.Group(name="尋覓模擬", description="尋覓模擬")
patrol_group = app_commands.Group(name="巡視模擬", description="巡視模擬")

tree = app_commands.CommandTree(bot)

tree.add_command(gacha_group)
tree.add_command(patrol_group)

def get_user_data_gacha_record(guild_id, user_id):
    """取得使用者抽卡數據"""
    cursor_gacha_record.execute("""
        SELECT 總計出金數量, 總計常駐數量, 總計限定數量, 總計出紫數量, 總計出藍數量, 上一次出金, 出金計數, 出紫計數
        FROM 抽卡紀錄 WHERE 伺服器_id = ? AND 使用者_id = ?
    """, (guild_id, user_id))
    data = cursor_gacha_record.fetchone()
    
    if not data:
        cursor_gacha_record.execute("""
            INSERT INTO 抽卡紀錄 (伺服器_id, 使用者_id)
            VALUES (?, ?)
        """, (guild_id, user_id))
        connection_db_gacha_record.commit()
        return (0, 0, 0, 0, 0, None, 0, 0)
    
    return data

def update_user_data_gacha_record(guild_id, user_id, gold_total, resident_total, up_total, purple_total, blue_total, last_gold, gold_count, blue_count):
    """更新使用者抽卡數據"""
    cursor_gacha_record.execute("""
        INSERT INTO 抽卡紀錄 (伺服器_id, 使用者_id, 總計出金數量, 總計常駐數量, 總計限定數量, 總計出紫數量, 總計出藍數量, 上一次出金, 出金計數, 出紫計數)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(伺服器_id, 使用者_id)
        DO UPDATE SET 
            總計出金數量 = ?, 
            總計常駐數量 = ?, 
            總計限定數量 = ?, 
            總計出紫數量 = ?, 
            總計出藍數量 = ?, 
            上一次出金 = ?, 
            出金計數 = ?, 
            出紫計數 = ?
    """, (guild_id, user_id, gold_total, resident_total, up_total, purple_total, blue_total, last_gold, gold_count, blue_count, gold_total, resident_total, up_total, purple_total, blue_total, last_gold, gold_count, blue_count))
    connection_db_gacha_record.commit()

def get_user_data_patrol_record(guild_id, user_id):
    """取得使用者巡視數據"""
    cursor_patrol_record.execute("""
        SELECT 總計出金數量, 總計出紫數量, 總計出藍數量, 目前巡視裝備, 目前巡視等級, 目前巡視時間, 巡視完成時間
        FROM 巡視紀錄 WHERE 伺服器_id = ? AND 使用者_id = ?
    """, (guild_id, user_id))
    data = cursor_patrol_record.fetchone()
    
    if not data:
        cursor_patrol_record.execute("""
            INSERT INTO 巡視紀錄 (伺服器_id, 使用者_id)
            VALUES (?, ?)
        """, (guild_id, user_id))
        connection_db_patrol_record.commit()
        return (0, 0, 0, None, None, None, None)
    
    return data

def update_user_data_patrol_record(guild_id, channel_id, user_id, gold_total, purple_total, blue_total, now_patrol, patrol_level, patrol_time, patrol_finish_time):
    """更新使用者巡視數據"""
    cursor_patrol_record.execute("""
        INSERT INTO 巡視紀錄 (伺服器_id, 頻道_id, 使用者_id, 總計出金數量, 總計出紫數量, 總計出藍數量, 目前巡視裝備, 目前巡視等級, 目前巡視時間, 巡視完成時間)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(伺服器_id, 使用者_id)
        DO UPDATE SET 
            頻道_id = ?,
            總計出金數量 = ?, 
            總計出紫數量 = ?, 
            總計出藍數量 = ?, 
            目前巡視裝備 = ?, 
            目前巡視等級 = ?, 
            目前巡視時間 = ?, 
            巡視完成時間 = ?
    """, (guild_id, channel_id, user_id, gold_total, purple_total, blue_total, now_patrol, patrol_level, patrol_time, patrol_finish_time, channel_id, gold_total, purple_total, blue_total, now_patrol, patrol_level, patrol_time, patrol_finish_time))
    connection_db_patrol_record.commit()


GOLD_RATE = 1.2
PURPLE_RATE = 15.0
BLUE_RATE = 83.8
PITY_LIMIT = 90

def gacha_精選尋覓(gold_total, resident_total, up_total, purple_total, blue_total, last_gold, gold_count, blue_count):
    gold_count += 1  # 累積抽卡次數
    roll = random.uniform(0, 100)

    if gold_count >= PITY_LIMIT:
        rarity = "金"
    elif blue_count == 9:
        rarity = "金" if roll <= GOLD_RATE else "紫"
    elif roll <= GOLD_RATE:
        rarity = "金"
    elif roll <= GOLD_RATE + PURPLE_RATE:
        rarity = "紫"
    else:
        rarity = "藍"

    if rarity == "金":
        if last_gold == "常駐":
            gold_type = "芙蕾"
            rarity = "芙蕾"
            up_total += 1
        else:
            gold_type = random.choice(["常駐", "芙蕾"])
            rarity = gold_type
            if gold_type == "芙蕾":
                up_total += 1
            else:
                resident_total += 1
        last_gold = gold_type
        gold_total += 1
        gold_count = 0
        blue_count = 0
    elif rarity == "紫":
        purple_total += 1
        blue_count = 0
    else:
        blue_total += 1
        blue_count += 1

    return rarity, gold_total, resident_total, up_total, purple_total, blue_total, last_gold, gold_count, blue_count



PATROL_LEVELS = [
    ("★", {"hours": 1, "mins": 0}, {"金裝": 0.00, "紫裝": 28.99, "藍裝": 71.01}),
    ("★★", {"hours": 1, "mins": 0}, {"金裝": 0.81, "紫裝": 31.97, "藍裝": 67.22}),
    ("★★★", {"hours": 1, "mins": 0}, {"金裝": 2.43, "紫裝": 35.06, "藍裝": 62.52}),
    ("★★★", {"hours": 1, "mins": 0}, {"金裝": 4.11, "紫裝": 46.17, "藍裝": 49.72}),
    ("★★★★", {"hours": 1, "mins": 30}, {"金裝": 5.79, "紫裝": 50.45, "藍裝": 43.76}),
    ("★★★★", {"hours": 2, "mins": 0}, {"金裝": 7.58, "紫裝": 65.23, "藍裝": 27.19}),
    ("★★★★★", {"hours": 1, "mins": 30}, {"金裝": 10.06, "紫裝": 52.10, "藍裝": 37.85}),
    ("★★★★★", {"hours": 2, "mins": 0}, {"金裝": 12.88, "紫裝": 70.50, "藍裝": 16.62}),
]

def patrol():
    level, time, rates = random.choice(PATROL_LEVELS)
    roll = random.uniform(0, 100)

    if roll <= rates["金裝"]:
        rarity = "金裝"
    elif roll <= rates["金裝"] + rates["紫裝"]:
        rarity = "紫裝"
    else:
        rarity = "藍裝"

    return level, time, rarity

@tasks.loop(minutes=1)
async def check_patrol_timers():
    cursor_patrol_record.execute("SELECT 伺服器_id, 頻道_id, 使用者_id, 巡視完成時間 FROM 巡視紀錄")
    rows = cursor_patrol_record.fetchall()
    current_time = datetime.now()
    for 伺服器_id, 頻道_id, 使用者_id, 巡視完成時間 in rows:
        gold_total, purple_total, blue_total, now_patrol, patrol_level, patrol_time, patrol_finish_time = get_user_data_patrol_record(伺服器_id, 使用者_id)
        if patrol_finish_time != None:
            patrol_finish_time = datetime.strptime(patrol_finish_time, "%Y-%m-%d %H:%M:%S.%f")
        if patrol_finish_time == None:
            continue
        elif patrol_finish_time < current_time:
            channel = bot.get_channel(頻道_id)
            if channel:
                await channel.send(f"<@{使用者_id}> 巡視為 {patrol_level}   {patrol_time}   巡視完成   恭喜獲得：{now_patrol}")
            patrol_finish_time = None
            if now_patrol == "金裝":
                gold_total += 1
            elif now_patrol == "紫裝":
                purple_total += 1
            elif now_patrol == "藍裝":
                blue_total += 1
            update_user_data_patrol_record(伺服器_id, 頻道_id, 使用者_id, gold_total, purple_total, blue_total, now_patrol, patrol_level, patrol_time, patrol_finish_time)

@gacha_group.command(name="單抽", description="進行單抽")
async def discord_single_gacha(interaction: discord.Interaction):
    guild_id, user_id = interaction.guild.id, interaction.user.id
    gold_total, resident_total, up_total, purple_total, blue_total, last_gold, gold_count, blue_count = get_user_data_gacha_record(guild_id, user_id)
    rarity = ""

    rarity, gold_total, resident_total, up_total, purple_total, blue_total, last_gold, gold_count, blue_count = gacha_精選尋覓(gold_total, resident_total, up_total, purple_total, blue_total, last_gold, gold_count, blue_count)

    update_user_data_gacha_record(guild_id, user_id, gold_total, resident_total, up_total, purple_total, blue_total, last_gold, gold_count, blue_count)
    await interaction.response.send_message(f"{interaction.user.mention} 目前尋覓：{gold_count}/90\n單抽結果：{rarity}")

@gacha_group.command(name="十抽", description="進行十抽")
async def discord_ten_gacha(interaction: discord.Interaction):
    guild_id, user_id = interaction.guild.id, interaction.user.id
    gold_total, resident_total, up_total, purple_total, blue_total, last_gold, gold_count, blue_count = get_user_data_gacha_record(guild_id, user_id)
    results = []
    for i in range(10):
        rarity, gold_total, resident_total, up_total, purple_total, blue_total, last_gold, gold_count, blue_count = gacha_精選尋覓(gold_total, resident_total, up_total, purple_total, blue_total, last_gold, gold_count, blue_count)
        results.append(rarity)

    update_user_data_gacha_record(guild_id, user_id, gold_total, resident_total, up_total, purple_total, blue_total, last_gold, gold_count, blue_count)
    await interaction.response.send_message(f"{interaction.user.mention} 目前尋覓：{gold_count}/90\n十抽結果：{' '.join(results)}")

@gacha_group.command(name="統計", description="查詢尋覓模擬的相關資料")
async def discord_query_gacha(interaction: discord.Interaction, 使用者: discord.Member = None):
    guild_id = interaction.guild.id
    user_id = 使用者.id if 使用者 else interaction.user.id
    gold_total, resident_total, up_total, purple_total, blue_total, last_gold, gold_count, blue_count = get_user_data_gacha_record(guild_id, user_id)
    if 使用者 and 使用者.nick is not None:
        名稱 = 使用者.nick
    elif 使用者 and 使用者.name is not None:
        if 使用者.id == interaction.user.id:
            名稱 = interaction.user.id
        else:
            名稱 = 使用者.name
    else:
        名稱 = interaction.user.mention
    embed = discord.Embed(title="尋覓模擬統計", color=discord.Color.gold())
    embed.add_field(name="名稱", value=使用者.mention if 使用者 else interaction.user.mention, inline=False)
    embed.add_field(name="目前尋覓", value=f"{gold_count}/90", inline=False)
    embed.add_field(name="總抽數", value=f"{gold_total+purple_total+blue_total}", inline=False)
    embed.add_field(name="總計常駐數量", value=f"{resident_total}", inline=True)
    embed.add_field(name="總計限定數量", value=f"{up_total}", inline=True)
    embed.add_field(name="總計出金數量", value=f"{gold_total}", inline=True)
    embed.add_field(name="總計出紫數量", value=f"{purple_total}", inline=True)
    embed.add_field(name="總計出藍數量", value=f"{blue_total}", inline=True)
    embed.add_field(name="上次出金英雄", value=f"{last_gold if last_gold else '無'}", inline=False)
    await interaction.response.send_message(embed=embed)

@patrol_group.command(name="巡視", description="進行裝備巡視，獲得金裝/紫裝/藍裝")
async def equipment_patrol(interaction: discord.Interaction):
    guild_id, channel_id, user_id = interaction.guild.id, interaction.channel_id, interaction.user.id
    gold_total, purple_total, blue_total, now_patrol, patrol_level, patrol_time, patrol_finish_time = get_user_data_patrol_record(guild_id, user_id)
    current_time = datetime.now()
    if patrol_finish_time != None:
        patrol_finish_time = datetime.strptime(patrol_finish_time, "%Y-%m-%d %H:%M:%S.%f")
    if patrol_finish_time == None:
        level, time, rarity = patrol()
        mins = "%02d" % time["mins"]
        await interaction.response.send_message(f"{interaction.user.mention} 巡視為 {level}   {time["hours"]}:{mins}   開始巡視")
        now_patrol = rarity

        time_to_add = timedelta(hours=time["hours"], minutes=time["mins"])
        patrol_finish_time = current_time + time_to_add
        patrol_level = level
        patrol_time = f"{time["hours"]}:{mins}"
        update_user_data_patrol_record(guild_id, channel_id, user_id, gold_total, purple_total, blue_total, now_patrol, patrol_level, patrol_time, patrol_finish_time)
    elif patrol_finish_time > current_time:
        time_difference = patrol_finish_time - current_time
        total_seconds = int(time_difference.total_seconds())
        hours_remaining = total_seconds // 3600
        minutes_remaining = (total_seconds % 3600) // 60
        seconds_remaining = total_seconds % 60

        minutes_remaining = f"{minutes_remaining:02d}"
        seconds_remaining = f"{seconds_remaining:02d}"

        await interaction.response.send_message(f"{interaction.user.mention} 巡視為 {patrol_level}   {patrol_time}   巡視還有{hours_remaining}:{minutes_remaining}:{seconds_remaining}")

@patrol_group.command(name="統計", description="查詢巡視模擬的相關資料")
async def discord_query_patrol(interaction: discord.Interaction, 使用者: discord.Member = None):
    guild_id = interaction.guild.id
    user_id = 使用者.id if 使用者 else interaction.user.id
    gold_total, purple_total, blue_total, now_patrol, patrol_level, patrol_time, patrol_finish_time = get_user_data_patrol_record(guild_id, user_id)
    embed = discord.Embed(title="巡視模擬統計", color=discord.Color.blue())
    embed.add_field(name="名稱", value=使用者.mention if 使用者 else interaction.user.mention, inline=False)
    embed.add_field(name="總巡視次數", value=f"{gold_total+purple_total+blue_total}", inline=False)
    embed.add_field(name="總計出金數量", value=f"{gold_total}", inline=True)
    embed.add_field(name="總計出紫數量", value=f"{purple_total}", inline=True)
    embed.add_field(name="總計出藍數量", value=f"{blue_total}", inline=True)
    await interaction.response.send_message(embed=embed)

@bot.event
async def on_ready():
    await tree.sync()
    check_patrol_timers.start()
    print(f"✅ {bot.user} 已上線！")

bot.run("YOUR_TOKEN")