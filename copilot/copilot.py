import os
import re
import aiohttp
import discord
from redbot.core import commands, Config
from sydney import SydneyClient

class Copilot(commands.Cog):
    """A Discord bot that uses Sydney.py to interact with users in text and image formats."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        # Register global settings for the bot
        self.config.register_global(
            sydney_cookies=None,
            max_history=20,
            context_mode='user', # Determines whether the context is user-specific or channel-specific
        )
        self.sydney_client = None
        self.message_history = {}

        # Initialize the Sydney Client asynchronously
        self.bot.loop.create_task(self.initialize_sydney_client())

    async def initialize_sydney_client(self):
        """Asynchronously initialize the Sydney Client with the configured settings."""
        cookies = await self.config.sydney_cookies()
        if cookies:
            os.environ["BING_COOKIES"] = cookies
            self.sydney_client = SydneyClient()
            await self.sydney_client.start_conversation()
        else:
            print("No cookies found. Please set the cookies using the setapikey command.")

    @commands.command()
    @commands.is_owner()
    async def setapikey(self, ctx, cookies: str):
        """Set the cookies for the Sydney Client."""
        await self.config.sydney_cookies.set(cookies)
        os.environ["BING_COOKIES"] = cookies
        await ctx.send("Cookies set successfully.")

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
        if message.author == self.bot.user or not self.sydney_client:
            return
        if self.bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
            cleaned_text = self.clean_discord_message(message.content)

            async with message.channel.typing():
                if message.attachments:
                    # Handle image messages
                    for attachment in message.attachments:
                        if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                            await message.add_reaction('🎨')

                            async with aiohttp.ClientSession() as session:
                                async with session.get(attachment.url) as resp:
                                    if resp.status != 200:
                                        await message.channel.send('Unable to download the image.')
                                        return
                                    image_data = await resp.read()
                                    response_text = await self.generate_response_with_image_and_text(image_data, cleaned_text)
                                    await self.split_and_send_messages(message, response_text, 1700)
                                    return
                else:
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
        """Generate a text response using Sydney Client."""
        async with SydneyClient() as sydney:
            response = await sydney.ask(message_text)
            return response

    async def generate_response_with_image_and_text(self, image_data, text):
        """Generate a text response using Sydney Client with an image attachment."""
        async with SydneyClient() as sydney:
            response = await sydney.ask(text, attachment=image_data)
            return response

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