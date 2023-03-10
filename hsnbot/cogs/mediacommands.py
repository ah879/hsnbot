from io import BytesIO

import discord
from discord.ext import commands
from PIL import Image, ImageDraw


class MediaCommands(commands.Cog, name="Media Commands"):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def bc(self, ctx, *, teams):
        if ctx.author.id != 707018912440647691: return
        if len(teams.split(",")) != 6: return await ctx.reply("Must be 6 teams, **separated by a comma!**! Like `.bc wolves, lightning, glizzies, coastal, dragons, owls`")

        im = Image.open("pictures/boncoscornerbackground.png")
        override_dict = {"wolves": (255, 204, 0)}
        coord_override = {"eagles": (0, 30)}
        draw = ImageDraw.Draw(im)
        teams = [x.strip() for x in teams.split(",")]

        for i, team in enumerate(teams):
            if team.lower() not in self.client.string_colors: return await ctx.reply(f"Invalid team: `{team}`")

            if team.lower() in override_dict: color = override_dict[team.lower()]
            else: color = self.client.string_colors[team.lower()]

            draw.rectangle([0, (i * 187.5), 570, (i * 187.5) + 187.5], fill=color)
            im2 = Image.open(f"pictures/{team.lower()}.png")
            im2.thumbnail((140, 125), Image.ANTIALIAS)

            coords = (10, (i * 187) + 30)
            if team.lower() in coord_override:
                coords = (coords[0] + coord_override[team.lower()][0], coords[1] + coord_override[team.lower()][1])
            print(coords)
            im.paste(im2, coords, im2)

        buffer = BytesIO()
        im.save(buffer, format="PNG")
        buffer.seek(0)
        f = discord.File(buffer, filename="image.png")
        await ctx.reply(file=f)

    @commands.command()
    async def spn(self, ctx, *, news=None):
        if ctx.author.id != 645762392789090331: return
        await ctx.reply("<:spn:850383404591480874>\_\_\*\*Welcome to SP News!\*\*\_\_ <:spn:850383404591480874>\n\n"
                        "<:spn:850383404591480874> \*\*\_\_ Today in SP News...\_\_\*\*  <:spn:850383404591480874>\n\n"
                        f"<:spn:850383404591480874> \*\*\_\_{news}\_\_\*\*  <:spn:850383404591480874>",)


def setup(client):
    client.add_cog(MediaCommands(client))