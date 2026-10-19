import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime, timedelta

# ตั้งค่า Intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ไฟล์เก็บข้อมูล Cooldown
COOLDOWN_FILE = "cooldowns.json"
COOLDOWN_DAYS = 7

# รายชื่อยศอาวุธทั้งหมด 9 ชนิด (ตรงกับยศใน Discord)
WEAPON_ROLES = [
    "ดาบมือเดียว 🗡️",
    "ขวานมือเดียว 🪓",
    "ค้อนมือเดียว 🔨",
    "ดาบสองมือ ⚔️",
    "ขวานสองมือ 🪓💥",
    "ค้อนสองมือ ⛏️",
    "หอก 🔱",
    "ธนู 🏹",
    "หน้าไม้ 🎯"
]

def load_cooldowns():
    if os.path.exists(COOLDOWN_FILE):
        with open(COOLDOWN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cooldowns(data):
    with open(COOLDOWN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

class WeaponSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=role_name, value=role_name)
            for role_name in WEAPON_ROLES
        ]
        super().__init__(
            placeholder="⚔️ เลือกสายอาวุธของคุณที่นี่...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        now = datetime.now()
        cooldowns = load_cooldowns()

        # ตรวจสอบ Cooldown 7 วัน
        if user_id in cooldowns:
            last_select_str = cooldowns[user_id]
            last_select = datetime.fromisoformat(last_select_str)
            next_available = last_select + timedelta(days=COOLDOWN_DAYS)

            if now < next_available:
                remaining = next_available - now
                days = remaining.days
                hours = remaining.seconds // 3600
                minutes = (remaining.seconds % 3600) // 60

                await interaction.response.send_message(
                    f"❌ **คุณติด คูลดาวน์!**\n"
                    f"คุณเพิ่งเปลี่ยนสายอาวุธไป สามารถเปลี่ยนได้อีกครั้งในอีก: **{days} วัน {hours} ชั่วโมง {minutes} นาที**",
                    ephemeral=True
                )
                return

        selected_role_name = self.values[0]
        guild = interaction.guild
        member = interaction.user

        # ลบยศอาวุธเก่าทั้งหมดก่อน
        roles_to_remove = [role for role in member.roles if role.name in WEAPON_ROLES]
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove)

        # ใส่ยศอาวุธใหม่
        new_role = discord.utils.get(guild.roles, name=selected_role_name)
        if new_role:
            await member.add_roles(new_role)
            # บันทึกเวลาที่เลือก
            cooldowns[user_id] = now.isoformat()
            save_cooldowns(cooldowns)

            await interaction.response.send_message(
                f"✅ **เปลี่ยนสายอาวุธสำเร็จ!**\n"
                f"คุณได้รับยศ **{selected_role_name}** เรียบร้อยแล้ว (ติดคูลดาวน์ 7 วัน)",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"⚠️ ไม่พบยศ `{selected_role_name}` ในเซิร์ฟเวอร์ กรุณาติดต่อแอดมิน",
                ephemeral=True
            )

class WeaponSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(WeaponSelect())

@bot.event
async def on_ready():
    print(f"🤖 บอทพร้อมใช้งานแล้วในชื่อ: {bot.user.name}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

# คำสั่งสร้างเมนูเลือกอาวุธ (ใช้ได้เฉพาะแอดมิน)
@bot.tree.command(name="setup_weapon_menu", description="สร้างเมนูเลือกสายอาวุธ")
@app_commands.default_permissions(administrator=True)
async def setup_weapon_menu(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚔️ เลือกสายอาวุธหลักของคุณ",
        description=(
            "โปรดเลือกสายอาวุธที่คุณใช้งานจากเมนูด้านล่าง\n\n"
            "⚠️ **ข้อควรระวัง:**\n"
            "• เมื่อเลือกแล้วจะมี **คูลดาวน์ 7 วัน** ถึงจะเปลี่ยนสายได้อีกครั้ง\n"
            "• ระบบจะเปลี่ยนยศให้อัตโนมัติทันที"
        ),
        color=discord.Color.gold()
    )
    await interaction.channel.send(embed=embed, view=WeaponSelectView())
    await interaction.response.send_message("สร้างเมนูเรียบร้อยแล้ว!", ephemeral=True)

# ใส่ Token ของบอทตรงนี้
bot.run("MTU2MTYwMzcyNjU0Njk2MDQyNg.G16SvJ.1Q9Id0SoA1TViVkPuTPr5ilj2a6MIjQmqtaV3A")
