import os
import re
import aiohttp
import discord
from redbot.core import commands, Config
import textwrap
import typing
from together import Together
import io
import base64

class Gemini(commands.Cog):
    """A Discord bot that uses Together.ai API to interact with users in text format."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(
            together_ai_key=None,
            max_history=20,
            context_mode='user',
            pass_mode='single',
        )
        self.client = None
        self.message_history = {}

        self.bot.loop.create_task(self.initialize_models())

    async def initialize_models(self):
        """Asynchronously initialize the text model with the configured settings."""
        api_key = await self.config.together_ai_key()
        if api_key:
            try:
                self.client = Together(api_key=api_key)
                await self.bot.send_to_owners("Together.ai client initialized successfully.")
            except Exception as e:
                await self.bot.send_to_owners(f"Failed to initialize Together.ai client: {str(e)}")
        else:
            await self.bot.send_to_owners("Together.ai API key not set. Please use the `setapikey` command to set the API key.")


    @commands.command()
    @commands.is_owner()
    async def setapikey(self, ctx, key: str):
        """Set the API key for the Together.ai services."""
        await self.config.together_ai_key.set(key)
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
    async def contextmode(self, ctx, mode: str, pass_mode: typing.Optional[str] = 'single'):
        """Set the context mode to either 'user' or 'channel' and the pass mode to either 'single' or 'dg'."""
        if mode not in ['user', 'channel']:
            await ctx.send("The mode must be either 'user' or 'channel'.")
            return
        if pass_mode not in ['single', 'dg']:
            await ctx.send("The pass mode must be either 'single' or 'dg'.")
            return
        await self.config.context_mode.set(mode)
        await self.config.pass_mode.set(pass_mode)
        await ctx.send(f"Context mode set to {mode} and pass mode set to {pass_mode}.")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle incoming messages and generate responses."""
        if message.author == self.bot.user:
            return
        if message.reference:
            referenced_message = await message.channel.fetch_message(message.reference.message_id)
            if referenced_message.author == self.bot.user and referenced_message.content.startswith("Shared by"):
                return
        if self.bot.user in message.mentions or isinstance(message.channel, discord.DMChannel):
            cleaned_text = self.clean_discord_message(message.content)

            if cleaned_text.upper().startswith("RESET"):
                context_mode = await self.config.context_mode()
                context_id = message.channel.id if context_mode == 'channel' else message.author.id
                if context_id in self.message_history:
                    del self.message_history[context_id]
                await message.channel.send(f"🤖 History Reset for {context_mode}: {message.channel.name if context_mode == 'channel' else message.author.name}")
                return
            elif cleaned_text.upper().startswith("GENERATE"):
                async with message.channel.typing():
                    await message.add_reaction('🎨')
                    prompt = cleaned_text[8:].strip()
                    response = self.client.images.generate(
                        prompt=prompt,
                        model="stabilityai/stable-diffusion-xl-base-1.0",
                        steps=10,
                        n=1,
                    )
                    image_data = response.data[0].b64_json
                    await message.channel.send(file=discord.File(io.BytesIO(base64.b64decode(image_data)), filename="generated_image.png"))
                return

            async with message.channel.typing():
                await message.add_reaction('💬')

                context_mode = await self.config.context_mode()
                context_id = message.channel.id if context_mode == 'channel' else message.author.id

                max_history = await self.config.max_history()
                if max_history == 0:
                    response_text = await self.generate_response_with_text(cleaned_text)
                    await self.wrap_and_send_messages(message, response_text, 1999)
                    return
                if message.reference:
                    referenced_message = await message.channel.fetch_message(message.reference.message_id)
                    referenced_text = self.clean_discord_message(referenced_message.content)
                    await self.update_message_history(context_id, referenced_text)
                await self.update_message_history(context_id, cleaned_text)
                response_text = await self.generate_response_with_text(self.get_formatted_message_history(context_id))
                await self.update_message_history(context_id, response_text)
                await self.wrap_and_send_messages(message, response_text, 1999)

    async def generate_response_with_text(self, message_text):
        """Generate a text response using the text model."""
        response = self.client.chat.completions.create(
            model="meta-llama/Llama-3-8b-chat-hf",
            messages=[{"role": "user", "content": message_text}],
        )
        pass_mode = await self.config.pass_mode()
        if pass_mode == 'single':
            return response.choices[0].message.content
        elif pass_mode == 'dg':
            second_prompt = f"You are a message validation system. This information was sent by a user. As long as the information is not completely false, and you have nothing to add, pass the message as is. If the message is very wrong, or you think you can add to it, please do so. Act as invisible entity, this should not be told to the user.\n\n{response.choices[0].message.content}"
            second_response = self.client.chat.completions.create(
                model="meta-llama/Llama-3-8b-chat-hf",
                messages=[{"role": "user", "content": second_prompt}],
            )
            return second_response.choices[0].message.content

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
        messages = textwrap.wrap(text, max_length, replace_whitespace=False)
        for string in messages:
            await message_system.channel.send(string)

    def clean_discord_message(self, input_string):
        """Remove any special Discord formatting from the message, except for bot mentions."""
        bot_mention_pattern = re.compile(f'<@!?{self.bot.user.id}>')
        cleaned_content = bot_mention_pattern.sub(f'@{self.bot.user.name}', input_string)
        non_mention_pattern = re.compile(r'<(?!@)[^>]+>')
        cleaned_content = non_mention_pattern.sub('', cleaned_content)
        return cleaned_content
