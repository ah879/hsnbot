import discord
from discord.ext import commands

class HelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        cogs = dict(self.context.bot.cogs)
        cogs.pop("OwnerCommands")
        cogs.pop("Media Commands")

        embed = discord.Embed(title="HSN Bot Help", color=self.context.bot.color)
        for name, cog in cogs.items():
            value = ""
            for command in cog.get_commands():
                if not command.hidden:
                    value += f"`{command.qualified_name}`- {command.description}\n"
            embed.add_field(name=name, value=value, inline=False)

        embed.set_footer(text="Type `.help <command>` for more info on a command.")
        await self.context.reply(embed=embed)

    async def send_command_help(self, command):
        if command.cog is not None and command.cog.qualified_name not in ["OwnerCommands", "Media Commands"]:
            embed = discord.Embed(title="Help Error", description=f"Command `{command}` not found.",  color=discord.Color.red())
            return await self.context.reply(embed=embed)

        if command.cog is None: return await self.context.reply(content="why are you so rude?")

        embed = discord.Embed(title=f"Command help `{command.name}`", description=command.description, color=self.context.bot.color)
        embed.add_field(name="Usage", value=f"`{command.usage}`", inline=False)
        if command.help:
            embed.add_field(name="Parameters", value=command.help, inline=False)
        await self.context.reply(embed=embed)

    async def send_error_message(self, error):
        command = " ".join(self.context.message.content.split(" ")[1:]).lower()
        embed = discord.Embed(title="Help Error", description=f"Command `{command}` not found.", color=discord.Color.red())
        await self.context.reply(embed=embed)
