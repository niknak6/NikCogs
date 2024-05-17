import discord
from redbot.core import commands, checks, errors
from redbot.core.utils.chat_formatting import pagify
from discord.ext.commands.converter import EmojiConverter
from PIL import Image, ImageSequence
import io
import asyncio
import imghdr
import subprocess
import os
import aiohttp  # Import aiohttp for handling HTTP requests

class RequestEmoji(commands.Cog):
    """A cog that allows users to request custom emojis."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="requestemoji", aliases=["reqemoji"], help="Request a custom emoji to be added to the server.", usage="<name> [attachment or URL]")
    @commands.guild_only()
    async def request_emoji(self, ctx, name: str):
        if not (2 <= len(name) <= 32 and name.isalnum() or "_"):
            raise commands.BadArgument("The name must be between 2 and 32 characters long and consist of alphanumeric characters and underscores only.")
        
        attachment = ctx.message.attachments[0] if ctx.message.attachments else None
        image_data = None

        if attachment:
            try:
                image_data = await attachment.read()
            except Exception as e:
                await ctx.send("There was an error while reading the image. Please try again with a valid PNG or JPG file.")
                return
        else:
            # Check for a URL in the message content if no attachment is found
            words = ctx.message.content.split()
            image_url = next((word for word in words if word.startswith("http")), None)
            if image_url:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(image_url) as resp:
                            if resp.status == 200:
                                image_data = await resp.read()
                            else:
                                await ctx.send("Failed to fetch image from URL.")
                                return
                except Exception as e:
                    await ctx.send("There was an error while fetching the image from the URL.")
                    return

        if not image_data:
            await ctx.send("No valid image found. Please attach an image or provide a valid image URL.")
            return

        if len(image_data) > 256000:
            try:
                image_data = resize_image_file(image_data, (128, 128))
            except ValueError as e:
                await ctx.send(f"There was an error while resizing the image file: {e}")
                return

        embed = discord.Embed(title=f"Emoji request: {name}", description=f"{ctx.author.mention} has requested a custom emoji with this name and image. An Officer or Guild Master can approve or deny this request by reacting with a checkmark or x emoji.", color=discord.Color.red())
        embed.set_image(url="attachment://emoji.gif")
        embed.set_footer(text="This request will expire in 30 minutes.")
        file = discord.File(io.BytesIO(image_data), filename="emoji.gif")
        message = await ctx.send(embed=embed, file=file)

        await message.add_reaction("\u2705")
        await message.add_reaction("\u274c")

        def check(reaction, user):
            return (reaction.message.id == message.id and user != self.bot.user and user.top_role.name in ["Officer", "Guild Master"] and reaction.emoji in ["\u2705", "\u274c"])

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=1800.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(f"The emoji request for {name} has expired after 30 minutes.")
            return

        if reaction.emoji == "\u2705":
            try:
                emoji = await ctx.guild.create_custom_emoji(name=name, image=image_data)
                await ctx.send(f"The emoji {emoji} was added successfully by {user.mention} for {ctx.author.mention}.")
            except discord.HTTPException as e:
                if e.code == 30008:
                    await ctx.send("The server has reached the maximum number of emojis. Please delete some existing emojis before requesting a new one.")
                elif e.code == 50035:
                    await ctx.send("The name or image is invalid. Please try again with a valid name and image.")
                else:
                    await ctx.send(f"There was an error while creating the emoji. Please try again later.")
                return

        if reaction.emoji == "\u274c":
            await ctx.send(f"The emoji request for {name} was denied by {user.mention} for {ctx.author.mention}.")

# Define a function that resizes an image file using the appropriate function based on the format
def resize_image_file(image_data, size):
    # Detect the image format using imghdr
    image_format = imghdr.what(None, image_data)
    # If the image format is gif, use the resize_gif function
    if image_format == "gif":
        return resize_gif(image_data, size)
    # If the image format is png or jpeg, use the resize_image function
    elif image_format in ["png", "jpeg"]:
        return resize_image(image_data, size)
    # If the image format is something else or unknown, raise an error and return None
    else:
        raise ValueError(f"Unsupported image format: {image_format}")
        return None

# Define a function that resizes a gif file using ImageMagick and preserves the animation
def resize_gif(image_data, size):
   # Save the image data to a temporary file as a gif file
   temp_file = "temp.gif"
   with open(temp_file, "wb") as f:
       f.write(image_data)
   # Use ImageMagick to resize the gif file and save it to another temporary file
   resized_file = "resized.gif"
   params = ['convert', '-resize', f'{size[0]}x{size[1]}', temp_file, resized_file]
   subprocess.check_call(params)
   # Read the resized file as bytes
   with open(resized_file, "rb") as f:
       resized_image_data = f.read()
   # Delete the temporary files
   os.remove(temp_file)
   os.remove(resized_file)
   # Return the resized image data
   return resized_image_data

# Define a function that resizes an image using thumbnail algorithm and preserves the aspect ratio
def resize_image(image_data, size):
    # Open the image data with PIL
    image = Image.open(io.BytesIO(image_data))
    # Resize the image using thumbnail algorithm
    image.thumbnail(size, Image.LANCZOS)
    # Convert the image to RGBA mode
    image = image.convert("RGBA")
    # Save the image to a BytesIO object as a PNG file
    output = io.BytesIO()
    image.save(output, format="PNG")
    # Seek to the beginning of the output
    output.seek(0)
    # Read the output as bytes
    resized_image_data = output.read()a
    # Close the output
    output.close()
    # Return the resized image data
    return resized_image_data
