import random, requests, logging, sqlite3, secrets, discord
from redbot.core import commands, Config
from redbot.core.data_manager import cog_data_path

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
        # Moved the database connection and cursor creation to the init method
        # Removed the createparty command and the party table creation
        # Create the pokedex and party tables on init
        self.conn = sqlite3.connect(cog_data_path(self) / 'pokemon.db')
        self.cur = self.conn.cursor()
        # Removed the pokemon_count column from the pokedex table
        self.cur.execute('CREATE TABLE IF NOT EXISTS pokedex (member_id INTEGER, pokemon_id INTEGER, pokemon_name VARCHAR, poketag VARCHAR (5), experience INTEGER, PRIMARY KEY (member_id, pokemon_id))')
        # Create the party table with the TEXT columns
        self.cur.execute('CREATE TABLE IF NOT EXISTS party (member_id INTEGER, position1 TEXT, position2 TEXT, position3 TEXT, position4 TEXT, position5 TEXT)')
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

class PokedexView(discord.ui.View):
    def __init__(self, ctx, embeds, pokemon_per_page, pokedex):
        super().__init__(timeout=None)
        self.ctx, self.embeds, self.current, self.pokemon_per_page, self.pokedex = ctx, embeds, 0, pokemon_per_page, pokedex
        self.total = (len(self.pokedex) + pokemon_per_page - 1) // pokemon_per_page
        self.update_footer()

    def update_footer(self):
        self.embeds[self.current].set_footer(text=f"Showing Pokémon {self.current * self.pokemon_per_page + 1} - {min((self.current + 1) * self.pokemon_per_page, len(self.pokedex))} of {len(self.pokedex)}")

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.blurple)
    async def previous(self, interaction, button):
        if interaction.user == self.ctx.author:
            await interaction.response.defer()
            self.current -= 1
            if self.current < 0:
                self.current = self.total - 1
            self.update_footer()
            try:
                await interaction.message.edit(embed=self.embeds[self.current])
            except Exception as e:
                print(e)
        else:
            try:
                await interaction.response.send_message("Only the author of the command can use this button.", ephemeral=True)
            except Exception as e:
                print(e)

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.blurple)
    async def next(self, interaction, button):
        if interaction.user == self.ctx.author:
            await interaction.response.defer()
            self.current += 1
            if self.current >= self.total:
                self.current = 0
            self.update_footer()
            try:
                await interaction.message.edit(embed=self.embeds[self.current])
            except Exception as e:
                print(e)
        else:
            try:
                await interaction.response.send_message("Only the author of the command can use this button.", ephemeral=True)
            except Exception as e:
                print(e)

# Remove the import statement for the party module and the TreacheryPokemon class from the party.py file
# Copy the contents of the party.py file and paste it at the end of the treacherypokemon.py file

@commands.guild_only()
@commands.command()
async def party(self, ctx, *poketags):
    # Check if the user has provided any poketags
    if poketags:
        # Check if the user has provided exactly 5 poketags
        if len(poketags) == 5:
            # Check if the user has all the poketags in their pokedex
            self.cur.execute('SELECT poketag FROM pokedex WHERE member_id = ?', (ctx.author.id,))
            user_poketags = [row[0] for row in self.cur.fetchall()]
            if all(poketag in user_poketags for poketag in poketags):
                # Update the party table with the poketags in the given order
                self.cur.execute('UPDATE party SET position1 = ?, position2 = ?, position3 = ?, position4 = ?, position5 = ? WHERE member_id = ?', (*poketags, ctx.author.id))
                self.conn.commit()
                await ctx.send("Your party has been updated.")
            else:
                await ctx.send("You do not have all the poketags in your pokedex. Please use valid poketags.")
        else:
            # Check if the user has less than 5 poketags in their pokedex
            self.cur.execute('SELECT poketag FROM pokedex WHERE member_id = ?', (ctx.author.id,))
            user_poketags = [row[0] for row in self.cur.fetchall()]
            if all(poketag in user_poketags for poketag in poketags):
                # Get the current party of the user
                self.cur.execute('SELECT position1, position2, position3, position4, position5 FROM party WHERE member_id = ?', (ctx.author.id,))
                current_party = self.cur.fetchone()
                # Create a dictionary to store the positions and poketags
                positions = {f"position{i}": poketag for i, poketag in enumerate(current_party, 1)}
                # Create a list to store the available positions
                available = [f"position{i}" for i in range(1, 6) if positions[f"position{i}"] is None]
                # Create an embed to show the current party and the poketags to be added
                embed = discord.Embed(title="Your Party", color=discord.Color.random())
                for position, poketag in positions.items():
                    if poketag is None:
                        embed.add_field(name=position, value="Empty", inline=True)
                    else:
                        embed.add_field(name=position, value=poketag.upper(), inline=True)
                embed.add_field(name="Poketags to be added", value=", ".join(poketag.upper() for poketag in poketags), inline=False)
                # Send the embed and ask the user to choose the positions for each poketag
                await ctx.send(embed=embed)
                await ctx.send("Please choose the positions for each poketag. For example, if you want to put the first poketag in position 2, type 2. If you want to skip a poketag, type 0.")
                # Create a view to handle the user input
                view = PartyView(ctx, poketags, positions, available)
                await ctx.send("Waiting for your input...", view=view)
            else:
                await ctx.send("You do not have all the poketags in your pokedex. Please use valid poketags.")
    else:
        # Get the current party of the user
        self.cur.execute('SELECT position1, position2, position3, position4, position5 FROM party WHERE member_id = ?', (ctx.author.id,))
        current_party = self.cur.fetchone()
        # Create an embed to show the current party
        embed = discord.Embed(title="Your Party", color=discord.Color.random())
        for position, poketag in enumerate(current_party, 1):
            if poketag is None:
                embed.add_field(name=f"position{position}", value="Empty", inline=True)
            else:
                embed.add_field(name=f"position{position}", value=poketag.upper(), inline=True)
        # Send the embed
        await ctx.send(embed=embed)

class PartyView(discord.ui.View):
    def __init__(self, ctx, poketags, positions, available):
        super().__init__(timeout=60)
        self.ctx, self.poketags, self.positions, self.available, self.index = ctx, poketags, positions, available, 0
        self.add_item(discord.ui.MessageInput(placeholder="Enter a position number (1-5) or 0 to skip"))

    async def interaction_check(self, interaction):
        if interaction.user == self.ctx.author:
            return True
        else:
            await interaction.response.send_message("Only the author of the command can use this input.", ephemeral=True)
            return False

    @discord.ui.message_input()
    async def on_message_input(self, interaction, message):
        # Check if the message is a valid number
        try:
            position = int(message.content)
        except ValueError:
            await interaction.response.send_message("Please enter a valid number.", ephemeral=True)
            return
        # Check if the number is between 0 and 5
        if position < 0 or position > 5:
            await interaction.response.send_message("Please enter a number between 0 and 5.", ephemeral=True)
            return
        # Check if the number is 0
        if position == 0:
            # Skip the current poketag and move to the next one
            await interaction.response.send_message(f"Skipped {self.poketags[self.index].upper()}.", ephemeral=True)
            self.index += 1
        else:
            # Check if the position is available
            if f"position{position}" in self.available:
                # Update the positions and available lists
                self.positions[f"position{position}"] = self.poketags[self.index]
                self.available.remove(f"position{position}")
                await interaction.response.send_message(f"Set {self.poketags[self.index].upper()} to position {position}.", ephemeral=True)
                self.index += 1
            else:
                await interaction.response.send_message(f"Position {position} is already occupied. Please choose another position.", ephemeral=True)
                return
        # Check if all the poketags have been assigned
        if self.index == len(self.poketags):
            # Update the party table with the new positions
            self.cur.execute('UPDATE party SET position1 = ?, position2 = ?, position3 = ?, position4 = ?, position5 = ? WHERE member_id = ?', (*self.positions.values(), self.ctx.author.id))
            self.conn.commit()
            # Create an embed to show the updated party
            embed = discord.Embed(title="Your Party", color=discord.Color.random())
            for position, poketag in self.positions.items():
                if poketag is None:
                    embed.add_field(name=position, value="Empty", inline=True)
                else:
                    embed.add_field(name=position, value=poketag.upper(), inline=True)
            # Send the embed and stop the view
            await interaction.response.send_message("Your party has been updated.", ephemeral=True)
            await interaction.channel.send(embed=embed)
            self.stop()
        else:
            # Ask the user to choose the position for the next poketag
            await interaction.response.send_message(f"Please choose the position for {self.poketags[self.index].upper()}.", ephemeral=True)