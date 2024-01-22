import random, requests, logging, sqlite3, secrets, discord
from redbot.core import commands, Config
from redbot.core.data_manager import cog_data_path
from io import BytesIO

logger = logging.getLogger("red.treacherypokemon")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename="treacherypokemon.log", encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)

class TreacheryPokemon(commands.Cog):
    def __init__(self, bot):
        self.bot, self.current_pokemon, self.current_sprite, self.base_url, self.pokemon_count = bot, None, None, "https://pokeapi.co/api/v2/pokemon/", 1025
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        self.config.register_guild(spawn_channel=None, spawn_rate=0.0)
        self.spawn_message, self.pokemon_id = None, None
        self.conn = sqlite3.connect(cog_data_path(self) / 'pokemon.db')
        self.cur = self.conn.cursor()
        # Removed the pokemon_count column from the table
        self.cur.execute('CREATE TABLE IF NOT EXISTS pokedex (member_id INTEGER, pokemon_id INTEGER, pokemon_name VARCHAR, poketag VARCHAR (5), experience INTEGER, PRIMARY KEY (member_id, pokemon_id))')
        self.conn.commit()
        # Added the party table creation
        self.cur.execute('CREATE TABLE IF NOT EXISTS party (member_id INTEGER, position1 TEXT, position2 TEXT, position3 TEXT, position4 TEXT, position5 TEXT, PRIMARY KEY (member_id))')
        self.conn.commit()

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.command()
    async def setpokemonspawn(self, ctx, channel: commands.TextChannelConverter, spawn_rate: float):
        await self.config.guild(ctx.guild).spawn_channel.set(channel.id)
        await self.config.guild(ctx.guild).spawn_rate.set(spawn_rate / 100)
        await ctx.send(f"Pokémon will now spawn in {channel.mention} with a spawn rate of {spawn_rate}% per message.")

    @commands.command()
    @commands.is_owner()
    @commands.cooldown(1, 10, commands.BucketType.channel)
    async def spawn(self, ctx):
        spawn_channel = discord.utils.get(ctx.guild.channels, id=await self.config.guild(ctx.guild).spawn_channel())
        if ctx.channel == spawn_channel:
            pokemon_id = random.randint(1, self.pokemon_count)
            pokemon_url = self.base_url + str(pokemon_id)
            response = requests.get(pokemon_url)
            if response.status_code == 200:
                pokemon_data = response.json()
                self.current_pokemon, self.current_sprite = pokemon_data['name'], pokemon_data['sprites']['other']['official-artwork']['front_default']
                image_data = BytesIO (requests.get (self.current_sprite).content)
                image_file = discord.File (image_data, filename="pokemon.png")
                embed_dict = {"title": "A wild Pokemon has appeared!", "image": {"url": "attachment://pokemon.png"}}
                embed = discord.Embed.from_dict(embed_dict)
                # Assign the message object to a single variable
                message = await ctx.send(file=image_file, embed=embed)
                # Extract the attributes you need from the message object
                self.spawn_message = message
                self.pokemon_id = message.embeds[0].description # Assuming the pokemon_id is in the embed description
            else:
                await ctx.send("Failed to spawn a Pokémon. Please try again.")

    @commands.Cog.listener()
    async def on_message_without_command(self, message):
        if message.author.bot or not message.guild:
            return
        spawn_channel = discord.utils.get(message.guild.channels, id=await self.config.guild(message.guild).spawn_channel())
        spawn_rate = await self.config.guild(message.guild).spawn_rate()
        if message.channel == spawn_channel and random.random() < spawn_rate:
            ctx = await self.bot.get_context(message)
            await self.bot.get_command("spawn").invoke(ctx)

    @commands.guild_only()
    @commands.command(name="pokecatch")
    async def pokecatch(self, ctx, *, pokemon: str):
        pokemon = pokemon.replace(" ", "-")
        if self.current_pokemon and self.current_pokemon == pokemon.lower():
            await ctx.send(f"Congratulations! You caught a {self.current_pokemon.capitalize()}!")
            # Removed the pokemon_count variable and the if-else statement
            # Always generate a new poketag and insert a new row into the database
            poketag, experience = secrets.token_hex(3), 0
            # Removed the pokemon_count variable from the database query
            self.cur.execute('INSERT INTO pokedex (member_id, pokemon_id, pokemon_name, poketag, experience) VALUES (?, ?, ?, ?, ?)', (ctx.author.id, self.pokemon_id, self.current_pokemon, poketag, experience))
            self.conn.commit()
            if self.spawn_message:
                new_embed = discord.Embed(title="Pokemon Caught", description=f"{self.current_pokemon.capitalize()} was caught by {ctx.author.name}.")
                await self.spawn_message.edit(embed=new_embed)
            self.current_pokemon, self.current_sprite, self.spawn_message = None, None, None
        else:
            await ctx.send("That is not the correct Pokémon name or there is no Pokémon to catch. Use the `spawn` command to spawn one.")

    @commands.guild_only()
    @commands.command()
    async def pokedex(self, ctx):
        self.cur.execute('SELECT pokemon_id, pokemon_name, poketag, experience FROM pokedex WHERE member_id = ?', (ctx.author.id,))
        pokedex = self.cur.fetchall()
        if pokedex:
            embeds = [self.create_embed(chunk) for chunk in (pokedex[i:i+10] for i in range(0, len(pokedex), 10))]
            view = PokedexView(ctx, embeds, 10, pokedex)
            await ctx.send(embed=embeds[0], view=view)
        else:
            await ctx.send("You have not caught any Pokémon yet.")

    def create_embed(self, chunk):
        embed = discord.Embed(title="Your Pokedex", color=discord.Color.random())
        for pokemon_id, pokemon_name, poketag, experience in chunk:
            if poketag is None:
                poketag = secrets.token_hex(3)
                self.cur.execute('UPDATE pokedex SET poketag = ? WHERE member_id = ? AND pokemon_id = ?', (poketag, ctx.author.id, pokemon_id))
                self.conn.commit()
            # Removed the pokemon_count variable and the x {pokemon_count} part from the field name
            # Just show the pokemon name as the field name
            embed.add_field(name=f"{pokemon_name.capitalize()}", value=f"Poketag: {poketag.upper()}\nEXP: {experience}", inline=True)
        return embed

    # Added the party command
    @commands.guild_only()
    @commands.command()
    async def party(self, ctx, *args):
        # Check if the user provided any arguments
        if args:
            # Check if the user provided exactly 5 arguments
            if len(args) == 5:
                # Check if the user has the poketags in their pokedex
                valid = True
                for arg in args:
                    self.cur.execute('SELECT poketag FROM pokedex WHERE member_id = ? AND poketag = ?', (ctx.author.id, arg.upper()))
                    result = self.cur.fetchone()
                    if not result:
                        # The user does not have this poketag
                        valid = False
                        await ctx.send(f"You do not have a Pokémon with the poketag {arg.upper()}.")
                        break
                if valid:
                    # The user has all the poketags
                    # Update the party table with the new party
                    self.cur.execute('REPLACE INTO party (member_id, position1, position2, position3, position4, position5) VALUES (?, ?, ?, ?, ?, ?)', (ctx.author.id, *args))
                    self.conn.commit()
                    await ctx.send("Your party has been updated.")
            else:
                # The user provided an invalid number of arguments
                await ctx.send("You need to provide exactly 5 poketags to set your party.")
        else:
            # The user did not provide any arguments
            # List the user's current party
            self.cur.execute('SELECT position1, position2, position3, position4, position5 FROM party WHERE member_id = ?', (ctx.author.id,))
            party = self.cur.fetchone()
            if party:
                # The user has a party
                # Resolve the poketags to pokemon names
                names = []
                for poketag in party:
                    self.cur.execute('SELECT pokemon_name FROM pokedex WHERE member_id = ? AND poketag = ?', (ctx.author.id, poketag))
                    name = self.cur.fetchone()[0]
                    names.append(name)
                # Create an embed to display the party
                embed = discord.Embed(title="Your Party", color=discord.Color.random())
                for i, (poketag, name) in enumerate(zip(party, names), 1):
                    embed.add_field(name=f"Position {i}", value=f"{name.capitalize()} ({poketag.upper()})", inline=True)
                await ctx.send(embed=embed)
            else:
                # The user does not have a party
                await ctx.send("You have not set a party yet.")