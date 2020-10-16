from discord.ext import commands

from basedbot import ConfigAccessLevel


def _is_admin(member):
    return member.guild_permissions.administrator


def _is_owner(member):
    return member.guild.owner == member


def _has_access_to_var(member, var):
    if var.access == ConfigAccessLevel.INTERNAL:
        return False

    if _is_admin(member) and var.access == ConfigAccessLevel.ADMIN:
        return True

    if _is_owner(member) and var.access == ConfigAccessLevel.OWNER:
        return True

    return False


def _var_to_string(ctx, var):
    return f"{var.name} = \"{var.get(ctx.guild.id)}\" (def. \"{var.default}\")"


def check_var_exists(func):
    async def wrapper(self, ctx, name, *args):
        if name not in self.bot.conf.registered_variables:
            await ctx.send(f"Variable **{name}** does not exist.")
            return

        await func(self, ctx, name, *args)

    return wrapper


def check_var_access(func):
    @check_var_exists
    async def wrapper(self, ctx, name, *args):
        var = self.bot.conf.var(name)

        if not _has_access_to_var(ctx.author, var):
            await ctx.send(f"You don't have access to the variable **{name}**.")
            return

        await func(self, ctx, name, *args)

    return wrapper


class DBotConf(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def conf(self, ctx):
        await ctx.send_help(ctx.command)
        return

    @conf.command(name="list")
    @commands.has_permissions(administrator=True)
    async def conf_list(self, ctx):
        text = ""

        for varname in self.bot.conf.registered_variables:
            var = self.bot.conf.var(varname)

            # Skip if we don't have access
            if not _has_access_to_var(ctx.author, var):
                continue

            line = _var_to_string(ctx, var) + "\n"

            if len(text) + len(line) >= 2000 - 6:
                await ctx.send(f"```{text}```")
                text = ""

            text += line

        if len(text) > 0:
            await ctx.send(f"```{text}```")
        else:
            await ctx.send("You don't have access to any variables.")

    @conf.command(name="get")
    @commands.has_permissions(administrator=True)
    @check_var_exists
    async def conf_get(self, ctx, name):
        var = self.bot.conf.var(name)
        await ctx.send(f"```{_var_to_string(ctx, var)}```")

    @conf.command(name="set")
    @commands.has_permissions(administrator=True)
    @check_var_access
    async def conf_set(self, ctx, name, value):
        var = self.bot.conf.var(name)
        var.set(ctx.guild.id, value)

        await ctx.message.add_reaction('\U00002705')

    @conf.command(name="unset")
    @commands.has_permissions(administrator=True)
    @check_var_access
    async def conf_unset(self, ctx, name):
        var = self.bot.conf.var(name)
        var.unset(ctx.guild.id)

        await ctx.message.add_reaction('\U00002705')


def setup(bot):
    bot.add_cog(DBotConf(bot))
