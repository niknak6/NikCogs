# Import the necessary modules
from redbot.core import commands, checks, Config # Added Config module
import discord
import urllib.parse # Added this module to parse URLs

# Define a custom function to validate URLs
def is_url(string):
    # Try to parse the string as a URL
    result = urllib.parse.urlparse(string)
    # Return True if the string has a valid scheme and netloc, False otherwise
    return result.scheme and result.netloc

# Define the cog class
class PinExtender(commands.Cog):
    """A cog that extends the pin limit of a channel by using a pinned message as a container for other pins."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890) # Get a Config instance for this cog
        self.config.register_channel(extended_pins=None) # Register the default value for extended_pins setting for each channel

    @commands.command()
    @checks.mod_or_permissions(manage_messages=True)
    async def pinextender(self, ctx):
        """Creates an extended pins message in the current channel and pins it."""
        # Check if the channel already has an extended pins message
        if await self.config.channel(ctx.channel).extended_pins(): # Use Config to get the value of extended_pins setting for this channel
            await ctx.send("This channel already has an extended pins message.")
            return

        # Create a new message with the text "Extended Pins" in bold and underlined
        message = await ctx.send("**__Extended Pins__**")

        # Pin the message to the channel
        await message.pin()

        # Store the message ID in the config setting
        await self.config.channel(ctx.channel).extended_pins.set(message.id) # Use Config to set the value of extended_pins setting for this channel

        # Send a confirmation message
        await ctx.send("Created and pinned an extended pins message for this channel.")

    @commands.Cog.listener()
    async def on_guild_channel_pins_update(self, channel, last_pin):
        """A listener that triggers when a channel's pins are updated."""
        # Check if the channel has an extended pins message and if it is at 49/50 pins
        if await self.config.channel(channel).extended_pins() and len(await channel.pins()) == 50: # Use Config to get the value of extended_pins setting for this channel
            # Get the extended pins message object
            extended_pins_message = await channel.fetch_message(await self.config.channel(channel).extended_pins()) # Use Config to get the value of extended_pins setting for this channel

            # Get the list of pinned messages in the channel
            pinned_messages = await channel.pins()

            # Get the last pinned message object from the list
            last_pinned_message = pinned_messages[0]

            # Get the message link and description of the last pinned message
            message_link = last_pinned_message.jump_url
            # Modified this line to check if the message content is only a valid URL or if it has any attachments or embeds, and use the :paperclip: emoji accordingly
            message_description = ":paperclip:" if (is_url(last_pinned_message.content) or last_pinned_message.attachments or last_pinned_message.embeds) else (last_pinned_message.content[:20] + "..." if len(last_pinned_message.content) > 20 else last_pinned_message.content)

            # Add the message link and description to the bottom of the extended pins message
            await extended_pins_message.edit(content=f"{extended_pins_message.content}\n{message_link} - {message_description}")

            # Remove the pin from the last pinned message
            await last_pinned_message.unpin()

            # Send a notification message to the channel
            await channel.send(f"Added {message_link} to the extended pins message and removed its pin.")
