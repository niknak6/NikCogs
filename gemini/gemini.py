import io
import re
import discord
from redbot.core import commands, Config
import textwrap
from pytgpt.imager import Imager
import asyncio

class Gemini(commands.Cog):
    """A Discord bot that uses gpt4free and Imager to interact with users in text and image formats."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.is_conversation = True
        self.history = []

    @commands.command()
    @commands.is_owner()
    async def setapikey(self, ctx, key: str):
        await ctx.send("API key setting not required for gpt4free or Imager.")

    @commands.command()
    @commands.is_owner()
    async def maxhistory(self, ctx, number: int):
        if number < 0:
            await ctx.send("The number must be positive or zero.")
            return
        self.history = self.history[-number:]
        await ctx.send(f"Max history set to {number}.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user or (message.reference and await self.is_bot_shared_message(message)):
            return
        if self.bot.user in message.mentions or isinstance(message.channel, discord.DMChannel):
            cleaned_text = self.clean_discord_message(message.content)
            if not await self.handle_commands(message, cleaned_text):
                await self.generate_response(message, cleaned_text)

    async def handle_commands(self, message, cleaned_text):
        command_map = {
            "RESET": (self.reset_history, [message]),
            "GENERATE": (self.generate_image, [message, cleaned_text])
        }
        for command, (handler, args) in command_map.items():
            if cleaned_text.upper().startswith(command):
                await handler(*args)
                return True
        return False

    async def reset_history(self, message):
        self.history = []
        await message.channel.send("🤖 History Reset.")

    async def generate_image(self, message, cleaned_text):
        async with message.channel.typing():
            await message.add_reaction('🎨')
            prompt = cleaned_text[8:].strip()  # Assuming 'GENERATE ' is 8 characters long
            img = Imager()

            # Create a list of tasks for generating images concurrently
            tasks = [self.bot.loop.run_in_executor(None, img.generate, prompt, 1, False) for _ in range(10)]
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks)

            # Process each result and prepare files
            files = []
            for result in results:
                image_data = result[0]  # Assuming each result is a list with one image
                image_bytes = io.BytesIO(image_data)
                image_bytes.seek(0)
                files.append(discord.File(image_bytes, filename=f"{prompt}_{len(files)+1}.png"))

            if files:
                await message.channel.send(content="Here are your images:", files=files)
            else:
                await message.channel.send("No images were generated.")

    async def generate_response(self, message, cleaned_text):
        async with message.channel.typing():
            await message.add_reaction('💬')
            gpt_bot = gpt4free.GPT4FREE(provider="DuckDuckGo", is_conversation=self.is_conversation, model="gpt-3.5-turbo", chat_completion=True)
            if self.is_conversation:
                self.history.append(cleaned_text)
                full_prompt = "\n".join(self.history)
                response_text = await self.bot.loop.run_in_executor(None, gpt_bot.chat, full_prompt)
            else:
                response_text = await self.bot.loop.run_in_executor(None, gpt_bot.chat, cleaned_text)
            self.history.append(response_text)
            await self.send_response(message, response_text)

    async def send_response(self, message, response_text, max_length=1999):
        for string in textwrap.wrap(response_text, max_length, replace_whitespace=False):
            await message.channel.send(string)

    def clean_discord_message(self, input_string):
        bot_mention_pattern = re.compile(f'<@!?{self.bot.user.id}>')
        cleaned_content = bot_mention_pattern.sub('', input_string).strip()
        non_mention_pattern = re.compile(r'<(?!@)[^>]+>')
        return non_mention_pattern.sub('', cleaned_content)
