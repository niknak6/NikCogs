from redbot.core import commands
from redbot.core.data_manager import cog_data_path
import sqlite3

class BetaAlpha(commands.Cog):
    """Interacts with a database for querying and updating."""
    
    def __init__(self, bot):
        self.bot = bot
        db_path = cog_data_path(self) / 'pokemon.db'
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def cog_unload(self):
        self.conn.close()

    async def dynamic_query_db(self, table, columns, **filters):
        query = f"SELECT {columns} FROM {table} WHERE " + " AND ".join([f"{k} = ?" for k in filters]) if filters else "1=1"
        values = tuple(filters.values())
        try:
            self.cursor.execute(query, values)
            return [dict(zip([col[0] for col in self.cursor.description], row)) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            return []

    async def update_field(self, table, field, value, **filters):
        where_clause = " AND ".join([f"{k} = ?" for k in filters]) if filters else "1=1"
        query = f"UPDATE {table} SET {field} = ? WHERE {where_clause}"
        values = (*filters.values(), value)
        try:
            self.cursor.execute(query, values)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            return False
        return True

    @commands.command(name="querydb")
    async def query_db(self, ctx, table: str, columns: str, **filters):
        """
        Queries the database based on provided table, columns, and filters.
        """
        result = await self.dynamic_query_db(table, columns, **filters)
        await ctx.send(f"Query Result: {result}" if result else "No results found.")

    @commands.command(name="updatedb")
    async def update_db(self, ctx, table: str, field: str, value, **filters):
        """
        Updates a field in the database based on provided table, field, value, and filters.
        """
        success = await self.update_field(table, field, value, **filters)
        if success:
            await ctx.send("Update successful.")
        else:
            await ctx.send("Update failed.")

async def setup(bot):
    bot.add_cog(BetaAlpha(bot))
