import collections
import typing

import attr


def restore_roles_toggle_converter(restore_roles_toggle: typing.Optional[bool]):
    return restore_roles_toggle if restore_roles_toggle != None else False


def default_perms_check_converter(default_perms_check: typing.Optional[bool]):
    return default_perms_check if default_perms_check != None else True


def custom_perm_roles_converter(custom_perm_roles: typing.Optional[typing.List[int]]):
    return custom_perm_roles if custom_perm_roles != None else []


@attr.s(slots=True, eq=False)
class GuildConfig:
    """A way of representing server configs in an easy way."""

    guild_id: int = attr.ib()
    starboard_id: typing.Optional[int] = attr.ib()
    star_limit: typing.Optional[int] = attr.ib()
    star_blacklist: typing.List[int] = attr.ib()
    star_toggle: bool = attr.ib()
    remove_reaction: bool = attr.ib()
    star_edit_messages: bool = attr.ib()
    pingable_roles: dict = attr.ib()
    pin_config: dict = attr.ib()
    prefixes: list = attr.ib()
    disables: dict = attr.ib()
    mer: dict = attr.ib()
    restore_roles_toggle: bool = attr.ib(converter=restore_roles_toggle_converter)
    default_perms_check: bool = attr.ib(converter=default_perms_check_converter)
    custom_perm_roles: typing.List[int] = attr.ib(converter=custom_perm_roles_converter)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.guild_id == other.guild_id

    @classmethod
    def from_db(cls, entry: dict):
        return cls(
            entry["guild_id"],
            entry["starboard_id"],
            entry["star_limit"],
            entry["star_blacklist"],
            entry["star_toggle"],
            entry["remove_reaction"],
            entry["star_edit_messages"],
            entry["pingable_roles"],
            entry["pin_config"],
            entry["prefixes"],
            entry["disables"],
            entry["mer"],
            entry.get("restore_roles_toggle"),  # type: ignore
            entry.get("default_perms_check"),  # type: ignore
            entry.get("custom_perm_roles"),  # type: ignore
        )

    @classmethod
    def new_config(cls, guild_id: int):
        return cls.from_db(
            {
                "starboard_id": None,
                "star_limit": None,
                "star_blacklist": [],
                "star_toggle": False,
                "remove_reaction": False,
                "star_edit_messages": True,
                "pingable_roles": {},
                "pin_config": {},
                "prefixes": ["s!"],
                "disables": {"users": {}, "channels": {}},
                "mer": {},
                "restore_roles_toggle": False,
                "default_perms_check": False,
                "custom_perm_roles": [],
                "guild_id": guild_id,
            }
        )

    def to_dict(self) -> dict:
        """Converts this class to a dict."""
        return {key: getattr(self, key) for key in self.__slots__ if hasattr(self, key)}


def entry_init():
    return collections.defaultdict(lambda: None)


@attr.s(slots=True)
class GuildConfigManager:
    """A way of managing server entries."""

    entries: typing.DefaultDict[int, typing.Optional[GuildConfig]] = attr.ib(
        factory=entry_init
    )
    added: typing.Set[int] = attr.ib(factory=set)
    updated: typing.Set[int] = attr.ib(factory=set)

    def reset_deltas(self):
        """Resets the deltas so that they have nothing."""
        self.added = set()
        self.updated = set()

    def create(self, guild_id: int):
        if self.entries[guild_id]:
            raise Exception(f"Entry {guild_id} already exists.")

        new_config = GuildConfig.new_config(guild_id)
        self.entries[guild_id] = new_config
        self.added.add(guild_id)
        return new_config

    def import_entry(self, db_entry: dict):
        guild_id = db_entry["guild_id"]

        if not self.entries[guild_id]:
            import_entry = GuildConfig.from_db(db_entry["config"])
            self.entries[guild_id] = import_entry
        else:
            raise Exception(f"Entry {guild_id} already exists.")

    def update(self, entry: GuildConfig):
        if self.entries[entry.guild_id]:
            self.entries[entry.guild_id] = entry
            self.updated.add(entry.guild_id)
        else:
            raise Exception(f"Entry {entry.guild_id} does not exists.")

    def get(self, guild_id: int) -> GuildConfig:
        return self.entries[guild_id] or self.create(guild_id)

    def getattr(self, guild_id: int, attribute: str):
        return getattr(self.get(guild_id), attribute)

    def setattr(self, guild_id: int, **kwargs):
        guild_config = self.get(guild_id)

        for key, item in kwargs.items():
            setattr(guild_config, key, item)

        self.update(guild_config)
