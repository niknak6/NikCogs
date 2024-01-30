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
        # create the pokedex table with the level and experience columns
        self.cur.execute('CREATE TABLE IF NOT EXISTS pokedex (member_id INTEGER, pokemon_id INTEGER, pokemon_name VARCHAR, level INTEGER, poketag VARCHAR (5), experience INTEGER, PRIMARY KEY (member_id, pokemon_id))')
        # create the party table with 5 positions for each user
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
        # if the message is in the spawn channel, give 1 experience to each pokemon in the user's party
        elif message.channel == spawn_channel:
            # get the user's party from the party table
            self.cur.execute('SELECT position1, position2, position3, position4, position5 FROM party WHERE member_id = ?', (message.author.id,))
            user_party = self.cur.fetchone()
            # if the user has a party, loop through each position
            if user_party is not None:
                for position in user_party:
                    # if the position is not empty, get the pokemon's poketag
                    if position != '-':
                        poketag = position.lower()
                        # get the pokemon's level and experience from the pokedex table
                        self.cur.execute('SELECT level, experience FROM pokedex WHERE member_id = ? AND poketag = ?', (message.author.id, poketag))
                        level, experience = self.cur.fetchone()
                        # calculate the number of messages required for the next level using the formula
                        messages_required = round(0.02 * level ** 2 + 0.2 * level + 1)
                        # if the experience is equal to the messages required, level up the pokemon and reset the experience
                        if experience == messages_required:
                            level += 1
                            experience = 0
                            # update the level and experience in the pokedex table
                            self.cur.execute('UPDATE pokedex SET level = ?, experience = ? WHERE member_id = ? AND poketag = ?', (level, experience, message.author.id, poketag))
                            self.conn.commit()
                            # get the pokemon's name from the pokedex table
                            self.cur.execute('SELECT pokemon_name FROM pokedex WHERE member_id = ? AND poketag = ?', (message.author.id, poketag))
                            pokemon_name = self.cur.fetchone()[0]
                            # send a message to the user that their pokemon has leveled up
                            await message.channel.send(f"{message.author.mention}, your {pokemon_name.capitalize()} has leveled up to level {level}!")
                        # otherwise, increase the experience by 1
                        else:
                            experience += 1
                            # update the experience in the pokedex table
                            self.cur.execute('UPDATE pokedex SET experience = ? WHERE member_id = ? AND poketag = ?', (experience, message.author.id, poketag))
                            self.conn.commit()

    @commands.guild_only()
    @commands.command(name="catch")
    async def pokecatch(self, ctx, *, pokemon: str):
        pokemon = pokemon.replace(" ", "-")
        if self.current_pokemon and self.current_pokemon == pokemon.lower():
            await ctx.send(f"Congratulations! You caught a {self.current_pokemon.capitalize()}!")
            # set the initial level and experience to 1 and 0
            level, experience = 1, 0
            # generate a random poketag
            poketag = secrets.token_hex(3)
            pokemon_name = self.current_pokemon.title()
            # insert the pokemon into the pokedex table with the level, poketag, and experience
            self.cur.execute('INSERT INTO pokedex (member_id, pokemon_id, pokemon_name, level, poketag, experience) VALUES (?, ?, ?, ?, ?, ?)', (ctx.author.id, self.pokemon_id, pokemon_name, level, poketag, experience))
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
        # get the pokemon_id, pokemon_name, poketag, level, and experience from the pokedex table
        self.cur.execute('SELECT pokemon_id, pokemon_name, poketag, level, experience FROM pokedex WHERE member_id = ?', (ctx.author.id,))
        pokedex = self.cur.fetchall()
        if pokedex:
            # create embeds for each chunk of 10 pokemon
            embeds = [self.create_embed(ctx, chunk) for chunk in (pokedex[i:i+10] for i in range(0, len(pokedex), 10))]
            # create a view for pagination
            view = PokedexView(ctx, embeds, pokedex)
            view.timeout = 300
            # send the first embed with the view
            await ctx.send(embed=embeds[0], view=view)
        else:
            await ctx.send("You have not caught any Pokémon yet.")

    def create_embed(self, ctx, chunk):
        embed = discord.Embed(title="Your Pokédex", color=discord.Color.random())
        for pokemon_id, pokemon_name, poketag, level, experience in chunk:
            if poketag is None:
                poketag = secrets.token_hex(3)
                self.cur.execute('UPDATE pokedex SET poketag = ? WHERE member_id = ? AND pokemon_id = ?', (poketag, ctx.author.id, pokemon_id))
                self.conn.commit()
            # add the level and experience to the embed field
            embed.add_field(name=f"{pokemon_name.capitalize()}", value=f"Poketag: {poketag.upper()}\nLevel: {level}\nEXP: {experience}", inline=True)
        return embed

    @commands.guild_only()
    @commands.command()
    async def party(self, ctx, *poketags: str):
        if len(poketags) == 0:
            self.cur.execute('SELECT position1, position2, position3, position4, position5 FROM party WHERE member_id = ?', (ctx.author.id,))
            current_party = self.cur.fetchone()
            if current_party is not None:
                # get the pokemon names, levels, and experience from the pokedex table
                pokemon_data = [self.cur.execute('SELECT pokemon_name, level, experience FROM pokedex WHERE member_id = ? AND poketag = ?', (ctx.author.id, poketag.lower())).fetchone() for poketag in current_party if poketag != '-']
                # create a list of strings for each pokemon in the party
                output = [f"{poketag.upper()} - {pokemon_name.capitalize()} (Level {level}, EXP {experience})" for poketag, (pokemon_name, level, experience) in zip(current_party, pokemon_data)]
                # join the list with newlines
                output = "\n".join(output)
                # create an embed with the output
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
                # get the current party of the member
                self.cur.execute('SELECT position1, position2, position3, position4, position5 FROM party WHERE member_id = ?', (ctx.author.id,))
                current_party = self.cur.fetchone()

                # if the member has a party, update it with the new poketags
                if current_party is not None:
                    # create a dictionary of positions and poketags
                    positions = dict(zip(['position1', 'position2', 'position3', 'position4', 'position5'], poketags))
                    # create a list of columns and values to update
                    columns = []
                    values = []
                    for column, value in positions.items():
                        # only update the columns that are not '-'
                        if value != '-':
                            columns.append(f"{column} = ?")
                            values.append(value)
                    # join the columns with commas
                    columns = ", ".join(columns)
                    # add the member_id to the values
                    values.append(ctx.author.id)
                    # execute the update statement
                    self.cur.execute(f'UPDATE party SET {columns} WHERE member_id = ?', values)
                    self.conn.commit()
                    await ctx.send("Your party has been updated.")
                # if the member does not have a party, insert a new one
                else:
                    self.cur.execute('INSERT INTO party (member_id, position1, position2, position3, position4, position5) VALUES (?, ?, ?, ?, ?, ?)', 
                                    (ctx.author.id, *poketags))
                    self.conn.commit()
                    await ctx.send("Your party has been created.")
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
        
    @commands.command()
    @commands.is_owner()
    async def resetpokedex(self, ctx):
        # update the level and experience of all pokemon in the pokedex table to 1 and 0
        self.cur.execute('UPDATE pokedex SET level = 1, experience = 0')
        self.conn.commit()
        # send a confirmation message to the owner
        await ctx.send("The pokedex has been reset. All pokemon have level 1 and experience 0.")