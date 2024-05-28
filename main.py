import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import os
import asyncio
import subprocess

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# yt-dlp options for downloading the video
ydl_opts = {
    'format': 'bestvideo+bestaudio/best',
    'outtmpl': 'downloaded_video.%(ext)s'
}

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Logged in as {bot.user.name}')

# Function to run ffmpeg asynchronously
async def run_ffmpeg_command(command):
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, command, output=stdout, stderr=stderr)

# Function to handle video downloading and uploading
async def handle_video(ctx, url, source):
    # Defer the response to prevent interaction expiration
    await ctx.response.defer()

    try:
        await ctx.followup.send(f"Downloading the video from {source}...")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            title = info.get('title', 'Unknown Title')

        # Check the file size
        file_size = os.path.getsize(file_path)
        if file_size > 8 * 1024 * 1024:  # 8MB in bytes
            await ctx.followup.send("The video is larger than 8MB, compressing the video...")

            # Compress the video using ffmpeg with a faster preset
            compressed_file_path = "compressed_" + os.path.splitext(file_path)[0] + ".mp4"
            ffmpeg_command = [
                'ffmpeg', '-i', file_path, '-vf', 'scale=640:-1', '-c:v', 'libx264', '-preset', 'fast', '-b:v', '500k',
                '-c:a', 'aac', '-b:a', '128k', compressed_file_path
            ]
            await run_ffmpeg_command(ffmpeg_command)

            # Remove the original file and replace with the compressed file
            os.remove(file_path)
            file_path = compressed_file_path

        # Send the video file to Discord
        await ctx.followup.send(f"Uploading video: **{title}**")
        await ctx.followup.send(file=discord.File(file_path))

        # Clean up the downloaded and/or compressed file
        os.remove(file_path)

    except Exception as e:
        await ctx.followup.send(f"An error occurred: {str(e)}")

@bot.tree.command(name="tiktok")
@app_commands.describe(url="The TikTok video URL")
async def tiktok(ctx: discord.Interaction, url: str):
    await handle_video(ctx, url, "TikTok")

@bot.tree.command(name="youtube")
@app_commands.describe(url="The YouTube video URL")
async def youtube(ctx: discord.Interaction, url: str):
    await handle_video(ctx, url, "YouTube")

# Add your token at the end to run the bot
bot.run(DISCORD_BOT_TOKEN)
