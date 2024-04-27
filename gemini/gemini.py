import re
import discord
from redbot.core import commands, Config
import textwrap
from together import Together
import io
import base64

class Gemini(commands.Cog):
    """A Discord bot that uses Together.ai API to interact with users in text format."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.default_generation_params = {
            "max_tokens": None,
            "temperature": 0.7,
            "top_p": 0.7,
            "top_k": 50,
            "repetition_penalty": 1,
            "prompt": "Your name is Cashew. You are Treachery's AI Assistant. Message length is important. Your responses should be short, concise, and direct."
        }
        self.config.register_global(
            together_ai_key=None,
            max_history=20,
            context_mode='user',
            **self.default_generation_params
        )
        self.client = None
        self.message_history = {}
        self.bot.loop.create_task(self.initialize_models())

    async def initialize_models(self):
        api_key = await self.config.together_ai_key()
        if api_key:
            try:
                self.client = Together(api_key=api_key)
            except Exception as e:
                await self.bot.send_to_owners(f"Failed to initialize Together.ai client: {str(e)}")
        else:
            await self.bot.send_to_owners("Together.ai API key not set. Please use the `setapikey` command to set the API key.")

    @commands.command()
    @commands.is_owner()
    async def setapikey(self, ctx, key: str):
        await self.config.together_ai_key.set(key)
        await ctx.send("Together.ai API key set successfully.")

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
        await self.config.context_mode.set(mode)
        await ctx.send(f"Context mode set to {mode}.")

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

    async def is_bot_shared_message(self, message):
        referenced_message = await message.channel.fetch_message(message.reference.message_id)
        return referenced_message.author == self.bot.user and referenced_message.content.startswith("Shared by")

    async def reset_history(self, message):
        context_mode = await self.config.context_mode()
        context_id = message.channel.id if context_mode == 'channel' else message.author.id
        self.message_history.pop(context_id, None)
        await message.channel.send(f"🤖 History Reset for {context_mode}: {message.channel.name if context_mode == 'channel' else message.author.name}")

    async def generate_image(self, message, cleaned_text):
        async with message.channel.typing():
            await message.add_reaction('🎨')
            prompt = cleaned_text[8:].strip()
            response = self.client.images.generate(
                prompt=prompt, model="stabilityai/stable-diffusion-xl-base-1.0",
                steps=20, n=1,
            )
            image_data = response.data[0].b64_json
            await message.channel.send(file=discord.File(io.BytesIO(base64.b64decode(image_data)), filename="generated_image.png"))

    async def generate_response(self, message, cleaned_text):
        async with message.channel.typing():
            await message.add_reaction('💬')
            context_mode = await self.config.context_mode()
            context_id = message.channel.id if context_mode == 'channel' else message.author.id
            max_history = await self.config.max_history()

            if max_history > 0 and message.reference:
                referenced_message = await message.channel.fetch_message(message.reference.message_id)
                referenced_text = self.clean_discord_message(referenced_message.content)
                await self.update_message_history(context_id, referenced_text)

            await self.update_message_history(context_id, cleaned_text)
            message_history = self.get_formatted_message_history(context_id)
            response_text = await self.generate_response_with_text(message_history if max_history > 0 else cleaned_text)
            await self.update_message_history(context_id, response_text)

        await self.send_response(message, response_text)

    async def generate_response_with_text(self, message_text):
        generation_params = {
            key: await self.config.get_raw(key) for key in self.default_generation_params
        }
        prompt = generation_params.pop("prompt", "")
        message_text = f"{prompt}\n{message_text}"
        response = self.client.chat.completions.create(
            model="mistralai/Mistral-7B-Instruct-v0.2",
            messages=[{"role": "user", "content": message_text}],
            **generation_params
        )
        return response.choices[0].message.content

    async def update_message_history(self, context_id, text):
        if context_id not in self.message_history:
            self.message_history[context_id] = []
        self.message_history[context_id].append(text)
        max_history = await self.config.max_history()
        if len(self.message_history[context_id]) > max_history:
            self.message_history[context_id].pop(0)

    def get_formatted_message_history(self, context_id):
        return '\n\n'.join(self.message_history.get(context_id, []))

    async def send_response(self, message, response_text, max_length=1999):
        for string in textwrap.wrap(response_text, max_length, replace_whitespace=False):
            await message.channel.send(string)

    def clean_discord_message(self, input_string):
        bot_mention_pattern = re.compile(f'<@!?{self.bot.user.id}>')
        cleaned_content = bot_mention_pattern.sub('', input_string).strip()
        non_mention_pattern = re.compile(r'<(?!@)[^>]+>')
        return non_mention_pattern.sub('', cleaned_content)