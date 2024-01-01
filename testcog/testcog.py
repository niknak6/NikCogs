from redbot.core import commands
import google.generativeai as genai
import os

genai.configure(
    api_key=os.environ['AIzaSyCaa3qXhCKf_8gffMFus0winnucnl_KMyk'])
model = genai.GenerativeModel(
    model_name='gemini-pro')


class TestCog(commands.Cog):
    """A cog that tests the google-generativeai module"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def test(self, ctx, prompt: str):
        """Generates content based on a given prompt"""
        response = model.generate_content(prompt)
        await ctx.send(response.text)