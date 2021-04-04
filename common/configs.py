import typing, collections

class GuildConfig:
    """A way of representing server configs in an easy way."""

    __slots__ = ("guild_id", "starboard_id", "star_limit", "star_blacklist",
                "star_toggle", "remove_reaction", "star_edit_messages",
                "pingable_roles", "pin_config", "prefixes", "disables", "mer")

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.guild_id == other.guild_id

    def __init__(self, guild_id: int, starboard_id: typing.Optional[int], 
    star_limit: typing.Optional[int], star_blacklist: typing.List[int], star_toggle: bool, remove_reaction: bool,
    star_edit_messages: bool, pingable_roles: dict, pin_config: dict, prefixes: list, disables: dict, mer: dict):
        self.guild_id = guild_id
        self.starboard_id = starboard_id
        self.star_limit = star_limit
        self.star_blacklist = star_blacklist
        self.star_toggle = star_toggle
        self.remove_reaction = remove_reaction
        self.star_edit_messages = star_edit_messages
        self.pingable_roles = pingable_roles
        self.pin_config = pin_config
        self.prefixes = prefixes
        self.disables = disables
        self.mer = mer

    @classmethod
    def from_db(cls, entry: dict):
        return cls(entry["guild_id"], entry["starboard_id"], entry["star_limit"], 
        entry["star_blacklist"], entry["star_toggle"], entry["remove_reaction"], entry["star_edit_messages"],
        entry["pingable_roles"], entry["pin_config"], entry["prefixes"], entry["disables"], entry["mer"])

    @classmethod
    def new_config(cls, guild_id: int):
        return cls.from_db({
            "starboard_id": None,
            "star_limit": None,
            "star_blacklist": [],
            "star_toggle": False,
            "remove_reaction": False,
            "star_edit_messages": True,
            "pingable_roles": {},
            "pin_config": {},
            "prefixes": ["s!"],
            "disables": {
                "users": {},
                "channels": {}
            },
            "mer": {},

            "guild_id": guild_id
        })

    def to_dict(self) -> dict:
        """Converts this class to a dict."""
        result = {
            key: getattr(self, key)
            for key in self.__slots__
            if hasattr(self, key)
        }

        return result

class GuildConfigManager():
    """A way of managing server entries."""

    __slots__ = ("entries", "added", "updated")

    def __init__(self):
        self.entries = collections.defaultdict(lambda: None)
        self.added = set()
        self.updated = set()
    
    def reset_deltas(self):
        """Resets the deltas so that they have nothing."""
        self.added = set()
        self.updated = set()

    def create(self, guild_id: int):
        if not self.entries[guild_id]:
            new_config = GuildConfig.new_config(guild_id)
            self.entries[guild_id] = new_config
            self.added.add(guild_id)
            return new_config
        else:
            raise Exception(f"Entry {guild_id} already exists.")

    def import_entry(self, db_entry: dict):
        guild_id = db_entry["guild_id"]

        if not self.entries[guild_id]:
            import_entry = GuildConfig.from_db(db_entry)
            self.entries[guild_id] = import_entry
        else:
            raise Exception(f"Entry {guild_id} already exists.")

    def update(self, entry: GuildConfig):
        if self.entries[entry.guild_id]:
            self.entries[entry.guild_id] = entry
            self.updated(entry.guild_id)
        else:
            raise Exception(f"Entry {entry.guild_id} does not exists.")

    def get(self, guild_id: int) -> typing.Optional[GuildConfig]:
        return self.entries[guild_id] or self.create(guild_id)

    def getattr(self, guild_id: int, attribute: str):
        return getattr(self.get(guild_id), attribute)
    
    def setattr(self, guild_id: int, **kwargs):
        guild_config = self.get(guild_id)

        for key, item in kwargs.items():
            setattr(guild_config, key, item)
        
        self.update(guild_config)