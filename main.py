import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import instaloader
import os
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

# Function to handle video downloading and uploading
async def handle_video(interaction, url, source):
    await interaction.response.send_message(f"Downloading the video from {source}...")

    try:
        if source == "Instagram":
            L = instaloader.Instaloader()
            post = instaloader.Post.from_shortcode(L.context, url.split('/')[-2])

            video_url = None
            for file in L.download_post(post, target='downloads'):
                if file.endswith('.mp4'):
                    video_url = file
                    break

            if not video_url:
                await interaction.followup.send("No video found in the provided URL.")
                return

            file_path = video_url
            title = post.title if post.title else "Unknown Title"
        else:
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
@app_commands.describe(url="The YouTube video URL")
async def youtube(interaction: discord.Interaction, url: str):
    await handle_video(interaction, url, "YouTube")

@bot.tree.command(name="instagram")
@app_commands.describe(url="The Instagram video URL")
async def instagram(interaction: discord.Interaction, url: str):
    await handle_video(interaction, url, "Instagram")

# Add your token at the end to run the bot
bot.run(DISCORD_BOT_TOKEN)
