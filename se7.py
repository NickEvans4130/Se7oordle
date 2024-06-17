import os
import json
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import random as r
from datetime import datetime

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))

intents = discord.Intents.default()
intents.message_content = True  # Enable privileged intent for message content
intents.messages = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

# A dictionary to keep track of user scores and last guess time
user_scores = {}
last_guess_time = {}
last_guess_result = {}

# Placeholder for the current word
current_word = ''

# Load word list
word_list = []

def load_word_list(filename='word_list.txt'):
    global word_list
    try:
        with open(filename, 'r') as file:
            word_list = [line.strip() for line in file if len(line.strip()) == 7]
        if not word_list:
            raise ValueError("The word list is empty or does not contain valid 7-letter words.")
    except FileNotFoundError:
        raise FileNotFoundError(f"The file {filename} was not found.")
    except Exception as e:
        raise e

def generate_new_word():
    return r.choice(word_list)

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
    change_word.start()

@tasks.loop(hours=1)
async def change_word():
    global current_word
    current_word = generate_new_word()
    print(current_word)
    channel = bot.get_channel(CHANNEL_ID)
    await channel.send(f'A new word has been chosen! Start guessing the 7-letter word.')

@bot.command()
async def guess(ctx, word: str):
    global current_word
    user = ctx.author

    if word not in word_list:
        await ctx.send(f'{user.mention}, that is not a valid word. Please guess a real 7-letter word.')
        return

    if len(word) != 7:
        await ctx.send(f'{user.mention}, your guess must be exactly 7 letters long.')
        return

    now = datetime.now()
    if user.id in last_guess_time and (now - last_guess_time[user.id]).total_seconds() < 1:
        await ctx.send(f'{user.mention}, you can only guess once every 5 minutes.')
        return

    user_id_str = str(user.id)
    if user_id_str not in user_scores:
        user_scores[user_id_str] = 0

    last_guess_time[user.id] = now

    guess_result = []
    yellow_to_green = 0
    points = 0

    for i in range(7):
        if word[i] == current_word[i]:
            if last_guess_result.get(user_id_str, [''] * 7)[i] != '🟩':
                guess_result.append('🟩')
                points += 2
            else:
                guess_result.append('🟩')
        elif word[i] in current_word:
            if last_guess_result.get(user_id_str, [''] * 7)[i] != '🟩':
                guess_result.append('🟨')
                points += 1
            else:
                guess_result.append('🟨')
        else:
            guess_result.append('⬜')

    previous_guess = last_guess_result.get(user_id_str, [''] * 7)
    for i in range(7):
        if previous_guess[i] == '🟨' and guess_result[i] == '🟩':
            yellow_to_green += 1

    points += yellow_to_green
    user_scores[user_id_str] += points
    last_guess_result[user_id_str] = guess_result  # Store the current guess result for the user
    save_scores()  # Save scores after updating

    await ctx.send(f'{user.mention} guessed {word}: {"".join(guess_result)} and earned {points} points.')

    if word == current_word:
        await ctx.send(f'{user.mention} has solved the word! The word was {current_word}.')
        for participant in user_scores:
            user_scores[participant] += 2
        save_scores()  # Save scores after awarding points

@bot.command()
async def top(ctx):
    global user_scores
    sorted_scores = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)
    leaderboard = [f'<@{user_id}>: {score} points' for user_id, score in sorted_scores]
    save_leaderboard()  # Save the sorted leaderboard
    await ctx.send(f'Leaderboard:\n' + '\n'.join(leaderboard))

@bot.command()
async def test(ctx):
    await change_word()
    await ctx.send('A new word cycle has started!')

# Run the bot
bot.run(TOKEN)  # replace with your bot token
