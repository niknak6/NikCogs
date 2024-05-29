import io
import re
import discord
from redbot.core import commands, Config
import textwrap
from g4f.client import Client
from g4f.Provider import RetryProvider, ProviderA, ProviderB, ProviderC

class Brain(commands.Cog):
    """A Discord bot that uses g4f for interacting with users in text and image formats."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.is_conversation = True
        self.history = []
        self.g4f_client = Client(
            api_key='your_api_key',
            provider=RetryProvider([ProviderA, ProviderB, ProviderC]),
            max_tokens=150,
            response_format={"type": "json_object"}
        )

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

        combined_text = message.content
        if message.reference and message.reference.resolved:
            resolved_message = message.reference.resolved
            if resolved_message.author == self.bot.user and resolved_message.content.startswith("Shared by:"):
                return
            combined_text = f"{resolved_message.content} {combined_text}"

        cleaned_text = self.clean_discord_message(combined_text)
        if self.bot.user in message.mentions or isinstance(message.channel, discord.DMChannel):
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

            response = self.g4f_client.images.generate(
                model="dall-e-3",
                prompt=prompt
            )

            image_url = response.data[0].url
            await message.channel.send(content="Here is your image:", file=discord.File(io.BytesIO(image_url), filename="image.png"))

    async def generate_response(self, message, cleaned_text):
        async with message.channel.typing():
            await message.add_reaction('💬')
            messages = [{"role": "user", "content": msg} for msg in self.history] + [{"role": "user", "content": cleaned_text}]
            
            chat_completion = self.g4f_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                response_format={"type": "json_object"}  # Ensure the response is in JSON format
            )

            response_text = chat_completion.choices[0].message.content or ""
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