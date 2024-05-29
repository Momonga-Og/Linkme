import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import os
import asyncio
import subprocess

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
INSTAGRAM_COOKIES_PATH = 'instagram_cookies.txt'

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Define yt-dlp options and other settings for each source
source_settings = {
    "youtube": {
        "ydl_opts": {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': 'downloaded_video.%(ext)s'
        },
        "compression_settings": {
            "scale": "640:-1",
            "preset": "fast",
            "bitrate": "500k",
            "audio_bitrate": "128k"
        }
    },
    "tiktok": {
        "ydl_opts": {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': 'downloaded_video.%(ext)s'
        },
        "compression_settings": {
            "scale": "480:-1",
            "preset": "fast",
            "bitrate": "400k",
            "audio_bitrate": "96k"
        }
    },
    "instagram": {  # Replaced Facebook with Instagram
        "ydl_opts": {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': 'downloaded_video.%(ext)s'
        },
        "compression_settings": {
            "scale": "720:-1",
            "preset": "fast",
            "bitrate": "600k",
            "audio_bitrate": "128k"
        }
    }
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
        
        #handle instagram

async def handle_instagram(ctx, url):
    try:
        await ctx.response.defer()
        await ctx.followup.send("Downloading the video from Instagram...")

        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': 'downloaded_instagram_video.%(ext)s',
            'cookies': INSTAGRAM_COOKIES_PATH,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            title = info.get('title', 'Unknown Title')

        await ctx.followup.send(f"Uploading video: **{title}**")
        await ctx.followup.send(file=discord.File(file_path))

        os.remove(file_path)
    except Exception as e:
        await ctx.followup.send(f"An error occurred: {str(e)}")


#download instgram 
def download_instagram_video(url):
    try:
        result = subprocess.run(
            [
                'yt-dlp',
                '--cookies', 'instagram_cookies.txt',  # Use the cookies file
                url
            ],
            check=True,
            text=True,
            capture_output=True
        )
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")

if __name__ == "__main__":
    urls = [
        "https://www.instagram.com/reel/C5hAGZEov5X/?utm_source=ig_web_copy_link",
        "https://www.instagram.com/reel/C7bXWfVy7Ie/?utm_source=ig_web_copy_link"
    ]

    for url in urls:
        download_instagram_video(url)
        


# Function to handle video downloading and uploading
async def handle_video(ctx, url, source):
    settings = source_settings[source]
    ydl_opts = settings["ydl_opts"]
    compression_settings = settings["compression_settings"]

    try:
        await ctx.response.defer()

        await ctx.followup.send(f"Downloading the video from {source}...")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            title = info.get('title', 'Unknown Title')

        # Check the file size
        file_size = os.path.getsize(file_path)
        if file_size > 8 * 1024 * 1024:  # 8MB in bytes
            await ctx.followup.send("The video is larger than 8MB, compressing the video...")

            # Compress the video using ffmpeg with the source-specific settings
            compressed_file_path = "compressed_" + os.path.splitext(file_path)[0] + ".mp4"
            ffmpeg_command = [
                'ffmpeg', '-i', file_path, '-vf', f'scale={compression_settings["scale"]}', '-c:v', 'libx264', 
                '-preset', compression_settings["preset"], '-b:v', compression_settings["bitrate"],
                '-c:a', 'aac', '-b:a', compression_settings["audio_bitrate"], compressed_file_path
            ]
            try:
                await run_ffmpeg_command(ffmpeg_command)
            except subprocess.CalledProcessError as e:
                await ctx.followup.send(f"An error occurred while compressing the video: {e.stderr.decode()}")
                return

            # Remove the original file and replace with the compressed file
            os.remove(file_path)
            file_path = compressed_file_path

        # Send the video file to Discord
        await ctx.followup.send(f"Uploading video: **{title}**")
        await ctx.followup.send(file=discord.File(file_path))

        # Clean up the downloaded and/or compressed file
        os.remove(file_path)

    except discord.errors.NotFound:
        await ctx.followup.send(f"An error occurred: Unknown interaction")
    except Exception as e:
        await ctx.followup.send(f"An error occurred: {str(e)}")

@bot.tree.command(name="tiktok")
@app_commands.describe(url="The TikTok video URL")
async def tiktok(ctx: discord.Interaction, url: str):
    await handle_video(ctx, url, "tiktok")

@bot.tree.command(name="youtube")
@app_commands.describe(url="The YouTube video URL")
async def youtube(ctx: discord.Interaction, url: str):
    await handle_video(ctx, url, "youtube")

@bot.tree.command(name="instagram")
@app_commands.describe(url="The Instagram reel URL")
async def instagram(ctx: discord.Interaction, url: str):
    await handle_video(ctx, url, "instagram")

# Add your token at the end to run the bot
bot.run(DISCORD_BOT_TOKEN)
