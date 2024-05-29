import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import os
import subprocess
from tempfile import TemporaryDirectory

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# yt-dlp options for downloading the video
ydl_opts = {
  'format': 'bestvideo+bestaudio/best',
  'outtmpl': '%(id)s.%(ext)s'
}

@bot.event
async def on_ready():
  await bot.tree.sync()
  print(f'Logged in as {bot.user.name}')

async def handle_video(interaction, url, source):
  await interaction.response.send_message(f"Downloading the video from {source}...")

  try:
    with TemporaryDirectory() as temp_dir:
      ydl_opts['outtmpl'] = os.path.join(temp_dir, '%(id)s.%(ext)s')

      with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)
        title = info.get('title', 'Unknown Title')

        # Check and potentially compress the video
        if os.path.getsize(file_path) > 8 * 1024 * 1024:  # 8MB in bytes
          await interaction.followup.send("The video is larger than 8MB, compressing the video...")

          # Implement video compression logic using ffmpeg (similar to previous code)
          # ...

        # Send the video file to Discord
        await interaction.followup.send(f"Uploading video: **{title}**")
        await interaction.followup.send(file=discord.File(file_path))

  except yt_dlp.exceptions.ExtractorError as e:
    await interaction.followup.send(f"An error occurred downloading the video: {str(e)}")
  except Exception as e:
    await interaction.followup.send(f"An unexpected error occurred: {str(e)}")

@bot.tree.command(name="tiktok")
@app_commands.describe(url="The TikTok video URL")
async def tiktok(interaction: discord.Interaction, url: str):
  await handle_video(interaction, url, "TikTok")

@bot.tree.command(name="youtube")
@app_commands.describe(url="The YouTube video URL")
async def youtube(interaction: discord.Interaction, url: str):
  await handle_video(interaction, url, "YouTube")

# Add your token at the end to run the bot
bot.run(DISCORD_BOT_TOKEN)
