from redbot.core import commands
import discord

class TreacheryNews(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def deleteforumpost(self, ctx, thread_id: int):
        """Delete a forum post by its thread ID."""
        guild = ctx.guild
        thread = discord.utils.get(guild.threads, id=thread_id)
        if thread is not None:
            await thread.delete()
            await ctx.send(f"Deleted thread with ID {thread_id}.")
        else:
            await ctx.send(f"No thread found with ID {thread_id}.")