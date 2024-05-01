from redbot.core import commands
import pytgpt.gpt4free as gpt4free
import asyncio
import threading

class BetaAlpha(commands.Cog):
    """A simple cog named BetaAlpha with a testgpt command."""

    def __init__(self, bot):
        self.bot = bot
        # Initializing GPT4FREE with additional parameters
        self.gpt_bot = gpt4free.GPT4FREE(
            provider="Feedough",
            is_conversation=False,  # Set to False if not a conversational context
            auth="None",  # Replace 'your_auth_token' with your actual authentication token if needed
            max_tokens=600,  # Adjust max_tokens as needed
            model="gpt-3.5-turbo",  # Specify the model you want to use
            chat_completion=False,  # Set to True if you want native auto-contexting
            ignore_working=False,  # Set to True to ignore the working status of the provider
            timeout=20,  # Adjust the timeout as needed
            intro=None,  # Optional introductory prompt
            filepath=None,  # Path to a file for conversation history if needed
            update_file=False,  # Set to True to update the file with new conversations
            proxies={},  # Specify HTTP request proxies if needed
            history_offset=10250,  # Adjust the history offset as needed
            act=None  # Use an awesome prompt key or index if you have one
        )

    def run_in_thread(self, func, *args):
        """Helper function to run a function in a separate thread."""
        result = []
        def wrapper():
            result.append(func(*args))
        thread = threading.Thread(target=wrapper)
        thread.start()
        thread.join()
        return result[0]

    @commands.command()
    async def testgpt(self, ctx, *, prompt: str):
        """Responds with output from the GPT4FREE model."""
        # Run the chat function in a separate thread to avoid event loop issues
        response = await self.bot.loop.run_in_executor(None, self.run_in_thread, self.gpt_bot.chat, prompt, False)
        await ctx.send(response)

def setup(bot):
    bot.add_cog(BetaAlpha(bot))
