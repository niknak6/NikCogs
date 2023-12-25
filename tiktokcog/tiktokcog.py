import os
import random
import re
import requests
from PIL import Image, ImageDraw
from redbot.core import commands

class TikTokCog(commands.Cog):
    """A custom cog that reposts tiktok urls"""

    def __init__(self, bot):
        self.bot = bot
        self.tiktok_pattern = re.compile(r"(?i)(.*?)(https?://)?((\w+)\.)?tiktok.com/(.+)(.*)")

    @commands.Cog.listener()
    async def on_message(self, message):
        """A listener that triggers when a message is sent"""
        if not message.author.bot and (tiktok_url := self.tiktok_pattern.search(message.content)):
            new_url, memo_text = self.process_message_content(message.content, tiktok_url)
            avatar_path = self.download_and_process_avatar(message.author.avatar.url)
            await self.repost_message(message, new_url, memo_text, avatar_path)

    def process_message_content(self, content, tiktok_url):
        new_url = self.construct_new_url(tiktok_url)
        memo_text = self.extract_memo_text(content)
        return new_url, memo_text

    def construct_new_url(self, tiktok_url):
        return tiktok_url.group(1) + tiktok_url.group(2) + tiktok_url.group(3) + "vxtiktok.com/" + tiktok_url.group(5) + tiktok_url.group(6)

    def extract_memo_text(self, content):
        return " ".join([part for part in content.split() if not part.lower().startswith(("https://", "http://"))])

    def download_and_process_avatar(self, avatar_url):
        avatar_path = "avatar.png"
        self.download_image(avatar_url, avatar_path)
        self.process_avatar(avatar_path)
        return avatar_path

    def download_image(self, url, path):
        response = requests.get(url)
        with open(path, "wb") as file:
            file.write(response.content)

    def process_avatar(self, path):
        image = Image.open(path).resize((128, 128))
        mask = Image.new("RGBA", image.size)
        ImageDraw.Draw(mask).ellipse([0, 0, *image.size], fill=(0, 0, 0, 255))
        Image.composite(image, Image.new("RGBA", image.size), mask).save(path)

    async def repost_message(self, message, new_url, memo_text, avatar_path):
        emoji = await self.create_custom_emoji(message.guild, avatar_path)
        formatted_message = self.format_message(message.author, emoji, new_url, memo_text)
        await message.channel.send(formatted_message)
        await message.delete()
        await emoji.delete()
        os.remove(avatar_path)

    async def create_custom_emoji(self, guild, avatar_path):
        emoji_name = f"user_avatar_{random.randint(0, 9999)}"
        with open(avatar_path, "rb") as image:
            return await guild.create_custom_emoji(name=emoji_name, image=image.read())

    def format_message(self, author, emoji, new_url, memo_text):
        return f"Shared by: {emoji} {author.mention}\n" + (f"Message: {memo_text}\n" if memo_text else "") + f"Link: {new_url}"