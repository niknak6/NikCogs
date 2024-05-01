import io
from redbot.core import commands
import pytgpt.gpt4free as gpt4free
from pytgpt.imager import Imager
import discord

class BetaAlpha(commands.Cog):
    """A simple cog named BetaAlpha with testgpt, gptclear, and generateimg commands."""

    def __init__(self, bot):
        self.bot = bot
        self.is_conversation = True
        self.history = []
        self.gpt_bot = gpt4free.GPT4FREE(provider="Feedough", is_conversation=self.is_conversation)

    @commands.command()
    async def testgpt(self, ctx, *, prompt: str):
        """Responds with output from the GPT4FREE model, using the conversation history if enabled."""
        if self.is_conversation:
            self.history.append(prompt)
            prompt = "\n".join(self.history)
        
        response = await self.bot.loop.run_in_executor(None, self.gpt_bot.chat, prompt)
        await ctx.send(response)
        
        if self.is_conversation:
            self.history.append(response)

    @commands.command()
    async def gptclear(self, ctx):
        """Clears the conversation history without toggling the conversation mode."""
        self.history = []
        await ctx.send("Conversation history has been cleared.")

    @commands.command()
    async def generateimg(self, ctx, *, prompt: str):
        """Generates images based on the provided prompt and sends them in the chat."""
        message = await ctx.send("Generating...")
        img = Imager()
        img_generator = img.generate(prompt, amount=7, stream=False)
        files = [discord.File(io.BytesIO(image_data), filename=f"{prompt}.png") for image_data in img_generator]
        await message.delete()
        if files:
            await ctx.send(content="Here are your images:", files=files)
        else:
            await ctx.send("No images were generated.")

def setup(bot):
    bot.add_cog(BetaAlpha(bot))