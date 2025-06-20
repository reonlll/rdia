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

import json
import os
import discord
import requests
import datetime
from discord.ext import commands
from discord import app_commands

# --- jsonbin.io用設定 ---
BALANCE_BIN_ID = "685190308960c979a5ab83e4"  # ←修正
ROLES_BIN_ID = "6851e9728960c979a5abb516"
API_KEY = "$2a$10$DUY6hRZaDGFQ1O6ddUbZpuDZY/k0xEA6iX69Ec2Qgc5Y4Rnihr9iO"

from discord import ui, Interaction, ButtonStyle

class HotelView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="🏩 ツーショ（10000Lydia／塔の住人は無料）", style=ButtonStyle.primary, custom_id="hotel_twoshot")
    async def twoshot(self, interaction: Interaction, button: ui.Button):
        await create_twoshot_vc(interaction)

    @ui.button(label="🔒 シークレット（30000Lydia）", style=ButtonStyle.secondary, custom_id="hotel_secret")
    async def secret(self, interaction: Interaction, button: ui.Button):
        await create_secret_vc(interaction)

    @ui.button(label="🌈 フリーダム（50000Lydia）", style=ButtonStyle.success, custom_id="hotel_freedom")
    async def freedom(self, interaction: Interaction, button: ui.Button):
        await create_freedom_vc(interaction)

await interaction.channel.send(
    embed=discord.Embed(
        title="🏨 ホテルメニュー",
        description=(
            "好きな部屋を選んで、VCを作成しよう！\n\n"
            "🏩 ツーショ：2人部屋（**10000Lydia／塔の住人は無料**）\n"
            "🔒 シークレット：誰にも見られない2人部屋（30000Lydia）\n"
            "🌈 フリーダム：何でもアリの自由な部屋（50000Lydia）\n\n"
            "※VCは12時間後に自動削除されます。"
        ),
        color=discord.Color.purple()
    ),
    view=HotelView()
)


def save_balances():
    url = f"https://api.jsonbin.io/v3/b/{BIN_ID}"
    headers = {
        "Content-Type": "application/json",
        "X-Master-Key": API_KEY,
        "X-Bin-Versioning": "false"
    }
    data = json.dumps(user_balances)
    res = requests.put(url, headers=headers, data=data)
    print("保存結果:", res.status_code)

def save_roles():
    save_to_jsonbin(ROLE_BIN_ID, user_owned_roles)

def load_balances():
    global user_balances
    url = f"https://api.jsonbin.io/v3/b/{BIN_ID}/latest"
    headers = {
        "X-Master-Key": API_KEY
    }
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        user_balances = {int(k): v for k, v in res.json()['record'].items()}
        print("読み込み成功:", user_balances)
    else:
        print("読み込み失敗:", res.status_code)

# 保存処理（共通化）
def save_to_jsonbin(bin_id, data):
    url = f"https://api.jsonbin.io/v3/b/{bin_id}"
    headers = {
        "Content-Type": "application/json",
        "X-Master-Key": API_KEY,
        "X-Bin-Versioning": "false"
    }
    requests.put(url, headers=headers, json=data)

def save_balances():
    save_to_jsonbin(BALANCE_BIN_ID, user_balances)

def save_roles():
    save_to_jsonbin(ROLES_BIN_ID, user_owned_roles)

def load_from_jsonbin(bin_id):
    url = f"https://api.jsonbin.io/v3/b/{bin_id}/latest"
    headers = {
        "X-Master-Key": API_KEY
    }
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return res.json()["record"]
    else:
        return {}

def load_balances():
    global user_balances
    user_balances = {int(k): v for k, v in load_from_jsonbin(BALANCE_BIN_ID).items()}

def load_roles():
    global user_owned_roles
    user_owned_roles = {int(k): v for k, v in load_from_jsonbin(ROLES_BIN_ID).items()}

# --- データ構造（残高・ロール記録など） ---
user_balances = {}
user_owned_roles = {}
last_stack_date = {}
tower_data = {
    "light": 0,
    "shadow": 0
}
LAST_STACK = {}

# MyClient定義
class MyClient(commands.Bot):
    async def setup_hook(self):
        await self.tree.sync()

# 意図的に「client」を使ってないなら、下の1行だけに統一しましょう👇

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
    save_balances()
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
    save_balances()
    
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
    save_balances()
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
        save_balances()

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
        save_balances()

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
        
@bot.tree.command(name="ロールガチャ設置", description="ロールガチャの説明とボタンを設置します（管理者限定）")
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
    save_roles()
    await interaction.response.send_message("✅ ガチャを設置しました！", ephemeral=True)

@bot.tree.command(name="ロール所持一覧", description="自分がガチャで引いたロール一覧を確認します。")
async def role_list(interaction: discord.Interaction):
    owned = user_owned_roles.get(interaction.user.id, [])
    if not owned:
        await interaction.response.send_message("まだロールガチャを引いていません。", ephemeral=True)
        return

    await interaction.response.send_message(
        "🎖 あなたの所持ロール：\n" + "\n".join(f"- {r}" for r in owned),
        ephemeral=True
    )
    
# オートコンプリート関数（asyncに修正）
async def autocomplete_roles(interaction: discord.Interaction, current: str):
    owned = user_owned_roles.get(interaction.user.id, [])
    return [
        app_commands.Choice(name=role, value=role)
        for role in owned
        if current.lower() in role.lower()
    ]

# ロール付与コマンド（選択式）
@bot.tree.command(name="ロール付与", description="自分が引いたロールから1つを選んで付与します。")
@app_commands.describe(role_name="付与したいロール名（選択式）")
@app_commands.autocomplete(role_name=autocomplete_roles)
async def assign_role(interaction: discord.Interaction, role_name: str):
    user = interaction.user
    guild = interaction.guild
    owned = user_owned_roles.get(user.id, [])
    save_roles()
    
    if role_name not in owned:
        await interaction.response.send_message("❌ このロールはガチャで獲得していません。", ephemeral=True)
        return

    role = discord.utils.get(guild.roles, name=role_name)
    if not role:
        await interaction.response.send_message("⚠️ 指定したロールがサーバーに存在しません。", ephemeral=True)
        return

    if role in user.roles:
        await interaction.response.send_message("✅ すでにこのロールは付与されています。", ephemeral=True)
        return

    try:
        await user.add_roles(role)
        await interaction.response.send_message(f"🎉 ロール **{role.name}** を付与しました！", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("🚫 Botにそのロールを付与する権限がありません。", ephemeral=True)

# 非同期オートコンプリート関数（必ず async def で書く）
async def autocomplete_owned_roles(interaction: discord.Interaction, current: str):
    owned = user_owned_roles.get(interaction.user.id, [])
    return [
        app_commands.Choice(name=role, value=role)
        for role in owned
        if current.lower() in role.lower()
    ]

# /ロール外しコマンド（記録は残す）
@bot.tree.command(name="ロール外し", description="自分からロールを外します（所持記録は残ります）")
@app_commands.describe(role_name="外したいロール名（選択式）")
@app_commands.autocomplete(role_name=autocomplete_owned_roles)
async def detach_role(interaction: discord.Interaction, role_name: str):
    user = interaction.user
    guild = interaction.guild
    owned = user_owned_roles.get(user.id, [])
    save_roles()
    if role_name not in owned:
        await interaction.response.send_message("❌ このロールはガチャで獲得していません。", ephemeral=True)
        return

    role = discord.utils.get(guild.roles, name=role_name)
    if not role:
        await interaction.response.send_message("⚠️ ロールがサーバー上に見つかりません。", ephemeral=True)
        return

    if role not in user.roles:
        await interaction.response.send_message("🔎 現在そのロールは付与されていません。", ephemeral=True)
        return

    try:
        await user.remove_roles(role)
        await interaction.response.send_message(f"🗑 ロール **{role.name}** を外しました。", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("🚫 Botにそのロールを外す権限がありません。", ephemeral=True)

from discord import ui, Interaction, ButtonStyle
import random

JANKEN_COST = 2000
JANKEN_CHOICES = {"✊": "グー", "✌️": "チョキ", "✋": "パー"}

class JankenView(ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=30)
        self.user_id = user_id

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("これは他の人のじゃんけんです。", ephemeral=True)
            return False
        return True

    @ui.button(label="✊", style=ButtonStyle.primary)
    async def rock(self, interaction: Interaction, button: ui.Button):
        await self.play_janken(interaction, "✊")

    @ui.button(label="✌️", style=ButtonStyle.primary)
    async def scissors(self, interaction: Interaction, button: ui.Button):
        await self.play_janken(interaction, "✌️")

    @ui.button(label="✋", style=ButtonStyle.primary)
    async def paper(self, interaction: Interaction, button: ui.Button):
        await self.play_janken(interaction, "✋")

    async def play_janken(self, interaction: Interaction, user_choice: str):
        user_id = interaction.user.id
        balance = user_balances.get(user_id, 0)

        if balance < JANKEN_COST:
            await interaction.response.edit_message(
                content="💸 Lydiaが足りません！（2000必要）", view=None)
            return

        bot_choice = random.choice(list(JANKEN_CHOICES.keys()))
        result_text = (
            f"🧑 {interaction.user.display_name} のじゃんけん！\n"
            f"あなた：{JANKEN_CHOICES[user_choice]} vs Bot：{JANKEN_CHOICES[bot_choice]}\n\n"
        )

        if user_choice == bot_choice:
            result_text += "🤝 あいこ！Lydiaの変動はありません。"
        elif (user_choice == "✊" and bot_choice == "✌️") or \
             (user_choice == "✌️" and bot_choice == "✋") or \
             (user_choice == "✋" and bot_choice == "✊"):
            user_balances[user_id] += JANKEN_COST
            result_text += f"🎉 勝ち！2000 Lydia 獲得！"
        else:
            user_balances[user_id] -= JANKEN_COST
            result_text += f"😢 負け… 2000 Lydia 消費"

        save_balances()
        await interaction.message.edit(content=result_text, view=None)

@bot.tree.command(name="じゃんけん", description="Botとじゃんけんをします（2000Lydia消費）")
async def janken(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"🕹 {interaction.user.display_name} がじゃんけんを開始しました！選んでください：",
        view=JankenView(interaction.user.id)
    )

@bot.tree.command(name="塔を見る", description="自分の所属する塔の進捗を確認します")
async def view_tower(interaction: discord.Interaction):
    user = interaction.user

    has_light_role = discord.utils.get(user.roles, name="黎明")
    has_shadow_role = discord.utils.get(user.roles, name="夜影")

    if has_light_role and not has_shadow_role:
        await interaction.response.send_message(f"🗼 **黎明の塔** は現在 **{tower_data['light']} 階**です。", ephemeral=True)

    elif has_shadow_role and not has_light_role:
        await interaction.response.send_message(f"🌙 **夜影の塔** は現在 **{tower_data['shadow']} 階**です。", ephemeral=True)

    elif has_light_role and has_shadow_role:
        await interaction.response.send_message("⚠️ あなたは『黎明』と『夜影』両方のロールを持っています。運営にご連絡ください。", ephemeral=True)

    else:
        await interaction.response.send_message("🔒 このコマンドを使うには「黎明」または「夜影」のロールが必要です。", ephemeral=True)

import datetime
import random

@bot.tree.command(name="塔を積む", description="あなたの勢力の塔を積み上げます（1日1回）")
async def stack_tower(interaction: discord.Interaction):
    user = interaction.user
    user_id = user.id

    # ロール取得（黎明＝light、夜影＝shadow）
    黎明ロール = discord.utils.get(user.roles, name="黎明")
    夜影ロール = discord.utils.get(user.roles, name="夜影")

    if not 黎明ロール and not 夜影ロール:
        await interaction.response.send_message("❌ あなたには黎明または夜影のロールが必要です。", ephemeral=True)
        return

    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    if LAST_STACK.get(user_id) == today:
        await interaction.response.send_message("📅 今日はもう塔を積みました。", ephemeral=True)
        return

    stack_amount = random.randint(1, 5)

    if 黎明ロール:
        tower_data["light"] += stack_amount
        tower_name = "黎明の塔"
    else:
        tower_data["shadow"] += stack_amount
        tower_name = "夜影の塔"

    LAST_STACK[user_id] = today

    await interaction.channel.send(
        f"🧱 {user.display_name} さんが **{tower_name}** に **{stack_amount}階** 積みました！"
    )
    await interaction.response.send_message("✅ 塔を積みました！", ephemeral=True)

@bot.tree.command(name="日にちリセット", description="全ユーザーの塔積み制限をリセットします（管理者専用）")
async def reset_stack_date(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ 管理者専用のコマンドです。", ephemeral=True)
        return

    LAST_STACK.clear()
    await interaction.response.send_message("✅ 全ユーザーの塔積み制限をリセットしました。")

from discord.ext import tasks
import asyncio

HOTEL_COST = 10000
HOTEL_ROLE_NAME = "塔の住人"

class HotelButtonView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="🏨 ツーショ部屋を借りる", style=discord.ButtonStyle.primary, custom_id="hotel_room")
    async def hotel_room_button(self, interaction: discord.Interaction, button: ui.Button):
        user = interaction.user
        guild = interaction.guild

        # 残高・ロールチェック
        is_free = HOTEL_ROLE_NAME in [role.name for role in user.roles]
        if not is_free:
            if user_balances.get(user.id, 0) < HOTEL_COST:
                await interaction.response.send_message("💸 残高が足りません（10000 Lydia 必要）", ephemeral=True)
                return
            user_balances[user.id] -= HOTEL_COST
            save_balances()

        # VCを作成
        category = discord.utils.get(guild.categories, name="ホテル")  # 既存カテゴリに設置
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(connect=True, view_channel=True),
            user: discord.PermissionOverwrite(connect=True, view_channel=True, manage_channels=True),
        }
        vc = await guild.create_voice_channel(
            name=f"ツーショ - {user.display_name}",
            overwrites=overwrites,
            category=category
        )
        await interaction.response.send_message(f"✅ ボイスチャンネル「{vc.name}」を作成しました！\n12時間後に削除されます。", ephemeral=True)

        # 削除タスク
        async def delete_after_delay():
            await asyncio.sleep(43200)  # 12時間
            await vc.delete()

        bot.loop.create_task(delete_after_delay())

@bot.tree.command(name="シークレットホテル", description="2人だけのシークレット部屋を作ります（30000Lydia）")
async def create_secret_hotel(interaction: discord.Interaction):
    user = interaction.user
    user_id = user.id
    guild = interaction.guild

    HOTEL_COST = 30000

    if user_balances.get(user_id, 0) < HOTEL_COST:
        await interaction.response.send_message("💸 残高が足りません（30000 Lydia 必要）", ephemeral=True)
        return

    # 残高を減らして保存
    user_balances[user_id] -= HOTEL_COST
    save_balances()

    # カテゴリ取得 or 作成
    category = discord.utils.get(guild.categories, name="ホテル")
    if not category:
        category = await guild.create_category("ホテル")

    # VC権限設定（作成者と管理者以外は見えない）
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        user: discord.PermissionOverwrite(view_channel=True, connect=True, speak=True),
    }

    for role in guild.roles:
        if role.permissions.administrator:
            overwrites[role] = discord.PermissionOverwrite(view_channel=True, connect=True)

    # VC作成
    vc = await guild.create_voice_channel(
        name=f"シークレット-{user.display_name}",
        category=category,
        user_limit=2,
        overwrites=overwrites
    )

    await interaction.response.send_message(f"✅ シークレット部屋を作成しました：{vc.mention}", ephemeral=True)

    # 12時間後に削除
    async def delete_channel_later():
        await asyncio.sleep(43200)  # 12時間 = 43200秒
        await vc.delete()

    asyncio.create_task(delete_channel_later())

@bot.tree.command(name="フリーダムホテル", description="自由な部屋を作成します（50000Lydia）")
async def create_freedom_hotel(interaction: discord.Interaction):
    user = interaction.user
    user_id = user.id
    guild = interaction.guild

    HOTEL_COST = 50000

    if user_balances.get(user_id, 0) < HOTEL_COST:
        await interaction.response.send_message("💸 残高が足りません（50000 Lydia 必要）", ephemeral=True)
        return

    # 残高を減らして保存
    user_balances[user_id] -= HOTEL_COST
    save_balances()

    # カテゴリ取得 or 作成
    category = discord.utils.get(guild.categories, name="ホテル")
    if not category:
        category = await guild.create_category("ホテル")

    # VC作成（制限なし・誰でも見える）
    vc = await guild.create_voice_channel(
        name=f"フリーダム-{user.display_name}",
        category=category
    )

    await interaction.response.send_message(f"✅ フリーダム部屋を作成しました：{vc.mention}", ephemeral=True)

    # 12時間後に削除
    async def delete_channel_later():
        await asyncio.sleep(43200)  # 12時間 = 43200秒
        await vc.delete()

    asyncio.create_task(delete_channel_later())

@bot.tree.command(name="ホテルボタン設置", description="ホテルメニューとVC作成ボタンを設置します（管理者限定）")
async def setup_hotel_buttons(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ このコマンドは管理者専用です。", ephemeral=True)
        return

    embed = discord.Embed(
        title="🏨 ホテルメニュー",
        description=(
            "以下から部屋を選んでVCを作成しましょう！\n\n"
            "🏩 **ツーショ**：2人部屋（**10000Lydia／塔の住人は無料**）\n"
            "🔒 **シークレット**：管理者以外見えない2人部屋（30000Lydia）\n"
            "🌈 **フリーダム**：自由な部屋（50000Lydia）\n\n"
            "※VCは12時間後に自動削除されます。"
        ),
        color=discord.Color.blurple()
    )

    await interaction.channel.send(embed=embed, view=HotelView())
    await interaction.response.send_message("✅ ホテルメニューを設置しました。", ephemeral=True)

# 起動時処理
@bot.event
async def on_ready():
    load_balances()
    load_roles()
    print(f"{bot.user} がログインしました！")

# 実行
keep_alive()
bot.run(os.environ["DISCORD_TOKEN"])
