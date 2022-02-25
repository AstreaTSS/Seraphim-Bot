#!/usr/bin/env python3.8
import asyncio
import enum
import logging
import typing

import asyncpg
import attr
import discord
from lru import LRU

import common.classes as cclass


class ReactorType(enum.Enum):
    """A way of sorting through the reactor list types."""

    ORI_REACTORS = 1
    VAR_REACTORS = 2
    ALL_REACTORS = 3


@attr.s(slots=True, eq=False)
class StarboardEntry:
    """A way of representing a starboard entry in an easy way."""

    ori_mes_id: int = attr.ib()
    ori_chan_id: int = attr.ib()
    star_var_id: typing.Optional[int] = attr.ib()
    starboard_id: typing.Optional[int] = attr.ib()
    author_id: int = attr.ib()
    ori_reactors: typing.Set[int] = attr.ib(converter=set)
    var_reactors: typing.Set[int] = attr.ib(converter=set)
    guild_id: int = attr.ib()
    forced: bool = attr.ib()
    frozen: bool = attr.ib()
    trashed: bool = attr.ib()
    updated: bool = attr.ib(default=False)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.ori_mes_id == other.ori_mes_id

    @classmethod
    def from_row(cls, row):
        """Returns an entry from a row."""
        return cls(
            row["ori_mes_id"],
            row["ori_chan_id"],
            row["star_var_id"],
            row["starboard_id"],
            row["author_id"],
            row["ori_reactors"],
            row["var_reactors"],
            row["guild_id"],
            row["forced"],
            row["frozen"],
            row["trashed"],
        )

    @classmethod
    def new_entry(
        cls,
        mes: discord.Message,
        author_id: int,
        reactor_id: typing.Optional[int],
        forced: bool = False,
    ):
        """Returns a new entry from base data."""
        if reactor_id:
            return cls(
                mes.id,
                mes.channel.id,
                None,
                None,
                author_id,
                {reactor_id},
                set(),
                mes.guild.id,
                forced,
                False,
                False,
                updated=True,
            )
        else:
            return cls(
                mes.id,
                mes.channel.id,
                None,
                None,
                author_id,
                set(),
                set(),
                mes.guild.id,
                forced,
                False,
                False,
                updated=True,
            )

    def get_reactors(self) -> typing.Set[int]:
        """Gets the total reactors, a mix of ori and var reactors."""
        if not isinstance(self.ori_reactors, set):
            self.ori_reactors = set(self.ori_reactors)
        if not isinstance(self.var_reactors, set):
            self.var_reactors = set(self.var_reactors)

        return self.ori_reactors | self.var_reactors

    def get_reactors_from_type(self, type_of_reactor: ReactorType) -> typing.Set[int]:
        """Gets the reactors for the type specified. Useful if you want the output to vary."""
        if type_of_reactor == ReactorType.ORI_REACTORS:
            return self.ori_reactors
        elif type_of_reactor == ReactorType.VAR_REACTORS:
            return self.var_reactors
        elif type_of_reactor == ReactorType.ALL_REACTORS:
            return self.get_reactors()
        else:
            raise AttributeError("Invalid reactor type.")

    def set_reactors_of_type(
        self, type_of_reactor: ReactorType, input: typing.Set[int]
    ):
        """Sets the reactors for the type specified. Useful if you want the output to vary."""
        if type_of_reactor == ReactorType.ORI_REACTORS:
            self.ori_reactors = input
        elif type_of_reactor == ReactorType.VAR_REACTORS:
            self.var_reactors = input
        else:
            raise AttributeError("Invalid reactor type.")

    def check_reactor(
        self, reactor_id: int, type_of_reactor=ReactorType.ALL_REACTORS
    ) -> bool:
        """Sees if the reactor ID provided is in the reactors for the type specified. Useful if you want the output to vary."""
        if type_of_reactor == ReactorType.ORI_REACTORS:
            return reactor_id in self.ori_reactors
        elif type_of_reactor == ReactorType.VAR_REACTORS:
            return reactor_id in self.var_reactors
        elif type_of_reactor == ReactorType.ALL_REACTORS:
            return reactor_id in self.get_reactors()
        else:
            raise AttributeError("Invalid reactor type.")

    def add_reactor(self, reactor_id: int, type_of_reactor: ReactorType):
        """Adds a reactor to the reactor type specified. Will silently fail if the entry already exists."""
        if reactor_id not in self.get_reactors():
            if type_of_reactor == ReactorType.ORI_REACTORS:
                self.ori_reactors.add(reactor_id)
            elif type_of_reactor == ReactorType.VAR_REACTORS:
                self.var_reactors.add(reactor_id)
            else:
                raise AttributeError("Invalid reactor type.")

    def remove_reactor(self, reactor_id: int):
        """Removes a reactor from an entry. Will silently fail if the entry does not exists."""
        if reactor_id in self.get_reactors():
            self.ori_reactors.discard(reactor_id)
            self.var_reactors.discard(reactor_id)


@attr.s(slots=True, eq=False, hash=False)
class StarboardSQLEntry:
    query: str = attr.ib()
    args: typing.Sequence[typing.Any] = attr.ib()

    def __hash__(self) -> int:
        return self.args[0]

    def __eq__(self, other) -> int:
        # if the ori_mes_id is the same with both
        # ensures discard for sets work as intended
        return isinstance(other, StarboardSQLEntry) and other.args[0] == self.args[0]


@attr.s(slots=True, init=False)
class StarboardEntries:
    """A way of managing starboard entries.
    Sort of like an ORM, but also not fully."""

    _pool: asyncpg.Pool = attr.ib()
    # note: entry cache isn't really a dict, but for typehinting purposes this works
    _entry_cache: typing.Dict[int, StarboardEntry] = attr.ib()
    _sql_loop_task: asyncio.Task = attr.ib()
    _sql_queries: cclass.SetUpdateAsyncQueue = attr.ib()

    def __init__(self, pool: asyncpg.Pool, cache_size: int = 200):
        self._pool = pool
        self._entry_cache = LRU(
            cache_size
        )  # the 200 should be raised as the bot grows bigger
        self._sql_queries = cclass.SetUpdateAsyncQueue()

        loop = asyncio.get_event_loop()
        self._sql_loop_task = loop.create_task(self._sql_loop())

    def stop(self):
        """Stops the SQL task loop."""
        self._sql_loop_task.cancel()

    async def _sql_loop(self):
        """Actually runs SQL updating, hopefully one after another.

        Saves speed on adding, deleting, and updating by offloading
        this step here."""
        try:
            while True:
                entry = await self._sql_queries.get()
                logging.getLogger("discord").debug(f"Running {entry.query}.")
                await self._pool.execute(entry.query, timeout=60, *entry.args)
                self._sql_queries.task_done()
        except asyncio.CancelledError:
            pass

    def _get_required_from_entry(self, entry: StarboardEntry):
        """Transforms data into the form needed for databases."""
        return (
            entry.ori_mes_id,
            entry.ori_chan_id,
            entry.star_var_id,
            entry.starboard_id,
            entry.author_id,
            list(entry.ori_reactors),
            list(entry.var_reactors),
            entry.guild_id,
            entry.forced,
            entry.frozen,
            entry.trashed,
        )

    def _str_builder_to_insert(
        self, str_builder: typing.List[str], entry: StarboardEntry
    ):
        """Takes data from a string builder list and eventually
        puts the data needed into the _sql_queries variable."""
        query = "".join(str_builder)
        args = self._get_required_from_entry(entry)
        self._sql_queries.put_nowait(StarboardSQLEntry(query, args))

    def _handle_upsert(self, entry: StarboardEntry):
        """Upserts an entry by using an INSERT with an ON CONFLICT cause.
        This is a PostgreSQL-specific feature, so that's nice!"""
        str_builder = [
            "INSERT INTO starboard(ori_mes_id, ori_chan_id, star_var_id, ",
            "starboard_id, author_id, ori_reactors, var_reactors, ",
            "guild_id, forced, frozen, trashed) VALUES($1, $2, $3, $4, ",
            "$5, $6, $7, $8, $9, $10, $11) ON CONFLICT (ori_mes_id) DO UPDATE ",
            "SET ori_chan_id = $2, star_var_id = $3, starboard_id = $4, ",
            "author_id = $5, ori_reactors = $6, var_reactors = $7, guild_id = $8, ",
            "forced = $9, frozen = $10, trashed = $11",
        ]
        self._str_builder_to_insert(str_builder, entry)

    def upsert(self, entry: StarboardEntry):
        """Either adds or updates an entry in the collection of entries."""
        temp_dict = {entry.ori_mes_id: entry}
        if entry.star_var_id:
            temp_dict[entry.star_var_id] = entry

        self._entry_cache.update(**temp_dict)  # type: ignore this is valid i promise
        self._handle_upsert(entry)

    def delete(self, entry_id: int):
        """Removes an entry from the collection of entries."""
        self._entry_cache.pop(entry_id, None)
        self._sql_queries.put_nowait(
            StarboardSQLEntry("DELETE FROM starboard WHERE ori_mes_id = $1", [entry_id])
        )

    async def get(
        self, entry_id: int, check_for_var: bool = False
    ) -> typing.Optional[StarboardEntry]:
        """Gets an entry from the collection of entries."""
        entry = None

        if self._entry_cache.has_key(entry_id):  # type: ignore
            entry = self._entry_cache[entry_id]
        else:
            entry = discord.utils.find(
                lambda e: e and e.star_var_id == entry_id, self._entry_cache.values()
            )

        if not entry:
            async with self._pool.acquire() as conn:
                data = await conn.fetchrow(
                    f"SELECT * FROM starboard WHERE ori_mes_id = {entry_id} OR star_var_id = {entry_id}"
                )
                if data:
                    entry = StarboardEntry.from_row(data)
                    self._entry_cache[entry_id] = entry

        if entry and check_for_var and not entry.star_var_id:
            return None

        return entry

    async def select_query(self, query: str):
        """Selects the starboard database directly for entries based on the query."""
        async with self._pool.acquire() as conn:
            data = await conn.fetch(f"SELECT * FROM starboard WHERE {query}")

            if not data:
                return None
            return tuple(StarboardEntry.from_row(row) for row in data)

    async def raw_query(self, query: str):
        """Runs the raw query against the pool, assuming the results are starboard entries."""
        async with self._pool.acquire() as conn:
            data = await conn.fetch(query)

            if not data:
                return None
            return tuple(StarboardEntry.from_row(row) for row in data)

    async def super_raw_query(self, query: str):
        """You want a raw query? You'll get one."""
        async with self._pool.acquire() as conn:
            return conn.fetch(query)

    async def query_entries(
        self, seperator: str = "AND", **conditions: typing.Dict[str, str]
    ) -> typing.Optional[typing.Tuple[StarboardEntry, ...]]:
        """Queries entries based on conditions provided.

        For example, you could do `query_entries(guild_id=143425)` to get
        entries with that guild id."""
        sql_conditions: list[str] = [
            f"{key} = {value}" for key, value in conditions.items()
        ]
        combined_statements = f" {seperator} ".join(sql_conditions)

        async with self._pool.acquire() as conn:
            data = await conn.fetch(
                f"SELECT * FROM starboard WHERE {combined_statements}"
            )

            if not data:
                return None
            return tuple(StarboardEntry.from_row(row) for row in data)

    async def get_random(self, guild_id: int) -> typing.Optional[StarboardEntry]:
        """Gets a random entry from a guild."""
        # query adapted from
        # https://github.com/Rapptz/RoboDanny/blob/1fb95d76d1b7685e2e2ff950e11cddfc96efbfec/cogs/stars.py#L1082
        query = """SELECT *
                   FROM starboard
                   WHERE guild_id=$1
                   AND star_var_id IS NOT NULL
                   OFFSET FLOOR(RANDOM() * (
                       SELECT COUNT(*)
                       FROM starboard
                       WHERE guild_id=$1
                       AND star_var_id IS NOT NULL
                   ))
                   LIMIT 1
                """

        async with self._pool.acquire() as conn:
            data = await conn.fetchrow(query, guild_id)
            if not data:
                return None
            return StarboardEntry.from_row(data)
