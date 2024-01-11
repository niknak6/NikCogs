import os
import re
import aiohttp
import discord
import google.generativeai as genai
from redbot.core import commands, Config
import textwrap # Import the textwrap module

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
            # Settings for the text model
            text_temperature=1.0,
            text_top_p=1,
            text_top_k=1,
            text_max_output_tokens=2048,
            text_safety_settings=[{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}],
            # Settings for the image model
            image_temperature=0.4,
            image_top_p=1,
            image_top_k=32,
            image_max_output_tokens=2048,
            image_safety_settings=[{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}]
        )
        self.text_model = None
        self.image_model = None
        self.message_history = {}

        # Initialize the models asynchronously
        self.bot.loop.create_task(self.initialize_models())

    async def initialize_models(self):
        """Asynchronously initialize the text and image models with the configured settings."""
        api_key = await self.config.google_ai_key()
        if api_key:
            genai.configure(api_key=api_key)
            # Retrieve and apply the settings for the text model
            text_temperature = await self.config.get_attr("text_temperature")()
            text_top_p = await self.config.get_attr("text_top_p")()
            text_top_k = await self.config.get_attr("text_top_k")()
            text_max_output_tokens = await self.config.get_attr("text_max_output_tokens")()
            text_safety_settings = await self.config.get_attr("text_safety_settings")()
            # Retrieve and apply the settings for the image model
            image_temperature = await self.config.get_attr("image_temperature")()
            image_top_p = await self.config.get_attr("image_top_p")()
            image_top_k = await self.config.get_attr("image_top_k")()
            image_max_output_tokens = await self.config.get_attr("image_max_output_tokens")()
            image_safety_settings = await self.config.get_attr("image_safety_settings")()
            # Initialize the text model
            self.text_model = genai.GenerativeModel(model_name="gemini-pro", generation_config={"temperature": text_temperature, "top_p": text_top_p, "top_k": text_top_k, "max_output_tokens": text_max_output_tokens}, safety_settings=text_safety_settings)
            # Initialize the image model
            self.image_model = genai.GenerativeModel(model_name="gemini-pro-vision", generation_config={"temperature": image_temperature, "top_p": image_top_p, "top_k": image_top_k, "max_output_tokens": image_max_output_tokens}, safety_settings=image_safety_settings)

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
                                    response_text = await self.generate_response_with_image_and_text(image_data, cleaned_text)
                                    responses.append(response_text)
                    # Concatenate the responses and send them together
                    response_text = '\n\n'.join(responses)
                    await self.wrap_and_send_messages(message, response_text, 1700) # Use the wrap_and_send_messages method
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
                        response_text = await self.generate_response_with_text(cleaned_text)
                        await self.wrap_and_send_messages(message, response_text, 1999) # Use the wrap_and_send_messages method
                        return
                    if message.reference:
                        referenced_message = await message.channel.fetch_message(message.reference.message_id)
                        referenced_text = self.clean_discord_message(referenced_message.content)
                        await self.update_message_history(context_id, referenced_text)
                    await self.update_message_history(context_id, cleaned_text)
                    response_text = await self.generate_response_with_text(self.get_formatted_message_history(context_id))
                    await self.update_message_history(context_id, response_text)
                    await self.wrap_and_send_messages(message, response_text, 1999) # Use the wrap_and_send_messages method

    async def generate_response_with_text(self, message_text):
        """Generate a text response using the text model."""
        prompt_parts = [message_text]
        response = self.text_model.generate_content(prompt_parts)
        if(response._error):
            return "❌" +  str(response._error)
        return response.text

    async def generate_response_with_image_and_text(self, image_data, text):
        """Generate a text response using the image model."""
        image_parts = [{"mime_type": "image/jpeg", "data": image_data}]
        prompt_parts = [image_parts[0], f"\n{text if text else 'What is this a picture of?'}"]
        response = self.image_model.generate_content(prompt_parts)
        if(response._error):
            return "❌" +  str(response._error)
        return response.text

    async def update_message_history(self, context_id, text):
        """Update the message history for the given context."""
        if context_id in self.message_history:
            self.message_history[context_id].append(text)
            max_history = await self.config.max_history()
            if len(self.message_history[context_id]) > max_history:
                self.message_history[context_id].pop(0)
        else:
            self.message_history[context_id] = [text]

    def get_formatted_message_history(self, context_id):
        """Retrieve the message history for the given context."""
        if context_id in self.message_history:
            return '\n\n'.join(self.message_history[context_id])
        else:
            return "No messages found for this user."

    async def wrap_and_send_messages(self, message_system, text, max_length):
        """Wrap the text into smaller chunks based on the maximum length and send them as separate messages."""
        messages = textwrap.wrap(text, max_length) # Use the textwrap.wrap function to split the text into a list of strings
        for string in messages:
            await message_system.channel.send(string)

    def clean_discord_message(self, input_string):
        """Remove any special Discord formatting from the message."""
        bracket_pattern = re.compile(r'<[^>]+>')
        cleaned_content = bracket_pattern.sub('', input_string)
        return cleaned_content