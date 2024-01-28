import random, requests, sqlite3, secrets, discord
from redbot.core import commands, Config
from redbot.core.data_manager import cog_data_path
from io import BytesIO

class TreacheryPokemon(commands.Cog):
    def __init__(self, bot):
        self.bot, self.current_pokemon, self.current_sprite, self.base_url, self.pokemon_count = bot, None, None, "https://pokeapi.co/api/v2/pokemon/", 1025
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        self.config.register_guild(spawn_channel=None, spawn_rate=0.0)
        self.spawn_message, self.pokemon_id = None, None
        self.conn = sqlite3.connect(cog_data_path(self) / 'pokemon.db')
        self.cur = self.conn.cursor()
        self.cur.execute('CREATE TABLE IF NOT EXISTS pokedex (member_id INTEGER, pokemon_id INTEGER, pokemon_name VARCHAR, level INTEGER, poketag VARCHAR (5), experience INTEGER, PRIMARY KEY (member_id, pokemon_id))')
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
                self.pokemon_id = pokemon_data['id']
                image_data = BytesIO (requests.get (self.current_sprite).content)
                image_file = discord.File (image_data, filename="pokemon.png")
                embed_dict = {"title": "A wild Pokémon has appeared!", "image": {"url": "attachment://pokemon.png"}}
                embed = discord.Embed.from_dict(embed_dict)
                message = await ctx.send(file=image_file, embed=embed)
                self.spawn_message = message
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
        self.cur.execute('SELECT position1, position2, position3, position4, position5 FROM party WHERE member_id = ?', (message.author.id,))
        party = self.cur.fetchone()
        if party is not None:
            for poketag in party:
                if poketag != '-':
                    # Check if the object has the update_experience method before calling it
                    if hasattr(self, 'update_experience'):
                        await self.update_experience(message.author.id, poketag)
                    else:
                        print("The object does not have the update_experience method.")

    @commands.guild_only()
    @commands.command(name="catch")
    async def pokecatch(self, ctx, *, pokemon: str):
        pokemon = pokemon.replace(" ", "-")
        if self.current_pokemon and self.current_pokemon == pokemon.lower():
            await ctx.send(f"Congratulations! You caught a {self.current_pokemon.capitalize()}!")
            poketag, experience = secrets.token_hex(3), 0
            pokemon_name = self.current_pokemon.title()
            self.cur.execute('INSERT INTO pokedex (member_id, pokemon_id, pokemon_name, poketag, experience) VALUES (?, ?, ?, ?, ?)', (ctx.author.id, self.pokemon_id, pokemon_name, poketag, experience))
            self.conn.commit()
            if self.spawn_message:
                new_embed = discord.Embed(title="Pokemon Caught", description=f"{pokemon_name} was caught by {ctx.author.name}.")
                await self.spawn_message.edit(embed=new_embed)
            self.current_pokemon, self.current_sprite, self.spawn_message = None, None, None
        else:
            await ctx.send("That is not the correct Pokémon name or there is no Pokémon to catch.")

    @commands.guild_only()
    @commands.command()
    async def pokedex(self, ctx):
        self.cur.execute('SELECT pokemon_id, pokemon_name, poketag, experience FROM pokedex WHERE member_id = ?', (ctx.author.id,))
        pokedex = self.cur.fetchall()
        if pokedex:
            embeds = [self.create_embed(ctx, chunk) for chunk in (pokedex[i:i+10] for i in range(0, len(pokedex), 10))]
            view = PokedexView(ctx, embeds, pokedex)
            await ctx.send(embed=embeds[0], view=view)
        else:
            await ctx.send("You have not caught any Pokémon yet.")

    def create_embed(self, ctx, chunk):
        embed = discord.Embed(title="Your Pokédex", color=discord.Color.random())
        for pokemon_id, pokemon_name, poketag, experience in chunk:
            if poketag is None:
                poketag = secrets.token_hex(3)
                self.cur.execute('UPDATE pokedex SET poketag = ? WHERE member_id = ? AND pokemon_id = ?', (poketag, ctx.author.id, pokemon_id))
                self.conn.commit()
            embed.add_field(name=f"{pokemon_name.capitalize()}", value=f"Poketag: {poketag.upper()}\nEXP: {experience}", inline=True)
        return embed

    @commands.guild_only()
    @commands.command()
    async def party(self, ctx, *poketags: str):
        if len(poketags) == 0:
            self.cur.execute('SELECT position1, position2, position3, position4, position5 FROM party WHERE member_id = ?', (ctx.author.id,))
            current_party = self.cur.fetchone()
            if current_party is not None:
                pokemon_names = [self.cur.execute('SELECT pokemon_name FROM pokedex WHERE member_id = ? AND poketag = ?', (ctx.author.id, poketag.lower())).fetchone()[0] for poketag in current_party if poketag != '-']
                output = "\n".join(f"{poketag.upper()} - {pokemon_name.capitalize()}" for poketag, pokemon_name in zip(current_party, pokemon_names))
                embed = discord.Embed(title="Your party", description=output, color=discord.Color.random())
                await ctx.send(embed=embed)
            else:
                await ctx.send("You don't have a party yet.")
        elif len(poketags) != 5:
            await ctx.send("You must provide exactly 5 Pokétags.")
        else:
            self.cur.execute('SELECT poketag FROM pokedex WHERE member_id = ?', (ctx.author.id,))
            user_poketags = [row[0] for row in self.cur.fetchall()]
            if all(poketag.lower() in user_poketags or poketag == '-' for poketag in poketags):
                self.cur.execute('REPLACE INTO party (member_id, position1, position2, position3, position4, position5) VALUES (?, ?, ?, ?, ?, ?)', 
                                (ctx.author.id, *poketags))
                self.conn.commit()
                await ctx.send("Your party has been updated.")
            else:
                await ctx.send("You do not have all of these Pokétags in your pokedex.")

class PokedexView(discord.ui.View):
    def __init__(self, ctx, embeds, pokedex):
        super().__init__(timeout=None)
        self.ctx, self.embeds, self.current, self.pokedex = ctx, embeds, 0, pokedex
        self.total = len(self.embeds)

    def update_footer(self):
        self.embeds[self.current].set_footer(text=f"Showing Pokémon {self.current * 10 + 1} - {min((self.current + 1) * 10, len(self.pokedex))} of {len(self.pokedex)}")

    async def handle_button(self, interaction, button, direction):
        if interaction.user == self.ctx.author:
            await interaction.response.defer()
            self.current += direction
            self.current %= self.total
            self.update_footer()
            await interaction.message.edit(embed=self.embeds[self.current])
        else:
            await interaction.response.send_message("Only the author of the command can use this button.", ephemeral=True)

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.blurple)
    async def previous(self, interaction, button):
        await self.handle_button(interaction, button, -1)

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.blurple)
    async def next(self, interaction, button):
        await self.handle_button(interaction, button, 1)

    async def update_experience(self, member_id, poketag):
        self.cur.execute('SELECT experience FROM pokedex WHERE member_id = ? AND poketag = ?', (member_id, poketag))
        experience = self.cur.fetchone()[0]
        experience += 1
        level = self.get_level(experience)
        next_level = self.get_experience(level + 1)
        if experience >= next_level:
            experience = 0
            level += 1
            self.cur.execute('UPDATE pokedex SET level = ? WHERE member_id = ? AND poketag = ?', (level, member_id, poketag))
            self.cur.execute('SELECT pokemon_name FROM pokedex WHERE member_id = ? AND poketag = ?', (member_id, poketag))
            pokemon_name = self.cur.fetchone()[0]
            spawn_channel = discord.utils.get(self.bot.get_guild(member_id).channels, id=await self.config.guild(self.bot.get_guild(member_id)).spawn_channel())
            await spawn_channel.send(f"Congratulations! Your {pokemon_name.capitalize()} has leveled up to {level}!")
        self.cur.execute('UPDATE pokedex SET experience = ? WHERE member_id = ? AND poketag = ?', (experience, member_id, poketag))
        self.conn.commit()

    def get_level(self, experience):
        low, high = 1, 99
        while low <= high:
            mid = (low + high) // 2
            messages = 0.02 * mid ** 2 + 0.2 * mid + 1
            if messages == experience:
                return mid
            elif messages < experience:
                low = mid + 1
            else:
                high = mid - 1
        return low - 1

    def get_experience(self, level):
        return 0.02 * level ** 2 + 0.2 * level + 1