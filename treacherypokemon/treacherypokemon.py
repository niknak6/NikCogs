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
        pokemon_url = self.base_url + pokemon_name.lower().replace(" ", "-").replace(".", "")
        response = requests.get(pokemon_url)
        response.raise_for_status()
        pokemon_data = response.json()
        moves = pokemon_data['moves']
        move = random.choice(moves)
        move_name = move['move']['name']
        move_url = move['move']['url']
        response = requests.get(move_url)
        response.raise_for_status()
        move_data = response.json()
        type_name = move_data['type']['name']
        return (move_name, type_name)

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
        
    @commands.command()
    async def battle(self, ctx, opponent: discord.Member):
        if opponent.bot:
            await ctx.send("You can't battle bots!")
            return

        if ctx.author.id in self.battles or opponent.id in self.battles:
            await ctx.send("A user can only participate in one battle at a time.")
            return

        self.cur.execute('SELECT position1, position2, position3, position4, position5, position6 FROM party WHERE member_id = ?', (ctx.author.id,))
        player1_party_tags = self.cur.fetchone()
        self.cur.execute('SELECT position1, position2, position3, position4, position5, position6 FROM party WHERE member_id = ?', (opponent.id,))
        player2_party_tags = self.cur.fetchone()

        player1_party = [self.cur.execute('SELECT pokemon_name FROM pokedex WHERE member_id = ? AND poketag = ?', (ctx.author.id, poketag.lower())).fetchone()[0] for poketag in player1_party_tags if poketag != '-']
        player2_party = [self.cur.execute('SELECT pokemon_name FROM pokedex WHERE member_id = ? AND poketag = ?', (opponent.id, poketag.lower())).fetchone()[0] for poketag in player2_party_tags if poketag != '-']

        if not player1_party or not player2_party:
            await ctx.send("Both users must have a Pokémon in their party to battle.")
            return

        battle_embed = Embed(title=f"{ctx.author.name} challenges {opponent.name} to a battle!")
        battle_message = await ctx.send(embed=battle_embed)
        await battle_message.add_reaction("⚔️")

        def check(reaction: Reaction, user):
            return user in [ctx.author, opponent] and str(reaction.emoji) == "⚔️" and reaction.message.id == battle_message.id

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=900, check=check)
        except TimeoutError:
            del self.battles[ctx.author.id]
            await battle_message.edit(content="Battle request timed out.", embed=None)
            return

        self.battles[ctx.author.id] = opponent.id
        self.battles[opponent.id] = ctx.author.id

        player1_pokemon_index = player2_pokemon_index = 0
        p1_pokemon = player1_party[player1_pokemon_index]
        p2_pokemon = player2_party[player2_pokemon_index]
        p1_hp = self.get_pokemon_health(p1_pokemon)
        p2_hp = self.get_pokemon_health(p2_pokemon)

        # Add a new attribute to store the last 5 actions
        self.last_actions = []

        # Initialize the list with empty strings
        for _ in range(5):
            self.last_actions.append("")

        while player1_pokemon_index < len(player1_party) and player2_pokemon_index < len(player2_party):
            next_p1_pokemon = player1_party[player1_pokemon_index + 1] if player1_pokemon_index + 1 < len(player1_party) else None
            next_p2_pokemon = player2_party[player2_pokemon_index + 1] if player2_pokemon_index + 1 < len(player2_party) else None

            # Use the helper function to get a random move and its type for each pokemon
            p1_move, p1_type = self.get_random_move(p1_pokemon)
            p2_move, p2_type = self.get_random_move(p2_pokemon)

            # Use the requests module to get the JSON data for the types from the pokeapi.co api
            p1_type_url = self.type_url + p1_type
            p2_type_url = self.type_url + p2_type
            p1_type_data = requests.get(p1_type_url).json()
            p2_type_data = requests.get(p2_type_url).json()

            # Extract the damage relations from the JSON data and use them to calculate the damage multiplier for each move
            p1_damage_relations = p1_type_data['damage_relations']
            p2_damage_relations = p2_type_data['damage_relations']
            p1_multiplier = 1.0
            p2_multiplier = 1.0
            # Check if p1_type is in the double_damage_to list of p2_type
            if any(p1_type == relation['name'] for relation in p2_damage_relations['double_damage_to']):
                p1_multiplier = 2.0
            # Check if p1_type is in the half_damage_to list of p2_type
            if any(p1_type == relation['name'] for relation in p2_damage_relations['half_damage_to']):
                p1_multiplier = 0.5
            # Check if p1_type is in the no_damage_to list of p2_type
            if any(p1_type == relation['name'] for relation in p2_damage_relations['no_damage_to']):
                p1_multiplier = 0.0
            # Do the same for p2_type
            if any(p2_type == relation['name'] for relation in p1_damage_relations['double_damage_to']):
                p2_multiplier = 2.0
            if any(p2_type == relation['name'] for relation in p1_damage_relations['half_damage_to']):
                p2_multiplier = 0.5
            if any(p2_type == relation['name'] for relation in p1_damage_relations['no_damage_to']):
                p2_multiplier = 0.0

            # Use the damage multiplier to adjust the damage done by each move
            p2_hp -= random.randint(10, 50) * p1_multiplier
            if p2_hp <= 0:
                player2_pokemon_index += 1
                if player2_pokemon_index < len(player2_party):
                    p2_pokemon = next_p2_pokemon
                    p2_hp = self.get_pokemon_health(p2_pokemon)
                else:
                    break

            p1_hp -= random.randint(10, 50) * p2_multiplier
            if p1_hp <= 0:
                player1_pokemon_index += 1
                if player1_pokemon_index < len(player1_party):
                    p1_pokemon = next_p1_pokemon
                    p1_hp = self.get_pokemon_health(p1_pokemon)
                else:
                    break

            battle_embed.title = f"{ctx.author.name}'s {p1_pokemon} ({p1_type}) VS {opponent.name}'s {p2_pokemon} ({p2_type})"
            battle_embed.clear_fields()
            battle_embed.add_field(name=ctx.author.name, value=f"HP: {p1_hp}\nMove: {p1_move.capitalize()}", inline=False)
            battle_embed.add_field(name=opponent.name, value=f"HP: {p2_hp}\nMove: {p2_move.capitalize()}", inline=False)

            # Format the action string with the move name, the damage, and the multiplier
            p1_action = f"{p1_pokemon} used {p1_move.capitalize()} and dealt {round(random.randint(10, 50) * p1_multiplier)} damage to {p2_pokemon} ({p1_multiplier}x)"
            p2_action = f"{p2_pokemon} used {p2_move.capitalize()} and dealt {round(random.randint(10, 50) * p2_multiplier)} damage to {p1_pokemon} ({p2_multiplier}x)"

            # Remove the oldest action and insert the newest one at the beginning of the list
            self.last_actions.pop()
            self.last_actions.insert(0, p2_action)
            self.last_actions.pop()
            self.last_actions.insert(0, p1_action)

            # Join the list with newlines to create the field value
            actions_value = "\n".join(self.last_actions)

            # Add a new field to the embed with the actions value
            battle_embed.add_field(name="Last 5 Actions", value=actions_value, inline=False)

            await battle_message.edit(embed=battle_embed)

            await asyncio.sleep(0.01)

        winner = ctx.author if player1_pokemon_index < len(player1_party) else opponent
        await battle_message.edit(content=f"{winner.name} wins the battle!", embed=None)
        del self.battles[ctx.author.id]
        del self.battles[opponent.id]

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