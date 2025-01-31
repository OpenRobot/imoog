from __future__ import annotations

from typing import (
    Tuple,
    Mapping,
    List,
    Any
)

import asyncpg

from .drivers import Driver # import the base driver impl


class PostgresDriver(Driver):
    async def connect(self, **kwargs):
        self.identifier = "postgres"

        connection_uri = kwargs["connection_uri"]
        max_size = kwargs["max_size"]
        min_size = kwargs["min_size"]
        table_name = kwargs["table_name"]

        self._table_name: str = table_name

        pool = await asyncpg.create_pool(
            connection_uri,
            min_size=min_size,
            max_size=max_size
        )
        
        self._connection = pool
        
        # Creating the table in psql on connect
        # if it doesn't exist.
        async with self._connection.acquire() as conn:
            query = (
                f"CREATE TABLE IF NOT EXISTS {table_name}("
                "name TEXT,"
                "image BYTEA,"
                "mime TEXT"
                ")"
            )
            
            await conn.execute(query)

        return self._connection

    async def insert(
        self,
        image: bytes,
        name: str,
        mime: str
    ):
        table_name = self._table_name
        async with self._connection.acquire() as conn:
            query = (
                f"INSERT INTO {table_name} (name, image, mime) VALUES ($1, $2, $3)"
            ) # this isn't vulnerable to SQL injection, as we have HARD-CODED values
            # controlled by YOU. So if you mess up, this isn't on us.
            await conn.execute(query, name, image, mime)

        return 0

    async def fetch(
        self,
        name: str
    ) -> Tuple[bytes, str]:
        table_name = self._table_name

        async with self._connection.acquire() as conn:
            query = (
                f"SELECT image, mime FROM {table_name} "
                "WHERE name = $1"
            )
            row = await conn.fetchrow(query, name)
    
        image = row["image"]
        mime = row["mime"]
        decompressed = self.decompress(image)
        return (decompressed, mime)

    async def delete(
        self,
        name: str
    ) -> bool:
        table_name = self._table_name
        
        try:
            async with self._connection.acquire() as conn:
                query = (
                    f"DELETE FROM {table_name} "
                    "WHERE name = $1"
                )
                await conn.execute(query, name)
        except Exception:
            return False
        else:
            return True

    async def fetch_all(self) -> List[Mapping[str, Any]]:
        table_name = self._table_name

        async with self._connection.acquire() as conn:
            rows = await conn.fetch(f"SELECT * FROM {table_name}")

        return (rows, "name")

    async def cleanup(self):
        return await self._connection.close()

_DRIVER = PostgresDriver
_DRIVER_TYPE = "POSTGRES"
