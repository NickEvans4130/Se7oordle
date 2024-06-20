import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('DISCORD_GUILD_ID'))

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="?", intents=intents)

@bot.event
async def on_ready():
    guild = bot.get_guild(GUILD_ID)
    if guild:
        green_emojis = {}
        yellow_emojis = {}
        grey_emojis = {}

        for emoji in guild.emojis:
            name_parts = emoji.name.split('_')
            if len(name_parts) == 2:
                letter, color = name_parts
                if color == 'green':
                    green_emojis[letter] = f"<:{emoji.name}:{emoji.id}>"
                elif color == 'yellow':
                    yellow_emojis[letter] = f"<:{emoji.name}:{emoji.id}>"
                elif color == 'grey':
                    grey_emojis[letter] = f"<:{emoji.name}:{emoji.id}>"

        print("green_emoji_ids = {")
        for key, value in green_emojis.items():
            print(f"    '{key}': '{value}',")
        print("}")

        print("\nyellow_emoji_ids = {")
        for key, value in yellow_emojis.items():
            print(f"    '{key}': '{value}',")
        print("}")

        print("\ngrey_emoji_ids = {")
        for key, value in grey_emojis.items():
            print(f"    '{key}': '{value}',")
        print("}")

    await bot.close()

# Run the bot
bot.run(TOKEN)
