import os
import re

import aiohttp
import discord
import google.generativeai as genai
from redbot.core import commands, Config

class Gemini(commands.Cog):
    """Discord bot that leverages the power of Google's Gemini-Pro API to interact with users in both text and image formats."""

    def __init__(self, bot):
        self.bot = bot
        # You can use the Config class to store your settings and data
        self.config = Config.get_conf(self, identifier=1234567890)
        # Set the default values for your settings
        self.config.register_global(
            google_ai_key=None, # You will set this with the setapikey command
            max_history=12 # You can change this with the maxhistory command
        )
        # Initialize the generative AI models
        self.text_model = None
        self.image_model = None
        # Create a dictionary to store the message history for each user
        self.message_history = {}

    @commands.command()
    @commands.is_owner()
    async def setapikey(self, ctx, key: str):
        """Sets the Google AI API key."""
        # Save the key in the config
        await self.config.google_ai_key.set(key)
        # Configure the generative AI models with the key
        genai.configure(api_key=key)
        self.text_model = genai.GenerativeModel(model_name="gemini-pro", generation_config={"temperature": 0.9, "top_p": 1, "top_k": 1, "max_output_tokens": 512}, safety_settings=[{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}, {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}, {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}, {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}])
        self.image_model = genai.GenerativeModel(model_name="gemini-pro-vision", generation_config={"temperature": 0.4, "top_p": 1, "top_k": 32, "max_output_tokens": 512}, safety_settings=[{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}, {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}, {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}, {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}])
        # Send a confirmation message
        await ctx.send("API key set successfully.")

    @commands.command()
    @commands.is_owner()
    async def maxhistory(self, ctx, number: int):
        """Sets the maximum number of messages to retain in history for each user."""
        # Validate the input
        if number < 0:
            await ctx.send("The number must be positive or zero.")
            return
        # Save the number in the config
        await self.config.max_history.set(number)
        # Send a confirmation message
        await ctx.send(f"Max history set to {number}.")

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore messages sent by the bot
        if message.author == self.bot.user:
            return
        # Check if the bot is mentioned or the message is a DM
        if self.bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
            # Start typing to seem like something happened
            cleaned_text = self.clean_discord_message(message.content)

            async with message.channel.typing():
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
                                    # Split the Message so discord does not get upset
                                    await self.split_and_send_messages(message, response_text, 1700)
                                    return
                # Not an Image do text response
                else:
                    print("New Message FROM:" + str(message.author.id) + ": " + cleaned_text)
                    # Check for Keyword Reset
                    if "RESET" in cleaned_text:
                        # End back message
                        if message.author.id in self.message_history:
                            del self.message_history[message.author.id]
                        await message.channel.send("🤖 History Reset for user: " + str(message.author.name))
                        return
                    await message.add_reaction('💬')

                    # Check if history is disabled just send response
                    max_history = await self.config.max_history()
                    if max_history == 0:
                        response_text = await self.generate_response_with_text(cleaned_text)
                        # Add AI response to history
                        await self.split_and_send_messages(message, response_text, 1700)
                        return
                    # Add users question to history
                    await self.update_message_history(message.author.id, cleaned_text)
                    response_text = await self.generate_response_with_text(self.get_formatted_message_history(message.author.id))
                    # Add AI response to history
                    await self.update_message_history(message.author.id, response_text)
                    # Split the Message so discord does not get upset
                    await self.split_and_send_messages(message, response_text, 1700)

    async def generate_response_with_text(self, message_text):
        prompt_parts = [message_text]
        print("Got textPrompt: " + message_text)
        response = self.text_model.generate_content(prompt_parts)
        if(response._error):
            return "❌" +  str(response._error)
        return response.text

    async def generate_response_with_image_and_text(self, image_data, text):
        image_parts = [{"mime_type": "image/jpeg", "data": image_data}]
        prompt_parts = [image_parts[0], f"\n{text if text else 'What is this a picture of?'}"]
        response = self.image_model.generate_content(prompt_parts)
        if(response._error):
            return "❌" +  str(response._error)
        return response.text

    async def update_message_history(self, user_id, text):
        # Check if user_id already exists in the dictionary
        if user_id in self.message_history:
            # Append the new message to the user's message list
            self.message_history[user_id].append(text)
            # If there are more than 12 messages, remove the oldest one
            max_history = await self.config.max_history()
            if len(self.message_history[user_id]) > max_history:
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

    async def split_and_send_messages(self, message_system, text, max_length):

        # Split the string into parts
        messages = []
        for i in range(0, len(text), max_length):
            sub_message = text[i:i+max_length]
            messages.append(sub_message)

        # Send each part as a separate message
        for string in messages:
            await message_system.channel.send(string)

    def clean_discord_message(self, input_string):
        # Create a regular expression pattern to match text between < and >
        bracket_pattern = re.compile(r'<[^>]+>')
        # Replace text between brackets with an empty string
        cleaned_content = bracket_pattern.sub('', input_string)
        return cleaned_content