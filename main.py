import discord
from discord.ext import commands
import yt_dlp
import os
import subprocess

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
    print(f'Logged in as {bot.user.name}')

@bot.command(name='tiktok')
async def tiktok(ctx, url):
    await ctx.send("Downloading the video from TikTok...")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            title = info.get('title', 'Unknown Title')

        # Check the file size
        file_size = os.path.getsize(file_path)
        if file_size > 8 * 1024 * 1024:  # 8MB in bytes
            await ctx.send("The video is larger than 8MB, compressing the video...")

            # Compress the video using ffmpeg
            compressed_file_path = "compressed_" + file_path
            ffmpeg_command = [
                'ffmpeg', '-i', file_path, '-vf', 'scale=640:-1', '-c:v', 'libx264', '-preset', 'slow', '-b:v', '500k',
                '-c:a', 'aac', '-b:a', '128k', compressed_file_path
            ]
            subprocess.run(ffmpeg_command, check=True)

            # Remove the original file and replace with the compressed file
            os.remove(file_path)
            file_path = compressed_file_path

        # Send the video file to Discord
        await ctx.send(f"Uploading video: **{title}**")
        await ctx.send(file=discord.File(file_path))

        # Clean up the downloaded and/or compressed file
        os.remove(file_path)

    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

bot.run('YOUR_BOT_TOKEN')
