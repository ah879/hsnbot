from converters.sortconverter import SortConverter
import discord
from discord.ext import commands

class Stats(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(description="Get a players stats for the current season!",
                      usage="stats [player]",
                      help="`player`- The player to get stats for (optional). Defaults to yourself."
                      )
    async def stats(self, ctx, *, player=None):
        await ctx.trigger_typing()
        doc = await self.client.find_player(player, ctx)
        if not doc: return

        result = self.client.sheets.values().get(spreadsheetId=self.client.gsid, range="Statistics!B3:L38").execute()
        values = result.get('values', [])

        stat_sheet = None
        for row in values:
            if not row: continue
            if row[2].lower() == doc['name'].lower():
                stat_sheet = row
                break

        if not stat_sheet:
            return await ctx.reply(
                embed=discord.Embed(description=f"`{player}` does not have any stats this season!", color=self.client.color))

        if stat_sheet[3] == "0":
            gaa = cspg = ppg = 0
            wl = "N/A"
        else:
            ppg = round((int(stat_sheet[4]) + int(stat_sheet[5])) / float(stat_sheet[3]), 1)
            gaa = round(int(stat_sheet[7]) / float(stat_sheet[3]), 2)
            cspg = round(int(stat_sheet[6]) / float(stat_sheet[3]), 1)
            wl = int((int(stat_sheet[-2]) / (float(stat_sheet[3]))) * 100)
            if wl > 100: wl = 100

        embed = discord.Embed(title=f"{stat_sheet[2]}'s Stats", color=self.client.colors_dict[doc['team']])
        embed.add_field(name="Points",
                        value=f"Goals: `{stat_sheet[4]}`\nAssists: `{stat_sheet[5]}`\nPoints: `{int(stat_sheet[4]) + int(stat_sheet[5])}`\nPPG: `{ppg}`")
        if stat_sheet[1].lower() in ['gk', 'all']:
            embed.add_field(name="GK", value=f"CS: `{stat_sheet[6]}`\nGAA: `{gaa}`\nCSPG: `{cspg}`")
        embed.add_field(name="Team",
                        value=f"W: `{stat_sheet[-2]}`\nL: `{stat_sheet[-1]}`\nW/L: `{wl}{'' if wl == 'N/A' else '%'}`\n+/-: `{stat_sheet[-3]}`")
        embed.add_field(name="Other", value=f"Position: `{stat_sheet[1]}` GP: `{stat_sheet[3]}`", inline=False)
        embed.set_thumbnail(url=f"https://cdn.discordapp.com/emojis/{self.client.logo_ids[doc['team']]}.png?v=1")
        await ctx.reply(embed=embed)

    @commands.command(description="Get the leaders for a certain statistic!",
                      usage="leaders <sort>",
                      help="`sort`- The stat to sort by."
                      )
    async def leaders(self, ctx, *, sort: SortConverter):
        await ctx.trigger_typing()

        result = self.client.sheets.values().get(spreadsheetId=self.client.gsid, range="Statistics!B3:L38").execute()
        values = result.get('values', [])

        all_stats = []

        headers = ['G', 'A', 'CS', "GA", '+/-', 'W', 'L']
        if sort.upper() in headers:
            index = headers.index(sort.upper()) + 4

            for row in values:
                try:
                    if row[index].isdigit() and row[index] != "0": all_stats.append((row[0], row[2], int(row[index])))
                except IndexError:
                    pass
        else:
            for row in values:
                try:
                    formula_dict = {"gaa": int(row[7]) / float(row[3]),
                                    "gpg": int(row[4]) / float(row[3]),
                                    "apg": int(row[5]) / float(row[3]),
                                    "p": int(row[4]) + int(row[5]),
                                    "ppg": (int(row[4]) + int(row[5])) / float(row[3]),
                                    "cspg": int(row[6]) / float(row[3]),
                                    "w/l": (int(row[-2]) / (int(row[3]))) * 100}

                    stat = round(formula_dict[sort], 2 if sort == "gaa" else 1)
                    if not ((stat == 0 and sort != "gaa") or (row[1].lower() == "fwd" and sort == "gaa")):
                        all_stats.append((row[0], row[2], stat))
                except BaseException:
                    pass

        all_stats = sorted(all_stats, key=lambda x: x[2], reverse=False if sort == "gaa" else True)
        embed = discord.Embed(title=f"{self.client.sortconverter.convert_dict[sort].title()} Leaders", description="",
                              color=self.client.color)

        index = 0
        last_num = -1
        for stat in all_stats:
            if stat[2] != last_num: index += 1
            embed.description += f"**{index}. {self.client.emoji_dict[stat[0].lower()]} {stat[1]}** - `{stat[2]}`\n"
            last_num = stat[2]
            if index == 11: break

        await ctx.reply(embed=embed)

    @commands.command(description="Get a players awards for their career!", aliases=["award"],
                      usage="awards [player]",
                      help="`player`- The player to get awards for (optional). Defaults to yourself."
                      )
    async def awards(self, ctx, *, player=None):
        doc = await self.client.find_player(player, ctx)
        if not doc: return

        try:
            award_dict = doc["awards"]
        except BaseException:
            award_dict = {'golden boots': 0, 'golden gloves': 0, 'mvps': 0, 'all stars': 0, 'championships': [],
                          'opoys': 0, 'dpoys': 0, 'mips': 0, 'coty': 0}
            new_points = {"$set": {"awards": award_dict}}
            self.client.col.update_one({"name": doc["name"]}, new_points)

        award_list = ["championships", "mvps", "all stars", "opoys", "dpoys", "mips", "golden boots", "golden gloves",
                      "cotys"]

        embed = discord.Embed(title=f"{doc['name']}'s Awards", color=self.client.color)
        for award in award_list:
            if award == "championships":
                teams = f"({' '.join([self.client.emoji_dict[x] for x in award_dict[award]])})"
                if teams == "()": teams = ""
                embed.add_field(name=f"{award.title()}", value=f"`{len(award_dict[award])}` {teams.strip()}\n")

            elif award.lower() not in ["golden boots", "golden gloves", "all stars"]:
                embed.add_field(name=f"{award[:-1].upper() + award[-1]}", value=f"`{award_dict[award]}`\n")
            else:
                embed.add_field(name=f"{award.title()}", value=f"`{award_dict[award]}`\n")
        await ctx.reply(embed=embed)

    @commands.command(description="Get a players bio!",
                      usage="bio [player]",
                      help="`player`- The player to get awards for (optional). Defaults to yourself.")
    async def bio(self, ctx, *, player=None):
        await ctx.reply("removed because FAXBALL wont do them anymore.")
        # doc = await self.client.find_player(player, ctx)
        # if not doc: return
        # user = await self.client.fetch_user(doc["uid"])
        #
        # embed = discord.Embed(title=doc["bio"]["title"], description=doc["bio"]["content"], color=self.client.color)
        # embed.set_thumbnail(url=user.display_avatar.url)
        # embed.set_footer(text="Bios were made by Faxball.")
        #
        # await ctx.reply(embed=embed)


def setup(client):
    client.add_cog(Stats(client))