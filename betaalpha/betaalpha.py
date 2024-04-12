from redbot.core import commands
from redbot.core.data_manager import cog_data_path
import sqlite3
from typing import Dict, List, Any

class BetaAlpha(commands.Cog):
    """Interacts with a database for querying and updating."""
    
    def __init__(self, bot):
        self.bot = bot
        db_path = cog_data_path(self) / 'pokemon.db'
        self.conn = sqlite3.connect(db_path)

    def cog_unload(self):
        self.conn.close()

    async def execute_query(self, query: str, values: tuple = ()) -> List[Dict[str, Any]]:
        """Executes a query and returns the results as a list of dictionaries."""
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(query, values)
                if query.lower().startswith("select"):
                    columns = [col[0] for col in cursor.description]
                    return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
        return []

    @commands.command(name="querydb")
    async def query_db(self, ctx, table: str, columns: str, **filters: str):
        """Queries the database based on provided table, columns, and filters."""
        where_clause = " AND ".join([f"{k} = ?" for k in filters]) if filters else "1=1"
        query = f"SELECT {columns} FROM {table} WHERE {where_clause}"
        result = await self.execute_query(query, tuple(filters.values()))
        await ctx.send(f"Query Result: {result}" if result else "No results found.")

    @commands.command(name="updatedb")
    async def update_db(self, ctx, table: str, field: str, value: str, **filters: str):
        """Updates a field in the database based on provided table, field, value, and filters."""
        where_clause = " AND ".join([f"{k} = ?" for k in filters]) if filters else "1=1"
        query = f"UPDATE {table} SET {field} = ? WHERE {where_clause}"
        await self.execute_query(query, (*filters.values(), value))
        await ctx.send("Update successful.")

async def setup(bot):
    bot.add_cog(BetaAlpha(bot))
