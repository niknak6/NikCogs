from redbot.core import commands
from re_edge_gpt import Chatbot, ImageGenAsync
import json


class Copilot(commands.Cog):
    """A cog that uses ReEdgeGPT to chat and generate images"""

    def __init__(self, bot):
        self.bot = bot
        self.chatbot = None
        self.imagegen = None

    async def create_chatbot(self):
        """Creates a chatbot instance using the cookies file"""
        cookies = json.loads(open("/bing_cookies.json", encoding="utf-8").read())
        self.chatbot = await Chatbot.create(cookies=cookies)

    async def create_imagegen(self):
        """Creates an image generator instance using the cookies file"""
        auth_cookie = open("bing_cookies.txt", "r+").read()
        self.imagegen = ImageGenAsync(auth_cookie=auth_cookie)

    @commands.command()
    async def chat(self, ctx, *, message: str):
        """Chat with the ReEdgeGPT chatbot"""
        if self.chatbot is None:
            await self.create_chatbot()
        response = await self.chatbot.ask(message)
        await ctx.send(response["item"]["messages"][1]["adaptiveCards"][0]["body"][0]["text"])

    @commands.command(name="copilotdraw")
    async def copilot_draw(self, ctx, *, prompt: str):
        """Generate an image using the ReEdgeGPT image generator"""
        if self.imagegen is None:
            await self.create_imagegen()
        image_list = await self.imagegen.get_images(prompt)
        await ctx.send(image_list[0])