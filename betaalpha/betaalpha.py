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

    @commands.command()
    async def testgpt(self, ctx, *, prompt: str):
        """Responds with output from the GPT4FREE model, using the conversation history if enabled."""
        gpt_bot = gpt4free.GPT4FREE(provider="You", is_conversation=self.is_conversation, model="gpt-3.5-turbo", chat_completion=True)
        if self.is_conversation:
            self.history.append(prompt)
            full_prompt = "\n".join(self.history)
            response = await self.bot.loop.run_in_executor(None, gpt_bot.chat, full_prompt)
        else:
            response = await self.bot.loop.run_in_executor(None, gpt_bot.chat, prompt)
        
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
        # Send a message that images are being generated
        message = await ctx.send("Generating...")

        # Start generating images
        img = Imager()
        img_generator = img.generate(prompt, amount=7, stream=False)
        
        # Collect all images into a list
        files = []
        for image_data in img_generator:
            image_bytes = io.BytesIO(image_data)
            image_bytes.seek(0)  # Move to the start of the BytesIO stream
            files.append(discord.File(image_bytes, filename=f"{prompt}.png"))
        
        # Delete the "Generating..." message
        await message.delete()

        # Send a new message with all images
        if files:
            await ctx.send(content="Here are your images:", files=files)
        else:
            await ctx.send("No images were generated.")

def setup(bot):
    bot.add_cog(BetaAlpha(bot))
