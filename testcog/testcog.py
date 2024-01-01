# Import the google-generativeai package
import google.generativeai as genai
# Import the discord and redbot.core packages
import discord
from redbot.core import commands
# Import the re, pathlib, asyncio, aiohttp, uuid, os, io, and PIL packages
import re
from pathlib import Path
import asyncio
import aiohttp
import uuid
import os
import io
from PIL import Image

# Define a cog class that inherits from commands.Cog
class TestCog(commands.Cog):
  # Initialize the cog with the bot and the optional api key
  def __init__(self, bot, api_key=None):
    self.bot = bot
    # Set the api key attribute of the cog
    self.api_key = api_key
    # Try to configure the genai package with the api key
    try:
      genai.configure(api_key=api_key)
      # Create a generative model object for the gemini-pro model
      self.model = genai.GenerativeModel('gemini-pro')
      # Start a chat session with the model
      self.chat = self.model.start_chat(history=[])
    except Exception as e:
      # If the api key is not set or invalid, print the error and set the model and chat to None
      print(f'Error: {e}')
      self.model = None
      self.chat = None
    # Create a list to store the conversation history for the server or the group
    self.conversation_history = []

  # Define a command that sets the api key
  @commands.command()
  async def geminiapi(self, ctx, api_key):
    # Set the api key attribute of the cog
    self.api_key = api_key
    # Try to configure the genai package with the api key
    try:
      genai.configure(api_key=api_key)
      # Create a generative model object for the gemini-pro model
      self.model = genai.GenerativeModel('gemini-pro')
      # Start a chat session with the model
      self.chat = self.model.start_chat(history=[])
      # Send a confirmation message to the user
      await ctx.send(f'Gemini API key set to {api_key}')
    except Exception as e:
      # If the api key is invalid, send an error message to the user
      await ctx.send(f'Invalid API key: {e}')

  # Define a function that downloads and compresses images from URLs and saves them locally
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

  # Define a function that compresses images to a maximum size
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

  # Define a function that processes images with the Gemini Pro Vision model and returns a text description of the images
  async def process_image_with_google_api(self, temp_file_path):
    def process_image():
        print(f"Processing image with Google API: {temp_file_path}")
        image = Image.open(temp_file_path)
        model = genai.GenerativeModel(model_name="gemini-pro-vision")
        return model.generate_content([image]).text
    return await asyncio.to_thread(process_image)

  # Define a listener that responds to bot mentions
  @commands.Cog.listener()
  async def on_message(self, message):
    # Check if the message mentions the bot
    if self.bot.user in message.mentions:
      # Check if the model and chat are not None
      if self.model is not None and self.chat is not None:
        # Check if the message content is an image URL
        if isinstance(message.content, str) and message.content.startswith("http"):
          # Download and compress the image from the URL using the download_image function
          uid = await self.download_image(message.content)
          # Check if the download was successful
          if uid:
            # Get the file path of the downloaded image
            file_path = Path('./images') / f"{uid}.jpg"
            # Open the image file as a PIL Image object
            image = Image.open(file_path)
            # Create a glm.Content object for the message content with the role "user" and a single glm.Part object containing the image
            message_content = glm.Content(parts=[glm.Part(image=image)], role="user")
            # Append the message content to the conversation history
            self.conversation_history.append(message_content)
            # Start a chat session with the model using the conversation history as the history parameter
            self.chat = self.model.start_chat(history=self.conversation_history)
            # Process the image with the Gemini Pro Vision model using the process_image_with_google_api function
            response_text = await self.process_image_with_google_api(file_path)
            # Create a glm.Content object for the response text with the role "model" and a single glm.Part object containing the text
            response_content = glm.Content(parts=[glm.Part(text=response_text)], role="model")
            # Append the response content to the conversation history
            self.conversation_history.append(response_content)
            # Send the response text and the image UID to the user
            await message.channel.send(response_text + f"\n> Image UID: {uid}")
          else:
            # If the download failed, send a message saying that the image could not be downloaded
            await message.channel.send("I'm sorry, I could not download the image from the URL.")
        else:
          # If the message content is not an image URL, treat it as text
          # Create a glm.Content object for the message content with the role "user" and a single glm.Part object containing the text
          message_content = glm.Content(parts=[glm.Part(text=message.content)], role="user")
          # Append the message content to the conversation history
          self.conversation_history.append(message_content)
          # Start a chat session with the model using the conversation history as the history parameter
          self.chat = self.model.start_chat(history=self.conversation_history)
          # Generate a response from the model using the send_message method, passing the message content and the stream parameter as True
          response = self.chat.send_message(message.content, stream=True)
          # Send the response to the user
          for chunk in response:
            await message.channel.send(chunk.text)
            # Create a glm.Content object for the response content with the role "model" and a single glm.Part object containing the text
            response_content = glm.Content(parts=[glm.Part(text=chunk.text)], role="model")
            # Append the response content to the conversation history
            self.conversation_history.append(response_content)
      else:
        # If the model or chat is None, send a message to the user to set the api key first
        await message.channel.send('Please set the Gemini API key first using the geminiapi command.')