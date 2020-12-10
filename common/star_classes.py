#!/usr/bin/env python3.7
import discord, collections, enum
import typing, random

class ReactorType(enum.Enum):
    """A way of sorting through the reactor list types."""
    ORI_REACTORS = 1
    VAR_REACTORS = 2
    ALL_REACTORS = 3

class StarboardEntry():
    """A way of representing a starboard entry in an easy way."""

    __slots__ = ("ori_mes_id", "ori_chan_id", "star_var_id", "starboard_id", "author_id",
         "ori_reactors", "var_reactors", "guild_id", "forced", "updated")

    def __repr__(self):
        return (f"<StarboardEntry ori_mes_id={self.ori_mes_id} ori_chan_id={self.ori_chan_id} star_var_id={self.star_var_id} " +
            f"starboard_id={self.starboard_id} author_id={self.author_id} ori_reactors={(self.ori_reactors)} " +
            f"var_reactors={(self.var_reactors)} guild_id={self.guild_id} forced={self.forced} updated={self.updated}>")

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.ori_mes_id == other.ori_mes_id

    def __init__(self, ori_mes_id, ori_chan_id, star_var_id, starboard_id,
        author_id, ori_reactors, var_reactors, guild_id, forced, updated = False):
        self.ori_mes_id = ori_mes_id
        self.ori_chan_id = ori_chan_id
        self.star_var_id = star_var_id
        self.starboard_id = starboard_id
        self.author_id = author_id
        self.ori_reactors = set(ori_reactors)
        self.var_reactors = set(var_reactors)
        self.guild_id = guild_id
        self.forced = forced
        self.updated = updated

    @classmethod
    def from_row(cls, row):
        """Returns an entry from a row."""
        data = row["data"]
        return cls(row["ori_mes_id"], data["ori_chan_id"], data["star_var_id"], data["starboard_id"],
            data["author_id"], data["ori_reactors"], data["var_reactors"], data["guild_id"], data["forced"])

    @classmethod
    def new_entry(cls, mes: discord.Message, author_id, reactor_id, forced = False):
        """Returns a new entry from base data."""
        if reactor_id:
            return cls(mes.id, mes.channel.id, None, None, author_id, {reactor_id}, set(), mes.guild.id, forced, updated=True)
        else:
            return cls(mes.id, mes.channel.id, None, None, author_id, set(), set(), mes.guild.id, forced, updated=True)

    def to_dict(self) -> dict:
        """Converts this class to a dict."""
        result = {
            key: getattr(self, key)
            for key in self.__slots__
            if hasattr(self, key)
        }

        return result

    def get_reactors(self) -> typing.Set[int]:
        """Gets the total reactors, a mix of ori and var reactors."""
        return self.ori_reactors | self.var_reactors

    def get_reactors_from_type(self, type_of_reactor: ReactorType) -> typing.List[int]:
        """Gets the reactors for the type specified. Useful if you want the output to vary."""
        if type_of_reactor == ReactorType.ORI_REACTORS:
            return self.ori_reactors
        elif type_of_reactor == ReactorType.VAR_REACTORS:
            return self.var_reactors
        elif type_of_reactor == ReactorType.ALL_REACTORS:
            return self.get_reactors()
        else:
            raise AttributeError("Invalid reactor type.")

    def set_reactors_of_type(self, type_of_reactor: ReactorType, input: set):
        """Sets the reactors for the type specified. Useful if you want the output to vary."""
        if type_of_reactor == ReactorType.ORI_REACTORS:
            self.ori_reactors = input
        elif type_of_reactor == ReactorType.VAR_REACTORS:
            self.var_reactors =  input
        else:
            raise AttributeError("Invalid reactor type.")

    def check_reactor(self, reactor_id, type_of_reactor = ReactorType.ALL_REACTORS) -> bool:
        """Sees if the reactor ID provided is in the reactors for the type specified. Useful if you want the output to vary."""
        if type_of_reactor == ReactorType.ORI_REACTORS:
            return reactor_id in self.ori_reactors
        elif type_of_reactor == ReactorType.VAR_REACTORS:
            return reactor_id in self.var_reactors
        elif type_of_reactor == ReactorType.ALL_REACTORS:
            return reactor_id in self.get_reactors()
        else:
            raise AttributeError("Invalid reactor type.")

    def add_reactor(self, reactor_id, type_of_reactor: ReactorType):
        """Adds a reactor to the reactor type specified. Will silently fail if the entry already exists."""
        if not reactor_id in self.get_reactors():
            if type_of_reactor == ReactorType.ORI_REACTORS:
                self.ori_reactors.add(reactor_id)
            elif type_of_reactor == ReactorType.VAR_REACTORS:
                self.var_reactors.add(reactor_id)
            else:
                raise AttributeError("Invalid reactor type.")

    def remove_reactor(self, reactor_id):
        """Removes a reactor from an entry. Will silently fail if the entry does not exists."""
        if reactor_id in self.get_reactors():
            self.ori_reactors.discard(reactor_id)
            self.var_reactors.discard(reactor_id)


class StarboardEntries():
    """A way of managing starboard entries."""

    __slots__ = ("entries", "added", "updated", "removed")

    def __init__(self):
        self.entries = collections.defaultdict(lambda: None)
        self.added = set()
        self.updated = set()
        self.removed = set()

    def reset_deltas(self):
        """Resets the deltas so that they have nothing."""
        self.added = set()
        self.updated = set()
        self.removed = set()

    def init_add(self, entry: StarboardEntry):
        """Adds an entry to the list of entries during initialization. Or, well, the dict of entries.
        Yes, it's a one-line difference"""
        if self.entries[entry.ori_mes_id] == None:
            self.entries[entry.ori_mes_id] = entry
        else:
            raise Exception(f"Entry {entry.ori_mes_id} already exists.")

    def add(self, entry: StarboardEntry):
        """Adds an entry to the list of entries. Or, well, the dict of entries."""
        if self.entries[entry.ori_mes_id] == None:
            self.entries[entry.ori_mes_id] = entry
            self.added.add(entry.ori_mes_id)
        else:
            raise Exception(f"Entry {entry.ori_mes_id} already exists.")

    def delete(self, entry_id):
        """Removes an entry from the dict of entries."""
        del self.entries[entry_id]

        if entry_id in self.added:
            self.added.discard(entry_id)
        else:
            if entry_id in self.updated:
                self.updated.discard(entry_id)
            self.removed.add(entry_id)

    def update(self, entry: StarboardEntry):
        """Updates an entry in the dict of entries."""
        if self.entries[entry.ori_mes_id] != None:
            self.entries[entry.ori_mes_id] = entry

            if not entry.ori_mes_id in self.added:
                self.updated.add(entry.ori_mes_id)
        else:
            raise KeyError(f"Entry {entry.ori_chan_id} does not exist in the current entries.")

    def get(self, entry_id, check_for_var = False) -> typing.Optional[StarboardEntry]:
        """Gets an entry based on the ID provides."""
        if self.entries[entry_id] != None:
            if not check_for_var or self.entries[entry_id].star_var_id != None:
                return self.entries[entry_id]
            else:
                return None
        else:
            entry = discord.utils.find(lambda e: e != None and e.star_var_id == entry_id, self.entries.values())
            return entry

    def get_list(self, list_filter) -> typing.List[StarboardEntry]:
        """Gets specific entries based on the filter (a lambda or function) specified."""
        return [e for e in self.entries.values() if e != None and list_filter(e)]

    def get_random(self, list_filter) -> StarboardEntry:
        """Gets a random entry based on the filter (a lambda or function) specified."""
        entries = self.get_list(list_filter)
        return random.choice(entries)