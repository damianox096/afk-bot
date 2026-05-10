import discord
import asyncio
import os
from discord.ext import tasks
from datetime import datetime
from flask import Flask
from threading import Thread

TOKEN = os.getenv("TOKEN")
AFK_CHANNEL_ID = 1502722226112430304

intents = discord.Intents.default()
intents.voice_states = True


client = discord.Client(intents=intents)

# konfiguracja AFK (domyslnie 5 min)
afk_time = 300

last_activity = {}
afk_start_time = {}
afk_log = {}

# ADMIN ROLE NAME
ADMIN_ROLE_NAME = "Admin"

@client.event
async def on_ready():
    print(f"Zalogowano jako {client.user}")
    check_afk.start()

@client.event
async def on_voice_state_update(member, before, after):

    if member.bot:
        return

    # POWROT Z AFK -> auto unmute
    if before.channel and after.channel:
        if member.id in afk_start_time:
            start = afk_start_time.pop(member.id)
            duration = (datetime.now() - start).total_seconds()

            afk_log[member.id] = afk_log.get(member.id, 0) + duration

            try:
                await member.edit(mute=False)
            except:
                pass

    # aktywnosc
    if after.channel:
        last_activity[member.id] = datetime.now()

@tasks.loop(seconds=30)
async def check_afk():

    for guild in client.guilds:
        afk_channel = guild.get_channel(AFK_CHANNEL_ID)
        if not afk_channel:
            continue

        for vc in guild.voice_channels:

            if vc.id == AFK_CHANNEL_ID:
                continue

            for member in vc.members:

                if member.bot:
                    continue

                # WYJATEK ADMINA
                if any(role.name == ADMIN_ROLE_NAME for role in member.roles):
                    continue

                last = last_activity.get(member.id, datetime.now())
                inactive = (datetime.now() - last).total_seconds()

                if inactive >= afk_time:

                    try:
                        await member.move_to(afk_channel)
                        await member.edit(mute=True)

                        afk_start_time[member.id] = datetime.now()

                        print(f"{member} -> AFK")

                    except Exception as e:
                        print(e)

@client.event
async def on_message(message):

    if message.author.bot:
        return

    # PANEL ADMINA + KOMENDY

    if message.content.startswith("!setafk"):

        if not message.author.guild_permissions.administrator:
            return

        try:
            minutes = int(message.content.split()[1])
            global afk_time
            afk_time = minutes * 60

            await message.channel.send(f"AFK ustawione na {minutes} minut")

        except:
            await message.channel.send("Uzycie: !setafk 5")

    # LOGI AFK
    if message.content == "!afklog":

        total = afk_log.get(message.author.id, 0) / 60

        await message.channel.send(
            f"{message.author.mention} lacznie AFK: {total:.1f} minut"
        )

@client.event
async def on_message(message):
    print("MSG:", message.content)

client.run(TOKEN)

app = Flask('')

@app.route('/')
def home():
    return "AFK Bot działa"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

Thread(target=run_web).start()
