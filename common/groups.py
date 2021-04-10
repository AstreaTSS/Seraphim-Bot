from discord.ext import commands
from discord.ext import flags
from discord.ext.commands.core import hooked_wrapped_callback


def flag_group(**kwargs):
    def inner(func):
        cls = kwargs.get("cls", CustomFlagGroup)
        return cls(func, **kwargs)

    return inner


def group(**kwargs):
    def inner(func):
        cls = kwargs.get("cls", CustomGroup)
        return cls(func, **kwargs)

    return inner


class CustomGroup(commands.Group):
    """A custom group that converts - to _ for subcommands."""

    async def invoke(self, ctx):
        ctx.invoked_subcommand = None
        ctx.subcommand_passed = None
        early_invoke = not self.invoke_without_command
        if early_invoke:
            await self.prepare(ctx)

        view = ctx.view
        previous = view.index
        view.skip_ws()
        trigger = view.get_word().replace("-", "_")

        if trigger:
            ctx.subcommand_passed = trigger
            ctx.invoked_subcommand = self.all_commands.get(trigger, None)

        if early_invoke:
            injected = hooked_wrapped_callback(self, ctx, self.callback)
            await injected(*ctx.args, **ctx.kwargs)

        if trigger and ctx.invoked_subcommand:
            ctx.invoked_with = trigger
            await ctx.invoked_subcommand.invoke(ctx)
        elif not early_invoke:
            # undo the trigger parsing
            view.index = previous
            view.previous = previous
            await super().invoke(ctx)


class CustomFlagGroup(CustomGroup, flags.FlagGroup):
    pass
