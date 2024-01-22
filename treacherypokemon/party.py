import random, requests, logging, sqlite3, secrets, discord
from redbot.core import commands, Config
from redbot.core.data_manager import cog_data_path
from treacherypokemon import TreacheryPokemon # Import the TreacheryPokemon class from the treacherypokemon.py file

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