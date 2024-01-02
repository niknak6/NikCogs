# aiemote.py

from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
import google.generativeai as genai
import re
import textwrap

genai.configure(api_key=None) # will be set by the user later

class AIEmote(commands.Cog):
    """A cog that uses Google Generative AI to generate text or image descriptions."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=754069)
        self.config.register_global(api_key=None)
        self.model = None # added this attribute to store the model object

    @commands.is_owner()
    @commands.command()
    async def setapikey(self, ctx: commands.Context, key: str):
        """Sets the Google API key for the cog."""
        await self.config.api_key.set(key)
        genai.configure(api_key=key)
        await ctx.send("API key set successfully.")

    @commands.Cog.listener()
    async def on_message_without_command(self, message):
        """Responds to mentions using Google Generative AI."""
        if self.bot.user.mentioned_in(message): # check if the bot is mentioned
            args = message.content.split() # split the message by spaces
            if len(args) > 1: # check if there is something after the mention
                args.pop(0) # remove the mention from the list
                input_text = " ".join(args) # join the rest of the message with spaces
                # the input_text is the message appended to the mention
                # you can use it as the input for the Google API
                input_messages = [{"role": "user", "content": input_text}]
                response = await self.ask_gpt(input_messages)
                # added this block to split the response into smaller chunks
                chunks = textwrap.wrap(response, width=1990) # wrap the response into lines of 1990 characters each
                for chunk in chunks:
                    await message.channel.send(chunk) # send each chunk as a separate message
            else:
                # if there is nothing after the mention, you can send a default message
                await message.channel.send("Hello, I am a bot that uses Google Generative AI to generate text or image descriptions. You can mention me with some input text and I will try to respond.")

    async def ask_gpt(self, input_messages, retry_attempts=3, delay=1):
        # added this block to create or load the model object with the history
        if not self.model: # check if the model object is None
            api_key = await self.config.api_key() # get the api key from the config
            if not api_key: # check if the api key is None
                print("No API key set for the cog.")
                return "No API key set for the cog."
            history = [] # an empty list for the history
            self.model = genai.GenerativeModel(model_name="gemini-pro", history=history) # create the model object with the history
        for attempt in range(retry_attempts):
            try:
                input_content = genai.ModelContent(role="user", parts=[genai.ModelContentPart(text=input_messages[0]['content'])]) # create the input content from the first message
                response_content = self.model.generate_content(input_content) # generate the response content from the model
                response_text = response_content.parts[0].text # get the text of the response
                return response_text
            except Exception as e:
                print(f"Error in ask_gpt with Google AI: {e}")
                if attempt < retry_attempts - 1:
                    await asyncio.sleep(delay)
                    continue
                return "I'm sorry, I couldn't process that due to an error in the Google service."