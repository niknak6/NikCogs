import discord
from redbot.core import commands

class PinFill(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def pinfill(self, ctx):
        # Create a variable to store the current number
        number = 1
        # Create a loop that runs until the channel's pins are full or a pin cannot be added
        while True:
            # Send a message with the current number and store it in a variable
            message = await ctx.send(number)
            # Try to pin the message using the pin method of the message object
            try:
                await message.pin()
            except discord.HTTPException:
                # If it fails, break the loop and send an error message
                await ctx.send("I can't pin any more messages in this channel.")
                break
            # Increment the current number by 1
            number += 1

    @commands.command()
    async def unpinfill(self, ctx):
        # Get a list of all pinned messages in the channel
        pins = await ctx.channel.pins()
        # Iterate over the pinned messages and unpin them
        for pin in pins:
            await pin.unpin()
        # Send a confirmation message
        await ctx.send("I have removed all pins from this channel.")

def setup(bot):
    bot.add_cog(PinFill(bot))
