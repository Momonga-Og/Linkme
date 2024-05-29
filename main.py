import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import os
import subprocess

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())

# yt-dlp options for downloading the video
ydl_opts = {
    'format': 'bestvideo+bestaudio/best',
    'outtmpl': 'downloaded_video.%(ext)s'
}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# Function to handle video downloading and uploading
async def handle_video(interaction: discord.Interaction, url: str, source: str):
    await interaction.followup.send(f"Downloading the video from {source}...")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            title = info.get('title', 'Unknown Title')

        # Check the file size
        file_size = os.path.getsize(file_path)
        if file_size > 8 * 1024 * 1024:  # 8MB in bytes
            await interaction.followup.send("The video is larger than 8MB, compressing the video...")

            # Compress the video using ffmpeg
            compressed_file_path = "compressed_" + os.path.splitext(file_path)[0] + ".mp4"
            ffmpeg_command = [
                'ffmpeg', '-i', file_path, '-vf', 'scale=640:-1', '-c:v', 'libx264', '-preset', 'slow', '-b:v', '500k',
                '-c:a', 'aac', '-b:a', '128k', compressed_file_path
            ]
            subprocess.run(ffmpeg_command, check=True)

            # Remove the original file and replace with the compressed file
            os.remove(file_path)
            file_path = compressed_file_path

        # Send the video file to Discord
        await interaction.followup.send(f"Uploading video: **{title}**")
        await interaction.followup.send(file=discord.File(file_path))

        # Clean up the downloaded and/or compressed file
        os.remove(file_path)

    except Exception as e:
        await interaction.followup.send(f"An error occurred: {str(e)}")

@bot.tree.command(name="tiktok")
@app_commands.describe(url="The TikTok video URL")
async def tiktok(interaction: discord.Interaction, url: str):
    await handle_video(interaction, url, "TikTok")

@bot.tree.command(name="youtube")
async def youtube(interaction: discord.Interaction, url: str):
    try:
        # Defer the interaction response to give more time for processing
        await interaction.response.defer()
        await handle_video(interaction, url, "YouTube")
    except discord.errors.NotFound as e:
        await interaction.followup.send(f"Failed to send message: {e}")
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}")

# Add the command to the bot
bot.tree.add_command(youtube)



# Add your token at the end to run the bot
bot.run(DISCORD_BOT_TOKEN)
