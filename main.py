from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

import os
import discord
from discord.ext import commands

# 環境変数からトークンを読み込む
TOKEN = os.environ.get("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command()
async def ping(ctx):
    await ctx.send("ぽん！")
    
from discord import app_commands

# 仮想通貨の残高を保存する辞書
user_balances = {}

@bot.tree.command(name="残高", description="自分のLydia残高を確認します")
async def check_balance(interaction: discord.Interaction):
    user_id = interaction.user.id
    balance = user_balances.get(user_id, 0)
    await interaction.response.send_message(
        f"あなたの残高は {balance} Lydia です。",
        ephemeral=True  # ← 自分だけに見える
    )

@bot.event
async def on_ready():
    print(f"{bot.user} がログインしました！")
    try:
        synced = await bot.tree.sync()
        print(f"Slashコマンド {len(synced)} 個を同期しました")
    except Exception as e:
        print(f"スラッシュコマンド同期エラー: {e}")

# トークン実行
keep_alive()
bot.run(TOKEN)
