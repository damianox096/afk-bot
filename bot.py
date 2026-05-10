import discord
from discord.ext import tasks
from datetime import datetime
from flask import Flask
from threading import Thread
import os

TOKEN = os.getenv("TOKEN")
AFK_CHANNEL_ID = "1502722226112430304"

# Flask hack dla Render
app = Flask('')

@app.route('/')
def home():
    return "AFK Bot działa"
    
def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

Thread(target=run_web).start()

# Discord
intents = discord.Intents.default()
intents.voice_states = True
intents.members = True

client = discord.Client(intents=intents)

last_activity = {}

@client.event
async def on_ready():
    print(f"Zalogowano jako {client.user}")
    check_afk.start()

@client.event
async def on_voice_state_update(member, before, after):

    if member.bot:
        return

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

                last = last_activity.get(member.id, datetime.now())
                inactive = (datetime.now() - last).total_seconds()

                # 5 minut
                if inactive >= 30:

                    try:
                        await member.move_to(afk_channel)
                        await member.edit(mute=True)

                        print(f"{member} -> AFK")

                    except Exception as e:
                        print(e)

@client.event
async def on_ready():
    print("VOICE CHANNELS:")

    for guild in client.guilds:
        for vc in guild.voice_channels:
            print(vc.name)

client.run(TOKEN)


