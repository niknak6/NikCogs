import re
import json
import aiohttp
import discord
from pathlib import Path
from redbot.core import commands, Config
from re_edge_gpt import Chatbot, ConversationStyle

class Copilot(commands.Cog):
    """A Discord bot that uses Bing's AI API to interact with users in text and image formats."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        # Register global settings for the bot
        self.config.register_global(
            max_history=20,
            context_mode='user', # Determines whether the context is user-specific or channel-specific
        )
        self.chatbot = None
        self.message_history = {}

        # Initialize the chatbot asynchronously
        self.bot.loop.create_task(self.initialize_chatbot())

    async def initialize_chatbot(self):
        """Asynchronously initialize the chatbot with the configured settings."""
        try:
            # Load cookies from the bing_cookies.json file
            cookies_path = Path(__file__).parent / 'bing_cookies.json'
            with cookies_path.open('r', encoding='utf-8') as f:
                cookies = json.load(f)
            # Initialize the chatbot with the loaded cookies
            self.chatbot = await Chatbot.create(cookies=cookies)
        except Exception as e:
            print(f"Failed to initialize chatbot: {e}")

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
                # Handle text messages
                if "RESET" in cleaned_text:
                    if message.author.id in self.message_history:
                        del self.message_history[message.author.id]
                    context_mode = await self.config.context_mode()
                    context_id = message.channel.id if context_mode == 'channel' else message.author.id
                    await message.channel.send(f"🤖 History Reset for {context_mode}: {message.channel.name if context_mode == 'channel' else message.author.name}")
                    return
                await message.add_reaction('💬')

                context_mode = await self.config.context_mode()
                context_id = message.channel.id if context_mode == 'channel' else message.author.id

                max_history = await self.config.max_history()
                if max_history == 0:
                    response_text = await self.generate_response_with_text(cleaned_text)
                    await self.split_and_send_messages(message, response_text, 1700)
                    return
                if message.reference:
                    referenced_message = await message.channel.fetch_message(message.reference.message_id)
                    referenced_text = self.clean_discord_message(referenced_message.content)
                    await self.update_message_history(context_id, referenced_text)
                await self.update_message_history(context_id, cleaned_text)
                response_text = await self.generate_response_with_text(self.get_formatted_message_history(context_id))
                await self.update_message_history(context_id, response_text)
                await self.split_and_send_messages(message, response_text, 1700)

    async def generate_response_with_text(self, message_text):
        """Generate a text response using the Bing AI API."""
        response = await self.chatbot.ask(
            prompt=message_text,
            conversation_style=ConversationStyle.balanced,
            simplify_response=True
        )
        # Extract the response text from the response object
        response_text = response["item"]["messages"][1]["adaptiveCards"][0]["body"][0]["text"]
        return response_text

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

    async def split_and_send_messages(self, message_system, text, max_length):
        """Split the response into multiple messages if it exceeds the maximum length."""
        messages = []
        for i in range(0, len(text), max_length):
            sub_message = text[i:i+max_length]
            messages.append(sub_message)
        for string in messages:
            await message_system.channel.send(string)

    def clean_discord_message(self, input_string):
        """Remove any special Discord formatting from the message."""
        bracket_pattern = re.compile(r'<[^>]+>')
        cleaned_content = bracket_pattern.sub('', input_string)
        return cleaned_content