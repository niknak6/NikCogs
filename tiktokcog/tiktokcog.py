import os
import random
import re
import requests
from PIL import Image, ImageOps, ImageDraw # Import PIL library
from redbot.core import commands

class TikTokCog(commands.Cog):
    """A custom cog that reposts tiktok urls"""

    def __init__(self, bot):
        self.bot = bot
        # Compile the tiktok pattern only once
        self.tiktok_pattern = re.compile(r"(?i)(.*?)(https?://)?((\w+)\.)?tiktok.com/(.+)(.*)") # Modified line

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
        new_url = tiktok_url.group(1) + tiktok_url.group(2) + tiktok_url.group(3) + "vxtiktok.com/" + tiktok_url.group(5) + tiktok_url.group(6) # Modified line

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

# Extract the memo text from the message content by splitting it by whitespace and removing any part that starts with https:// or http:// (including it)
memo_text = " ".join([part for part in message.content.split() if not part.lower().startswith(("https://", "http://"))])

# Remove any whitespace before https:// or http:// in the message content (this will remove any text before or after the url)
message_content = " ".join([part for part in new_url.split() if part.lower().startswith(("https://", "http://"))])

# Create a formatted message with the custom emoji, the mention, modified url and memo text

# Modified line: Removed whitespace after new_url 
formatted_message = f"Shared by: {emoji} {user.mention}\nMessage: {memo_text}\nLink: {message_content}"

# Repost the formatted message and remove the original message
await message.channel.send(formatted_message)
await message.delete()

# Delete the custom emoji
await emoji.delete()

# Delete the avatar.png and avatar_cropped.png files
os.remove("avatar.png")
os.remove("avatar_cropped.png")
