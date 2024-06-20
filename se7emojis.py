import os
import json
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import random as r
from datetime import datetime, timedelta
import asyncio

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))

intents = discord.Intents.default()
intents.message_content = True  # Enable privileged intent for message content
intents.messages = True
intents.guilds = True
bot = commands.Bot(command_prefix="?", intents=intents)

# A dictionary to keep track of user scores and last guess time
user_scores = {}
last_guess_time = {}
last_guess_result = {}

# Placeholder for the current word
current_word = ''

# Load word list
word_list = []

# Example emoji ID dictionaries
green_emoji_ids = {
    'a': '<:green_a:123456789012345678>',
    'b': '<:green_b:123456789012345678>',
    'c': '<:green_c:123456789012345678>',
    # Add all letters
}
yellow_emoji_ids = {
    'a': '<:yellow_a:123456789012345678>',
    'b': '<:yellow_b:123456789012345678>',
    'c': '<:yellow_c:123456789012345678>',
    # Add all letters
}
grey_emoji_ids = {
    'a': '<:grey_a:123456789012345678>',
    'b': '<:grey_b:123456789012345678>',
    'c': '<:grey_c:123456789012345678>',
    # Add all letters
}

def load_word_list(filename='word_list.txt'):
    global word_list
    try:
        with open(filename, 'r') as file:
            word_list = [line.strip().lower() for line in file if len(line.strip()) == 7]
        if not word_list:
            raise ValueError("The word list is empty or does not contain valid 7-letter words.")
    except FileNotFoundError:
        raise FileNotFoundError(f"The file {filename} was not found.")
    except Exception as e:
        raise e

def generate_new_word():
    return r.choice(word_list).lower()

def load_scores():
    global user_scores
    try:
        if os.path.getsize('scores.json') == 0:
            user_scores = {}
        else:
            with open('scores.json', 'r') as f:
                user_scores = json.load(f)
    except FileNotFoundError:
        user_scores = {}
    except json.JSONDecodeError:
        user_scores = {}

def save_scores():
    with open('scores.json', 'w') as f:
        json.dump(user_scores, f)

def load_leaderboard(filename='leaderboard.txt'):
    global leaderboard
    try:
        with open(filename, 'r') as file:
            leaderboard = [line.strip() for line in file]
    except FileNotFoundError:
        leaderboard = []

def save_leaderboard(filename='leaderboard.txt'):
    global leaderboard
    with open(filename, 'w') as file:
        file.write('\n'.join(leaderboard))

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    load_word_list()  # Load the word list on startup
    load_scores()  # Load the scores on startup
    load_leaderboard()  # Load the leaderboard on startup

    # Calculate the delay until the next top of the hour
    now = datetime.now()
    delay = (60 - now.minute) * 60 - now.second
    await asyncio.sleep(delay)

    change_word.start()

@tasks.loop(hours=1)
async def change_word():
    global current_word
    current_word = generate_new_word()
    print(current_word)
    channel = bot.get_channel(CHANNEL_ID)
    if channel is not None:
        embed = discord.Embed(
            title="New Word",
            description="A new word has been chosen! Start guessing the 7-letter word.",
            color=discord.Color.blue()
        )
        await channel.send(embed=embed)
    else:
        print(f"Channel with ID {CHANNEL_ID} not found.")

@bot.command()
async def guess(ctx, word: str):
    global current_word
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
    if user.id in last_guess_time and (now - last_guess_time[user.id]).total_seconds() < 1:
        embed = discord.Embed(
            title="Too Soon",
            description=f"{user.display_name}, you can only guess once every 5 minutes.",
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

    # Check the previous guess result, if any
    previous_guess = last_guess_result.get(user_id_str, [])

    # Create a copy of the current word to mark used letters
    current_word_copy = list(current_word)

    # First pass to find green tiles
    for i in range(7):
        if word[i] == current_word[i]:
            guess_result.append(green_emoji_ids[word[i]])
            points += 2  # Award 2 points for correct letter in correct place
            current_word_copy[i] = None  # Mark this letter as used
        else:
            guess_result.append(None)

    # Second pass to find yellow tiles
    for i in range(7):
        if guess_result[i] is None:  # Only check letters that are not already green
            if word[i] in current_word_copy:
                guess_result[i] = yellow_emoji_ids[word[i]]
                points += 1  # Award 1 point for correct letter in incorrect place
                current_word_copy[current_word_copy.index(word[i])] = None  # Mark this letter as used
            else:
                guess_result[i] = grey_emoji_ids[word[i]]

    user_scores[user_id_str] += points
    previous_guess.append((word, ''.join(guess_result)))
    last_guess_result[user_id_str] = previous_guess  # Store the current guess result for the user
    save_scores()  # Save scores after updating

    response = f'{user.display_name} guessed {word}: {"".join(guess_result)} and earned {points} points.\n'
    for guess, result in previous_guess[:-1]:  # Exclude the last guess as it's already added above
        response += f'{user.display_name} guessed {guess}: {result}\n'
    
    embed = discord.Embed(
        title="Guess Result",
        description=response.strip(),
        color=discord.Color.green()
    )
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
        save_scores()  # Save scores after awarding points

@bot.command()
async def top(ctx):
    global user_scores
    sorted_scores = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)
    leaderboard = [f'<@{user_id}>: {score} points' for user_id, score in sorted_scores]
    save_leaderboard()  # Save the sorted leaderboard

    embed = discord.Embed(
        title="Leaderboard",
        description='\n'.join(leaderboard),
        color=discord.Color.purple()
    )
    await ctx.send(embed=embed)

@bot.command()
async def test(ctx):
    await change_word()
    embed = discord.Embed(
        title="Test",
        description="A new word cycle has started!",
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed)

# Run the bot
bot.run(TOKEN)  # replace with your bot token
