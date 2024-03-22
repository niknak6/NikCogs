import random, requests, sqlite3, secrets, discord
from redbot.core.commands import converter
from discord.utils import get
from redbot.core import commands, Config
from redbot.core.commands.converter import Optional
from redbot.core.data_manager import cog_data_path
from discord import Embed, Reaction
from io import BytesIO
import datetime
import asyncio
import traceback

class TreacheryPokemon(commands.Cog):
    def __init__(self, bot):
        self.bot, self.current_pokemon, self.current_sprite, self.base_url, self.pokemon_count = bot, None, None, "https://pokeapi.co/api/v2/pokemon/", 1025
        self.type_url = "https://pokeapi.co/api/v2/type/"
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        self.config.register_guild(spawn_channel=None, spawn_rate=0.0, spawn_cooldown=15.0)
        self.spawn_message, self.pokemon_id = None, None
        self.conn = sqlite3.connect(cog_data_path(self) / 'pokemon.db')
        self.cur = self.conn.cursor()
        self.cur.execute('CREATE TABLE IF NOT EXISTS pokedex (member_id INTEGER, pokemon_id INTEGER, pokemon_name VARCHAR, level INTEGER, poketag VARCHAR (5), experience INTEGER, PRIMARY KEY (member_id, pokemon_id))')
        self.cur.execute('CREATE TABLE IF NOT EXISTS party (member_id INTEGER, position1 TEXT, position2 TEXT, position3 TEXT, position4 TEXT, position5 TEXT, position6 TEXT, PRIMARY KEY (member_id))')
        self.conn.commit()
        self.last_spawn = None
        self.trades = {}
        self.battles = {}

    def get_random_move(self, pokemon_name):
        pokemon_url = f"{self.base_url}{pokemon_name.lower().replace(' ', '-').replace('.', '')}"
        pokemon_data = requests.get(pokemon_url).json()
        move = random.choice(pokemon_data['moves'])
        move_data = requests.get(move['move']['url']).json()
        return move['move']['name'], move_data['type']['name']

    def get_pokemon_health(self, pokemon_name):
        pokemon_url = self.base_url + pokemon_name.lower().replace(" ", "-").replace(".", "")
        response = requests.get(pokemon_url)
        response.raise_for_status()
        pokemon_data = response.json()
        level = pokemon_data['stats'][0]['base_stat']
        attack = pokemon_data['stats'][1]['base_stat']
        defense = pokemon_data['stats'][2]['base_stat']
        special_attack = pokemon_data['stats'][3]['base_stat']
        speed = pokemon_data['stats'][5]['base_stat']
        base_health = 50
        level_modifier = level * 2
        stat_modifier = (attack + defense + special_attack + speed) / 8
        health = round(base_health + level_modifier + stat_modifier)
        return health
    
    async def on_command_error(self, ctx: commands.Context, error):
        # Handle your errors here
        if isinstance(error, commands.MemberNotFound):
            await ctx.send(f"I could not find member '{error.argument}'. Please try again")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"'{error.param.name}' is a required argument.")
        elif isinstance(error, commands.CommandError):
            await ctx.send(error) # Send the error message to the context channel
        else:
            # All unhandled errors will print their original traceback
            print(f'Ignoring exception in command {ctx.command}:', file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.command()
    async def setpokemonspawn(self, ctx, channel: commands.TextChannelConverter, spawn_rate: float, cooldown: converter.Optional[float] = 15.0): # added cooldown argument
        await self.config.guild(ctx.guild).spawn_channel.set(channel.id)
        await self.config.guild(ctx.guild).spawn_rate.set(spawn_rate / 100)
        await self.config.guild(ctx.guild).spawn_cooldown.set(cooldown)
        await ctx.send(f"Pokémon will now spawn in {channel.mention} with a spawn rate of {spawn_rate}% per message and a cooldown of {cooldown} minutes.") # updated confirmation message

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.channel)
    async def spawn(self, ctx):
        if ctx.invoked_with == "spawn" and not await self.bot.is_owner(ctx.author):
            await ctx.send("Only the owner of the bot can manually spawn a Pokémon.")
            return
        spawn_channel = discord.utils.get(ctx.guild.channels, id=await self.config.guild(ctx.guild).spawn_channel())
        spawn_cooldown = await self.config.guild(ctx.guild).spawn_cooldown()
        if ctx.channel == spawn_channel:
                now = datetime.datetime.now()
                if self.last_spawn is None or (now - self.last_spawn).total_seconds() >= spawn_cooldown * 60 or await self.bot.is_owner(ctx.author):
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
                        self.last_spawn = now
                    else:
                        await ctx.send("Failed to spawn a Pokémon. Please try again.")
        else:
            raise commands.CheckFailure("You are not the owner of this bot.")

    @commands.Cog.listener()
    async def on_message_without_command(self, message):
        if message.author.bot or not message.guild:
            return
        spawn_channel = discord.utils.get(message.guild.channels, id=await self.config.guild(message.guild).spawn_channel())
        spawn_rate = await self.config.guild(message.guild).spawn_rate()
        if message.channel == spawn_channel and random.random() < spawn_rate:
            ctx = await self.bot.get_context(message)
            await self.bot.get_command("spawn").invoke(ctx)
        elif message.channel == spawn_channel:
            self.cur.execute('SELECT position1, position2, position3, position4, position5, position6 FROM party WHERE member_id = ?', (message.author.id,))
            user_party = self.cur.fetchone()
            if user_party is not None:
                leveled_up = []
                for position in user_party:
                    if position != '-':
                        poketag = position.lower()
                        self.cur.execute('SELECT level, experience FROM pokedex WHERE member_id = ? AND poketag = ?', (message.author.id, poketag))
                        level, experience = self.cur.fetchone()
                        messages_required = round(0.02 * level ** 2 + 0.2 * level + 1)
                        if experience == messages_required:
                            level += 1
                            experience = 0
                            self.cur.execute('UPDATE pokedex SET level = ?, experience = ? WHERE member_id = ? AND poketag = ?', (level, experience, message.author.id, poketag))
                            self.conn.commit()
                            self.cur.execute('SELECT pokemon_name FROM pokedex WHERE member_id = ? AND poketag = ?', (message.author.id, poketag))
                            pokemon_name = self.cur.fetchone()[0]
                            if level in [10, 20, 30, 40, 50, 60, 70, 80, 90, 99]:
                                leveled_up.append((pokemon_name, level))
                        else:
                            experience += 1
                            self.cur.execute('UPDATE pokedex SET experience = ? WHERE member_id = ? AND poketag = ?', (experience, message.author.id, poketag))
                            self.conn.commit()
                if leveled_up:
                    output = [f"{pokemon_name.capitalize()} has leveled up to level {level}!" for pokemon_name, level in leveled_up]
                    output = "\n".join(output)
                    await message.channel.send(f"{message.author.mention}, your Pokémon have leveled up!\n\n{output}")

    @commands.guild_only()
    @commands.command(name="catch")
    async def pokecatch(self, ctx, *, pokemon: str):
        pokemon = pokemon.replace(" ", "-")
        if self.current_pokemon and self.current_pokemon == pokemon.lower():
            await ctx.send(f"Congratulations! You caught a {self.current_pokemon.capitalize()}!")
            level, experience = 1, 0
            poketag = secrets.token_hex(3)
            pokemon_name = self.current_pokemon.title()
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
    async def freepokemon(self, ctx, poketag: str):
        """Free a Pokémon from your Pokédex by its Poketag."""
        self.cur.execute('SELECT pokemon_id, pokemon_name FROM pokedex WHERE member_id = ? AND poketag = ?', (ctx.author.id, poketag.lower()))
        pokemon_data = self.cur.fetchone()
        if pokemon_data is None:
            await ctx.send("You do not have that Pokémon in your Pokédex.")
            return
        pokemon_id, pokemon_name = pokemon_data
        self.cur.execute('SELECT position1, position2, position3, position4, position5, position6 FROM party WHERE member_id = ?', (ctx.author.id,))
        user_party = self.cur.fetchone()
        if user_party is not None and poketag.lower() in user_party:
            await ctx.send("You cannot free a Pokémon that is in your party.")
            return
        self.cur.execute('DELETE FROM pokedex WHERE member_id = ? AND poketag = ?', (ctx.author.id, poketag.lower()))
        self.conn.commit()
        await ctx.send(f"You have freed your {pokemon_name.capitalize()} from your Pokédex.")

    @commands.guild_only()
    @commands.command()
    async def pokedex(self, ctx):
        self.cur.execute('SELECT pokemon_id, pokemon_name, poketag, level, experience FROM pokedex WHERE member_id = ? ORDER BY pokemon_id', (ctx.author.id,))
        pokedex = self.cur.fetchall()
        if pokedex:
            embeds = [self.create_embed(ctx, chunk) for chunk in (pokedex[i:i+15] for i in range(0, len(pokedex), 15))]
            view = PokedexView(ctx, embeds, pokedex)
            view.timeout = 300
            await ctx.send(embed=embeds[0], view=view)
        else:
            await ctx.send("You have not caught any Pokémon yet.")

    def create_embed(self, ctx, chunk):
        embed = discord.Embed(title=f"{ctx.author.name}'s Pokédex", color=discord.Color.random())
        for pokemon_id, pokemon_name, poketag, level, experience in chunk:
            if poketag is None:
                poketag = secrets.token_hex(3)
                self.cur.execute('UPDATE pokedex SET poketag = ? WHERE member_id = ? AND pokemon_id = ?', (poketag, ctx.author.id, pokemon_id))
                self.conn.commit()
            pokemon_name = "{} (#{})".format(pokemon_name.capitalize(), pokemon_id)
            messages_required = round(0.02 * level ** 2 + 0.2 * level + 1)
            experience_left = messages_required - experience
            experience_fraction = f"{experience}/{messages_required}"
            embed.add_field(name=pokemon_name, value=f"Poketag: {poketag.upper()}\nLevel: {level}\nEXP: {experience_fraction}", inline=True)
        return embed

    @commands.guild_only()
    @commands.command()
    async def party(self, ctx, *poketags: str):
        if len(poketags) == 0:
            self.cur.execute('SELECT position1, position2, position3, position4, position5, position6 FROM party WHERE member_id = ?', (ctx.author.id,))
            current_party = self.cur.fetchone()
            if current_party is not None:
                pokemon_data = [self.cur.execute('SELECT pokemon_name, level, experience FROM pokedex WHERE member_id = ? AND poketag = ?', (ctx.author.id, poketag.lower())).fetchone() for poketag in current_party if poketag != '-']
                experience = [exp for _, _, exp in pokemon_data]
                messages_required = [round(0.02 * level ** 2 + 0.2 * level + 1) for _, level, _ in pokemon_data]
                experience_left = [required - exp for required, exp in zip(messages_required, experience)]
                experience_fraction = [f"{exp}/{required}" for exp, required in zip(experience, messages_required)]
                output = [f"{poketag.upper()} - {pokemon_name.capitalize()} (Level {level}, EXP {exp_frac})" for poketag, (pokemon_name, level, _), exp_frac in zip(current_party, pokemon_data, experience_fraction)]
                output = "\n".join(output)
                embed = discord.Embed(title=f"{ctx.author.name}'s Party", description=output, color=discord.Color.random())
                await ctx.send(embed=embed)
            else:
                await ctx.send("You don't have a party yet.")
        elif len(poketags) != 6:
            await ctx.send("You must provide exactly 6 Pokétags.")
        else:
            self.cur.execute('SELECT poketag FROM pokedex WHERE member_id = ?', (ctx.author.id,))
            user_poketags = [row[0] for row in self.cur.fetchall()]
            if all(poketag.lower() in user_poketags or poketag == '-' for poketag in poketags):
                self.cur.execute('SELECT position1, position2, position3, position4, position5, position6 FROM party WHERE member_id = ?', (ctx.author.id,))
                current_party = self.cur.fetchone()

                if current_party is not None:
                    positions = dict(zip(['position1', 'position2', 'position3', 'position4', 'position5', 'position6'], poketags))

                    columns = []
                    values = []
                    for column, value in positions.items():
                        if value != '-':
                            columns.append(f"{column} = ?")
                            values.append(value)
                    columns = ", ".join(columns)
                    values.append(ctx.author.id)
                    self.cur.execute(f'UPDATE party SET {columns} WHERE member_id = ?', values)
                    self.conn.commit()
                    await ctx.send("Your party has been updated.")
                else:
                    self.cur.execute('INSERT INTO party (member_id, position1, position2, position3, position4, position5, position6) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                                    (ctx.author.id, *poketags))
                    self.conn.commit()
                    await ctx.send("Your party has been created.")
            else:
                await ctx.send("You do not have all of these Pokétags in your Pokédex.")

    @commands.guild_only()
    @commands.command()
    async def trade(self, ctx, user: commands.MemberConverter, poketag: str):
        """Initiate a trade with another user."""
        self.cur.execute('SELECT pokemon_name FROM pokedex WHERE member_id = ? AND poketag = ?', (ctx.author.id, poketag.lower()))
        pokemon_name = self.cur.fetchone()
        if pokemon_name is None:
            await ctx.send("You do not have that Pokémon in your Pokédex.")
            return
        if user == ctx.author:
            await ctx.send("You cannot trade with yourself.")
            return
        trade_message = await ctx.send(f"{user.mention}, {ctx.author.name} wants to trade their {pokemon_name[0].capitalize()} to you. Please reply with the Poketag of the Pokémon you are offering.")
        if not hasattr(self, "trades"):
            self.trades = {}
        self.trades[trade_message.id] = {"sender": ctx.author, "receiver": user, "sender_poketag": poketag.lower(), "receiver_poketag": None}
    
    # Define the on_command_error event handler
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        # Handle your errors here
        if isinstance(error, commands.CommandError):
            await ctx.send(error) # Send the error message to the context channel
        else:
            # All unhandled errors will print their original traceback
            print(f'Ignoring exception in command {ctx.command}:', file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        
    @commands.command()
    async def battle(self, ctx, opponent: discord.Member):
        if opponent.bot or ctx.author.id in self.battles or opponent.id in self.battles:
            return await ctx.send("Cannot start battle due to one of the conditions not being met.")

        # Fetch party tags and validate parties
        player1_party_tags = self.cur.execute('SELECT position1, position2, position3, position4, position5, position6 FROM party WHERE member_id = ?', (ctx.author.id,)).fetchone()
        player2_party_tags = self.cur.execute('SELECT position1, position2, position3, position4, position5, position6 FROM party WHERE member_id = ?', (opponent.id,)).fetchone()
        if not player1_party_tags or not player2_party_tags:
            raise commands.CommandError("Both players must have a party.")

        # Initialize parties and health
        player1_party = [self.cur.execute('SELECT pokemon_name FROM pokedex WHERE member_id = ? AND poketag = ?', (ctx.author.id, tag.lower())).fetchone()[0] for tag in player1_party_tags if tag != '-']
        player2_party = [self.cur.execute('SELECT pokemon_name FROM pokedex WHERE member_id = ? AND poketag = ?', (opponent.id, tag.lower())).fetchone()[0] for tag in player2_party_tags if tag != '-']
        player1_hp = {pokemon: self.get_pokemon_health(pokemon) for pokemon in player1_party}
        player2_hp = {pokemon: self.get_pokemon_health(pokemon) for pokemon in player2_party}

        # Start battle
        battle_embed = Embed(title=f"Battle: {ctx.author.display_name} VS {opponent.display_name}", description="")
        battle_message = await ctx.send(embed=battle_embed)
        await battle_message.add_reaction("⚔️")
        self.battles[ctx.author.id], self.battles[opponent.id] = opponent.id, ctx.author.id

        # Battle loop
        while player1_party and player2_party:
            p1_pokemon = player1_party[0]
            p2_pokemon = player2_party[0]

            # Damage calculation and HP update using list comprehensions and lambda functions
            calculate_damage = lambda move, multiplier: random.randint(10, 50) * multiplier
            p1_move, p1_type = self.get_random_move(p1_pokemon)
            p2_move, p2_type = self.get_random_move(p2_pokemon)

            # Inline get_multiplier logic
            def get_multiplier(damage_relations, opposing_type):
                return next((multiplier for key, multiplier in {
                    'double_damage_to': 2.0,
                    'half_damage_to': 0.5,
                    'no_damage_to': 0.0
                }.items() if opposing_type in [relation['name'] for relation in damage_relations[key]]), 1.0)

            p1_type_data = requests.get(self.type_url + p1_type).json()['damage_relations']
            p2_type_data = requests.get(self.type_url + p2_type).json()['damage_relations']
            p1_multiplier = get_multiplier(p1_type_data, p2_type)
            p2_multiplier = get_multiplier(p2_type_data, p1_type)

            # Calculate damage
            p1_damage = calculate_damage(p1_move, p1_multiplier)
            p2_damage = calculate_damage(p2_move, p2_multiplier)

            # Update HP
            player1_hp[p1_pokemon] = max(player1_hp[p1_pokemon] - p2_damage, 0)
            player2_hp[p2_pokemon] = max(player2_hp[p2_pokemon] - p1_damage, 0)

            # Update battle embed with current HP, moves, and multipliers
            battle_embed.clear_fields()
            battle_embed.add_field(name=f"{ctx.author.display_name}'s {p1_pokemon}", value=f"HP: {player1_hp[p1_pokemon]}\nMove: {p1_move.capitalize()} ({p1_multiplier}x)", inline=True)
            battle_embed.add_field(name=f"{opponent.display_name}'s {p2_pokemon}", value=f"HP: {player2_hp[p2_pokemon]}\nMove: {p2_move.capitalize()} ({p2_multiplier}x)", inline=True)
            
            # Check for defeated Pokémon and update embed description
            if player1_hp[p1_pokemon] <= 0:
                player1_party.pop(0)  # Remove the defeated pokemon from the party
                battle_embed.description += f"\n{ctx.author.display_name}'s {p1_pokemon} has been defeated!"
            if player2_hp[p2_pokemon] <= 0:
                player2_party.pop(0)  # Remove the defeated pokemon from the party
                battle_embed.description += f"\n{opponent.display_name}'s {p2_pokemon} has been defeated!"

            await battle_message.edit(embed=battle_embed)
            await asyncio.sleep(1)  # Adjust the sleep duration as needed

        # Declare the winner and update embed description
        if not player1_party:
            winner = opponent.display_name
        elif not player2_party:
            winner = ctx.author.display_name

        # Clear fields and update embed with the winner announced in bold
        battle_embed.clear_fields()
        battle_embed.description += f"\n**{winner} wins the battle!**"
        await battle_message.edit(embed=battle_embed)

        # Clean up after battle
        del self.battles[ctx.author.id], self.battles[opponent.id]

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle the completion of the trade."""
        if message.reference and message.reference.message_id in self.trades:
            trade = self.trades[message.reference.message_id]
            if message.author == trade["receiver"]:
                poketag = message.content.lower()
                self.cur.execute('SELECT pokemon_name FROM pokedex WHERE member_id = ? AND poketag = ?', (message.author.id, poketag))
                pokemon_name = self.cur.fetchone()
                if pokemon_name is None:
                    await message.channel.send("You do not have that Pokémon in your Pokédex.")
                    return
                trade["receiver_poketag"] = poketag
                self.cur.execute('UPDATE pokedex SET member_id = ? WHERE member_id = ? AND poketag = ?', (trade["receiver"].id, trade["sender"].id, trade["sender_poketag"]))
                self.cur.execute('UPDATE pokedex SET member_id = ? WHERE member_id = ? AND poketag = ?', (trade["sender"].id, trade["receiver"].id, trade["receiver_poketag"]))
                self.conn.commit()
                await message.channel.send(f"The trade between {trade['sender'].name} and {trade['receiver'].name} was completed successfully.")
                del self.trades[message.reference.message_id]
            else:
                await message.channel.send("Only the receiver of the trade can reply to this message.")

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