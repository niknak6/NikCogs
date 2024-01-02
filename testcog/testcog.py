# testcog.py

from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
from google.cloud import aiplatform # added this import to use Vertex AI SDK for Python
import re
from PIL import Image
from pathlib import Path
import asyncio
import aiohttp
import uuid
import os
import io
import textwrap # added this module to wrap long responses

aiplatform.init(project=None, location=None) # will be set by the user later

class TestCog(commands.Cog):
    """A cog that uses Google Generative AI to generate text or image descriptions."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(project_id=None, location=None)
        self.chat = None # added this attribute to store the chat object

    @commands.is_owner()
    @commands.command()
    async def setprojectid(self, ctx: commands.Context, project_id: str):
        """Sets the Google Cloud project ID for the cog."""
        await self.config.project_id.set(project_id)
        aiplatform.init(project=project_id) # initialize the Vertex AI SDK with the project ID
        await ctx.send("Project ID set successfully.")

    @commands.is_owner()
    @commands.command()
    async def setlocation(self, ctx: commands.Context, location: str):
        """Sets the Google Cloud location for the cog."""
        await self.config.location.set(location)
        aiplatform.init(location=location) # initialize the Vertex AI SDK with the location
        await ctx.send("Location set successfully.")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Responds to mentions using Google Generative AI."""
        if self.bot.user.mentioned_in(message): # check if the bot is mentioned
            args = message.content.split() # split the message by spaces
            if len(args) > 1: # check if there is something after the mention
                args.pop(0) # remove the mention from the list
                input_text = " ".join(args) # join the rest of the message with spaces
                # the input_text is the message appended to the mention
                # you can use it as the input for the Google API
                if input_text.startswith("http"):
                    # assume it's an image URL
                    uid = await self.download_image(input_text)
                    if uid:
                        response = await self.ask_gpt([], is_image=True, context_uids=[uid])
                        await message.channel.send(response)
                    else:
                        await message.channel.send("Failed to download the image.")
                else:
                    # assume it's text input
                    input_messages = [{"role": "user", "content": input_text}]
                    # added this block to fetch the referenced message and add it to the input_messages list
                    if message.reference: # check if the message is a reply
                        ref_msg = message.reference.cached_message or await message.channel.fetch_message(message.reference.message_id) # get the referenced message object
                        input_messages.append({"role": "bot", "content": ref_msg.content}) # add the referenced message content to the input_messages list
                    response = await self.ask_gpt(input_messages, is_image=False)
                    # added this block to split the response into smaller chunks
                    chunks = textwrap.wrap(response, width=1990) # wrap the response into lines of 1990 characters each
                    for chunk in chunks:
                        await message.channel.send(chunk) # send each chunk as a separate message
            else:
                # if there is nothing after the mention, you can send a default message
                await message.channel.send("Hello, I am a bot that uses Google Generative AI to generate text or image descriptions. You can mention me with some input text or an image URL and I will try to respond.")

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
            model = aiplatform.gapic.GenerativeModel(model_name="gemini-pro-vision")
            return model.generate_content([image]).text
        return await asyncio.to_thread(process_image)

    async def ask_gpt(self, input_messages, is_image=False, retry_attempts=3, delay=1):
        # added this block to create or load the chat object
        if not self.chat: # check if the chat object is None
            project_id = await self.config.project_id() # get the project ID from the config
            location = await self.config.location() # get the location from the config
            if not project_id or not location: # check if the project ID or the location is None
                print("No project ID or location set for the cog.")
                return "No project ID or location set for the cog."
            self.chat = aiplatform.gapic.GenerativeModel(model_name="gemini-pro").start_chat() # create the chat object
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
                input_text = input_messages[0]['content'] # get the input text from the first message
                response = self.chat.send_message(input_text) # send the input text to the chat object and get the response
                response_text = response.text # get the text of the response
                return response_text
            except Exception as e:
                print(f"Error in ask_gpt with Google AI: {e}")
                if attempt < retry_attempts - 1:
                    await asyncio.sleep(delay)
                    continue
                return "I'm sorry, I couldn't process that due to an error in the Google service."