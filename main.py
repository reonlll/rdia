from flask import Flask
from threading import Thread

# keep_alive設定
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
from discord import app_commands

# 仮想通貨残高を保存
user_balances = {}

# MyClient定義
class MyClient(commands.Bot):
    async def setup_hook(self):
        await self.tree.sync()

intents = discord.Intents.default()
intents.message_content = True

bot = MyClient(command_prefix="!", intents=intents)

# /残高
@bot.tree.command(name="残高", description="自分のLydia残高を確認します")
async def check_balance(interaction: discord.Interaction):
    user_id = interaction.user.id
    balance = user_balances.get(user_id, 0)
    await interaction.response.send_message(
        f"あなたの残高は {balance} Lydia です。",
        ephemeral=True
    )

# /送金
@bot.tree.command(name="送金", description="他のユーザーにLydiaを送金します")
@app_commands.describe(member="送金相手", amount="送金額")
async def transfer(interaction: discord.Interaction, member: discord.Member, amount: int):
    sender_id = interaction.user.id
    receiver_id = member.id
    if amount <= 0:
        await interaction.response.send_message("送金額は1以上にしてください。", ephemeral=True)
        return
    if user_balances.get(sender_id, 0) < amount:
        await interaction.response.send_message("残高が足りません。", ephemeral=True)
        return
    user_balances[sender_id] -= amount
    user_balances[receiver_id] = user_balances.get(receiver_id, 0) + amount
    await interaction.response.send_message(
        f"{member.display_name} さんに {amount} Lydia を送金しました！\n"
        f"あなたの新しい残高は {user_balances[sender_id]} Lydia です。",
        ephemeral=True
    )

# /金額増加
@bot.tree.command(name="金額増加", description="管理者専用：ユーザーのLydiaを増加")
@app_commands.describe(member="対象ユーザー", amount="増加額")
async def increase(interaction: discord.Interaction, member: discord.Member, amount: int):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("管理者専用です", ephemeral=True)
        return
    if amount <= 0:
        await interaction.response.send_message("金額は1以上で指定してください。", ephemeral=True)
        return
    user_balances[member.id] = user_balances.get(member.id, 0) + amount
    await interaction.response.send_message(
        f"{member.display_name} さんに {amount} Lydia を増加しました。\n"
        f"現在の残高：{user_balances[member.id]} Lydia", ephemeral=True)

# /金額減少
@bot.tree.command(name="金額減少", description="管理者専用：ユーザーのLydiaを減少")
@app_commands.describe(member="対象ユーザー", amount="減少額")
async def decrease(interaction: discord.Interaction, member: discord.Member, amount: int):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("管理者専用です", ephemeral=True)
        return
    if amount <= 0:
        await interaction.response.send_message("金額は1以上で指定してください。", ephemeral=True)
        return
    current = user_balances.get(member.id, 0)
    if current < amount:
        await interaction.response.send_message("残高が足りません。", ephemeral=True)
        return
    user_balances[member.id] = current - amount
    await interaction.response.send_message(
        f"{member.display_name} さんから {amount} Lydia を減少しました。\n"
        f"現在の残高：{user_balances[member.id]} Lydia", ephemeral=True)

# /金額一覧（ランキング）
@bot.tree.command(name="金額一覧", description="管理者専用：全ユーザーのLydiaをランキング表示")
async def ranking(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("管理者専用です", ephemeral=True)
        return
    if not user_balances:
        await interaction.response.send_message("まだ誰もLydiaを持っていません。", ephemeral=True)
        return
    sorted_bal = sorted(user_balances.items(), key=lambda x: x[1], reverse=True)
    lines = []
    for i, (uid, bal) in enumerate(sorted_bal, start=1):
        member = interaction.guild.get_member(uid)
        name = member.display_name if member else f"不明なユーザー（ID: {uid}）"
        lines.append(f"{i}. {name}：{bal} Lydia")
    text = "\n".join(lines)
    await interaction.response.send_message(f"💰 **Lydiaランキング** 💰\n{text}", ephemeral=True)

# 起動時処理
@bot.event
async def on_ready():
    print(f"{bot.user} がログインしました！")

# 実行
keep_alive()
bot.run
