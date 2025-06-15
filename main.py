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

@bot.tree.command(name="送金", description="他のユーザーにLydiaを送金します")
@app_commands.describe(member="送金相手のユーザー", amount="送金するLydiaの額")
async def transfer_balance(interaction: discord.Interaction, member: discord.Member, amount: int):
    sender_id = interaction.user.id
    receiver_id = member.id

    if amount <= 0:
        await interaction.response.send_message("送金額は1以上にしてください。", ephemeral=True)
        return

    sender_balance = user_balances.get(sender_id, 0)

    if sender_balance < amount:
        await interaction.response.send_message("残高が足りません。", ephemeral=True)
        return

    # 送金処理
    user_balances[sender_id] = sender_balance - amount
    user_balances[receiver_id] = user_balances.get(receiver_id, 0) + amount

    await interaction.response.send_message(
        f"{member.display_name} さんに {amount} Lydia を送金しました！\n"
        f"あなたの新しい残高は {user_balances[sender_id]} Lydia です。",
        ephemeral=True  # 自分だけに表示
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
