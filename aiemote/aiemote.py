import os
import re
import random
import emoji
import aiohttp
import discord
import google.generativeai as genai
from redbot.core import commands, Config

class AiEmote(commands.Cog):
    """Discord bot that randomly reacts to messages with emojis based on the Google's Gemini-Pro API."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(
            google_ai_key=None,
            percentage=10 # This is the new setting for the percentage of the time that the bot will react to a message
        )
        self.text_model = None

        # Create a task to initialize the model
        self.bot.loop.create_task(self.initialize_model())

    # Define an async method to read the config values and initialize the model
    async def initialize_model(self):
        api_key = await self.config.google_ai_key() # Added await here
        if api_key:
            genai.configure(api_key=api_key)
            self.text_model = genai.GenerativeModel(model_name="gemini-pro", generation_config={"temperature": 1.0, "top_p": 1.0, "top_k": 1, "max_output_tokens": 2048}, safety_settings=[{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}])

    @commands.command(name="setreactkey") # Changed the command name here
    @commands.is_owner()
    async def setreactkey(self, ctx, key: str): # Renamed the method here
        """Sets the Google AI key for the Gemini-Pro model. # Updated the docstring here"""
        await self.config.google_ai_key.set(key) # Added await here
        genai.configure(api_key=key)
        self.text_model = genai.GenerativeModel(model_name="gemini-pro", generation_config={"temperature": 1.0, "top_p": 1.0, "top_k": 1, "max_output_tokens": 2048}, safety_settings=[{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}])
        await ctx.send("React key set successfully.") # Updated the success message here

    @commands.command()
    @commands.is_owner()
    async def percentage(self, ctx, number: int):
        if number < 0 or number > 100:
            await ctx.send("The number must be between 0 and 100.")
            return
        await self.config.percentage.set(number) # Added await here
        await ctx.send(f"Percentage set to {number}%.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if not message.content.startswith((await self.bot.command_prefix(self.bot, message))[0]) and not self.bot.user.mentioned_in(message): # Fixed both errors here
            percentage = await self.config.percentage() # Added await here
            random_number = random.randint(0, 100)
            if random_number < percentage:
                cleaned_text = self.clean_discord_message(message.content)

                # Deleted the line below and unindented the lines after it
                # async with message.channel.typing():
                print("New Message FROM:" + str(message.author.id) + ": " + cleaned_text)
                await message.add_reaction(await self.generate_emoji_reaction(cleaned_text))

    async def generate_emoji_reaction(self, message_text):
        prompt_parts = [message_text, "\nWhat emoji best describes the premise of this sentence?"]
        print("Got textPrompt: " + message_text)
        response = self.text_model.generate_content(prompt_parts)
        if(response._error):
            return "❌" +  str(response._error)
        emoji_response = self.extract_emoji(response.text)
        return emoji_response

    def extract_emoji(self, text):
        default_emoji = '😀'
        emoji_pattern = re.compile(r'[\U00010000-\U0010ffff]', flags=re.UNICODE)
        emoji_matches = emoji_pattern.findall(text)
        if emoji_matches:
            emoji_match = emoji_matches[0]
            if emoji.is_emoji(emoji_match):
                return emoji.emojize(emoji_match, language='alias') # Changed this line to use the language argument instead of the use_aliases argument
            else:
                return default_emoji
        else:
            return default_emoji

    def clean_discord_message(self, input_string):
        bracket_pattern = re.compile(r'<[^>]+>')
        cleaned_content = bracket_pattern.sub('', input_string)
        return cleaned_content