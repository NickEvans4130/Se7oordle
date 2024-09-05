import os
import json
import discord
from discord.ext import commands, tasks
from discord.ui import View, Button
from dotenv import load_dotenv
import random as r
from datetime import datetime, timedelta
import asyncio
from discord.ext.commands import CommandError, has_permissions

# Load the bot token and other settings from the environment
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="?", intents=intents)

# Declare global variables here (same as before)
user_scores = {}
last_guess_time = {}
last_guess_result = {}
current_word = ''
current_greens = []
current_yellows = []
word_list = []
recent_words = []
frequency = 24
user_games_played = {}  
game_start_time = None 

green_emoji_ids = {
    'A': '<:A_green:1253309996008214618>',
    'B': '<:B_green:1253310007240429620>',
    'C': '<:C_green:1253310018095153152>',
    'D': '<:D_green:1253310027205181482>',
    'E': '<:E_green:1253310038072889374>',
    'F': '<:F_green:1253310055210811503>',
    'G': '<:G_green:1253310070759096381>',
    'H': '<:H_green:1253310084780527616>',
    'I': '<:I_green:1253310091835215933>',
    'J': '<:J_green:1253310102845259806>',
    'K': '<:K_green:1253310109694693488>',
    'L': '<:L_green:1253310117844090993>',
    'M': '<:M_green:1253310123762516008>',
    'O': '<:O_green:1253310143349915678>',
    'P': '<:P_green:1253310149469405205>',
    'Q': '<:Q_green:1253310160152035390>',
    'R': '<:R_green:1253310167391670344>',
    'N': '<:N_green:1253699658186887269>',
    'S': '<:S_green:1253699677405184083>',
    'T': '<:T_green:1253699689782710415>',
    'U': '<:U_green:1253699708497563700>',
    'V': '<:V_green:1253699720862236705>',
    'W': '<:W_green:1253699733797601385>',
    'X': '<:X_green:1253699746632040500>',
    'Y': '<:Y_green:1253699761450778644>',
    'Z': '<:Z_green:1253699773148696658>',
}

yellow_emoji_ids = {
    'A': '<:A_yellow:1253310003436060672>',
    'B': '<:B_yellow:1253310013993386026>',
    'C': '<:C_yellow:1253310024068104193>',
    'D': '<:D_yellow:1253310033815539772>',
    'E': '<:E_yellow:1253310048713834627>',
    'F': '<:F_yellow:1253310064983281725>',
    'G': '<:G_yellow:1253310081924071475>',
    'H': '<:H_yellow:1253310089599914075>',
    'I': '<:I_yellow:1253310098508480614>',
    'J': '<:J_yellow:1253310106603622460>',
    'K': '<:K_yellow:1253310116233478156>',
    'L': '<:L_yellow:1253310121451323403>',
    'M': '<:M_yellow:1253310128795553792>',
    'N': '<:N_yellow:1253310139105284147>',
    'O': '<:O_yellow:1253310147145760778>',
    'P': '<:P_yellow:1253310157094518784>',
    'Q': '<:Q_yellow:1253699663207333939>',
    'R': '<:R_yellow:1253699672225091675>',
    'S': '<:S_yellow:1253699686154371093>',
    'T': '<:T_yellow:1253699706010210456>',
    'U': '<:U_yellow:1253699716798091304>',
    'V': '<:V_yellow:1253699728974151812>',
    'W': '<:W_yellow:1253699741481697351>',
    'X': '<:X_yellow:1253699757239701648>',
    'Y': '<:Y_yellow:1253699768400740374>',
    'Z': '<:Z_yellow:1253699782086492160>',
}

grey_emoji_ids = {
    'A': '<:A_grey:1253309999598272573>',
    'B': '<:B_grey:1253310010960773241>',
    'C': '<:C_grey:1253310021505388567>',
    'D': '<:D_grey:1253310030392987719>',
    'E': '<:E_grey:1253310042510196756>',
    'F': '<:F_grey:1253310059639738389>',
    'G': '<:G_grey:1253310076505296897>',
    'H': '<:H_grey:1253310087489917039>',
    'I': '<:I_grey:1253310094695731251>',
    'J': '<:J_grey:1253310104892080224>',
    'K': '<:K_grey:1253310112584568853>',
    'L': '<:L_grey:1253310119681462303>',
    'M': '<:M_grey:1253310125519671360>',
    'N': '<:N_grey:1253310133618999378>',
    'O': '<:O_grey:1253310145249804319>',
    'P': '<:P_grey:1253310152795357276>',
    'Q': '<:Q_grey:1253310162513432659>',
    'R': '<:R_grey:1253699667598770268>',
    'S': '<:S_grey:1253699682064924772>',
    'T': '<:T_grey:1253699703363862599>',
    'U': '<:U_grey:1253699713023217755>',
    'V': '<:V_grey:1253699724951945226>',
    'W': '<:W_grey:1253699737589387315>',
    'X': '<:X_grey:1253699752466448474>',
    'Y': '<:Y_grey:1253699764831125555>',
    'Z': '<:Z_grey:1253699777405780089>',
}


def load_settings(guild_id):
    try:
        with open('settings.json', 'r') as f:
            settings = json.load(f)
        return settings.get(str(guild_id), {"frequency": 24, "cooldown": 300})  # Default values
    except FileNotFoundError:
        return {"frequency": 24, "cooldown": 300}  # Default values

def save_settings(guild_id, frequency, cooldown):
    try:
        with open('settings.json', 'r') as f:
            settings = json.load(f)
    except FileNotFoundError:
        settings = {}
    
    settings[str(guild_id)] = {"frequency": frequency, "cooldown": cooldown}
    
    with open('settings.json', 'w') as f:
        json.dump(settings, f)

def ensure_setup(func):
    async def wrapper(ctx, *args, **kwargs):
        guild_id = str(ctx.guild.id)
        settings = load_settings(guild_id)

        if guild_id not in settings:
            await ctx.send("This server is not set up yet. Please run the `/setup` command to configure the bot.")
        else:
            await func(ctx, *args, **kwargs)
    return wrapper

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

def load_recent_words():
    global recent_words
    try:
        if os.path.getsize('recent_words.json') == 0:
            recent_words = []
        else:
            with open('recent_words.json', 'r') as f:
                recent_words = json.load(f)
    except FileNotFoundError:
        recent_words = []
    except json.JSONDecodeError:
        recent_words = []

def save_recent_words():
    with open('recent_words.json', 'w') as f:
        json.dump(recent_words, f)


def generate_new_word():
    global recent_words
    
    # Filter the word list to exclude recently used words
    available_words = [word for word in word_list if word not in recent_words]
    
    # If all words have been used in the last 7 days, reset recent_words
    if not available_words:
        recent_words = []
        available_words = word_list[:]

    # Select a new word from the available list
    new_word = r.choice(available_words).lower()

    # Add the new word to recent_words and ensure the list doesn't exceed 7 items
    recent_words.append(new_word)
    if len(recent_words) > 7*frequency:
        recent_words.pop(0)
    
    return new_word

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

def load_games_played():
    global user_games_played
    try:
        if os.path.getsize('games_played.json') == 0:
            user_games_played = {}
        else:
            with open('games_played.json', 'r') as f:
                user_games_played = json.load(f)
    except FileNotFoundError:
        user_games_played = {}
    except json.JSONDecodeError:
        user_games_played = {}

def save_games_played():
    with open('games_played.json', 'w') as f:
        json.dump(user_games_played, f)

def finish_unsolved_game():
    global user_scores, last_guess_result, current_word, current_greens, current_yellows
    
    # Check if the word has been solved
    if not any(result[-1] == 2 for user_id, guesses in last_guess_result.items() for guess, result, points in guesses if guess == current_word):
        # Notify that the word wasn't solved
        channel = bot.get_channel(CHANNEL_ID)
        if channel is not None:
            embed = discord.Embed(
                title="Word Not Solved",
                description=f"The word '{current_word}' was not solved in time. No points will be awarded for this round.",
                color=discord.Color.red()
            )
            asyncio.create_task(channel.send(embed=embed))
        else:
            print(f"Channel with ID {CHANNEL_ID} not found.")

    # Reset the game state for the next word
    last_guess_time.clear()
    user_scores.clear()
    last_guess_result.clear()
    current_greens.clear()
    current_yellows.clear()

    
class WordGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="setup", with_app_command=True, description="Set up the bot for the server")
    @has_permissions(administrator=True)
    async def setup(self, ctx, frequency: int = 24, cooldown: int = 300):
        """Sets up the bot with the specified frequency and cooldown (in seconds)."""
        guild_id = str(ctx.guild.id)
        save_settings(guild_id, frequency, cooldown)
        await ctx.send(f"Bot setup complete! Frequency: {frequency} hours, Cooldown: {cooldown} seconds.")

    @ensure_setup
    @commands.hybrid_command(name="guess", with_app_command=True, description="Make a guess for the current word")
    async def guess(self, ctx, word: str):
        # Logic for guess command remains unchanged
        ...

    @ensure_setup
    @commands.hybrid_command(name="top", with_app_command=True, description="Display the top players")
    async def top(self, ctx):
        # Logic for top command remains unchanged
        ...

    @tasks.loop(hours=1)
    async def change_word(self):
        # Logic for change_word task remains unchanged
        ...

    @commands.Cog.listener()
    async def on_ready(self):
        global frequency

        print(f'Logged in as {self.bot.user.name}')
        load_word_list()
        load_scores()
        load_recent_words()
        load_games_played()
        load_leaderboard()

        for guild in self.bot.guilds:
            settings = load_settings(guild.id)
            if str(guild.id) in settings:
                frequency = settings[str(guild.id)].get('frequency', 24)

        now = datetime.now()
        delay = (60 - now.minute) * 60 - now.second
        await asyncio.sleep(delay)
        
        self.change_word.start()

# Register the cog
bot.add_cog(WordGame(bot))

# Run the bot
bot.run(TOKEN)
