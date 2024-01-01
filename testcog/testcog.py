# gpt.py

from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
import google.generativeai as genai
import re
from PIL import Image
from pathlib import Path
import asyncio
import aiohttp
import uuid
import os
import io

genai.configure(api_key=None) # will be set by the user later

class GPT(commands.Cog):
    """A cog that uses Google Generative AI to generate text or image descriptions."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(api_key=None)
        self.config.register_guild(context={}) # a dictionary of message UIDs and their content

    @commands.is_owner()
    @commands.command()
    async def setapikey(self, ctx: commands.Context, key: str):
        """Sets the Google API key for the cog."""
        await self.config.api_key.set(key)
        genai.configure(api_key=key)
        await ctx.send("API key set successfully.")

    @commands.command()
    async def gpt(self, ctx: commands.Context, *args):
        """Generates text or image descriptions using Google Generative AI."""
        if not await self.config.api_key():
            await ctx.send("The Google API key is not set. Please use the `setapikey` command first.")
            return
        if not args:
            await ctx.send("Please provide some input text or an image URL.")
            return
        if args[0].startswith("http"):
            # assume it's an image URL
            uid = await self.download_image(args[0])
            if uid:
                response = await self.ask_gpt([], is_image=True, context_uids=[uid])
                await ctx.send(response)
            else:
                await ctx.send("Failed to download the image.")
        else:
            # assume it's text input
            input_messages = [{"role": "user", "content": " ".join(args)}]
            guild_context = await self.config.guild(ctx.guild).context()
            context_uids = list(guild_context.keys())
            response = await self.ask_gpt(input_messages, is_image=False, context_uids=context_uids)
            await ctx.send(response)
            # store the input and output messages in the guild context
            input_uid = str(uuid.uuid4())
            output_uid = str(uuid.uuid4())
            guild_context[input_uid] = input_messages[0]['content']
            guild_context[output_uid] = response
            await self.config.guild(ctx.guild).context.set(guild_context)

    async def download_image(self, image_url):
        print(f"Downloading image from URL: {image_url}")
        uid = str(uuid.uuid4())
        images_dir = Path('./images')
        images_dir.mkdir(exist_ok=True)
        file_path = images_dir / f"{uid}.jpg"
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    image = Image.open(io.BytesIO(image_data))
                    image = self.compress_image(image, max_size=4*1024*1024)
                    image.save(file_path, quality=85, optimize=True)
                    print(f"Image downloaded and compressed as: {file_path}")
                    return uid
                else:
                    print(f"Failed to download image. HTTP status: {response.status}")
                    return None

    def compress_image(self, image, max_size):
        img_byte_arr = io.BytesIO()
        quality = 95
        if image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        while True:
            img_byte_arr.seek(0)
            image.save(img_byte_arr, format='JPEG', quality=quality)
            if img_byte_arr.tell() <= max_size or quality <= 10:
                break
            quality -= 5
        img_byte_arr.seek(0)
        return Image.open(img_byte_arr)

    async def process_image_with_google_api(self, temp_file_path):
        def process_image():
            print(f"Processing image with Google API: {temp_file_path}")
            image = Image.open(temp_file_path)
            model = genai.GenerativeModel(model_name="gemini-pro-vision")
            return model.generate_content([image]).text
        return await asyncio.to_thread(process_image)

    async def ask_gpt(self, input_messages, is_image=False, context_uids=[], retry_attempts=3, delay=1):
        combined_messages = " " + " ".join(msg['content'] for msg in input_messages if msg['role'] == 'user')
        for uid in context_uids:
            image_path = Path('./images') / f'{uid}.jpg'
            if image_path.exists():
                response_text = await self.process_image_with_google_api(image_path)
                combined_messages += " " + response_text
            else:
                print(f"Image with UID {uid} not found in context.")
        for attempt in range(retry_attempts):
            try:
                if is_image:
                    uid = None
                    for msg in input_messages:
                        uid_match = re.search(r'> Image UID: (\S+)', msg['content'])
                        if uid_match:
                            uid = uid_match.group(1)
                            break
                    if uid:
                        image_path = Path('./images') / f'{uid}.jpg'
                        if not image_path.exists():
                            print(f"Image not found at path: {image_path}")
                            return "Image not found."
                        response_text = await self.process_image_with_google_api(image_path)
                        print("Image processing completed.")
                        return response_text + f"\n> Image UID: {uid}"
                    else:
                        print("No valid UID found in the message.")
                        return "No valid UID found."
                model = genai.GenerativeModel(model_name="gemini-pro")
                chat = model.start_chat()
                print(f"Sending text to Google AI: {combined_messages}")
                response = chat.send_message(combined_messages)
                return response.text
            except Exception as e:
                print(f"Error in ask_gpt with Google AI: {e}")
                if attempt < retry_attempts - 1:
                    await asyncio.sleep(delay)
                    continue
                return "I'm sorry, I couldn't process that due to an error in the Google service."
