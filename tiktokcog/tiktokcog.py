import os
import random
import re
import requests
from PIL import Image, ImageOps, ImageDraw # Import PIL library
from redbot.core import commands

# Import the discord module
import discord

class TikTokCog(commands.Cog):
    """A custom cog that reposts tiktok urls"""

    def __init__(self, bot):
        self.bot = bot
        # Compile the tiktok pattern only once
        self.tiktok_pattern = re.compile(r"(?i)(https?://)?((\w+)\.)?tiktok.com/(.+)")

    @commands.Cog.listener()
    async def on_message(self, message):
        """A listener that triggers when a message is sent"""
        # Check if the message is from a user and contains a tiktok url
        if message.author.bot:
            return
        tiktok_url = self.tiktok_pattern.search(message.content)
        if not tiktok_url:
            return

        # Add vx in front of tiktok.com in the url, while preserving the protocol, subdomain, and path parts
        new_url = tiktok_url.expand(r"\1\2vxtiktok.com/\4")

        # Get the user object from the message
        user = message.author

        # Get the avatar URL from the user object
        avatar_url = user.avatar.url

        # Download the image from the URL and save it as avatar.png
        response = requests.get(avatar_url)
        with open("avatar.png", "wb") as file:
            file.write(response.content)

        # Open the avatar image file
        image = Image.open("avatar.png")

        # Resize the image to 128x128 pixels
        image = image.resize((128, 128))

        # Create a mask image with the same size and RGBA mode
        mask = Image.new("RGBA", image.size)

        # Create a Draw object for the mask image
        draw = ImageDraw.Draw(mask)

        # Draw a black circle on the mask image using the ellipse method
        draw.ellipse([0, 0, *image.size], fill=(0, 0, 0, 255))

        # Apply the mask to the avatar image using the Image.composite method
        image = Image.composite(image, Image.new("RGBA", image.size), mask)

        # Save the cropped image as avatar_cropped.png
        image.save("avatar_cropped.png")

        # Get the guild object from the message
        guild = message.guild

        # Open the cropped image file in binary mode
        with open("avatar_cropped.png", "rb") as image:

            # Create a custom emoji with a random name and the image file
            emoji_name = f"user_avatar_{random.randint(0, 9999)}"
            emoji = await guild.create_custom_emoji(name=emoji_name, image=image.read())

        # Extract the text and mentions from the original message
        text = message.content.replace(tiktok_url.group(0), "").strip()
        mentions = [user.mention for user in message.mentions]

        # Create a formatted message with the custom emoji, the mention and modified url of tiktok video, and any additional text and mentions
        formatted_message = f"{emoji} {user.mention} originally shared this embedded TikTok video.\n{new_url}\n"

        # Append any additional text and mentions to the formatted message if they are not too long
        if len(text) + len(mentions) < 2000:
            formatted_message += f"{text} {' '.join(mentions)}"

        # Define a mention pattern that matches user, role, or channel mentions
        mention_pattern = re.compile(r"<(@[!&]?|#)\d+>")

        # Define a function that escapes a mention by adding a backslash before the @ sign
        def escape_mention(match):
            return match.group(0).replace("@", "\\@")

        # Replace any mention in the formatted message with its escaped version using the re.sub function and the escape_mention function
        formatted_message = re.sub(mention_pattern, escape_mention, formatted_message)

        # Repost the formatted message and remove the original message
        await message.channel.send(formatted_message)
        await message.delete()

        # Delete the custom emoji
        await emoji.delete()

        # Delete the avatar.png and avatar_cropped.png files
        os.remove("avatar.png")
        os.remove("avatar_cropped.png")
