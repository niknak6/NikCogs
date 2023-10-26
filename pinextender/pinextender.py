# Import the necessary modules
from redbot.core import commands, Config
import discord

# Define the cog class
class PinExtender(commands.Cog):
    """A cog that extends the pin limit of a channel by using a pinned message as a container for other pins."""

    # Initialize the cog with a config attribute
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        # Register the default settings for each channel
        self.config.register_channel(
            extended_pins_message=None, # The message ID of the extended pins message
            extended_pins=[] # A list of tuples containing the message link and description of each extended pin
        )

    # Define a command to create or reset the extended pins message for the current channel
    @commands.command()
    async def pinextender(self, ctx):
        """Create or reset the extended pins message for the current channel."""
        # Check if the channel already has an extended pins message
        extended_pins_message_id = await self.config.channel(ctx.channel).extended_pins_message()
        if extended_pins_message_id is not None:
            # Try to fetch and delete the existing message
            try:
                extended_pins_message = await ctx.channel.fetch_message(extended_pins_message_id)
                await extended_pins_message.delete()
            except discord.NotFound:
                pass
            # Reset the config settings for the channel
            await self.config.channel(ctx.channel).extended_pins_message.set(None)
            await self.config.channel(ctx.channel).extended_pins.clear()
            # Return after deleting the existing message
            return
        # Create a new message with the text "Extended Pins" in bold and underlined
        extended_pins_message = await ctx.send("**__Extended Pins__**")
        # Pin the message to the channel
        await extended_pins_message.pin()
        # Save the message ID to the config
        await self.config.channel(ctx.channel).extended_pins_message.set(extended_pins_message.id)
        # Send a confirmation message to the user
        await ctx.send("The extended pins message has been created or reset for this channel.")

    # Define an event listener for when a message is edited in a channel
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """An event listener for when a message is edited in a channel."""
        # Check if the channel is a text channel and has an extended pins message
        if isinstance(after.channel, discord.TextChannel):
            extended_pins_message_id = await self.config.channel(after.channel).extended_pins_message()
            if extended_pins_message_id is not None:
                # Try to fetch the extended pins message
                try:
                    extended_pins_message = await after.channel.fetch_message(extended_pins_message_id)
                except discord.NotFound:
                    return
                # Check if there are more than 49 pinned messages (excluding the extended pins message)
                pinned_messages = await after.channel.pins()
                if len(pinned_messages) > 49:
                    # Check if the edited message was pinned or unpinned
                    if not before.pinned and after.pinned: # The message was pinned
                        # Get the message link and description of the new pin
                        new_pin_link = after.jump_url 
                        new_pin_description = after.content[:20] + "..." if len(after.content) > 20 else after.content
                        # Add the new pin to the list of extended pins in the config
                        async with self.config.channel(after.channel).extended_pins() as extended_pins:
                            extended_pins.insert(0, (new_pin_link, new_pin_description))
                        # Unpin the new pin from the channel
                        await after.unpin()
                        # Update the content of the extended pins message with the list of extended pins
                        await self.update_extended_pins_content(after.channel) # Use a helper function instead of repeating code.
                    elif before.pinned and not after.pinned: # The message was unpinned
                        # Check if the unpinned message is in the list of extended pins
                        async with self.config.channel(after.channel).extended_pins() as extended_pins:
                            for i, (link, description) in enumerate(extended_pins):
                                if link == after.jump_url: 
                                    # Remove the unpinned message from the list of extended pins
                                    del extended_pins[i]
                                    # Update the content of the extended pins message with the updated list of extended pins
                                    await self.update_extended_pins_content(after.channel) # Use a helper function instead of repeating code.
                                    break

    # Define an event listener for when a reaction is added to a message in a channel
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """An event listener for when a reaction is added to a message in a channel."""
        # Check if the reaction is a wastebasket emoji and the user is not a bot
        if payload.emoji.name == "🗑️" and not payload.member.bot:
            # Get the channel and guild from the payload
            channel = self.bot.get_channel(payload.channel_id)
            guild = self.bot.get_guild(payload.guild_id)
            # Check if the channel is a text channel and has an extended pins message
            if isinstance(channel, discord.TextChannel):
                extended_pins_message_id = await self.config.channel(channel).extended_pins_message()
                if extended_pins_message_id is not None:
                    # Try to fetch the extended pins message
                    try:
                        extended_pins_message = await channel.fetch_message(extended_pins_message_id)
                    except discord.NotFound:
                        return
                    # Get the message that was reacted to
                    try:
                        reacted_message = await channel.fetch_message(payload.message_id)
                    except discord.NotFound:
                        return
                    # Check if the reacted message is in the list of extended pins
                    async with self.config.channel(channel).extended_pins() as extended_pins:
                        for i, (link, description) in enumerate(extended_pins):
                            if link == reacted_message.jump_url: 
                                # Remove the reacted message from the list of extended pins
                                del extended_pins[i]
                                # Update the content of the extended pins message with the updated list of extended pins
                                await self.update_extended_pins_content(channel) # Use a helper function instead of repeating code.
                                # Send a confirmation message to the user
                                await channel.send(f"The message {reacted_message.jump_url} has been removed from the extended pins.", delete_after=10)
                                break

    # Define a helper function to update the content of the extended pins message with the list of extended pins
    async def update_extended_pins_content(self, channel):
        """A helper function to update the content of the extended pins message with the list of extended pins."""
        # Get the extended pins message ID from the config
        extended_pins_message_id = await self.config.channel(channel).extended_pins_message()
        # Try to fetch the extended pins message
        try:
            extended_pins_message = await channel.fetch_message(extended_pins_message_id)
        except discord.NotFound:
            return
        # Get the list of extended pins from the config
        extended_pins = await self.config.channel(channel).extended_pins()
        # Generate the content of the extended pins message with the list of extended pins
        extended_pins_content = "**__Extended Pins__**\n\n"
        for link, description in extended_pins: 
            extended_pins_content += f"- {link} - {description}\n" 
        # Edit the content of the extended pins message
        await extended_pins_message.edit(content=extended_pins_content)

    # Define an event listener for when a raw message is edited in a channel
    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        """An event listener for when a raw message is edited in a channel."""
        # Check if the payload has data and content
        if payload.data and "content" in payload.data:
            # Get the channel and guild from the payload
            channel = self.bot.get_channel(payload.channel_id)
            guild = self.bot.get_guild(payload.guild_id)
            # Check if the channel is a text channel and has an extended pins message
            if isinstance(channel, discord.TextChannel):
                extended_pins_message_id = await self.config.channel(channel).extended_pins_message()
                if extended_pins_message_id is not None:
                    # Check if the edited message is a system message and contains the word "pinned"
                    if payload.data["type"] == 6 and "pinned" in payload.data["content"]:
                        # Try to fetch the edited message
                        try:
                            edited_message = await channel.fetch_message(payload.message_id)
                        except discord.NotFound:
                            return
                        # Add the :pushpin: emoji to the edited message
                        await edited_message.add_reaction("📌")
