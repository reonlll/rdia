import os
import discord
from discord.ext import commands

# 環境変数からトークンを読み込む
TOKEN = os.environ.get("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} がログインしました！")

@bot.command()
async def ping(ctx):
    await ctx.send("ぽん！")

# トークン実行
bot.run(TOKEN)
