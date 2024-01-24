import discord
from redbot.core import commands, Config, app_commands
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

class TreacheryPokemon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_pokemon = None
        self.current_sprite = None
        self.base_url = "https://pokeapi.co/api/v2/pokemon/"
        self.pokemon_count = 1025
        self.config = Config.get_conf(
            self, identifier=1234567890, force_registration=True
        )
        self.config.register_guild(spawn_channel=None, spawn_rate=0.0)
        self.spawn_message = None
        self.pokemon_id = None

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.command()
    async def setpokemonspawn(
        self, ctx, channel: commands.TextChannelConverter, spawn_rate: float
    ):
        await self.config.guild(ctx.guild).spawn_channel.set(channel.id)
        await self.config.guild(ctx.guild).spawn_rate.set(spawn_rate / 100)
        await ctx.send(
            f"Pokémon will now spawn in {channel.mention} with a spawn rate of {spawn_rate}% per message."
        )

    @commands.command()
    @commands.is_owner()
    @commands.cooldown(1, 10, commands.BucketType.channel)
    async def spawn(self, ctx):
        spawn_channel = discord.utils.get(
            ctx.guild.channels, id=await self.config.guild(ctx.guild).spawn_channel()
        )
        if ctx.channel == spawn_channel:
            pokemon_id = random.randint(1, self.pokemon_count)
            pokemon_url = self.base_url + str(pokemon_id)
            async with self.bot.session.get(pokemon_url) as response:
                if response.status == 200:
                    pokemon_data = await response.json()
                    self.current_pokemon = pokemon_data["name"]
                    self.current_sprite = pokemon_data["sprites"]["other"][
                        "official-artwork"
                    ]["front_default"]
                    image_data = BytesIO(
                        await self.bot.session.get(self.current_sprite).read()
                    )
                    image_file = discord.File(image_data, filename="pokemon.png")
                    embed_dict = {
                        "title": "A wild Pokémon has appeared!",
                        "image": {"url": "attachment://pokemon.png"},
                    }
                    embed = discord.Embed.from_dict(embed_dict)
                    message = await ctx.send(file=image_file, embed=embed)
                    self.spawn_message = message
                    self.pokemon_id = message.embeds[0].description
                else:
                    await ctx.send("Failed to spawn a Pokémon. Please try again.")

    @commands.Cog.listener()
    async def on_message_without_command(self, message):
        if message.author.bot or not message.guild:
            return
        spawn_channel = discord.utils.get(
            message.guild.channels, id=await self.config.guild(message.guild).spawn_channel()
        )
        spawn_rate = await self.config.guild(message.guild).spawn_rate()
        if message.channel == spawn_channel and random.random() < spawn_rate:
            ctx = await self.bot.get_context(message)
            await self.bot.get_command("spawn").invoke(ctx)

    @commands.guild_only()
    @commands.command(name="catch")
    async def pokecatch(self, ctx, *, pokemon: str):
        pokemon = pokemon.replace(" ", "-")
        if self.current_pokemon and self.current_pokemon == pokemon.lower():
            await ctx.send(f"Congratulations! You caught a {self.current_pokemon.capitalize()}!")
            poketag, experience = secrets.token_hex(3), 0
            await self.config.member(ctx.author).pokedex.set_raw(
                self.pokemon_id,
                value={
                    "pokemon_name": self.current_pokemon,
                    "poketag": poketag,
                    "experience": experience,
                },
            )
            if self.spawn_message:
                new_embed = discord.Embed(
                    title="Pokemon Caught",
                    description=f"{self.current_pokemon.capitalize()} was caught by {ctx.author.name}.",
                )
                await self.spawn_message.edit(embed=new_embed)
            self.current_pokemon, self.current_sprite, self.spawn_message = None, None, None
        else:
            await ctx.send(
                "That is not the correct Pokémon name or there is no Pokémon to catch. Use the `spawn` command to spawn one."
            )

    @commands.guild_only()
    @commands.command()
    async def pokedex(self, ctx):
        pokedex = await self.config.member(ctx.author).pokedex()
        if pokedex:
            pages = [
                self.create_embed(ctx, chunk)
                for chunk in (
                    pokedex[i : i + 10] for i in range(0, len(pokedex), 10)
                )
            ]
            await menu(ctx, pages, DEFAULT_CONTROLS)
        else:
            await ctx.send("You have not caught any Pokémon yet.")

    def create_embed(self, ctx, chunk):
        embed = discord.Embed(title="Your Pokédex", color=discord.Color.random())
        for pokemon_id, data in chunk.items():
            pokemon_name = data["pokemon_name"]
            poketag = data["poketag"] or secrets.token_hex(3)
            experience = data["experience"]
            embed.add_field(
                name=f"{pokemon_name.capitalize()}",
                value=f"Poketag: {poketag.upper()}\nEXP: {experience}",
                inline=True,
            )
        return embed

    @commands.guild_only()
    @commands.command()
    async def party(self, ctx, *poketags: str):
        if len(poketags) == 0:
            # Fetch and send the current party if no poketags were provided
            current_party = await self.config.member(ctx.author).party()
            if current_party is not None:
                # Get the pokemon names from the pokedex using the poketags
                pokemon_names = [
                    await self.config.member(ctx.author).pokedex.get_raw(poketag.lower())[
                        "pokemon_name"
                    ]
                    for poketag in current_party
                ]
                # Pair up the poketags and pokemon names
                pairs = zip(current_party, pokemon_names)
                # Format the output as a string
                output = "\n".join(
                    f"{poketag.upper()} - {pokemon_name.capitalize()}"
                    for poketag, pokemon_name in pairs
                )
                # Create an embed to display the output
                embed = discord.Embed(title="Your party", description=output, color=discord.Color.random())
                await ctx.send(embed=embed)
            else:
                await ctx.send("You don't have a party yet.")
        elif len(poketags) != 5:
            await ctx.send("You must provide exactly 5 Pokétags.")
        else:
            user_poketags = await self.config.member(ctx.author).pokedex.keys()
            if all(poketag.lower() in user_poketags or poketag == '-' for poketag in poketags):
                current_party = await self.config.member(ctx.author).party() or [
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                ]
                new_party = [
                    poketag if poketag != "-" else current_party[i]
                    for i, poketag in enumerate(poketags)
                ]
                await self.config.member(ctx.author).party.set(new_party)
                await ctx.send("Your party has been updated.")
            else:
                await ctx.send("You do not have all of these Pokétags in your pokedex.")