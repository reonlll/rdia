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

# ガチャで引いたロールの記録用（再起動で消える）
user_owned_roles = {}  # user_id: [ロール名, ロール名, ...]


# MyClient定義
class MyClient(commands.Bot):
    async def setup_hook(self):
        await self.tree.sync()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
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

@bot.tree.command(name="ロール増加", description="指定したロールの全員にLydiaを増加します")
@app_commands.describe(role="対象のロール", amount="増加させるLydiaの金額")
async def add_to_role(interaction: discord.Interaction, role: discord.Role, amount: int):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("このコマンドは管理者のみ使用できます。", ephemeral=True)
        return

    if amount <= 0:
        await interaction.response.send_message("増加額は1以上にしてください。", ephemeral=True)
        return

    recipients = [member for member in role.members if not member.bot]
    for member in recipients:
        user_balances[member.id] = user_balances.get(member.id, 0) + amount

    await interaction.response.send_message(
        f"{role.name} ロールの {len(recipients)} 人に {amount} Lydia を増加させました。",
        ephemeral=True
    )
    
@bot.tree.command(name="ロール減少", description="指定したロールの全員からLydiaを減少させます")
@app_commands.describe(role="対象のロール", amount="減少させるLydiaの金額")
async def subtract_from_role(interaction: discord.Interaction, role: discord.Role, amount: int):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("このコマンドは管理者のみ使用できます。", ephemeral=True)
        return

    if amount <= 0:
        await interaction.response.send_message("減少額は1以上にしてください。", ephemeral=True)
        return

    recipients = [member for member in role.members if not member.bot]
    for member in recipients:
        current = user_balances.get(member.id, 0)
        user_balances[member.id] = max(current - amount, 0)

    await interaction.response.send_message(
        f"{role.name} ロールの {len(recipients)} 人から {amount} Lydia を減少させました。",
        ephemeral=True
    )

import random
from discord import ui

GACHA_COST = 30000  # 1回のガチャに必要なLydia
GACHA_ROLE_NAMES = [
    "ロールガチャテスト R",
    "ロールガチャテスト SR",
    "ロールガチャテスト SSR",
    "ロールガチャテスト UR"
]

class GachaButtonView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="🎲 ガチャを回す！（30000Lydia）", style=discord.ButtonStyle.primary, custom_id="gacha_button")
    async def gacha(self, interaction: discord.Interaction, button: ui.Button):
        user_id = interaction.user.id
        balance = user_balances.get(user_id, 0)

        if balance < GACHA_COST:
            await interaction.response.send_message("💸 Lydiaが足りません！（30000必要）", ephemeral=True)
            return

        user_balances[user_id] -= GACHA_COST
        result = random.choice(GACHA_ROLE_NAMES)

        owned = user_owned_roles.setdefault(user_id, [])
        if result not in owned:
            owned.append(result)

        await interaction.response.send_message(
            f"🎉 あなたは **{result}** を引きました！\n（残高：{user_balances[user_id]} Lydia）",
            ephemeral=True
        )
        
@client.tree.command(name="ロールガチャ設置", description="ロールガチャの説明とボタンを設置します（管理者限定）")
async def setup_gacha(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("このコマンドは管理者限定です。", ephemeral=True)
        return

    embed = discord.Embed(
        title="🎁 ロールガチャ - ZeniTh coin",
        description=(
            f"以下のボタンからロールガチャが引けます！\n"
            f"価格：**{GACHA_COST} Lydia**\n\n"
            "**排出ロール一覧：**\n"
            "🟢 ロールガチャテスト R\n"
            "🔵 ロールガチャテスト SR\n"
            "🟣 ロールガチャテスト SSR\n"
            "🟡 ロールガチャテスト UR"
        ),
        color=discord.Color.gold()
    )

    await interaction.channel.send(embed=embed, view=GachaButtonView())
    await interaction.response.send_message("✅ ガチャを設置しました！", ephemeral=True)

@client.tree.command(name="ロール所持一覧", description="自分がガチャで引いたロール一覧を確認します。")
async def role_list(interaction: discord.Interaction):
    owned = user_owned_roles.get(interaction.user.id, [])
    if not owned:
        await interaction.response.send_message("まだロールガチャを引いていません。", ephemeral=True)
        return

    await interaction.response.send_message(
        "🎖 あなたの所持ロール：\n" + "\n".join(f"- {r}" for r in owned),
        ephemeral=True
    )
    



# 起動時処理
@bot.event
async def on_ready():
    print(f"{bot.user} がログインしました！")

# 実行
keep_alive()
bot.run(os.environ["DISCORD_TOKEN"])
