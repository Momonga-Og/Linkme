import discord
from discord.ext import commands
import yt_dlp
import os
import asyncio
import subprocess

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
INSTAGRAM_COOKIES_PATH = 'instagram_cookies.txt'

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

async def run_ffmpeg_command(command):
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, command, output=stdout, stderr=stderr)

async def handle_video(ctx, url, source):
    try:
        await ctx.response.defer()
        await ctx.followup.send(f"Downloading the video from {source}...")

        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': f'downloaded_{source}_video.%(ext)s'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            title = info.get('title', 'Unknown Title')

        file_size = os.path.getsize(file_path)
        if file_size > 8 * 1024 * 1024:  # 8MB in bytes
            await ctx.followup.send(f"The video is larger than 8MB, compressing the video from {source}...")

            compressed_file_path = f"compressed_{source}_" + os.path.splitext(file_path)[0] + ".mp4"
            ffmpeg_command = [
                'ffmpeg', '-i', file_path, '-vf', 'scale=640:-1', '-c:v', 'libx264', 
                '-preset', 'fast', '-b:v', '500k', '-c:a', 'aac', '-b:a', '64k', compressed_file_path
            ]
            try:
                await run_ffmpeg_command(ffmpeg_command)
            except subprocess.CalledProcessError as e:
                await ctx.followup.send(f"An error occurred while compressing the video from {source}: {e.stderr.decode()}")
                return

            os.remove(file_path)
            file_path = compressed_file_path

        await ctx.followup.send(f"Uploading video from {source}: **{title}**")
        await ctx.followup.send(file=discord.File(file_path))

        os.remove(file_path)
    except Exception as e:
        await ctx.followup.send(f"An error occurred: {str(e)}")

@bot.command(name="instagram")
async def instagram(ctx: discord.Interaction, url: str):
    await handle_video(ctx, url, "Instagram")

@bot.command(name="youtube")
async def youtube(ctx: discord.Interaction, url: str):
    await handle_video(ctx, url, "YouTube")

@bot.command(name="tiktok")
async def tiktok(ctx: discord.Interaction, url: str):
    await handle_video(ctx, url, "TikTok")

bot.run(DISCORD_BOT_TOKEN)
