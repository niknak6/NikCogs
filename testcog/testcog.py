# testcog.py

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
import textwrap # added this module to wrap long responses

genai.configure(api_key=None) # will be set by the user later

class TestCog(commands.Cog):
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
                        response = await self.generate_content([], is_image=True, context_uids=[uid])
                        await message.channel.send(response)
                    else:
                        await message.channel.send("Failed to download the image.")
                else:
                    # assume it's text input
                    input_messages = [{"role": "user", "content": input_text}]
                    guild_context = await self.config.guild(message.guild).context()
                    context_uids = list(guild_context.keys())
                    # added this block to fetch the referenced message and add it to the input_messages list
                    history = [] # initialize an empty history list
                    if message.reference: # check if the message is a reply
                        ref_msg = message.reference.cached_message or await message.channel.fetch_message(message.reference.message_id) # get the referenced message object
                        ref_uid = ref_msg.id # get the referenced message id
                        if ref_uid in guild_context: # check if the referenced message id is in the guild context
                            ref_content = guild_context[ref_uid] # get the referenced message content from the guild context
                            history.append(genai.Content(parts=[genai.Part(text=ref_content)])) # add the referenced message content as a Content object to the history list
                    response = await self.generate_content(input_messages, is_image=False, context_uids=context_uids, history=history) # pass the history list to the generate_content method
                    # added this block to split the response into smaller chunks
                    chunks = textwrap.wrap(response, width=1990) # wrap the response into lines of 1990 characters each
                    for chunk in chunks:
                        await message.channel.send(chunk) # send each chunk as a separate message
                    # store the input and output messages in the guild context
                    input_uid = str(uuid.uuid4())
                    output_uid = str(uuid.uuid4())
                    guild_context[input_uid] = input_messages[0]['content']
                    guild_context[output_uid] = response
                    await self.config.guild(message.guild).context.set(guild_context)
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
            model = genai.GenerativeModel(model_name="gemini-pro-vision")
            return model.generate_content([image]).text
        return await asyncio.to_thread(process_image)

    async def generate_content(self, input_messages, is_image=False, context_uids=[], history=[], retry_attempts=3, delay=1):
        input_contents = [] # initialize an empty list of input contents
        for msg in input_messages: # loop through the input messages
            if msg['role'] == 'user': # check if the message is from the user
                input_contents.append(genai.Content(parts=[genai.Part(text=msg['content'])])) # create a Content object with the message text and append it to the input contents list
        for uid in context_uids: # loop through the context UIDs
            image_path = Path('./images') / f'{uid}.jpg' # get the image path
            if image_path.exists(): # check if the image exists
                image = Image.open(image_path) # open the image
                input_contents.append(genai.Content(parts=[genai.Part(image=image)])) # create a Content object with the image and append it to the input contents list
            else:
                print(f"Image with UID {uid} not found in context.")
        for attempt in range(retry_attempts): # loop through the retry attempts
            try:
                if is_image: # check if the input is an image
                    uid = None
                    for msg in input_messages: # loop through the input messages
                        uid_match = re.search(r'> Image UID: (\S+)', msg['content']) # try to find the image UID in the message
                        if uid_match: # check if there is a match
                            uid = uid_match.group(1) # get the UID
                            break
                    if uid: # check if there is a UID
                        image_path = Path('./images') / f'{uid}.jpg' # get the image path
                        if not image_path.exists(): # check if the image exists
                            print(f"Image not found at path: {image_path}")
                            return "Image not found."
                        response_text = await self.process_image_with_google_api(image_path) # process the image with the Google API
                        print("Image processing completed.")
                        return response_text + f"\n> Image UID: {uid}" # return the response text with the image UID
                    else:
                        print("No valid UID found in the message.")
                        return "No valid UID found."
                model = genai.GenerativeModel(model_name="gemini-pro") # create a generative model object
                chat = model.start_chat(history=history) # start a chat session with the history list
                print(f"Sending contents to Google AI: {input_contents}")
                response = chat.send_content(input_contents) # send the input contents to the Google AI
                return response.text # return the response text
            except Exception as e: # catch any exception
                print(f"Error in generate_content with Google AI: {e}")
                if attempt < retry_attempts - 1: # check if there are more attempts left
                    await asyncio.sleep(delay) # wait for some delay
                    continue
                return "I'm sorry, I couldn't process that due to an error in the Google service."