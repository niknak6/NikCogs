from redbot.core import commands
import pytgpt.gpt4free as gpt4free

class BetaAlpha(commands.Cog):
    """A simple cog named BetaAlpha with a testgpt and gptclear commands."""

    def __init__(self, bot):
        self.bot = bot
        self.is_conversation = False
        self.history = []

    @commands.command()
    async def testgpt(self, ctx, *, prompt: str):
        """Responds with output from the GPT4FREE model, using the conversation history if enabled."""
        gpt_bot = gpt4free.GPT4FREE(provider="Feedough", is_conversation=self.is_conversation)
        if self.is_conversation:
            # Append the new prompt to history
            self.history.append(prompt)
            # Join the history into a single string to pass as context
            full_prompt = "\n".join(self.history)
            response = await self.bot.loop.run_in_executor(None, gpt_bot.chat, full_prompt)
        else:
            response = await self.bot.loop.run_in_executor(None, gpt_bot.chat, prompt)
        
        await ctx.send(response)
        if self.is_conversation:
            # Append the response to history
            self.history.append(response)

    @commands.command()
    async def gptclear(self, ctx):
        """Clears the conversation history without toggling the conversation mode."""
        self.history = []  # Clear the history
        await ctx.send("Conversation history has been cleared.")

def setup(bot):
    bot.add_cog(BetaAlpha(bot))
