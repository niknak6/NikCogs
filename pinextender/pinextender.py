# Import the necessary modules
from redbot.core import commands, checks, Config
import discord
import urllib.parse
import logging
import validators # Added this module to validate URLs
from discord.utils import escape_markdown # Added this

# Define the cog class
class PinExtender(commands.Cog):
    """A cog that extends the pin limit of a channel by using a pinned message as a container for other pins."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890) # Get a Config instance for this cog
        # Register the default values for extended_pins and message_ids settings for each channel
        self.config.register_channel(extended_pins=None, message_ids=[]) 

    @commands.command()
    @checks.mod_or_permissions(manage_messages=True)
    async def pinextender(self, ctx):
        """Creates an extended pins message in the current channel and pins it."""
        # Check if the channel already has an extended pins message
        if await self.config.channel(ctx.channel).extended_pins():
            await ctx.send("This channel already has an extended pins message.")
            return

        # Create a new message with the text "Extended Pins" in bold and underlined
        message = await ctx.send("**__Extended Pins__**")

        # Pin the message to the channel
        await message.pin()

        # Store the message ID in the config setting
        await self.config.channel(ctx.channel).extended_pins.set(message.id)

        # Send a confirmation message
        await ctx.send("Created and pinned an extended pins message for this channel.")

    @commands.Cog.listener()
    async def on_guild_channel_pins_update(self, channel, last_pin):
        """A listener that triggers when a channel's pins are updated."""
        try: # Added a try-except block to handle any exceptions
            # Get the list of pinned messages in the channel
            pinned_messages = await channel.pins()

            # Check if there are any pinned messages in the channel
            if pinned_messages:
                # Get the last pinned message object from the list by comparing the created_at attribute with the last_pin parameter
                last_pinned_message = next((message for message in pinned_messages if message.created_at == last_pin), None) # Simplified this line using a generator expression and next function

                # Check if the last pinned message is not None and is not the extended pins message for the channel
                if last_pinned_message and await self.config.channel(channel).extended_pins() != last_pinned_message.id:
                    # Get the built-in pin confirmation message object by fetching the latest system message in the channel
                    pin_confirmation_message = await channel.fetch_message(channel.last_message_id)

                    # React to the built-in pin confirmation message with a :pushpin: emoji to indicate that it was added to the extended pins message
                    await pin_confirmation_message.add_reaction("\U0001F4CC")

                    # Get the extended pins message object
                    extended_pins_message = await channel.fetch_message(await self.config.channel(channel).extended_pins())

                    # Get the message link and description of the last pinned message
                    message_link = last_pinned_message.jump_url

                    # Check if the message content is only a valid URL or if it has any attachments or embeds, and use the :paperclip: emoji accordingly
                    if validators.url(last_pinned_message.content) or last_pinned_message.attachments or last_pinned_message.embeds: 
                        message_description = ":paperclip:"
                    else:
                        # Escape any markdown characters in the message content
                        escaped_content = escape_markdown(last_pinned_message.content)
                        # Truncate the content to 20 characters and add ellipsis if it is longer, otherwise keep it as it is
                        message_description = f"{escaped_content[:20]}..." if len(escaped_content) > 20 else escaped_content

                    # Create an embed with the author, timestamp, image, and description of the last pinned message
                    embed = discord.Embed(
                        title=message_description,
                        url=message_link,
                        timestamp=last_pinned_message.created_at,
                        color=discord.Color.blurple()
                    )
                    embed.set_author(name=last_pinned_message.author.display_name, icon_url=last_pinned_message.author.avatar_url)
                    if last_pinned_message.attachments:
                        embed.set_image(url=last_pinned_message.attachments[0].url)
                    elif last_pinned_message.embeds:
                        embed.set_image(url=last_pinned_message.embeds[0].thumbnail.url)

                    # Add the embed to the bottom of the extended pins message using the embeds parameter
                    await extended_pins_message.edit(embeds=extended_pins_message.embeds + [embed])

                    # Remove the pin from the last pinned message
                    await last_pinned_message.unpin()

                    # React to each embed in the extended pins message with a :pushpin: emoji to allow unpinning them later
                    await extended_pins_message.add_reaction("\U0001F4CC")

                    # Get the list of message IDs for each embed in the extended pins message from the config setting
                    message_ids = await self.config.channel(channel).message_ids()

                    # Append the last pinned message ID to the list
                    message_ids.append(last_pinned_message.id)

                    # Store the updated list in the config setting
                    await self.config.channel(channel).message_ids.set(message_ids)

                    # Log the event
                    logging.info(f"Added {message_link} - {message_description} to the extended pins message in {channel.name}")
        except Exception as e: # Catch any exception and log it
            logging.error(f"An error occurred in on_guild_channel_pins_update: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """A listener that triggers whenever a reaction is added to a message."""
        try: # Added a try-except block to handle any exceptions
            # Check if the reaction is from a user (not a bot) and is a :pushpin: emoji
            if not payload.user_id == self.bot.user.id and payload.emoji.name == "\U0001F4CC":
                # Get the channel, message, and user objects from the payload
                channel = self.bot.get_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)
                user = self.bot.get_user(payload.user_id)

                # Check if the message is an extended pins message for the channel
                if await self.config.channel(channel).extended_pins() == message.id:
                    # Get the embeds from the message
                    embeds = message.embeds

                    # Check if there are any embeds in the message
                    if embeds:
                        # Get the list of message IDs for each embed in the extended pins message from the config setting
                        message_ids = await self.config.channel(channel).message_ids()

                        # Check if the list exists and has the same length as the embeds
                        if message_ids and len(message_ids) == len(embeds):
                            # Get the URL of the last embed that contains the message link
                            message_link_url = embeds[-1].url 
                            # Parse the URL and get the ID from it
                            message_link_id = message_link_url.split("/")[-1]

                            # Get the index of the embed that corresponds to the reaction by finding the position of the message_link_id in the list
                            index = message_ids.index(message_link_id)

                            # Get the embed to be removed from the embeds
                            embed = embeds[index]

                            # Remove the embed from the embeds
                            embeds.pop(index)

                            # Remove the message ID from the list
                            message_ids.pop(index)

                            # Edit the message with the updated embeds using the embeds parameter
                            await message.edit(embeds=embeds)

                            # Store the updated list in the config setting
                            await self.config.channel(channel).message_ids.set(message_ids)

                            # Remove the reaction from the message
                            await message.remove_reaction(payload.emoji, user)

                            # Send a confirmation message to the channel with a link to the unpinned message
                            await channel.send(f"Removed {embed.title} - [link] from the extended pins message.", embed=embed) # Added this line

                            # Log the event
                            logging.info(f"Removed {embed.title} - {embed.url} from the extended pins message in {channel.name}")
        except Exception as e: # Catch any exception and log it
            logging.error(f"An error occurred in on_raw_reaction_add: {e}")
