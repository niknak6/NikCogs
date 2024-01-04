import asyncio
import json
import logging
import random
import re
from typing import Optional

import discord
import tiktoken
from emoji import EMOJI_DATA
from openai import AsyncOpenAI
from redbot.core import Config, checks, commands
from redbot.core.bot import Red
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import ReactionPredicate
from redbot.core.utils.views import SimpleMenu

logger = logging.getLogger("red.bz_cogs.aiemote")


class Emoji:
    # A base class for all emojis
    def __init__(self, description, emoji):
        self.description = description
        self.emoji = emoji
        self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

    def validate(self, ctx: commands.Context):
        # Check if the emoji is valid
        if self.emoji in EMOJI_DATA.keys():
            return True
        if (not bool(re.fullmatch(AIEmote.MATCH_DISCORD_EMOJI_REGEX, self.emoji))):
            ctx.send("Invalid emoji!")
            return False
        partial_emoji = discord.PartialEmoji.from_str(self.emoji)
        isBotEmoji = bool(discord.utils.get(ctx.bot.emojis, name=partial_emoji.name, id=partial_emoji.id))
        if not isBotEmoji:
            ctx.send("Invalid emoji! Custom emojis must be usable by the bot itself")
            return False
        return True


class AIEmote(commands.Cog):
    MATCH_DISCORD_EMOJI_REGEX = r"<a?:[A-Za-z0-9]+:[0-9]+>"

    def __init__(self, bot):
        super().__init__()
        self.bot: Red = bot
        # Use the EmojiConfig subclass instead of the Config class
        self.config = EmojiConfig.get_conf(self, identifier=754069)
        self.aclient = None

        default_global = {
            "percent": 50,
            "global_emojis": [
                Emoji("A happy face", "😀"),
                Emoji("A sad face", "😢"),
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

    @commands.Cog.listener()
    async def on_red_api_tokens_update(self, service_name, api_tokens):
        if service_name == "openai":
            self.initalize_openai()

    async def initalize_openai(self, ctx: commands.Context = None):
        key = (await self.bot.get_shared_api_tokens("openai")).get("api_key")
        if not key and ctx:
            return await ctx.send(
                f"OpenAI API key not set for `aiemote`. "
                f"Please set it with `{ctx.clean_prefix}set api openai api_key,API_KEY`")
        if not key:
            logger.error(
                F"OpenAI API key not set for `aiemote` yet! Please set it with `{ctx.clean_prefix}set api openai api_key,API_KEY`")
            return

        self.aclient = AsyncOpenAI(
            api_key=key,
            timeout=50.0
        )

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
            options += f"{index}. {value.description}\n"

        logit_bias = {}
        for i in range(len(emojis)):
            encoded_value = emojis[i].encoding.encode(str(i))
            if len(encoded_value) == 1:
                logit_bias[encoded_value[0]] = 100

        system_prompt = f"You are in a chat room. You will pick an emoji for the following message. {await self.config.extra_instruction()} Here are your options: {options} Your answer will be a int between 0 and {len(emojis)-1}."
        content = f"{message.author.display_name} : {self.stringify_any_mentions(message)}"
        try:
            response = await self.aclient.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                max_tokens=1,
                logit_bias=logit_bias,
            )
        except:
            logger.warning(f"Skipping react in {message.guild.name}! Failed to get response from OpenAI")
            return None

        response = response.choices[0].message.content
        if response.isnumeric():
            index = int(response)
            if index < 0 or index >= len(emojis):
                return None
            partial_emoji = discord.PartialEmoji.from_str(emojis[index].emoji)
            return partial_emoji
        else:
            logger.warning(
                f"Skipping react in {message.guild.name}! Non-numeric response from OpenAI: {response}. (Please report to dev if this occurs often)")
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

        if not self.aclient:
            await self.initalize_openai(ctx)
            if not self.aclient:
                return False

        # skipping images / embeds
        if not ctx.message.content or (ctx.message.attachments and len(ctx.message.attachments) > 0):
            return False

        # skipping long / short messages
        if len(ctx.message.content) > 1500 or len(ctx.message.content) < 10:
            logger.debug(f"Skipping message in {ctx.guild.name} with length {len(ctx.message.content)}")
            return False

    # Define a custom encoder for the Emoji class
    class EmojiEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, Emoji):
                return obj.__dict__
            return super().default(obj)

    # Use the custom encoder when dumping the kwargs
    def _register_default(self, group, **kwargs):
        data = json.loads(json.dumps(kwargs, cls=EmojiEncoder))
        self._defaults[group] = data
        self._do_write(group, data)

# Define a subclass of Config that uses the EmojiEncoder class
class EmojiConfig(Config):
    def _register_default(self, group, **kwargs):
        data = json.loads(json.dumps(kwargs, cls=EmojiEncoder))
        self._defaults[group] = data
        self._do_write(group, data)