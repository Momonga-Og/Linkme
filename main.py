import discord
from discord.ext import commands
from discord import app_commands
import requests
import os

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Logged in as {bot.user.name}')

def get_instagram_media_url(media_id):
    url = f'https://graph.instagram.com/{media_id}?fields=id,media_type,media_url,thumbnail_url,timestamp,username&access_token={INSTAGRAM_ACCESS_TOKEN}'
    response = requests.get(url)
    response.raise_for_status()
    media_data = response.json()
    return media_data.get('media_url')

async def handle_video(interaction, url, source):
    await interaction.response.defer()  # Defer the interaction to acknowledge it immediately
    try:
        if source == "Instagram":
            media_id = url.split('/')[-2]
            video_url = get_instagram_media_url(media_id)
            if not video_url:
                await interaction.followup.send("No video found in the provided URL.")
                return

            video_response = requests.get(video_url)
            video_filename = 'downloaded_video.mp4'
            with open(video_filename, 'wb') as video_file:
                video_file.write(video_response.content)

            await interaction.followup.send("Video downloaded successfully. Processing...")

            file_path = video_filename
            title = "Instagram Video"

            file_size = os.path.getsize(file_path)
            if file_size > 8 * 1024 * 1024:  # 8MB in bytes
                await interaction.followup.send("The video is larger than 8MB, compressing the video...")

                compressed_file_path = "compressed_" + file_path
                ffmpeg_command = [
                    'ffmpeg', '-i', file_path, '-vf', 'scale=640:-1', '-c:v', 'libx264', '-preset', 'slow', '-b:v', '500k',
                    '-c:a', 'aac', '-b:a', '128k', compressed_file_path
                ]
                subprocess.run(ffmpeg_command, check=True)

                os.remove(file_path)
                file_path = compressed_file_path

            await interaction.followup.send(f"Uploading video: **{title}**")
            await interaction.followup.send(file=discord.File(file_path))

            os.remove(file_path)

        else:
            await interaction.followup.send(f"Unsupported source: {source}")

    except Exception as e:
        await interaction.followup.send(f"An error occurred: {str(e)}")

@bot.tree.command(name="instagram")
@app_commands.describe(url="The Instagram video URL")
async def instagram(interaction: discord.Interaction, url: str):
    await handle_video(interaction, url, "Instagram")

bot.run(DISCORD_BOT_TOKEN)
