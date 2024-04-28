from redbot.core import commands, Config
import asyncio
from re_gpt import SyncChatGPT

class BetaAlpha(commands.Cog):
    """A simple cog to interact with ChatGPT using re_gpt library."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        self.config.register_global(session_token=None)

    @commands.command()
    async def betaalpha(self, ctx, *, query: str):
        """Query ChatGPT with a given prompt."""
        session_token = await self.config.session_token()
        if not session_token:
            await ctx.send("Session token is not set. Use `!betaalphasession` to set the token.")
            return

        # Run the synchronous code in an executor to prevent blocking the event loop
        try:
            response = await self.bot.loop.run_in_executor(None, self.query_chatgpt, session_token, query)
            await ctx.send(response)
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    def query_chatgpt(self, session_token, query):
        """Handles querying ChatGPT synchronously."""
        with SyncChatGPT(session_token=session_token) as chatgpt:
            conversation = chatgpt.create_new_conversation()
            responses = []
            for message in conversation.chat(query):
                responses.append(message["content"])
            return "\n".join(responses)

    @commands.command()
    async def betaalphasession(self, ctx, *, token: str):
        """Set the session token for ChatGPT queries."""
        await self.config.session_token.set(token)
        await ctx.send("Session token updated successfully.")

def setup(bot):
    bot.add_cog(BetaAlpha(bot))
