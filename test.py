import os
import json
import discord
from discord.ext import commands, tasks
from discord.ui import View, Button
from dotenv import load_dotenv
import random as r
from datetime import datetime, timedelta
import asyncio
from discord.ext.commands import CommandError, MissingPermissions

load_dotenv()
TOKEN = "token"
CHANNEL_ID = 1252254456209346623
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
bot = commands.Bot(command_prefix="?", intents=intents)

user_scores = {}
last_guess_time = {}
last_guess_result = {}
current_word = ''
current_greens = []
current_yellows = []
word_list = []
recent_words = []
user_games_played = {}  
game_start_time = None 
settings_file = 'settings.json'
AUTHORIZED_USER_ID = 1079143556322697246

# Helper function to load settings from JSON
def load_settings():
    if os.path.exists(settings_file):
        with open(settings_file, 'r') as f:
            return json.load(f)
    else:
        return {}

# Helper function to save settings to JSON
def save_settings(settings):
    with open(settings_file, 'w') as f:
        json.dump(settings, f, indent=4)

# Command to set up the guild-specific settings
@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx, frequency: int, cooldown: int):
    guild_id = str(ctx.guild.id)
    settings = load_settings()

    # Store the settings for the guild
    settings[guild_id] = {
        'frequency': frequency,
        'cooldown': cooldown
    }
    save_settings(settings)

    await ctx.send(f"Setup complete for this server. Frequency set to {frequency} hours and cooldown set to {cooldown} seconds.")

# Decorator to ensure that the guild is set up before any command can be executed
def ensure_setup(func):
    async def wrapper(ctx, *args, **kwargs):
        guild_id = str(ctx.guild.id)
        settings = load_settings()

        if guild_id not in settings:
            await ctx.send("This server is not set up yet. Please run the `?setup` command to configure the bot.")
        else:
            await func(ctx, *args, **kwargs)
    return wrapper

# Apply the decorator to commands that require setup
@bot.command()
@ensure_setup
async def guess(ctx, word: str):
    global current_word, last_guess_time, user_scores, last_guess_result, current_greens, current_yellows
    settings = load_settings()
    guild_id = str(ctx.guild.id)
    cooldown = settings[guild_id]['cooldown']
    frequency = settings[guild_id]['frequency']

    user = ctx.author
    word = word.lower()

    if word not in word_list:
        embed = discord.Embed(
            title="Invalid Word",
            description=f"{user.display_name}, that is not a valid word. Please guess a real 7-letter word.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    if len(word) != 7:
        embed = discord.Embed(
            title="Invalid Length",
            description=f"{user.display_name}, your guess must be exactly 7 letters long.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    now = datetime.now()
    if user.id in last_guess_time and (now - last_guess_time[user.id]).total_seconds() < cooldown:
        remaining_time = timedelta(seconds=cooldown) - (now - last_guess_time[user.id])
        minutes, seconds = divmod(remaining_time.total_seconds(), 60)
        embed = discord.Embed(
            title="Too Soon!",
            description=f"{user.display_name}, you can only guess once every {cooldown // 60} minutes. Try again in {int(minutes)} minutes and {int(seconds)} seconds.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    user_id_str = str(user.id)
    if user_id_str not in user_scores:
        user_scores[user_id_str] = 0

    last_guess_time[user.id] = now

    guess_result = []
    points = 0

    current_word_copy = list(current_word)

    for i in range(7):
        if word[i] == current_word[i]:
            guess_result.append(green_emoji_ids[word[i].upper()])
            if word[i] in current_yellows:
                points += 1
            elif word[i] in current_greens:
                points += 0
            else:
                points += 2
            current_greens.append(word[i])
            current_word_copy[i] = None
        else:
            guess_result.append(None)

    for i in range(7):
        if guess_result[i] is None:
            if word[i] in current_word_copy:
                guess_result[i] = yellow_emoji_ids[word[i].upper()]
                if word[i] not in current_yellows:
                    current_yellows.append(word[i])
                    points += 1
                current_word_copy[current_word_copy.index(word[i])] = None
            else:
                guess_result[i] = grey_emoji_ids[word[i].upper()]

    user_scores[user_id_str] += points
    if user_id_str not in last_guess_result:
        last_guess_result[user_id_str] = []
    last_guess_result[user_id_str].append((word, ''.join(guess_result), points))
    save_scores()

    response = ""
    for user_id, guesses in last_guess_result.items():
        member = ctx.guild.get_member(int(user_id))
        if member:
            user_name = member.display_name
        else:
            user_name = f"User {user_id}"
        
        for guess, result, points in guesses:
            response += f'{result} (+{points} <@{user_id}> )\n'

    # Keyboard layout
    keyboard_layout = [
        "QWERTYUIOP",
        "ASDFGHJKL",
        "ZXCVBNM"
    ]
    
    keyboard_display = ""
    for row in keyboard_layout:
        for letter in row:
            if letter.lower() in current_greens:
                keyboard_display += green_emoji_ids[letter] + " "
            elif letter.lower() in current_yellows:
                keyboard_display += yellow_emoji_ids[letter] + " "
            else:
                keyboard_display += grey_emoji_ids[letter] + " "
        keyboard_display += "\n"

    embed = discord.Embed(
        title="Guess Result",
        description=response.strip(),
        color=discord.Color.green()
    )
    embed.add_field(name="Keyboard", value=keyboard_display, inline=False)
    await ctx.send(embed=embed)
    
    if word == current_word:
        embed = discord.Embed(
            title="Word Solved",
            description=f'{user.display_name} has solved the word! The word was {current_word}.',
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)
        for participant in user_scores:
            user_scores[participant] += 2
        save_scores()

# Apply the decorator to other commands
@bot.command()
@ensure_setup
async def top(ctx):
    global user_scores, user_games_played, game_start_time

    if game_start_time is None:
        # Handle the case where game_start_time is not set
        hours_since_start = 1  # Set to 1 to avoid division by zero
    else:
        hours_since_start = (datetime.now() - game_start_time).total_seconds() / 3600

    settings = load_settings()
    guild_id = str(ctx.guild.id)
    frequency = settings[guild_id]['frequency']
    
    max_games_per_day = 24 / frequency

    average_games_per_day = {
        user_id: games_played / (hours_since_start / 24)
        for user_id, games_played in user_games_played.items()
    }

    average_points_per_game = {
        user_id: user_scores[user_id] / games_played
        for user_id, games_played in user_games_played.items()
    }

    # Create the leaderboard embed
    sorted_scores = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)
    leaderboard = [f'<@{user_id}>: {score} points' for user_id, score in sorted_scores]

    embed_leaderboard = discord.Embed(
        title="Leaderboard",
        description='\n'.join(leaderboard),
        color=discord.Color.purple()
    )

    # Create the average games per day embed
    sorted_avg_games = sorted(average_games_per_day.items(), key=lambda x: x[1], reverse=True)
    avg_games_display = [f'<@{user_id}>: {avg:.2f} games/day' for user_id, avg in sorted_avg_games]

    embed_avg_games = discord.Embed(
        title="Average Games Per Day",
        description='\n'.join(avg_games_display),
        color=discord.Color.blue()
    )

    # Create the average points per game embed
    sorted_avg_points = sorted(average_points_per_game.items(), key=lambda x: x[1], reverse=True)
    avg_points_display = [f'<@{user_id}>: {avg:.2f} points/game' for user_id, avg in sorted_avg_points]

    embed_avg_points = discord.Embed(
        title="Average Points Per Game",
        description='\n'.join(avg_points_display),
        color=discord.Color.green()
    )

    await ctx.send(embed=embed_leaderboard)
    await ctx.send(embed=embed_avg_games)
    await ctx.send(embed=embed_avg_points)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    load_word_list()
    load_scores()
    load_recent_words()
    load_games_played()
    load_leaderboard()
    
    now = datetime.now()
    delay = (60 - now.minute) * 60 - now.second
    await asyncio.sleep(delay)
    
    change_word.start()

@tasks.loop(hours=1)
@ensure_setup
async def change_word():
    global current_word, last_guess_time, user_scores, last_guess_result, current_greens, current_yellows

    for guild in bot.guilds:
        guild_id = str(guild.id)
        settings = load_settings()

        if guild_id not in settings:
            continue

        config = settings[guild_id]
        frequency = config['frequency']
        cooldown = config['cooldown']

        # Skip iterations based on frequency
        if (datetime.now().hour % frequency) != 0:
            continue

        finish_unsolved_game()

        # Generate and post the new word
        current_word = generate_new_word()
        print(current_word)

        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="New Word",
                description="A new word has been chosen! Start guessing the 7-letter word.",
                color=discord.Color.blue()
            )
            await channel.send(embed=embed)
        else:
            print(f"Channel with ID {CHANNEL_ID} not found.")

bot.run(TOKEN)
