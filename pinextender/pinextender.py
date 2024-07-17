from redbot.core import commands, Config
import discord
from typing import List, Tuple, Optional

class PinExtender(commands.Cog):
    """A cog that extends the pin limit of a channel using a pinned message as a container."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_channel(
            extended_pins_message=None,
            extended_pins=[]
        )

    @commands.command()
    @commands.is_owner()
    async def pinextender(self, ctx):
        """Create or reset the extended pins message for the current channel."""
        await self._reset_extended_pins(ctx.channel)
        await ctx.send("The extended pins message has been created or reset for this channel.")

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Handle message edits for extended pins."""
        if not isinstance(after.channel, discord.TextChannel):
            return

        extended_pins_message = await self._get_extended_pins_message(after.channel)
        if not extended_pins_message:
            return

        pinned_messages = await after.channel.pins()
        if len(pinned_messages) <= 49:
            return

        if not before.pinned and after.pinned:
            await self._add_extended_pin(after, extended_pins_message)
        elif before.pinned and not after.pinned:
            await self._remove_extended_pin(after, extended_pins_message)
        elif before.pinned and after.pinned:
            await self._update_extended_pin(after, extended_pins_message)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Handle reaction adds for removing extended pins."""
        if payload.emoji.name != "🗑️" or payload.member.bot:
            return

        channel = self.bot.get_channel(payload.channel_id)
        if not isinstance(channel, discord.TextChannel):
            return

        extended_pins_message = await self._get_extended_pins_message(channel)
        if not extended_pins_message:
            return

        reacted_message = await channel.fetch_message(payload.message_id)
        await self._remove_extended_pin(reacted_message, extended_pins_message)
        await channel.send(f"The message {reacted_message.jump_url} has been removed from the extended pins.")

    @commands.command()
    @commands.is_owner()
    async def remove_extended_pins(self, ctx, keyword: str):
        """Remove extended pins that contain the specified keyword."""
        channel = ctx.channel
        extended_pins_message = await self._get_extended_pins_message(channel)
        if not extended_pins_message:
            await ctx.send("No extended pins message found in this channel.")
            return

        removed_count = 0
        async with self.config.channel(channel).extended_pins() as extended_pins:
            original_count = len(extended_pins)
            extended_pins[:] = [pin for pin in extended_pins if keyword.lower() not in pin[1].lower()]
            removed_count = original_count - len(extended_pins)

        await self._update_extended_pins_embed(channel, extended_pins_message)
        await ctx.send(f"Removed {removed_count} extended pins containing '{keyword}'.")

    async def _reset_extended_pins(self, channel: discord.TextChannel):
        """Reset the extended pins for a channel."""
        async with self.config.channel(channel).all() as channel_data:
            if channel_data["extended_pins_message"]:
                try:
                    message = await channel.fetch_message(channel_data["extended_pins_message"])
                    await message.delete()
                except discord.NotFound:
                    pass

            embed = discord.Embed(title="**__Extended Pins__**", color=discord.Color.blurple())
            new_message = await channel.send(embed=embed)
            await new_message.pin()

            channel_data["extended_pins_message"] = new_message.id
            channel_data["extended_pins"] = []

    async def _get_extended_pins_message(self, channel: discord.TextChannel) -> Optional[discord.Message]:
        """Get the extended pins message for a channel."""
        message_id = await self.config.channel(channel).extended_pins_message()
        if not message_id:
            return None
        try:
            return await channel.fetch_message(message_id)
        except discord.NotFound:
            return None

    async def _add_extended_pin(self, message: discord.Message, extended_pins_message: discord.Message):
        """Add a message to extended pins."""
        new_pin = (message.jump_url, message.content[:20] + "..." if len(message.content) > 20 else message.content)
        async with self.config.channel(message.channel).extended_pins() as extended_pins:
            extended_pins.insert(0, new_pin)
        await self._update_extended_pins_embed(message.channel, extended_pins_message)
        await message.unpin()
        await message.add_reaction("📌")

    async def _remove_extended_pin(self, message: discord.Message, extended_pins_message: discord.Message):
        """Remove a message from extended pins."""
        removed = False
        async with self.config.channel(message.channel).extended_pins() as extended_pins:
            for i, (link, _) in enumerate(extended_pins):
                if link == message.jump_url:
                    del extended_pins[i]
                    removed = True
                    break
        
        if removed:
            await self._update_extended_pins_embed(message.channel, extended_pins_message)
            await message.remove_reaction("📌", self.bot.user)
            await message.remove_reaction("🗑️", message.author)

    async def _update_extended_pin(self, message: discord.Message, extended_pins_message: discord.Message):
        """Update an existing extended pin."""
        async with self.config.channel(message.channel).extended_pins() as extended_pins:
            for i, (link, _) in enumerate(extended_pins):
                if link == message.jump_url:
                    new_description = message.content[:20] + "..." if len(message.content) > 20 else message.content
                    extended_pins[i] = (link, new_description)
                    break
        await self._update_extended_pins_embed(message.channel, extended_pins_message)

    async def _update_extended_pins_embed(self, channel: discord.TextChannel, message: discord.Message):
        """Update the extended pins embed."""
        extended_pins = await self.config.channel(channel).extended_pins()
        embed = discord.Embed(title="**__Extended Pins__**", color=discord.Color.blurple())
        for link, description in extended_pins:
            embed.add_field(name=description, value=link, inline=False)
        await message.edit(embed=embed)