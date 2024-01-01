import redbot.core
import google.generativeai as genai
from redbot.core import commands

class Gemini(commands.Cog):
    """A cog that uses the Google Gemini Pro AI API to generate content"""

    def __init__(self, bot):
        self.bot = bot
        # Configure the Gemini API with your API key and product ID
        genai.configure(api_key="AIzaSyCaa3qXhCKf_8gffMFus0winnucnl_KMyk", product_id="advance-sector-409906")
        # Create a GenerativeModel object with the name of the model you want to use
        self.model = genai.GenerativeModel("gemini-pro")

    @commands.command()
    async def gemini(self, ctx):
        """Generate content using the Gemini API"""
        # Get the message content as a prompt
        prompt = ctx.message.content
        # Define the generation config and safety settings parameters
        config = {
            "max_output_tokens": 2048,
            "temperature": 0.9,
            "top_p": 1
        }
        safety_settings = {
            genai.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.HarmBlockThreshold.BLOCK_NONE,
            genai.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.HarmBlockThreshold.BLOCK_NONE,
            genai.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.HarmBlockThreshold.BLOCK_NONE,
            genai.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.HarmBlockThreshold.BLOCK_NONE,
        }
        # Generate content using the Gemini API
        response = self.model.generate_content(prompt, generation_config=config, safety_settings=safety_settings, stream=True)
        # Send the generated content as a response
        for chunk in response:
            await ctx.send(chunk.text)