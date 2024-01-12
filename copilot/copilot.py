import discord # add this line
import json
import os
import re # add this line
from redbot.core import commands
from re_edge_gpt import Chatbot, ImageGenAsync, ConversationStyle


class Copilot(commands.Cog):
    """A cog that uses ReEdgeGPT to chat and generate images"""

    def __init__(self, bot):
        self.bot = bot
        self.chatbot = None
        self.imagegen = None
        self.style = ConversationStyle.balanced # default style

    async def create_chatbot(self):
        """Creates a chatbot instance using the cookies file"""
        cookies = json.loads(open(os.path.join(os.getcwd(), "/root/.local/share/Red-DiscordBot/data/redbot/cogs/CogManager/cogs/copilot/bing_cookies.json"), encoding="utf-8").read())
        self.chatbot = await Chatbot.create(cookies=cookies)

    async def create_imagegen(self):
        """Creates an image generator instance using the cookies file"""
        # use the same path as the bing_cookies.json file
        auth_cookie = open(os.path.join(os.getcwd(), "/root/.local/share/Red-DiscordBot/data/redbot/cogs/CogManager/cogs/copilot/bing_cookies.txt"), "r+").read()
        self.imagegen = ImageGenAsync(auth_cookie=auth_cookie)

    # disable the copilotdraw command
    @commands.command(name="copilotdraw", enabled=False)
    async def copilot_draw(self, ctx, *, prompt: str):
        """Generate an image using the ReEdgeGPT image generator"""
        if self.imagegen is None:
            await self.create_imagegen()
        image_list = await self.imagegen.get_images(prompt)
        await ctx.send(image_list[0])

    @commands.group()
    async def copilotstyle(self, ctx):
        """Change the conversation style of the ReEdgeGPT chatbot"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    @copilotstyle.command()
    async def creative(self, ctx):
        """Set the conversation style to creative"""
        self.style = ConversationStyle.creative
        await ctx.send("Conversation style changed to creative. 🎨")

    @copilotstyle.command()
    async def balanced(self, ctx):
        """Set the conversation style to balanced"""
        self.style = ConversationStyle.balanced
        await ctx.send("Conversation style changed to balanced. 🧘")

    @copilotstyle.command()
    async def precise(self, ctx):
        """Set the conversation style to precise"""
        self.style = ConversationStyle.precise
        await ctx.send("Conversation style changed to precise. 🔬")

    # add the reset command
    @commands.command(name="copilotreset")
    async def copilot_reset(self, ctx):
        """Reset the conversation with the ReEdgeGPT chatbot"""
        if self.chatbot is None:
            await self.create_chatbot()
        try:
            await self.chatbot.reset()
            await ctx.send("Conversation reset successfully. 😊")
        except Exception as error:
            await ctx.send(f"An error occurred while resetting the conversation: {error}")

    # add the listener function
    @commands.Cog.listener()
    async def on_message(self, message):
        """Check if the bot is mentioned or replied to in any message"""
        if message.author == self.bot.user:
            return # ignore the bot's own messages
        if message.reference and message.reference.resolved.author == self.bot.user:
            # the message is a reply to the bot
            await message.add_reaction("\U0001f916") # add the robot emoji
            async with message.channel.typing(): # start typing
                await self.chat(message) # chat with the user
        elif self.bot.user in message.mentions:
            # the message mentions the bot
            if re.search("(generate picture|generate image)", message.content, re.IGNORECASE): # use re.search with re.IGNORECASE
                # the message contains the keywords
                await message.add_reaction("\U0001f3a8") # add the art emoji
                async with message.channel.typing(): # start typing
                    await self.copilot_draw(message) # generate an image
            else:
                # the message does not contain the keywords
                await message.add_reaction("\U0001f916") # add the robot emoji
                async with message.channel.typing(): # start typing
                    await self.chat(message) # chat with the user

    async def chat(self, message):
        """Chat with the ReEdgeGPT chatbot"""
        if self.chatbot is None:
            await self.create_chatbot()
        response = await self.chatbot.ask(message.clean_content, conversation_style=self.style)
        # split the response into chunks of 1999 characters or less
        chunks = [response["item"]["messages"][1]["adaptiveCards"][0]["body"][0]["text"][i:i+1999] for i in range(0, len(response["item"]["messages"][1]["adaptiveCards"][0]["body"][0]["text"]), 1999)]
        # send each chunk to the channel
        for chunk in chunks:
            await message.channel.send(chunk)

    async def copilot_draw(self, message):
        """Generate an image using the ReEdgeGPT image generator"""
        if self.imagegen is None:
            await self.create_imagegen()
        prompt = message.clean_content # get the clean message content
        prompt = prompt.replace("generate picture", "", 1) # remove the first occurrence of the keyword
        prompt = prompt.replace("generate image", "", 1) # remove the first occurrence of the keyword
        prompt = prompt.strip() # remove any leading or trailing whitespace
        image_list = await self.imagegen.get_images(prompt) # get the images for the prompt
        await message.channel.send(image_list[0]) # send the first image to the channel

# change the command prefix to only mention
# add the intents argument
intents = discord.Intents.all() # or any other intents you want
client = commands.Bot(command_prefix=commands.when_mentioned_or(""), intents=intents)