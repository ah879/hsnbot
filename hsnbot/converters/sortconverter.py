import discord
from discord.ext import commands


class SortConverter(commands.Converter):
    def __init__(self):
        self.convert_dict = {'g': "goals", "a": "assists", "cs": "clean sheets", "+/-": "plus minus", "w": "wins", "l": "losses",
                             "gaa": "goals against average", "gpg": "goals per game", "apg": "assists per game", "p": "points",
                             "ppg": "points per game", "cspg": "clean sheets per game", "w/l": "win loss"}
    async def convert(self, ctx, argument):
        for k, v in self.convert_dict.items():
            if argument.lower() == k or argument.lower() == v or argument.lower() == v[:-1]:
                return k

        raise commands.BadArgument(f"`{argument}` is not a valid stat to sort by!")
