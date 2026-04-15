from dotenv import load_dotenv
import discord

import json
import os

from discord.ext import commands

load_dotenv()
token = os.getenv("COUNT_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# THREAD_ID = 1482035625057190038
THREAD_ID = 1493740557195939960
STATE_FILE = "counting_state.json"
TEMP_FILE = "counting_state.tmp"

current_number = 0
last_user_ids = []  # stores last two valid users

@bot.event
async def on_ready():
    global current_number, last_user_ids

    print(f"Logged in as {bot.user}")

    thread = await bot.fetch_channel(THREAD_ID)

    current_number, last_user_ids = load_state()

    start = f"The bot is up! The count is at **{current_number}**."

    if len(last_user_ids) == 1:
        user = await bot.fetch_user(last_user_ids[0])
        start += f" Counter @{user.name} counted last!"

    if len(last_user_ids) == 2:
        user1 = await bot.fetch_user(last_user_ids[0])
        user2 = await bot.fetch_user(last_user_ids[1])
        start += f" Counters @{user1.name} and @{user2.name} counted last!"

    start += " Good luck, have fun!"

    await thread.send(start)

@bot.event
async def on_message(message):
    global current_number, last_user_ids

    if message.channel.id != THREAD_ID:
        return

    # Ignore bot messages
    if message.author.bot:
        return

    content = message.content.strip()

    # Ignore comments starting with -#
    if content.startswith("-# "):
        return

    # Try to parse integer
    try:
        num = int(content)
    except ValueError:
        await message.add_reaction("❓")
        return

    # Check user rules
    if len(last_user_ids) >= 1 and message.author.id == last_user_ids[-1]:
        await message.add_reaction("⏳")
        return

    if len(last_user_ids) >= 2 and message.author.id == last_user_ids[-2]:
        await message.add_reaction("⏳")
        return

    # Check if number is valid (+1 or -1)
    if num != current_number + 1 and num != current_number - 1:
        await message.add_reaction("❌")
        return

    # If all checks pass
    current_number = num
    last_user_ids.append(message.author.id)

    # Keep only last 2 users
    if len(last_user_ids) > 2:
        last_user_ids.pop(0)

    save_state()
    await message.add_reaction("✅")

    await bot.process_commands(message)

def load_state():
    if not os.path.exists(STATE_FILE):
        return 0, []

    with open(STATE_FILE, "r") as f:
        data = json.load(f)
        return data["current_number"], data["last_user_ids"]

def save_state():
    data = {
        "current_number": current_number,
        "last_user_ids": last_user_ids
    }

    # write to temp file first
    with open(TEMP_FILE, "w") as f:
        json.dump(data, f)

    # replace original file safely
    os.replace(TEMP_FILE, STATE_FILE)

bot.run(token)