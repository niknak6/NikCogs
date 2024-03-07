import os
import re
import aiohttp
import discord
import google.generativeai as genai
from redbot.core import commands, Config
import textwrap # Import the textwrap module
import typing # Import the typing module

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
            dg_mode='single', # Determines whether the DoubleGemini mode is enabled or not
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
    async def contextmode(self, ctx, mode: str, dg_mode: typing.Optional[str] = 'single'):
        """Set the context mode to either 'user' or 'channel' and the DoubleGemini mode to either 'single' or 'dg'."""
        if mode not in ['user', 'channel']:
            await ctx.send("The mode must be either 'user' or 'channel'.")
            return
        if dg_mode not in ['single', 'dg']:
            await ctx.send("The DoubleGemini mode must be either 'single' or 'dg'.")
            return
        await self.config.context_mode.set(mode)
        await self.config.dg_mode.set(dg_mode)
        await ctx.send(f"Context mode set to {mode} and DoubleGemini mode set to {dg_mode}.")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle incoming messages and generate responses."""
        if message.author == self.bot.user:
            return
        # Check if the message is a reply to a bot message that starts with "Shared by"
        if message.reference:
            referenced_message = await message.channel.fetch_message(message.reference.message_id)
            if referenced_message.author == self.bot.user and referenced_message.content.startswith("Shared by"):
                # Skip the message processing
                return
        # Continue with the rest of the message processing
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
        # Check the DoubleGemini mode
        dg_mode = await self.config.dg_mode()
        if dg_mode == 'dg':
            # Perform a second query to the API with a validation prompt
            validation_prompt = f"Please verify that the following information is correct:\n{response.text}"
            validation_response = self.text_model.validate_content(validation_prompt)
            if(validation_response._error):