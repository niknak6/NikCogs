from redbot.core import commands, Config
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

        with SyncChatGPT(session_token=session_token) as chatgpt:
            conversation = chatgpt.create_new_conversation()
            for message in conversation.chat(query):
                await ctx.send(message["content"])

    @commands.command()
    async def betaalphasession(self, ctx, *, token: str):
        """Set the session token for ChatGPT queries."""
        await self.config.session_token.set(token)
        await ctx.send("Session token updated successfully.")

def setup(bot):
    bot.add_cog(BetaAlpha(bot))
