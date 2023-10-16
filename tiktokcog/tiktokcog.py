import os
import random
import urllib.parse # Import urllib.parse module
import requests
from PIL import Image, ImageOps, ImageDraw # Import PIL library
from redbot.core import commands

class TikTokCog(commands.Cog):
    """A custom cog that reposts tiktok urls"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """A listener that triggers when a message is sent"""
        # Check if the message is from a user and contains a tiktok url
        if message.author.bot:
            return
        try: # Added line
            # Parse the message content as a url and store it in a ParseResult object
            parsed_url = urllib.parse.urlparse(message.content) # Added line

            # Check if the netloc part of the url contains tiktok.com
            if "tiktok.com" not in parsed_url.netloc: # Added line
                return

            # Modify the netloc part of the url by adding vx in front of tiktok.com
            new_netloc = parsed_url.netloc.replace("tiktok.com", "vxtiktok.com") # Added line

            # Rebuild the url with the new netloc and store it in a string
            new_url = urllib.parse.urlunparse(parsed_url._replace(netloc=new_netloc)) # Added line
        except ValueError: # Added line
            # If the message content is not a valid url, return
            return # Added line

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

        # Create a formatted message with the custom emoji, the user's mention, and the modified url
        formatted_message = f"{emoji} {user.mention} shared this TikTok!\n{new_url}" # Modified line

        # Repost the formatted message and remove the original message
        await message.channel.send(formatted_message)
        await message.delete()

        # Delete the custom emoji
        await emoji.delete()

        # Delete the avatar.png and avatar_cropped.png files
        os.remove("avatar.png")
        os.remove("avatar_cropped.png")
