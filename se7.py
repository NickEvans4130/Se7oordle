import os
import json
import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
from dotenv import load_dotenv
import random as r
from datetime import datetime, timedelta
import asyncio

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
GAME_FREQUENCY_HOURS = 1  # Set the frequency of the game in hours

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
bot = commands.Bot(command_prefix="?", intents=intents)

user_scores = {}
last_guess_time = {}
last_guess_result = {}
games_played = 0
game_timestamps = []
current_word = ''
word_list = []
used_words = {}

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
    global word_list, used_words
    now = datetime.now()
    one_week_ago = now - timedelta(days=7)

    available_words = [word for word in word_list if word not in used_words or used_words[word] < one_week_ago]

    if not available_words:
        used_words = {}
        available_words = word_list

    new_word = r.choice(available_words).lower()
    used_words[new_word] = now
    save_used_words()

    return new_word

def load_used_words(filename='used_words.json'):
    global used_words
    try:
        with open(filename, 'r') as f:
            used_words = json.load(f)
            used_words = {word: datetime.fromisoformat(timestamp) for word, timestamp in used_words.items()}
    except (FileNotFoundError, json.JSONDecodeError):
        used_words = {}

def save_used_words(filename='used_words.json'):
    global used_words
    used_words = {word: timestamp.isoformat() for word, timestamp in used_words.items()}
    with open(filename, 'w') as f:
        json.dump(used_words, f)

def load_scores():
    global user_scores, games_played, game_timestamps
    try:
        with open('scores.json', 'r') as f:
            data = json.load(f)
            user_scores = data.get('user_scores', {})
            games_played = data.get('games_played', 0)
            game_timestamps = [datetime.fromisoformat(ts) for ts in data.get('game_timestamps', [])]
    except (FileNotFoundError, json.JSONDecodeError):
        user_scores = {}
        games_played = 0
        game_timestamps = []

def save_scores():
    data = {
        'user_scores': user_scores,
        'games_played': games_played,
        'game_timestamps': [ts.isoformat() for ts in game_timestamps]
    }
    with open('scores.json', 'w') as f:
        json.dump(data, f)

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

def calculate_average_games_per_day():
    now = datetime.now()
    if game_timestamps:
        earliest_game = min(game_timestamps)
        days_elapsed = (now - earliest_game).days + 1
        avg_games_per_day = games_played / days_elapsed
    else:
        avg_games_per_day = 0
    max_games_per_day = 24 / GAME_FREQUENCY_HOURS
    return avg_games_per_day, max_games_per_day

def calculate_average_points_per_game():
    if games_played == 0:
        return 0
    total_points = sum(user_scores.values())
    avg_points_per_game = total_points / games_played
    return avg_points_per_game

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    load_word_list()
    load_scores()
    load_leaderboard()
    load_used_words()

    now = datetime.now()
    delay = (60 - now.minute) * 60 - now.second
    await asyncio.sleep(delay)

    change_word.start()

@tasks.loop(hours=GAME_FREQUENCY_HOURS)
async def change_word():
    global current_word, games_played, game_timestamps
    current_word = generate_new_word()
    games_played += 1
    game_timestamps.append(datetime.now())
    save_scores()

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
    if user.id in last_guess_time and (now - last_guess_time[user.id]).total_seconds() < 300:
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

    previous_guess = last_guess_result.get(user_id_str, [])

    current_word_copy = list(current_word)

    for i in range(7):
        if word[i] == current_word[i]:
            guess_result.append('🟩')
            points += 2
            current_word_copy[i] = None
        else:
            guess_result.append(None)

    for i in range(7):
        if guess_result[i] is None:
            if word[i] in current_word_copy:
                guess_result[i] = '🟨'
                points += 1
                current_word_copy[current_word_copy.index(word[i])] = None
            else:
                guess_result[i] = '⬜'

    user_scores[user_id_str] += points
    previous_guess.append((word, ''.join(guess_result)))
    last_guess_result[user_id_str] = previous_guess
    save_scores()

    response = f'{user.display_name} guessed {word}: {"".join(guess_result)} and earned {points} points.\n'
    for guess, result in previous_guess[:-1]:
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
        save_scores()

class LeaderboardView(View):
    def __init__(self, ctx, embeds):
        super().__init__()
        self.ctx = ctx
        self.embeds = embeds
        self.current_page = 0

        self.previous_button = Button(label="Previous", style=discord.ButtonStyle.primary)
        self.previous_button.callback = self.previous_page
        self.next_button = Button(label="Next", style=discord.ButtonStyle.primary)
        self.next_button.callback = self.next_page

        self.add_item(self.previous_button)
        self.add_item(self.next_button)

    async def previous_page(self, interaction):
        if self.current_page > 0:
            self.current_page -= 1
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    async def next_page(self, interaction):
        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

@bot.command()
async def top(ctx):
    global user_scores

    sorted_scores = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)
    leaderboard = [f'<@{user_id}>: {score} points' for user_id, score in sorted_scores]

    avg_games_per_day, max_games_per_day = calculate_average_games_per_day()
    avg_points_per_game = calculate_average_points_per_game()

    leaderboard_embed = discord.Embed(
        title="Leaderboard",
        description='\n'.join(leaderboard),
        color=discord.Color.purple()
    )

    avg_games_embed = discord.Embed(
        title="Average Games Per Day",
        description=f"Average Games Played per Day: {avg_games_per_day:.2f} out of {max_games_per_day:.2f}",
        color=discord.Color.blue()
    )

    avg_points_embed = discord.Embed(
        title="Average Points Per Game",
        description=f"Average Points Scored per Game: {avg_points_per_game:.2f}",
        color=discord.Color.green()
    )

    embeds = [leaderboard_embed, avg_games_embed, avg_points_embed]
    view = LeaderboardView(ctx, embeds)

    await ctx.send(embed=embeds[0], view=view)

@bot.command()
async def test(ctx):
    await change_word()
    embed = discord.Embed(
        title="Test",
        description="A new word cycle has started!",
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed)

bot.run(TOKEN)
