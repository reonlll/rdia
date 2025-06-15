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

@bot.tree.command(name="金額増加", description="管理者専用：指定ユーザーのLydiaを増やします")
@app_commands.describe(member="増加させる相手", amount="増加させるLydiaの金額")
async def increase_balance(interaction: discord.Interaction, member: discord.Member, amount: int):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("このコマンドは管理者のみ使用できます。", ephemeral=True)
        return

    if amount <= 0:
        await interaction.response.send_message("増加額は1以上にしてください。", ephemeral=True)
        return

    user_balances[member.id] = user_balances.get(member.id, 0) + amount

    await interaction.response.send_message(
        f"{member.display_name} さんのLydia残高を {amount} 増加させました。\n"
        f"現在の残高：{user_balances[member.id]} Lydia",
        ephemeral=True
    )
@bot.tree.command(name="金額一覧", description="管理者専用：全ユーザーのLydiaをランキング形式で表示します")
async def balance_ranking(interaction: discord.Interaction):
    # 管理者チェック
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("このコマンドは管理者のみ使用できます。", ephemeral=True)
        return

    if not user_balances:
        await interaction.response.send_message("まだ誰もLydiaを持っていません。", ephemeral=True)
        return

    # 残高降順ソート
    sorted_balances = sorted(user_balances.items(), key=lambda x: x[1], reverse=True)

    ranking_lines = []
    for i, (user_id, balance) in enumerate(sorted_balances, start=1):
        member = interaction.guild.get_member(user_id)
        if member:
            ranking_lines.append(f"{i}. {member.display_name}：{balance} Lydia")
        else:
            ranking_lines.append(f"{i}. 不明なユーザー（ID: {user_id}）：{balance} Lydia")

    ranking_text = "\n".join(ranking_lines)

    await interaction.response.send_message(
        f"💰 **Lydiaランキング** 💰\n\n{ranking_text}",
        ephemeral=True  # 自分にだけ見える
    )

@bot.tree.command(name="金額減少", description="管理者専用：指定ユーザーのLydiaを減少させます")
@app_commands.describe(member="減少させる相手", amount="減少させるLydiaの金額")
async def decrease_balance(interaction: discord.Interaction, member: discord.Member, amount: int):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("このコマンドは管理者のみ使用できます。", ephemeral=True)
        return

    if amount <= 0:
        await interaction.response.send_message("減少額は1以上にしてください。", ephemeral=True)
        return

    current_balance = user_balances.get(member.id, 0)

    if current_balance < amount:
        await interaction.response.send_message(
            f"{member.display_name} さんの残高が不足しています。\n現在の残高：{current_balance} Lydia",
            ephemeral=True
        )
        return

    user_balances[member.id] = current_balance - amount

    await interaction.response.send_message(
        f"{member.display_name} さんのLydia残高を {amount} 減少させました。\n"
        f"新しい残高：{user_balances[member.id]} Lydia",
        ephemeral=True
    )

from discord import app_commands

@bot.tree.command(name="ロール送金", description="指定したロールの全メンバーにLydiaを送金します")
@app_commands.describe(role="対象のロール", amount="送金するLydiaの金額")
async def send_to_role(interaction: discord.Interaction, role: discord.Role, amount: int):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("このコマンドは管理者専用です。", ephemeral=True)
        return

    if amount <= 0:
        await interaction.response.send_message("送金額は1以上にしてください。", ephemeral=True)
        return

    recipients = [member for member in role.members if not member.bot]

    if not recipients:
        await interaction.response.send_message("このロールには送金対象となるメンバーがいません。", ephemeral=True)
        return

    for member in recipients:
        current = user_balances.get(member.id, 0)
        user_balances[member.id] = current + amount

    await interaction.response.send_message(
        f"{role.name} ロールの {len(recipients)} 人に {amount} Lydia を送金しました。",
        ephemeral=True
    )

from discord import app_commands
from discord.ext import commands
import discord

# 辞書に残高を保存
user_balances = {}

class MyClient(commands.Bot):
    async def setup_hook(self):
        await self.tree.sync()

bot = MyClient(command_prefix="!", intents=discord.Intents.all())

@bot.tree.command(name="ロール増加", description="指定したロールの全員にLydiaを増加します")
@app_commands.describe(role="対象のロール", amount="増加させるLydiaの金額")
async def add_to_role(interaction: discord.Interaction, role: discord.Role, amount: int):
    # 管理者のみ実行可能
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("このコマンドは管理者のみ使用できます。", ephemeral=True)
        return

    if amount <= 0:
        await interaction.response.send_message("増加金額は1以上にしてください。", ephemeral=True)
        return

    recipients = role.members
    if not recipients:
        await interaction.response.send_message("このロールにはメンバーがいません。", ephemeral=True)
        return

    for member in recipients:
        user_balances[member.id] = user_balances.get(member.id, 0) + amount

    await interaction.response.send_message(
        f"{role.name} のメンバー {len(recipients)} 人に {amount} Lydia を増加させました。",
        ephemeral=True
    )
    
@bot.tree.command(name="ロール減少", description="指定したロールの全員からLydiaを減少させます")
@app_commands.describe(
    role="対象のロール",
    amount="減少させるLydiaの金額"
)
async def decrease_from_role(interaction: discord.Interaction, role: discord.Role, amount: int):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("このコマンドは管理者のみ使用できます。", ephemeral=True)
        return

    if amount <= 0:
        await interaction.response.send_message("減少額は1以上にしてください。", ephemeral=True)
        return

    recipients = role.members
    if not recipients:
        await interaction.response.send_message("このロールにはメンバーがいません。", ephemeral=True)
        return

    for member in recipients:
        current = user_balances.get(member.id, 0)
        new_balance = max(current - amount, 0)
        user_balances[member.id] = new_balance

    await interaction.response.send_message(
        f"{role.name} のメンバー {len(recipients)} 人から {amount} Lydia を減少させました。",
        ephemeral=True
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
