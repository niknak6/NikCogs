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
from PIL import Image
from io import BytesIO

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

    def get_random_move(self, ctx, pokemon_name):
        # Fetch the member's ID from the context
        member_id = ctx.author.id

        # Fetch the Pokémon's level from the database
        self.cur.execute('SELECT level FROM pokedex WHERE member_id = ? AND pokemon_name = ?', (member_id, pokemon_name))
        result = self.cur.fetchone()
        pokemon_level = result[0] if result else 1  # Default to level 1 if not found

        # Proceed with fetching the Pokémon's moves from the API
        pokemon_url = f"{self.base_url}{pokemon_name.lower().replace(' ', '-').replace('.', '')}"
        pokemon_data = requests.get(pokemon_url).json()
        
        # Filter moves by level_learned_at and move_learn_method
        moves = [move for move in pokemon_data['moves']
                if any(version_group['level_learned_at'] <= pokemon_level and 
                        version_group['move_learn_method']['name'] == 'level-up'
                        for version_group in move['version_group_details'])]
        
        # Define a set of moves to blacklist
        blacklisted_moves = {
            'after-you', 'quash', 'helping-hand', 'ally-switch', 
            'follow-me', 'rage-powder', 'aromatic-mist', 
            'hold-hands', 'spotlight'
        }

        # Filter out blacklisted moves
        moves = [move for move in moves if move['move']['name'] not in blacklisted_moves]

        # If no moves are available at the current level or all are blacklisted, default to "NULL"
        if not moves:
            return "NULL", "NULL", 0  # Return 0 as the default move power
        
        # Select a random move from the filtered list
        move = random.choice(moves)
        move_data = requests.get(move['move']['url']).json()
        move_power = move_data.get('power', 0)  # Use get() to return 0 if 'power' key is not present
        return move['move']['name'], move_data['type']['name'], move_power

    def get_pokemon_health(self, pokemon_name):
        pokemon_url = self.base_url + pokemon_name.lower().replace(" ", "-").replace(".", "")
        response = requests.get(pokemon_url)
        response.raise_for_status()
        pokemon_data = response.json()
        hp = pokemon_data['stats'][0]['base_stat']
        return hp

    
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
        
    def combatsprite(self, ctx, player1_pokemon_name, player2_pokemon_name):
        # Fetch sprite URLs for both Pokémon in battle
        player1_sprite_url = f"{self.base_url}{player1_pokemon_name.lower().replace(' ', '-').replace('.', '')}"
        player2_sprite_url = f"{self.base_url}{player2_pokemon_name.lower().replace(' ', '-').replace('.', '')}"

        # Get the sprite data from the API
        player1_response = requests.get(player1_sprite_url)
        player1_data = player1_response.json()
        player1_sprite = player1_data['sprites']['other']['official-artwork']['front_default']

        player2_response = requests.get(player2_sprite_url)
        player2_data = player2_response.json()
        player2_sprite = player2_data['sprites']['other']['official-artwork']['front_default']

        # Download the sprites using requests and open them with PIL
        player1_sprite_image = Image.open(BytesIO(requests.get(player1_sprite).content))
        player2_sprite_image = Image.open(BytesIO(requests.get(player2_sprite).content))

        # Create a new image with a width that's the sum of both sprites' widths
        total_width = player1_sprite_image.width + player2_sprite_image.width
        max_height = max(player1_sprite_image.height, player2_sprite_image.height)
        combined_sprite = Image.new('RGBA', (total_width, max_height))

        # Paste the two sprites side by side in the new image
        combined_sprite.paste(player1_sprite_image, (0, 0))
        combined_sprite.paste(player2_sprite_image, (player1_sprite_image.width, 0))

        # Save the combined image to a BytesIO object and create a discord.File from it
        combined_image_io = BytesIO()
        combined_sprite.save(combined_image_io, format='PNG')
        combined_image_io.seek(0)
        combined_image_file = discord.File(combined_image_io, filename='combined_sprite.png')

        return combined_image_file
    
    @commands.command()
    async def battle(self, ctx, opponent: discord.Member):
        if opponent.bot or ctx.author.id in self.battles or opponent.id in self.battles:
            return await ctx.send("Cannot start battle due to one of the conditions not being met.")

        # Helper function to format move names
        def format_move_name(move_name):
            return ' '.join(word.capitalize() for word in move_name.replace('-', ' ').split())

        # Fetch and validate parties
        def fetch_party(member_id):
            return [self.cur.execute('SELECT pokemon_name FROM pokedex WHERE member_id = ? AND poketag = ?', (member_id, tag.lower())).fetchone()[0]
                    for tag in self.cur.execute('SELECT position1, position2, position3, position4, position5, position6 FROM party WHERE member_id = ?', (member_id,)).fetchone()
                    if tag != '-']

        player1_party, player2_party = fetch_party(ctx.author.id), fetch_party(opponent.id)
        if not player1_party or not player2_party:
            raise commands.CommandError("Both players must have a party.")

        # Initialize health
        player1_hp = {pokemon: self.get_pokemon_health(pokemon) for pokemon in player1_party}
        player2_hp = {pokemon: self.get_pokemon_health(pokemon) for pokemon in player2_party}

        # Get the initial Pokémon names for sprite generation
        player1_pokemon_name = player1_party[0]
        player2_pokemon_name = player2_party[0]

        # Generate the combined sprite image
        combined_image_file = self.combatsprite(ctx, player1_pokemon_name, player2_pokemon_name)

        # Create an embed with the combined image
        battle_embed = discord.Embed(title=f"Battle: {ctx.author.display_name} VS {opponent.display_name}", description="")
        battle_embed.add_field(name=f"{ctx.author.display_name}'s {player1_party[0]} HP", value="Loading...", inline=True)
        battle_embed.add_field(name=f"{opponent.display_name}'s {player2_party[0]} HP", value="Loading...", inline=True)
        battle_embed.add_field(name="Moves", value="Waiting...", inline=False)
        battle_embed.set_image(url="attachment://combined_sprite.png")

        # Send the initial battle message with the combined image
        battle_message = await ctx.send(file=combined_image_file, embed=battle_embed)

        # Add reactions to the battle message for interactive battling
        await battle_message.add_reaction("⚔️")
        self.battles[ctx.author.id], self.battles[opponent.id] = opponent.id, ctx.author.id

        # Battle loop
        while player1_party and player2_party:
            # Inline functions for damage calculation and multiplier retrieval
            calculate_damage = lambda move_power, multiplier: move_power * multiplier
            get_multiplier = lambda damage_relations, opposing_type: next((multiplier for key, multiplier in {
                'double_damage_to': 2.0, 'half_damage_to': 0.5, 'no_damage_to': 0.0
            }.items() if opposing_type in [relation['name'] for relation in damage_relations[key]]), 1.0)

            # Battle mechanics
            moves_display = ""
            for player_party, player_hp, player_display in [(player1_party, player1_hp, ctx.author.display_name), (player2_party, player2_hp, opponent.display_name)]:
                pokemon = player_party[0]
                move, type_, move_power = self.get_random_move(ctx, pokemon)
                type_data = requests.get(self.type_url + type_).json()['damage_relations']
                multiplier = get_multiplier(type_data, type_)
                damage = calculate_damage(move_power, multiplier)
                player_hp[pokemon] = max(player_hp[pokemon] - damage, 0)
                hp_field_index = 0 if player_display == ctx.author.display_name else 1
                battle_embed.set_field_at(hp_field_index, name=f"{player_display}'s {pokemon} HP", value=f"{player_hp[pokemon]}", inline=True)
                formatted_move_name = format_move_name(move) if move != "NULL" else "No move available"
                moves_display += f"{player_display}'s {pokemon}: {formatted_move_name} ({multiplier}x)\n"
                if player_hp[pokemon] <= 0:
                    player_party.pop(0)
                    battle_embed.description += f"\n{player_display}'s {pokemon} has been defeated!"
                    if player_party:
                        new_pokemon = player_party[0]
                        new_pokemon_hp = player_hp[new_pokemon]
                        # Update the combined sprite image with the new Pokémon
                        if player_display == ctx.author.display_name:
                            player1_pokemon_name = new_pokemon
                        else:
                            player2_pokemon_name = new_pokemon
                        combined_image_file = self.combatsprite(ctx, player1_pokemon_name, player2_pokemon_name)
                        battle_embed.set_image(url="attachment://combined_sprite.png")
                        battle_embed.set_field_at(hp_field_index, name=f"{player_display}'s {new_pokemon} HP", value=f"{new_pokemon_hp}", inline=True)
                        await battle_message.edit(embed=battle_embed, attachments=[combined_image_file])
                        await asyncio.sleep(3)  # Add a 3-second cooldown
                    else:
                        winner = opponent.display_name if player_display == ctx.author.display_name else ctx.author.display_name
                        battle_embed.clear_fields()
                        battle_embed.description += f"\n**{winner} wins the battle!**"
                        battle_embed.set_image(url=None)  # Remove the image from the embed
                        await battle_message.edit(content="", embed=battle_embed, attachments=[])

                        # Get the winner's party
                        if winner == ctx.author.display_name:
                            winner_id = ctx.author.id
                            loser_id = opponent.id
                        else:
                            winner_id = opponent.id
                            loser_id = ctx.author.id

                        self.cur.execute('SELECT position1, position2, position3, position4, position5, position6 FROM party WHERE member_id = ?', (winner_id,))
                        winner_party = self.cur.fetchone()

                        # Update the levels of the winner's Pokémon
                        for poketag in winner_party:
                            if poketag != '-':
                                self.cur.execute('UPDATE pokedex SET level = level + 0 WHERE member_id = ? AND poketag = ?', (winner_id, poketag.lower()))

                        self.conn.commit()

                        # Inform the winner that their Pokémon have leveled up
                        winner_member = ctx.guild.get_member(winner_id)
                        await ctx.send(f"{winner_member.mention}, your Pokémon have leveled up after winning the battle!")

                        del self.battles[ctx.author.id], self.battles[opponent.id]
                        return

            battle_embed.set_field_at(2, name="Moves", value=moves_display.strip(), inline=False)
            await battle_message.edit(embed=battle_embed)
            await asyncio.sleep(.5)

        # If the loop exits naturally, check for any remaining Pokémon and declare the winner
        winner = ctx.author.display_name if player2_party else opponent.display_name
        battle_embed.clear_fields()
        battle_embed.description += f"\n**{winner} wins the battle!**"
        battle_embed.set_image(url=None)  # Remove the image from the embed
        await battle_message.edit(content="", embed=battle_embed, attachments=[])
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