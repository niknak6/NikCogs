import io
import re
import discord
from redbot.core import commands, Config
import textwrap
import pytgpt.gpt4free as gpt4free
from pytgpt.imager import Imager

class Brain(commands.Cog):
    """A Discord bot that uses gpt4free and Imager to interact with users in text and image formats."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.is_conversation = True
        self.history = []

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
        if message.author == self.bot.user:
            return

        # Check if the message is a reply and if the bot is mentioned
        if message.reference and message.reference.resolved:
            resolved_message = message.reference.resolved
            if resolved_message.author == self.bot.user and resolved_message.content.startswith("Shared by:"):
                return  # Do not respond to these messages

            # Add the content of the replied-to message to history if not present
            if resolved_message.content and resolved_message.content not in self.history:
                self.history.append(resolved_message.content)

            # If the bot is mentioned in the reply, handle it
            if self.bot.user in message.mentions:
                cleaned_text = self.clean_discord_message(message.content)
                await self.generate_response(message, cleaned_text, additional_context=resolved_message.content)
                return

        # Existing check for direct mentions or DMs
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

            files = []
            for _ in range(6):  # Generate 6 images one by one
                image_data = img.generate(prompt, amount=1, stream=False)[0]  # Generate one image at a time
                image_bytes = io.BytesIO(image_data)
                image_bytes.seek(0)
                files.append(discord.File(image_bytes, filename=f"{prompt}_{len(files)+1}.png"))

            if files:
                await message.channel.send(content="Here are your images:", files=files)
            else:
                await message.channel.send("No images were generated.")

    async def generate_response(self, message, cleaned_text, additional_context=None):
        async with message.channel.typing():
            await message.add_reaction('💬')
            gpt_bot = gpt4free.GPT4FREE(provider="DuckDuckGo", is_conversation=self.is_conversation, model="gpt-3.5-turbo", chat_completion=True)
            if self.is_conversation:
                if additional_context:
                    self.history.append(additional_context)
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