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
    "facebook": {
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

async def run_ffmpeg_command(command):
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, command, output=stdout, stderr=stderr)
    return stdout, stderr

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

        file_size = os.path.getsize(file_path)
        if file_size > 8 * 1024 * 1024:  # 8MB in bytes
            await ctx.followup.send("The video is larger than 8MB, compressing the video...")

            compressed_file_path = "compressed_" + os.path.splitext(file_path)[0] + ".mp4"
            ffmpeg_command = [
                'ffmpeg', '-i', file_path, '-vf', f'scale={compression_settings["scale"]}', '-c:v', 'libx264',
                '-preset', compression_settings["preset"], '-b:v', compression_settings["bitrate"],
                '-c:a', 'aac', '-b:a', compression_settings["audio_bitrate"], compressed_file_path
            ]
            try:
                stdout, stderr = await run_ffmpeg_command(ffmpeg_command)
                print("FFmpeg stdout:", stdout.decode())
                print("FFmpeg stderr:", stderr.decode())
            except subprocess.CalledProcessError as e:
                await ctx.followup.send(f"An error occurred while compressing the video: {e.stderr.decode()}")
                return

            os.remove(file_path)
            file_path = compressed_file_path

        await ctx.followup.send(f"Uploading video: **{title}**")
        await ctx.followup.send(file=discord.File(file_path))

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

@bot.tree.command(name="facebook")
@app_commands.describe(url="The Facebook video URL")
async def facebook(ctx: discord.Interaction, url: str):
    await handle_video(ctx, url, "facebook")

bot.run(DISCORD_BOT_TOKEN)
