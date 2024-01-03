import os
import re

import aiohttp
import discord
import google.generativeai as genai
from redbot.core import commands, Config

class Gemini(commands.Cog):
    """Discord bot that leverages the power of Google's Gemini-Pro API to interact with users in both text and image formats."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(
            google_ai_key=None,
            max_history=12,
            context_mode='user' # This is the global setting for context mode
        )
        self.text_model = None
        self.image_model = None
        self.message_history = {}

    @commands.command()
    @commands.is_owner()
    async def setapikey(self, ctx, key: str):
        await self.config.google_ai_key.set(key)
        genai.configure(api_key=key)
        self.text_model = genai.GenerativeModel(model_name="gemini-pro", generation_config={"temperature": 0.9, "top_p": 1, "top_k": 1, "max_output_tokens": 512}, safety_settings=[{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}])
        self.image_model = genai.GenerativeModel(model_name="gemini-pro-vision", generation_config={"temperature": 0.4, "top_p": 1, "top_k": 32, "max_output_tokens": 512}, safety_settings=[{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}])
        await ctx.send("API key set successfully.")

    @commands.command()
    @commands.is_owner()
    async def maxhistory(self, ctx, number: int):
        if number < 0:
            await ctx.send("The number must be positive or zero.")
            return
        await self.config.max_history.set(number)
        await ctx.send(f"Max history set to {number}.")

    @commands.command()
    @commands.is_owner()
    async def contextmode(self, ctx, mode: str):
        if mode not in ['user', 'channel']:
            await ctx.send("The mode must be either 'user' or 'channel'.")
            return
        await self.config.context_mode.set(mode) # This updates the global setting for context mode
        await ctx.send(f"Context mode set to {mode}.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if self.bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
            cleaned_text = self.clean_discord_message(message.content)

            async with message.channel.typing():
                if message.attachments:
                    print("New Image Message FROM:" + str(message.author.id) + ": " + cleaned_text)
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
                    print("New Message FROM:" + str(message.author.id) + ": " + cleaned_text)
                    if "RESET" in cleaned_text:
                        if message.author.id in self.message_history:
                            del self.message_history[message.author.id]
                        await message.channel.send("🤖 History Reset for user: " + str(message.author.name))
                        return
                    await message.add_reaction('💬')

                    context_mode = await self.config.context_mode() # This gets the global setting for context mode
                    context_id = message.channel.id if context_mode == 'channel' else message.author.id # This determines the context id based on the context mode

                    max_history = await self.config.max_history()
                    if max_history == 0:
                        response_text = await self.generate_response_with_text(cleaned_text)
                        await self.split_and_send_messages(message, response_text, 1700)
                        return
                    await self.update_message_history(context_id, cleaned_text)
                    response_text = await self.generate_response_with_text(self.get_formatted_message_history(context_id))
                    await self.update_message_history(context_id, response_text)
                    await self.split_and_send_messages(message, response_text, 1700)

    async def generate_response_with_text(self, message_text):
        prompt_parts = [message_text]
        print("Got textPrompt: " + message_text)
        response = self.text_model.generate_content(prompt_parts)
        if(response._error):
            return "❌" +  str(response._error)
        return response.text

    async def generate_response_with_image_and_text(self, image_data, text):
        image_parts = [{"mime_type": "image/jpeg", "data": image_data}]
        prompt_parts = [image_parts[0], f"\n{text if text else 'What is this a picture of?'}"]
        response = self.image_model.generate_content(prompt_parts)
        if(response._error):
            return "❌" +  str(response._error)
        return response.text

    async def update_message_history(self, context_id, text):
        if context_id in self.message_history:
            self.message_history[context_id].append(text)
            max_history = await self.config.max_history()
            if len(self.message_history[context_id]) > max_history:
                self.message_history[context_id].pop(0)
        else:
            self.message_history[context_id] = [text]

    def get_formatted_message_history(self, context_id):
        if context_id in self.message_history:
            return '\n\n'.join(self.message_history[context_id])
        else:
            return "No messages found for this user."

    async def split_and_send_messages(self, message_system, text, max_length):
        messages = []
        for i in range(0, len(text), max_length):
            sub_message = text[i:i+max_length]
            messages.append(sub_message)
        for string in messages:
            await message_system.channel.send(string)

    def clean_discord_message(self, input_string):
        bracket_pattern = re.compile(r'<[^>]+>')
        cleaned_content = bracket_pattern.sub('', input_string)
        return cleaned_content