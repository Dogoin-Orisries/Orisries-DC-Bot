import random
import sqlite3
import discord
from discord import app_commands

# 連接 SQLite 資料庫
conn = sqlite3.connect("data/gacha_record.db")
cursor = conn.cursor()

# 建立抽卡紀錄表
cursor.execute("""
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
conn.commit()

bot = discord.Client(intents=discord.Intents.default())
tree = app_commands.CommandTree(bot)

def get_user_data(guild_id, user_id):
    """取得使用者抽卡數據"""
    cursor.execute("""
        SELECT 總計出金數量, 總計常駐數量, 總計限定數量, 總計出紫數量, 總計出藍數量, 上一次出金, 出金計數, 出紫計數
        FROM 抽卡紀錄 WHERE 伺服器_id = ? AND 使用者_id = ?
    """, (guild_id, user_id))
    data = cursor.fetchone()
    
    if not data:
        cursor.execute("""
            INSERT INTO 抽卡紀錄 (伺服器_id, 使用者_id)
            VALUES (?, ?)
        """, (guild_id, user_id))
        conn.commit()
        return (0, 0, 0, 0, 0, None, 0, 0)
    
    return data

def update_user_data(guild_id, user_id, gold_total, resident_total, up_total, purple_total, blue_total, last_gold, gold_count, blue_count):
    """更新使用者抽卡數據"""
    cursor.execute("""
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
    conn.commit()

GOLD_RATE = 1.2
PURPLE_RATE = 15.0
BLUE_RATE = 83.8
PITY_LIMIT = 90

def gacha(gold_total, resident_total, up_total, purple_total, blue_total, last_gold, gold_count, blue_count):
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

@tree.command(name="尋覓模擬單抽", description="進行單抽")
async def discord_single_gacha(interaction: discord.Interaction):
    guild_id, user_id = interaction.guild.id, interaction.user.id
    gold_total, resident_total, up_total, purple_total, blue_total, last_gold, gold_count, blue_count = get_user_data(guild_id, user_id)
    rarity = ""

    rarity, gold_total, resident_total, up_total, purple_total, blue_total, last_gold, gold_count, blue_count = gacha(gold_total, resident_total, up_total, purple_total, blue_total, last_gold, gold_count, blue_count)

    update_user_data(guild_id, user_id, gold_total, resident_total, up_total, purple_total, blue_total, last_gold, gold_count, blue_count)
    await interaction.response.send_message(f"{interaction.user.mention} 目前尋覓：{gold_count}/90\n單抽結果：{rarity}")

@tree.command(name="尋覓模擬十抽", description="進行十抽")
async def discord_ten_gacha(interaction: discord.Interaction):
    guild_id, user_id = interaction.guild.id, interaction.user.id
    gold_total, resident_total, up_total, purple_total, blue_total, last_gold, gold_count, blue_count = get_user_data(guild_id, user_id)
    results = []
    for i in range(10):
        rarity, gold_total, resident_total, up_total, purple_total, blue_total, last_gold, gold_count, blue_count = gacha(gold_total, resident_total, up_total, purple_total, blue_total, last_gold, gold_count, blue_count)
        results.append(rarity)

    update_user_data(guild_id, user_id, gold_total, resident_total, up_total, purple_total, blue_total, last_gold, gold_count, blue_count)
    await interaction.response.send_message(f"{interaction.user.mention} 目前尋覓：{gold_count}/90\n十抽結果：{' '.join(results)}")

@tree.command(name="查詢尋覓模擬", description="查詢尋覓模擬的相關資料")
async def discord_query_gacha(interaction: discord.Interaction):
    guild_id, user_id = interaction.guild.id, interaction.user.id
    gold_total, resident_total, up_total, purple_total, blue_total, last_gold, gold_count, blue_count = get_user_data(guild_id, user_id)

    await interaction.response.send_message(f"{interaction.user.mention}\n目前尋覓：{gold_count}/90\n總抽數：{gold_total+purple_total+blue_total}\n總計常駐數量：{resident_total}\n總計限定數量：{up_total}\n總計出金數量：{gold_total}\n總計出紫數量：{purple_total}\n總計出藍數量：{blue_total}\n上次出金英雄：{last_gold}")

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ {bot.user} 已上線！")

bot.run("YOUR_TOKEN")