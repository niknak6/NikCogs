import os
import re
import aiohttp
import discord
import google.generativeai as genai
import textwrap
from redbot.core import commands, Config
from discord.utils import remove_markdown
from collections import defaultdict

class Gemini(commands.Cog):
    """A Discord bot that uses Google's Gemini-Pro API to interact with users in text and image formats."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        # Register global settings for the bot
        self.config.register_global(
            google_ai_key=None,
            max_history=20,
            context_mode='user', # Determines whether the context is user-specific or channel-specific
        )
        # Define the settings for the text and image models
        self.model_settings = {
            "text": {
                "temperature": 1.0,
                "top_p": 1,
                "top_k": 1,
                "max_output_tokens": 2048,
                "safety_settings": [{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}]
            },
            "image": {
                "temperature": 0.4,
                "top_p": 1,
                "top_k": 32,
                "max_output_tokens": 2048,
                "safety_settings": [{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}]
            }
        }
        self.models = {}
        self.message_history = defaultdict(list)

        # Initialize the models asynchronously
        self.bot.loop.create_task(self.initialize_models())

    async def initialize_models(self):
        """Asynchronously initialize the text and image models with the configured settings."""
        api_key = await self.config.google_ai_key()
        if api_key:
            genai.configure(api_key=api_key)
            # Retrieve and apply the settings for the text and image models
            for model_type in ["text", "image"]:
                for setting in self.model_settings[model_type]:
                    self.model_settings[model_type][setting] = await self.config.get_attr(f"{model_type}_{setting}")()
                # Initialize the models
                self.models[model_type] = genai.GenerativeModel(model_name=f"gemini-pro-{model_type}", generation_config=self.model_settings[model_type], safety_settings=self.model_settings[model_type]["safety_settings"])

    @commands.command()
    @commands.is_owner()
    async def setapikey(self, ctx, key: str):
        """Set the API key for the Google AI services."""
        await self.config.google_ai_key.set(key)
        genai.configure(api_key=key)
        await ctx.send("API key set successfully.")

    @commands.command()
    @commands.is_owner()
    async def maxhistory(self, ctx, number: int):
        """Set the maximum number of messages to keep in the history."""
        if number < 0:
            await ctx.send("The number must be positive or zero.")
            return
        await self.config.max_history.set(number)
        await ctx.send(f"Max history set to {number}.")

    @commands.command()
    @commands.is_owner()
    async def contextmode(self, ctx, mode: str):
        """Set the context mode to either 'user' or 'channel'."""
        if mode not in ['user', 'channel']:
            await ctx.send("The mode must be either 'user' or 'channel'.")
            return
        await self.config.context_mode.set(mode)
        await ctx.send(f"Context mode set to {mode}.")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle incoming messages and generate responses."""
        if message.author == self.bot.user:
            return
        if self.bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
            cleaned_text = self.clean_discord_message(message.content)

            async with message.channel.typing():
                if message.attachments:
                    # Handle image messages
                    responses = [] # A list of responses for each attachment
                    for attachment in message.attachments:
                        if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                            await message.add_reaction('🎨')

                            async with aiohttp.ClientSession() as session:
                                async with session.get(attachment.url) as resp:
                                    if resp.status != 200:
                                        responses.append('Unable to download the image.')
                                        continue
                                    image_data = await resp.read()
                                    response_text = await self.generate_content("image", [image_data, f"\n{cleaned_text if cleaned_text else 'What is this a picture of?'}"])
                                    responses.append(response_text)
                    # Concatenate the responses and send them together
                    response_text = '\n\n'.join(responses)
                    await self.split_and_send_messages(message, response_text, 1700)
                    return
                else:
                    # Handle text messages
                    reset_pattern = re.compile(r'\bRESET\b') # A pattern to match the word RESET as a whole word
                    if reset_pattern.search(cleaned_text):
                        # Get the context mode and ID
                        context_mode = await self.config.context_mode()
                        context_id = message.channel.id if context_mode == 'channel' else message.author.id
                        # Delete the entry for that context ID from the message history
                        if context_id in self.message_history:
                            del self.message_history[context_id]
                        await message.channel.send(f"🤖 History Reset for {context_mode}: {message.channel.name if context_mode == 'channel' else message.author.name}")
                        return
                    await message.add_reaction('💬')

                    # Get the context mode and ID
                    context_mode = await self.config.context_mode()
                    context_id = message.channel.id if context_mode == 'channel' else message.author.id

                    max_history = await self.config.max_history()
                    if max_history == 0:
                        response_text = await self.generate_content("text", [cleaned_text])
                        await self.split_and_send_messages(message, response_text, 1700)
                        return
                    if message.reference:
                        referenced_message = await message.channel.fetch_message(message.reference.message_id)
                        referenced_text = self.clean_discord_message(referenced_message.content)
                        await self.update_message_history(context_id, referenced_text)
                    await self.update_message_history(context_id, cleaned_text)
                    response_text = await self.generate_content("text", [self.get_formatted_message_history(context_id)])
                    await self.update_message_history(context_id, response_text)
                    await self.split_and_send_messages(message, response_text, 1700)

    async def generate_content(self, model_type, prompt_parts):
        """Generate a response using the specified model."""
        response = self.models[model_type].generate_content(prompt_parts)
        if(response._error):
            return "❌" +  str(response._error)
        return response.text

    async def update_message_history(self, context_id, text):
        """Update the message history for the given context."""
        # Append the text to the message history for the context ID
        self.message_history[context_id].append(text)
        max_history = await self.config.max_history()
        # Remove the oldest message if the history exceeds the maximum limit
        if len(self.message_history[context_id]) > max_history:
            self.message_history[context_id].pop(0)

    def get_formatted_message_history(self, context_id):
        """Retrieve the message history for the given context."""
        # Return the message history or a default message
        return '\n\n'.join(self.message_history[context_id]) if self.message_history[context_id] else "No messages found for this user."

    async def split_and_send_messages(self, message_system, text, max_length):
        """Split the response into multiple messages if it exceeds the maximum length."""
        # Use textwrap to split the text into messages of the max length
        messages = textwrap.wrap(text, max_length)
        # Send each message
        for string in messages:
            await message_system.channel.send(string)

    def clean_discord_message(self, input_string):
        """Remove any special Discord formatting from the message."""
        # Use remove_markdown to strip the formatting
        cleaned_content = remove_markdown(input_string)
        return cleaned_content