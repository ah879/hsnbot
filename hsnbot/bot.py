import os
import re
from help import HelpCommand
from converters.sortconverter import SortConverter
import discord
import pymongo
from discord.ext import commands
from interactions import UpvoteCounter, ReactionRoles
from googleapiclient.discovery import build
from google.oauth2 import service_account


class HSNBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True

        super().__init__(command_prefix=".", help_command=HelpCommand(), case_insensitive=True)
        self.persistent_views_added = False
        self.sortconverter = SortConverter()
        self.color = discord.Color.blue()
        self.gsid = '1Y2KhSeTPR2Kcsgh0W1XzQ1o5B7Q_mWMxV98Q2Qhe3e8'

        creds = service_account.Credentials.from_service_account_file('keys.json', scopes=[
            'https://www.googleapis.com/auth/spreadsheets.readonly'])
        service = build('sheets', 'v4', credentials=creds)
        self.sheets = service.spreadsheets()

        self.db = pymongo.MongoClient("mongodb://localhost:27017/")["haxball"]
        self.col = self.db["players"]

        self.logo_ids = {"remotes": 829454674124996608, "huskies": 848606199905910827, "spartans": 847157307338129438,
                         "jackrabbits": 850121168304210001, "chargers": 845423821967458304,
                         "glizzies": 829454674129059880,
                         "wolves": 860351913991209000, "lightning": 860352350769774643, "coastal": 860352888634212352,
                         "owls": 860352195638460456, "dragons": 860353322971168808, "centurions": 944864748632154144,
                         "eagles": 944864254140514305, "vamps": 944864273811775488, "laggers": 944864665886928938,
                         "hyenas": 944864438828290078, "bears": 944864294221262858}

        self.colors_dict = {"glizzies": 0xfffc74, "jackrabbits": 0xffdc04, "remotes": 0x18347c, "chargers": 0xe0643c,
                            "spartans": 0xb80c14, "huskies": 0x306414, "dragons": 0x066c3d, "wolves": 0x650B8F,
                            "coastal": 0xff78d3,
                            "lightning": 0x000080, "owls": 0xd4d3d2, "vamps": 0x380000, "eagles": 0x000080,
                            "centurions": 0x080909,
                            "hyenas": 0xffa774, "laggers": 0x0ffa5e, "bears": 0x820009}

        self.string_colors = {"glizzies": "#fffc74", "jackrabbits": "#ffdc04", "remotes": "#18347c",
                              "chargers": "#e0643c",
                              "spartans": "#b80c14", "huskies": "#306414", "dragons": "#066c3d", "wolves": "#650B8F",
                              "coastal": "#ff78d3", "lightning": "#000080", "owls": "#d4d3d2", "vamps": "#380000",
                              "eagles": "#000080", "centurions": "#080909",
                              "hyenas": "#ffa774", "laggers": "#0ffa5e", "bears": "#820009"}

        self.emoji_dict = {"remotes": "<:remotes:860353485849231391>", "huskies": "<:huskies:860396555022237748>",
                           "spartans": "<:spartans:860396346585776128>",
                           "jackrabbits": "<:jackrabbits:860396410419150848>",
                           "chargers": "<:chargers:860353614969831495>", "glizzies": "<:Glizzies:829454674129059880>",
                           "ht": "<:ht:856249356809535498>", "nflchl": "<:nflchl:850143026348556379>",
                           "wolves": "<:wolves:860351913991209000>",
                           "lightning": "<:lightning:860352350769774643>", "coastal": "<:coastal:860352888634212352>",
                           "owls": "<:owls:860352195638460456>",
                           "dragons": "<:dragons:860353322971168808>",
                           "mhfc": "<:MarlonHumphreyFanClub:813139710691901490>",
                           "centurions": "<:centurions:944864748632154144>",
                           "eagles": "<:eagles:944864254140514305>", "vamps": "<:vamps:944864273811775488>",
                           "laggers": "<:laggers:944864665886928938>",
                           "hyenas": "<:hyenas:944864438828290078>", "bears": "<:bears:944864294221262858>"}

        self.aliases = {
            ("sand", "sandwhiches", "supergoodsandwiches"): "sandwiches",
            ("amogn suzz", "amogn"): "Faxball",
            ("dog", "common dog"): "a common dog",
            ("fac", "det", "faclir", "fcl"): "Facilr",
            ("anders", "anderseg", "anderseng", "andersang"): "Andersng",
            ("buddsterr", "buddster", "budster"): "Buddsterr15",
            ("cheers", "bombo"): "bomboclaat",
            ("cringe", "cringe"): "anno",
            ("vick's dog", "lebrondhi"): "vicks dog",
            ("vvins", "vins", "vinns"): "vvinns",
            ("rem", "remasturd"): "Remastered",
            ("sqai", "sqai"): "Invaded"
        }

    async def find_player(self, player, ctx):
        if player is None or "<@" in player:
            if player and "<@" in player:
                player = player.strip("<@!").strip(">")
            else:
                player = ctx.author.id
            try:
                doc = ctx.bot.col.find({"uid": int(player)})[0]
                return doc
            except IndexError:
                await ctx.reply(
                    embed=discord.Embed(description=f"We couldn't find a user under that name!", color=ctx.bot.color))
                return

        for alias in ctx.bot.aliases:
            if player.lower() in alias:
                player = ctx.bot.aliases[alias]
                break

        doc = ctx.bot.col.find({"name": re.compile(player, re.IGNORECASE)})
        user_list = []
        for x in doc:
            if player.lower().strip() == x["name"].lower().strip():
                return x
            elif player.lower() in x["name"].lower():
                user_list.append(x)

        if len(user_list) == 1: return user_list[0]

        if len(user_list) == 0:
            await ctx.reply(embed=discord.Embed(description=f"We couldn't find a user under the name `{player}`!",
                                                color=ctx.bot.color))
            return

        embed = discord.Embed(title=f"We found multiple users for the name `{player}`", color=ctx.bot.color)
        embed.add_field(name="Did you mean...", value="\n".join([f"{x['name']}" for x in user_list]))
        embed.set_footer(
            text="Make sure to type '.fifa <user>' to get their card, or '.compare <player1>, <player2>' to compare!")
        await ctx.reply(embed=embed)


client = HSNBot()


@client.event
async def on_ready():
    if not client.persistent_views_added:
        client.add_view(ReactionRoles())
        client.persistent_views_added = True

    print("HSN bot SZN??")


@client.event
async def on_message(message):
    for x in client.db["gifs"].find():
        if message.content == f".{x['name']}":
            view = UpvoteCounter(client.db["gifs"], x)
            msg = await message.reply(f"<:upvote:850242364404793364> **Upvotes:** `{len(x['upvotes'])}`\n"
                                      f"{x['gif']}", view=view)
            view.message = msg

    await client.process_commands(message)


for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        client.load_extension(f"cogs.{filename[:-3]}")
        print(filename, "cog loaded.")


@client.command()
async def leave(ctx):
    guild = client.get_guild(809956355657170965)
    await guild.leave()

client.run("ODM5Njk1ODEyMDIzNjgxMDM0.YJNZqg.CSVS8dFOk1uHcNZzAZfVVoKvE2A")
