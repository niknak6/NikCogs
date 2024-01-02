import asyncio
import logging
import random
import re
from typing import Optional

import discord
from emoji import EMOJI_DATA
from redbot.core import Config, checks, commands
from redbot.core.bot import Red
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import ReactionPredicate
from redbot.core.utils.views import SimpleMenu
import google.generativeai as genai
import textwrap

genai.configure(api_key=None) # will be set by the user later

logger = logging.getLogger("red.bz_cogs.aiemote")

class AIEmote(commands.Cog):
    MATCH_DISCORD_EMOJI_REGEX = r"<a?:[A-Za-z0-9]+:[0-9]+>"

    def __init__(self, bot):
        super().__init__()
        self.bot: Red = bot
        self.config = Config.get_conf(self, identifier=754069)
        self.model = None # added this attribute to store the model object

        default_global = {
            "percent": 50,
            "global_emojis": [
                {
                    "description": "A happy face",
                    "emoji": "😀",
                },
                {
                    "description": "A sad face",
                    "emoji": "😢",
                },
            ],
            "extra_instruction": "",
            "optin": [],
            "optout": []
        }

        default_guild = {
            "server_emojis": [],
            "whitelist": [],
            "optin_by_default": False
        }

        self.config.register_guild(**default_guild)
        self.config.register_global(**default_global)

    async def cog_load(self):
        self.whitelist = {}
        all_config = await self.config.all_guilds()
        self.percent = await self.config.percent()
        self.optin_users = await self.config.optin()
        self.optout_users = await self.config.optout()
        for guild_id, config in all_config.items():
            self.whitelist[guild_id] = config["whitelist"]

    @commands.is_owner()
    @commands.command()
    async def setapikey(self, ctx: commands.Context, key: str):
        """Sets the Google API key for the cog."""
        await self.config.api_key.set(key)
        genai.configure(api_key=key)
        await ctx.send("API key set successfully.")

    @commands.Cog.listener()
    async def on_message_without_command(self, message: discord.Message):
        ctx: commands.Context = await self.bot.get_context(message)
        if not (await self.is_valid_to_react(ctx)):
            return
        if (self.percent < random.randint(0, 99)):
            return
        emoji = await self.pick_emoji(message)
        if emoji:
            await message.add_reaction(emoji)

    async def pick_emoji(self, message: discord.Message):
        options = "\n"
        emojis = await self.config.guild(message.guild).server_emojis() or []
        emojis += await self.config.global_emojis() or []

        if not emojis:
            logger.warning(f"Skipping react! No valid emojis to use in {message.guild.name}")
            return None

        for index, value in enumerate(emojis):
            options += f"{index}. {value['description']}\n"

        system_prompt = f"You are in a chat room. You will pick an emoji for the following message. {await self.config.extra_instruction()} Here are your options: {options} Your answer will be a int between 0 and {len(emojis)-1}."
        content = f"{message.author.display_name} : {self.stringify_any_mentions(message)}"
        try:
            # added this block to create or load the model object with the history
            if not self.model: # check if the model object is None
                api_key = await self.config.api_key() # get the api key from the config
                if not api_key: # check if the api key is None
                    print("No API key set for the cog.")
                    return "No API key set for the cog."
                history = [] # an empty list for the history
                self.model = genai.GenerativeModel(model_name="gemini-pro", history=history) # create the model object with the history
            input_content = genai.ModelContent(role="user", parts=[genai.ModelContentPart(text=content)]) # create the input content from the first message
            response_content = self.model.generate_content(input_content) # generate the response content from the model
            response_text = response_content.parts[0].text # get the text of the response
        except:
            logger.warning(f"Skipping react in {message.guild.name}! Failed to get response from Google AI")
            return None

        if response_text.isnumeric():
            index = int(response_text)
            if index < 0 or index >= len(emojis):
                return None
            partial_emoji = discord.PartialEmoji.from_str(emojis[index]["emoji"])
            return partial_emoji
        else:
            logger.warning(
                f"Skipping react in {message.guild.name}! Non-numeric response from Google AI: {response_text}. (Please report to dev if this occurs often)")
            return None

    async def is_valid_to_react(self, ctx: commands.Context):
        if ctx.guild is None or ctx.author.bot:
            return False

        whitelist = self.whitelist.get(ctx.guild.id, [])
        if await self.bot.cog_disabled_in_guild(self, ctx.guild):
            return False

        if (not isinstance(ctx.channel, discord.Thread) and (ctx.channel.id not in whitelist)):
            return False
        if (isinstance(ctx.channel, discord.Thread) and (ctx.channel.parent_id not in whitelist)):
            return False

        if not await self.bot.ignored_channel_or_guild(ctx):
            return False
        if not await self.bot.allowed_by_whitelist_blacklist(ctx.author):
            return False
        if ctx.author.id in self.optout_users:
            return False
        if (not ctx.author.id in self.optin_users) and (not (await self.config.guild(ctx.guild).optin_by_default())):
            return False

        # skipping images / embeds
        if not ctx.message.content or (ctx.message.attachments and len(ctx.message.attachments) > 0):
            return False

        # skipping long / short messages
        if len(ctx.message.content) > 1500 or len(ctx.message.content) < 10:
            logger.debug(f"Skipping message in {ctx.guild.name} with length {len(ctx.message.content)}")
            return False

        return True

    def stringify_any_mentions(self, message: discord.Message) -> str:
        """
        Converts mentions to text
        """
        content = message.content
        mentions = message.mentions + message.role_mentions + message.channel_mentions

        if not mentions:
            return content

        for mentioned in mentions:
            if mentioned in message.channel_mentions:
                content = content.replace(mentioned.mention, f'#{mentioned.name}')
            elif mentioned in message.role_mentions:
                content = content.replace(mentioned.mention, f'@{mentioned.name}')
            else:
                content = content.replace(mentioned.mention, f'@{mentioned.display_name}')

        return content

    @commands.group(name="aiemote", alias=["ai_emote"])
    @checks.admin_or_permissions(manage_guild=True)
    async def aiemote(self, _):
        """ Totally not glorified sentiment analysis™

            Picks a reaction for a message using gpt-3.5-turbo

            To get started, please add a channel to the whitelist with:
            `[p]aiemote allow <#channel>`
        """
        pass

    @aiemote.command(name="whitelist")
    @checks.admin_or_permissions(manage_guild=True)
    async def whitelist_list(self, ctx: commands.Context):
        """ List all channels in the whitelist """
        whitelist = self.whitelist.get(ctx.guild.id, [])
        if not whitelist:
            return await ctx.send("No channels in whitelist")
        channels = [ctx.guild.get_channel(channel_id) for channel_id in whitelist]
        embed = discord.Embed(title="Whitelist", color=await ctx.embed_color())
        embed.add_field(name="Channels", value="\n".join([channel.mention for channel in channels]))
        await ctx.send(embed=embed)

    @aiemote.command(name="allow", aliases=["add"])
    @checks.admin_or_permissions(manage_guild=True)
    async def whitelist_add(self, ctx: commands.Context, channel: discord.TextChannel):
        """ Add a channel to the whitelist

            *Arguments*
            - `<channel>` The mention of channel
        """
        whitelist = self.whitelist.get(ctx.guild.id, [])
        if channel.id in whitelist:
            return await ctx.send("Channel already in whitelist")
        whitelist.append(channel.id)
        self.whitelist[ctx.guild.id] = whitelist
        await self.config.guild(ctx.guild).whitelist.set(whitelist)
        return await ctx.tick()

    @aiemote.command(name="remove", aliases=["rm"])
    @checks.admin_or_permissions(manage_guild=True)
    async def whitelist_remove(self, ctx