from io import BytesIO
import discord
import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageOps
from discord.ext import commands
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

class FunCommands(commands.Cog, name="Fun Commands"):
    def __init__(self, client):
        self.client = client

    async def choose_fifa(self, doc, user):
        if doc["position"] == "fwd":
            return self.fifa_card_maker(doc["team"], doc["name"], doc["fifa"]["shooting"], doc["fifa"]["passing"],
                                   doc["fifa"]["dribbling"], doc["fifa"]["corners"], doc["fifa"]["positioning"],
                                   doc["fifa"]["defense"], doc["fifa"]["overall"], "fwd", doc["nationality"],
                                   await user.display_avatar.read())
        else:
            return self.fifa_card_maker(doc["team"], doc["name"], doc["fifa"]["reflexes"], doc["fifa"]["passing"],
                                   doc["fifa"]["dribbling"], doc["fifa"]["iq"], doc["fifa"]["positioning"],
                                   doc["fifa"]["offense"], doc["fifa"]["overall"], "gk", doc["nationality"],
                                   await user.display_avatar.read())

    def fifa_card_maker(self, team, name, stat1, stat2, stat3, stat4, stat5, stat6, overall, pos, nationality, av):
        color = (0, 0, 0)
        if int(overall) >= 90:
            im = Image.open(f"pictures/{pos}/diamond.png")
            color = (255, 255, 255)
        elif int(overall) >= 80:
            im = Image.open(f"pictures/{pos}/gold.png")
        elif int(overall) >= 70:
            im = Image.open(f"pictures/{pos}/silver.png")
        else:
            im = Image.open(f"pictures/{pos}/bronze.png")

        avatar = Image.open(BytesIO(av)).convert("RGB")
        mask = Image.open('pictures/mask.png').convert('L')
        avatar = ImageOps.fit(avatar, mask.size, centering=(0.5, 0.5))
        avatar.putalpha(mask)
        avatar = avatar.resize((385, 385), Image.ANTIALIAS)

        team = Image.open(f"pictures/{team}.png")

        im.paste(avatar, (365, 215), avatar)

        team = team.resize((128, 128), Image.ANTIALIAS)
        im.paste(team, (190, 525), team)

        draw = ImageDraw.Draw(im)
        font = ImageFont.truetype("fonts/Press Feeling.ttf", 70)

        stat_dict = {0: [stat1, stat4], 1: [stat2, stat5], 2: [stat3, stat6]}
        for i in range(3):
            for j in range(2):
                draw.text(([200, 560][j], 800 + (85 * i)), stat_dict[i][j], color, font=font)

        font = ImageFont.truetype("fonts/NHLCHICA.ttf", 75)
        draw.text((190 + (15 * (16 - (len(name)))), 700), name, color, font=font)
        font = ImageFont.truetype("fonts/Press Feeling.ttf", 125)
        draw.text((210, 190), overall, color, font=font)

        nationality_dict = {"can": "canada.png", "algeria": "algeria.jpg", "brazil": "brazil.png",
                            "serbia": "serbia.png"}
        if nationality_dict.get(nationality):
            nat_image = Image.open(f"pictures/{nationality_dict[nationality]}")
            nat_image.thumbnail((150, 150), Image.ANTIALIAS)
            im.paste(nat_image, (180, 405))

        buffer = BytesIO()
        im.save(buffer, format="PNG")
        buffer.seek(0)
        return discord.File(buffer, filename="fifa_image.png"), im

    @commands.command(description="Get a players fifa card!",
                      usage="fifa [player]",
                      help="`player`- The player to get the fifa card for (optional). Defaults to yourself.")
    async def fifa(self, ctx, *, player=None):
        await ctx.trigger_typing()
        doc = await self.client.find_player(player, ctx)
        if not doc: return

        user = await self.client.fetch_user(doc["uid"])

        x, _ = await self.choose_fifa(doc, user)

        await ctx.reply(file=x)

    @commands.command(description="Get a players badges!",
                      usage="badges [player]",
                      help="`player`- The player to get badges for (optional). Defaults to yourself.")
    async def badges(self, ctx, *, player=None):
        await ctx.trigger_typing()
        doc = await self.client.find_player(player, ctx)
        if not doc: return

        if not doc.get("badges"):
            return await ctx.send("That player has no badges!")

        images = []
        for k, v in doc["badges"].items():
            e = Image.open(f"pictures/badges/{''.join(k.split())}/{''.join(k.split())}_{v}.png")
            e = e.resize((90, 90))
            images.append(e)

        width = sum([im.width for im in images][:5])
        height = 90 * (((len(images)-1)//5)+1)

        dst = Image.new('RGBA', (width, height))
        for i, image in enumerate(images):
            multi = (i-5) if i > 4 else i
            print(multi)
            dst.paste(image, ((image.width * multi), (i//5)*images[0].height))

        embed = discord.Embed(title=f"{doc['name']}'s Badges",
                              description=", ".join([f'**{x.title()}**' for x in doc["badges"]]), color=self.client.color)

        buffer = BytesIO()
        dst.save(buffer, format="PNG")
        buffer.seek(0)

        file = discord.File(buffer, filename="badge_image.png")
        embed.set_image(url="attachment://badge_image.png")
        embed.set_footer(text="Type `.badgehelp <badge>` to see what a badge is for!")

        await ctx.reply(embed=embed, file=file)

    @commands.command(description="Compare 2 players fifa cards!",
                      usage="compare <player1>, <player2>",
                      help="`player1`- The first player to compare.\n"
                           "`player2`- The second player to compare."
                      )
    async def compare(self, ctx, *, players=None):
        await ctx.trigger_typing()

        specify_embed = discord.Embed(title="Please specify two players to compare!",
                                      description="Example: `.compare Nfab, Andersng`", color=self.client.color)
        if not players: return await ctx.reply(embed=specify_embed, mention_author=False)

        try:
            player1, player2 = [x.strip() for x in players.split(",")]
        except BaseException:
            return await ctx.reply(embed=specify_embed, mention_author=False)

        doc1, doc2 = await self.client.find_player(player1, ctx), await self.client.find_player(player2, ctx)
        if None in [doc1, doc2]: return

        if doc2["position"] != doc1["position"]:
            return await ctx.reply(
                embed=discord.Embed(title="You can't compare two players who play different positions!", color=self.client.color))

        im = Image.new("RGBA", (1800, 1300), (255, 255, 255, 0))
        for i, doc in enumerate([doc1, doc2]):
            user = await self.client.fetch_user(doc["uid"])

            _, x = await self.choose_fifa(doc, user)
            im.paste(x, (i * 900, 0), x)

        embed = discord.Embed(title=f"{doc1['name']} vs. {doc2['name']}", color=self.client.color)

        same, up, down = ("<:powerrankingssame:850249838675230720>", "<:powerrankingsup:850242891602853888>",
                          "<:powerrankingsdown:850242903082008647>")

        for attribute in doc1["fifa"]:
            attribute1, attribute2 = doc1["fifa"][attribute], doc2["fifa"][attribute]

            emoji1 = up if attribute1 > attribute2 else down
            emoji2 = up if emoji1 == down else down

            if attribute1 == attribute2: emoji1 = emoji2 = same

            if attribute == "overall":
                embed.title = f"{emoji1} {doc1['name']} ({attribute1}) vs. {doc2['name']} ({attribute2}) {emoji2}"
                continue

            embed.add_field(name=attribute.title(), value=f"{emoji1} `{attribute1}` VS. `{attribute2}` {emoji2}")

        buffer = BytesIO()
        im.save(buffer, format="PNG")
        buffer.seek(0)

        file = discord.File(buffer, filename="compare_image.png")
        embed.set_image(url="attachment://compare_image.png")

        await ctx.reply(embed=embed, file=file)

    @commands.command(description="Find out what badges mean!",
                      usage="badgehelp [badge]",
                      help="`badge`- The badge to get a description for (optional). Defaults to all badges.")
    async def badgehelp(self, ctx, *, badge=""):
        badge_help_dict = {"ankle breaker": "given to players who are good at faking out people on wall bounces",
                           "bot": "given to players who have poor mechanics and positioning (usually newbies)",
                           "brick wall": "given to goalkeepers who are good at consistently saving shots",
                           "choke artist": "given to players who perform poorly in clutch moments",
                           "clown": "given to players who are clowns, on and off the field",
                           "clutch": "given to players who perform well in clutch moments",
                           "dimer": "given to people who are good at getting assists",
                           "gps": "given to players who are excellent at positioning",
                           "guardian angel": "given to goalkeepers who save impossibly hard shots",
                           "highlight machine": "given to players who never fail to perform highlight plays",
                           "leader": "given to players who are leaders on and off the field",
                           "lifts for days": "given to players who are good at performing lifts/dribble moves",
                           "lockdown": "given to forwards who are good on defense",
                           "needle threader": "given to players who are good at making tough passes",
                           "pick pocket": "given to players who are good at stealing passes",
                           "rocketeer": "given to players who are good at performing rockets",
                           "salty": "given to players who are usually salty after a defeat",
                           "sniper": "given to players who are good at shooting"}

        if badge not in badge_help_dict:
            embed = discord.Embed(title="Badge Descriptions", description="\n".join([f'**{k.title()}:** {v.capitalize()}' for k, v in badge_help_dict.items()]), color=self.client.color)
            await ctx.reply(embed=embed)

        else:
            embed = discord.Embed(title=badge.title(), description=f"The {badge.lower()} badge is {badge_help_dict[badge]}.", color=self.client.color)
            file = discord.File(f"pictures/badges/{''.join(badge.split())}/{''.join(badge.split())}_hof.png", filename="badge_image.png")
            embed.set_thumbnail(url="attachment://badge_image.png")
            await ctx.reply(embed=embed, file=file)

    @commands.command(description="Visualize someone's fifa card in a radar chart!",
                      usage="radar [player]",
                      help="`player`- The player to get badges for (optional). Defaults to yourself.")
    async def radar(self, ctx, player=None):
        await ctx.trigger_typing()

        doc = await self.client.find_player(player, ctx)
        if not doc: return

        rows = []

        if doc["position"] == "gk": categories = ['reflexes', 'passing', 'dribbling', 'positioning', 'iq', 'offense']
        else: categories = ["shooting", "passing", "dribbling", "corners", "positioning", "defense"]

        column_headers = ["name"] + categories
        for x in self.client.col.find():
            if x["position"] == doc["position"]:
                rows.append([x["name"]] + [x["fifa"][stat] for stat in categories])

        df = pd.DataFrame(rows, columns=column_headers)

        for i in categories:
            df[i + '_rank'] = df[i].rank(pct=True)

        mpl.rcParams['font.size'] = 16
        mpl.rcParams['xtick.major.pad'] = 15
        mpl.rcParams['xtick.color'] = "#FFFFFF"

        offset = np.pi / 6
        angles = np.linspace(0, 2 * np.pi, len(categories) + 1) + offset

        def create_radar_chart(ax, player_data):
            ax.plot(angles, np.append(player_data[-(len(angles) - 1):], player_data[-(len(angles) - 1)]), color=self.client.string_colors[doc["team"]], linewidth=2)
            ax.fill(angles, np.append(player_data[-(len(angles) - 1):], player_data[-(len(angles) - 1)]), color=self.client.string_colors[doc["team"]], alpha=0.2)

            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories)
            ax.set_yticklabels([])

        def get_data(data): return np.asarray(data[data['name'] == doc["name"]])[0]

        fig = plt.figure(figsize=(8, 8), facecolor='white')
        ax = fig.add_subplot(projection='polar', facecolor='#ededed')
        data = get_data(df)
        ax = create_radar_chart(ax, data)

        buffer = BytesIO()
        fig.savefig(buffer, transparent=True, bbox_inches='tight', pad_inches=0)
        buffer.seek(0)

        f = discord.File(buffer, filename="image.png")
        embed = discord.Embed(color=self.client.color, title=f"{doc['name']}'s Radar Chart")
        embed.set_image(url="attachment://image.png")
        await ctx.reply(embed=embed, file=f)


def setup(client):
    client.add_cog(FunCommands(client))