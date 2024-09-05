import discord
from discord.ext import commands
from discord.ui import Button, View

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
bot = commands.Bot(command_prefix="?", intents=intents)

# Define the user ID to ping
USER_ID = 1079194220650319953
AUTHORIZED_USER_ID = 1079143556322697246
# Define a view with buttons for the command
class AttendanceView(View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == 1079143556322697246:
            embed = discord.Embed(
                title="Stream is on!",
                description="🎉 Georgia will be in stream! 🎉",
                color=0x00ff00
            )
            await interaction.response.send_message(embed=embed)
            self.stop()
        else:
            await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == 1079143556322697246:
            embed = discord.Embed(
                title="It might not happen haha!",
                description="😢 Georgia won't be in stream 😢",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
            self.stop()
        else:
            await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)


@bot.command()
async def willgeogeorgiaabeinattendanceotherwiseidoubtithaha(ctx):
    
    user = await bot.fetch_user(AUTHORIZED_USER_ID)
    
    embed = discord.Embed(
        title="Attendance Question",
        description=f"Will {user.mention} be in attendance?",
        color=0x0000ff
    )

    view = AttendanceView(ctx)
    await ctx.send(embed=embed, view=view)

@bot.event
async def on_ready():
    print(f'Bot {bot.user} is ready and online!')

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

@bot.event
async def on_message_delete(message):
    if message.guild:
        async for entry in message.guild.audit_logs(action=discord.AuditLogAction.message_delete, limit=1):
            deleter = entry.user
            delete_time = entry.created_at
            break
    else:
        deleter = None
        delete_time = message.created_at

    embed = discord.Embed(title="Message Deleted", color=discord.Color.red())
    embed.add_field(name="Author", value=message.author.mention, inline=False)
    embed.add_field(name="Channel", value=message.channel.mention, inline=False)
    embed.add_field(name="Message Content", value=message.content or "No content (possibly an embed/attachment)", inline=False)
    embed.set_footer(text=f"Deleted by {deleter} at {delete_time}")

    log_channel = discord.utils.get(message.guild.channels, name="test")  
    if log_channel:
        await log_channel.send(embed=embed)

# Run the bot with your token
bot.run("MTI0OTc4OTM1NTQ2NDIwMDIyMw.GR0pjj.m-WbkIFIeulbR4E8VhlZCKSj4yPwBAKXaR6G2k")
