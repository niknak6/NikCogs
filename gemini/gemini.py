# Import the necessary modules
import os
import re

import aiohttp
import discord
import google.generativeai as genai
from redbot.core import commands, Config

# Create a cog class that inherits from commands.Cog
class Gemini(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Set up the config system
        default_global = {
            "google_ai_key": None,
            "max_history": 0
        }
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(**default_global)
        # Configure the generative AI models
        genai.configure(api_key=await self.config.google_ai_key())
        text_generation_config = {
            "temperature": 0.9,
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 512,
        }
        image_generation_config = {
            "temperature": 0.4,
            "top_p": 1,
            "top_k": 32,
            "max_output_tokens": 512,
        }
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
        ]
        self.text_model = genai.GenerativeModel(model_name="gemini-pro", generation_config=text_generation_config, safety_settings=safety_settings)
        self.image_model = genai.GenerativeModel(model_name="gemini-pro-vision", generation_config=image_generation_config, safety_settings=safety_settings)
        # Initialize the message history dictionary
        self.message_history = {}

    # Create a command to set the Google AI API key
    @commands.is_owner()
    @commands.command()
    async def setapikey(self, ctx, key: str):
        """Sets the Google AI API key."""
        await self.config.google_ai_key.set(key)
        await ctx.send("API key set.")

    # Create a command to set the max history value
    @commands.is_owner()
    @commands.command()
    async def setmaxhistory(self, ctx, value: int):
        """Sets the maximum number of messages to retain in history for each user."""
        await self.config.max_history.set(value)
        await ctx.send(f"Max history set to {value}.")

    # Register a listener for the on_message event
    @commands.Cog.listener()
    async def on_message(self, message):
        # Get the context of the message
        ctx = await self.bot.get_context(message)
        # Convert the message content to a cleaned string
        cleaned_text = await commands.clean_content().convert(ctx, message.content)

        # Check for image attachments
        if message.attachments:
            print("New Image Message FROM:" + str(message.author.id) + ": " + cleaned_text)
            # Currently no chat history for images
            for attachment in message.attachments:
                # These are the only image extensions it currently accepts
                if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                    await message.add_reaction('🎨')

                    async with aiohttp.ClientSession() as session:
                        async with session.get(attachment.url) as resp:
                            if resp.status != 200:
                                await message.channel.send('Unable to download the image.')
                                return
                            image_data = await resp.read()
                            response_text = await self.generate_response_with_image_and_text(image_data, cleaned_text)
                            # Create a paginator and add the response text to it
                            paginator = commands.Paginator()
                            paginator.add_line(response_text)
                            # Send the paginator to the message channel
                            await self.bot.send_pages(paginator, message.channel)
                            return
        # Not an image, do text response
        else:
            print("New Message FROM:" + str(message.author.id) + ": " + cleaned_text)
            # Check for keyword reset
            if "RESET" in cleaned_text:
                # Send back message
                if message.author.id in self.message_history:
                    del self.message_history[message.author.id]
                await message.channel.send("🤖 History Reset for user: " + str(message.author.name))
                return
            await message.add_reaction('💬')

            # Check if history is disabled, just send response
            if (await self.config.max_history()) == 0:
                response_text = await self.generate_response_with_text(cleaned_text)
                # Create a paginator and add the response text to it
                paginator = commands.Paginator()
                paginator.add_line(response_text)
                # Send the paginator to the message channel
                await self.bot.send_pages(paginator, message.channel)
                return
            # Add user's question to history
            self.update_message_history(message.author.id, cleaned_text)
            response_text = await self.generate_response_with_text(self.get_formatted_message_history(message.author.id))
            # Add AI response to history
            self.update_message_history(message.author.id, response_text)
            # Create a paginator and add the response text to it
            paginator = commands.Paginator()
            paginator.add_line(response_text)
            # Send the paginator to the message channel
            await self.bot.send_pages(paginator, message.channel)

    # Define the methods for generating responses with text and image
    async def generate_response_with_text(self, message_text):
        prompt_parts = [message_text]
        print("Got textPrompt: " + message_text)
        response = self.text_model.generate_content(prompt_parts)
        if (response._error):
            return "❌" + str(response._error)
        return response.text

    async def generate_response_with_image_and_text(self, image_data, text):
        image_parts = [{"mime_type": "image/jpeg", "data": image_data}]
        prompt_parts = [image_parts[0], f"\n{text if text else 'What is this a picture of?'}"]
        response = self.image_model.generate_content(prompt_parts)
        if (response._error):
            return "❌" + str(response._error)
        return response.text

    # Define the methods for updating and formatting the message history
    def update_message_history(self, user_id, text):
        # Check if user_id already exists in the dictionary
        if user_id in self.message_history:
            # Append the new message to the user's message list
            self.message_history[user_id].append(text)
            # If there are more than max history messages, remove the oldest one
            if len(self.message_history[user_id]) > (await self.config.max_history()):
                self.message_history[user_id].pop(0)
        else:
            # If the user_id does not exist, create a new entry with the message
            self.message_history[user_id] = [text]

    def get_formatted_message_history(self, user_id):
        """
        Function to return the message history for a given user_id with two line breaks between each message.
        """
        if user_id in self.message_history:
            # Join the messages with two line breaks
            return '\n\n'.join(self.message_history[user_id])
        else:
            return "No messages found for this user."

# Define a function to load the cog
def setup(bot):
    bot.add_cog(Gemini(bot))