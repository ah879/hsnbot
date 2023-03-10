from converters.sortconverter import SortConverter
import discord
from discord.ext import commands
from interactions import StandingsButton

class LeagueCommands(commands.Cog, name="League Commands"):
    def __init__(self, client):
        self.client = client

    @commands.command(description="Get the league standings!",
                      usage="standings")
    async def standings(self, ctx):
        await ctx.trigger_typing()
        result = self.client.sheets.values().get(spreadsheetId=self.client.gsid, range="Standings!B3:I8").execute()
        values = result.get('values', [])

        embed = discord.Embed(title="NFLCHL Standings", description="", color=self.client.color)
        for i, team in enumerate(values):
            embed.description += f"**{i + 1}. {self.client.emoji_dict[team[0].lower()]} {team[0]}** `{team[1]}-{team[3]}` (`{team[-1]}` PTS)\n"

        view = StandingsButton(ctx, values)
        msg = await ctx.reply(embed=embed, view=view)
        view.message = msg

    @commands.command(description="Get the link to the NFLCHL Stat Sheet!", usage="sheet")
    async def sheet(self, ctx):
        embed = discord.Embed(title="NFLCHL Stat Sheet",
                              url="https://docs.google.com/spreadsheets/d/1Y2KhSeTPR2Kcsgh0W1XzQ1o5B7Q_mWMxV98Q2Qhe3e8/edit#gid=1791412265",
                              color=discord.Color.blue())
        await ctx.reply(embed=embed)

    @commands.command(description="Get the links to HSN Rooms!", usage="links")
    async def links(self, ctx):
        channel = self.client.get_channel(871271143917621269)
        message_list = await channel.history(limit=1, oldest_first=True).flatten()
        embed = discord.Embed(color=self.client.color).add_field(name="HSN VPS Links", value=message_list[0].content)
        await ctx.reply(embed=embed)

    @commands.command(description="Get a list of player GIFs!", usage="gifs")
    async def gifs(self, ctx):
        col2 = self.client.db["gifs"]
        embed = discord.Embed(title="All Player GIFs", color=self.client.color)
        desc = ""
        for x in col2.find():
            desc += f"`.{x['name']}`\n"
        embed.description = desc
        await ctx.reply(embed=embed)

    #draft, rosters, schedule command



def setup(client):
    client.add_cog(LeagueCommands(client))