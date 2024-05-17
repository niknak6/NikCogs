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
    async def request_emoji(self, ctx, *, content: str):
        words = content.split()
        name = None
        image_url = None

        for word in words:
            if word.startswith("http"):
                image_url = word
            else:
                name = word

        if not name or not (2 <= len(name) <= 32 and name.isalnum() or "_"):
            await ctx.send("The name must be between 2 and 32 characters long and consist of alphanumeric characters and underscores only.")
            return

        attachment = ctx.message.attachments[0] if ctx.message.attachments else None
        image_data = None

        if attachment:
            try:
                image_data = await attachment.read()
            except Exception as e:
                await ctx.send("There was an error while reading the image. Please try again with a valid PNG or JPG file.")
                return
        elif image_url:
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
                handle_emoji_creation_error(e, ctx)

        if reaction.emoji == "\u274c":
            await ctx.send(f"The emoji request for {name} was denied by {user.mention} for {ctx.author.mention}.")

def handle_emoji_creation_error(e, ctx):
    if e.code == 30008:
        ctx.send("The server has reached the maximum number of emojis. Please delete some existing emojis before requesting a new one.")
    elif e.code == 50035:
        ctx.send("The name or image is invalid. Please try again with a valid name and image.")
    else:
        ctx.send(f"There was an error while creating the emoji. Please try again later.")

def resize_image_file(image_data, size):
    image_format = imghdr.what(None, image_data)
    if image_format == "gif":
        return resize_gif(image_data, size)
    elif image_format in ["png", "jpeg"]:
        return resize_image(image_data, size)
    else:
        raise ValueError(f"Unsupported image format: {image_format}")
        return None

def resize_gif(image_data, size):
    temp_file = "temp.gif"
    with open(temp_file, "wb") as f:
        f.write(image_data)
    resized_file = "resized.gif"
    params = ['convert', '-resize', f'{size[0]}x{size[1]}', temp_file, resized_file]
    subprocess.check_call(params)
    with open(resized_file, "rb") as f:
        resized_image_data = f.read()
    os.remove(temp_file)
    os.remove(resized_file)
    return resized_image_data

def resize_image(image_data, size):
    image = Image.open(io.BytesIO(image_data))
    image.thumbnail(size, Image.LANCZOS)
    image = image.convert("RGBA")
    output = io.BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    resized_image_data = output.read()
    output.close()
    return resized_image_data
