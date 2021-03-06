import discord
from discord.ext import commands, tasks


class AutoRole(commands.Cog):
    """Auto-role configuration"""

    def __init__(self, bot):
        self.bot = bot
        self.add_roles.start()
        super().__init__()

    @commands.group(invoke_without_command=True)
    @commands.cooldown(1, 3, commands.BucketType.channel)
    async def autorole(self, ctx: commands.Context):
        """Group of commands to manage auto-roles configuration in this server"""

        config = ctx.bot.roles.get(ctx.guild.id, {})

        embed = discord.Embed(
            title="Auto-role",
            description=f"Use `{ctx.prefix}help autorole` for more info"
            "\nCurrent configuration:",
        )
        embed.add_field(
            name="Default member role",
            value=f"<@&{config['autorole']}>" if "autorole" in config else "None",
        )
        embed.add_field(
            name="Default bot role",
            value=f"<@&{config['autorole-bot']}>"
            if "autorole-bot" in config
            else "None",
        )

        await ctx.send(embed=embed)

    @autorole.command(name="set")
    @commands.cooldown(3, 30, commands.BucketType.guild)
    @commands.has_guild_permissions(manage_guild=True, manage_roles=True)
    async def autorole_set(
        self, ctx: commands.Context, *, role: commands.RoleConverter = None
    ):
        """Sets or unsets the role given to all members on join"""

        config = ctx.bot.roles.get(ctx.guild.id, {})
        if role:
            config["autorole"] = str(role.id)
        else:
            del config["autorole"]
        ctx.bot.roles.put(ctx.guild.id, config)

        await ctx.send(
            embed=discord.Embed(
                title="Auto-role",
                description=f"All members will now get {role.mention} on join"
                if role
                else "Members will no longer get a role on join",
            )
        )

    @autorole.command(name="set-bot")
    @commands.cooldown(3, 30, commands.BucketType.guild)
    @commands.has_guild_permissions(manage_guild=True, manage_roles=True)
    async def autorole_set_bot(
        self, ctx: commands.Context, *, role: commands.RoleConverter = None
    ):
        """Sets or unsets the role given to all bots on join"""

        config = ctx.bot.roles.get(ctx.guild.id, {})
        if role:
            config["autorole-bot"] = str(role.id)
        else:
            del config["autorole-bot"]
        ctx.bot.roles.put(ctx.guild.id, config)

        await ctx.send(
            embed=discord.Embed(
                title="Auto-role",
                description=f"All bots will now get {role.mention} on join"
                if role
                else "Bots will no longer get a role on join",
            )
        )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        config = self.bot.roles.get(member.guild.id, {})

        autorole = config.get("autorole" if not member.bot else "autorole-bot", None)

        if autorole:
            await member.add_roles(discord.Object(id=int(autorole)))

    @tasks.loop(minutes=5.0)
    async def add_roles(self):
        for guild in self.bot.guilds:
            guild_config = self.bot.roles.get(guild.id, {})

            member_role, bot_role = tuple(
                discord.Object(id=int(guild_config[key]))
                if key in guild_config
                else None
                for key in ("autorole", "autorole-bot")
            )

            for member in guild.members:
                role = member_role if not member.bot else bot_role
                if role is None:
                    continue

                if role.id not in [role.id for role in member.roles]:
                    await member.add_roles(role)

    @add_roles.before_loop
    async def before_add_roles(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(AutoRole(bot))
