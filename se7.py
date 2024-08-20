import os
import json
import discord
from discord.ext import commands, tasks
from discord.ui import View, Button
from dotenv import load_dotenv
import random as r
from datetime import datetime, timedelta
import asyncio
from discord.ext.commands import CommandError

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
frequency = 24
user_games_played = {}  
game_start_time = None 
USER_ID = 1079194220650319953
AUTHORIZED_USER_ID = 1079143556322697246




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

# Call these functions in the appropriate places (on bot startup and game reset):
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
async def change_word():
    global current_word, last_guess_time, user_scores, last_guess_result, current_greens, current_yellows

    # Finish the unsolved game before posting the new word
    finish_unsolved_game()

    # Generate and post the new word
    current_word = generate_new_word()
    print(current_word)

    # Notify the channel
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
    global current_word, last_guess_time, user_scores, last_guess_result, current_greens, current_yellows
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
        remaining_time = timedelta(seconds=300) - (now - last_guess_time[user.id])
        minutes, seconds = divmod(remaining_time.total_seconds(), 60)
        embed = discord.Embed(
            title="Too Soon!",
            description=f"{user.display_name}, you can only guess once every 5 minutes. Try again in {int(minutes)} minutes and {int(seconds)} seconds.",
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

@bot.command()
async def top(ctx):
    global user_scores, user_games_played, game_start_time

    if game_start_time is None:
        # Handle the case where game_start_time is not set
        hours_since_start = 1  # Set to 1 to avoid division by zero
    else:
        hours_since_start = (datetime.now() - game_start_time).total_seconds() / 3600

    frequency = 1  # Frequency in hours
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

    # Define the view for pagination
    class TopView(View):
        def __init__(self):
            super().__init__(timeout=60)
            self.current_page = 0
            self.embeds = [embed_leaderboard, embed_avg_games, embed_avg_points]

        async def update_embed(self, interaction):
            embed = self.embeds[self.current_page]
            await interaction.response.edit_message(embed=embed, view=self)

        @discord.ui.button(label="Leaderboard", style=discord.ButtonStyle.blurple)
        async def leaderboard_button(self, interaction: discord.Interaction, button: Button):
            self.current_page = 0
            await self.update_embed(interaction)

        @discord.ui.button(label="Avg Games/Day", style=discord.ButtonStyle.green)
        async def avg_games_button(self, interaction: discord.Interaction, button: Button):
            self.current_page = 1
            await self.update_embed(interaction)

        @discord.ui.button(label="Avg Points/Game", style=discord.ButtonStyle.green)
        async def avg_points_button(self, interaction: discord.Interaction, button: Button):
            self.current_page = 2
            await self.update_embed(interaction)

    view = TopView()
    await ctx.send(embed=embed_leaderboard, view=view)

@bot.command()
async def test(ctx):
    if ctx.author.id != 980497294745030716:
        raise CommandError("You do not have permission to run this command.")
    
    await change_word()
    embed = discord.Embed(
        title="Test",
        description="A new word cycle has started!",
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed)

@bot.command()
async def stream(ctx):

    user = await bot.fetch_user(USER_ID)

    embed = discord.Embed(
        title="Stream Notification",
        description=f"{user.mention} Time to stream!",
        color=0x00ff00
    )

    # Send the embed in the channel
    await ctx.send(embed=embed)

bot.run(TOKEN)

