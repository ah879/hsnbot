import asyncio
from interactions import Paginator, ReactionRoles
import discord
from discord.ext import commands

class OwnerCommands(commands.Cog, command_attrs=dict(hidden=True)):
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.is_owner()
    async def change_teams(self, ctx):
        def check(m):
            return ctx.author == m.author and ctx.channel == m.channel

        for doc in self.client.col.find():
            await ctx.reply(f"What is {doc['name']}'s new **team** (previous team `{doc['team']}`)?")
            msg = await self.client.wait_for("message", check=check)

            new_points = {"$set": {"team": msg.content.strip()}}
            self.client.col.update_one({"name": doc["name"]}, new_points)
        await ctx.send("Done.")

    @commands.command()
    @commands.is_owner()
    async def addbadge(self, ctx, *, player):
        doc = await self.client.find_player(player, ctx)
        if not doc: return

        if not doc.get("badges"):
            player_badges = {}
            await ctx.send(
                "This player currently has no badges. What badge should I add and what should it's rarity be?\n"
                "E.G. `hof ankle breaker`")
        else:
            player_badges = doc["badges"]
            await ctx.send(
                f"Player badges: `{player_badges}`. What badge should I add and what should it's rarity be?\n"
                "E.G. `hof ankle breaker`")

        def check(m):
            return ctx.author == m.author and ctx.channel == m.channel

        msg = await self.client.wait_for("message", check=check)

        rarity = msg.content.lower().split()[0]

        player_badges[" ".join(msg.content.lower().split()[1:])] = rarity

        new_points = {"$set": {"badges": player_badges}}
        self.client.col.update_one({"name": doc["name"]}, new_points)

        await ctx.send("Done.")

    @commands.command()
    @commands.is_owner()
    async def clearbadges(self, ctx, *, player):
        doc = await self.client.find_player(player, ctx)
        if not doc: return

        new_points = {"$set": {"badges": {}}}
        self.client.col.update_one({"name": doc["name"]}, new_points)

        await ctx.send("Done.")

    async def change_awards(self, ctx, player, add):
        doc = await self.client.find_player(player, ctx)
        if not doc: return
        award_dict = doc["awards"]

        await ctx.reply(embed=discord.Embed(title="What new award did they get?",
                                            description="\n".join([award.title() for award in award_dict]),
                                            color=self.client.color))

        def check(m):
            return ctx.author == m.author and ctx.channel == m.channel

        msg = await self.client.wait_for("message", check=check)
        if msg.content.lower() == "championships":
            if add:
                await ctx.reply(embed=discord.Embed(description="What team were they on?", color=self.client.color))
                msg = await self.client.wait_for("message", check=check)
                award_dict["championships"].append(msg.content.lower())
            else:
                award_dict["championships"] = []

        else:
            try:
                award_dict[msg.content.lower()] += 1 if add else -1
            except BaseException:
                return await ctx.reply(f"`{msg.content.lower()}` is not a valid award. Make sure it's plural!")

        new_points = {"$set": {"awards": award_dict}}
        self.client.col.update_one({"name": doc["name"]}, new_points)
        await ctx.reply("Done.")

    @commands.is_owner()
    @commands.command()
    async def addaward(self, ctx, *, player):
        await self.change_awards(ctx, player, True)

    @commands.is_owner()
    @commands.command()
    async def removeaward(self, ctx, *, player):
        await self.change_awards(ctx, player, False)

    @commands.is_owner()
    @commands.command()
    async def startpodcast(self, ctx, members: commands.Greedy[discord.Member]):
        if ctx.channel.id != 936855399498391623:
            return await ctx.reply("Do that in <#936855399498391623>!")

        members.append(ctx.author)
        messages = []
        await ctx.reply(
            f"Podcast started with {', '.join([member.name for member in members])}! Type `end` to end the podcast. If you forget, the podcast auto-ends 10 minutes after no messages have been sent.")

        def check(m):
            return m.channel == ctx.channel and m.author in members

        while True:
            try:
                msg = await self.client.wait_for("message", timeout=600, check=check)
            except asyncio.TimeoutError:
                await ctx.send("Podcast auto-ending...")
                break

            if msg.content.lower() == "end":
                await ctx.send("Podcast ending")
                break

            messages.append((msg.author.display_name, msg.content))

        message_split_list = []
        current_message = ""
        last_author = messages[0][0]
        for message in messages:
            message_append = f"\n**{message[0]}:** {message[1]}"
            if message[0] != last_author:
                message_append = "\n" + message_append
            if len(current_message) + len(message_append) > 1000:
                message_split_list.append(current_message)
                current_message = ""
            current_message += message_append
            last_author = message[0]

        message_split_list.append(current_message)
        view = Paginator(ctx, 0, len(message_split_list) - 1, "podcast", message_list=message_split_list)
        embed = discord.Embed(title="Podcast", description=message_split_list[0], color=self.client.color)
        msg = await ctx.reply(embed=embed, view=view)
        view.message = msg

    @commands.command()
    async def addgif(self, ctx, player, link):
        if ctx.author.id in [618919529472589845, 712057428765704192, 525860407676633108, 659804078011973662]:
            col2 = self.client.db["gifs"]
            if list(col2.find({"name": player})):
                return await ctx.reply(f"There already is a `{player}` gif!")

            col2.insert_one({"name": player.lower(), "gif": link, "upvotes": []})
            await ctx.reply(f"Added. Type `.{player.lower()}` to see the gif!")

    @commands.command()
    async def removegif(self, ctx, gifname):
        if ctx.author.id in [618919529472589845, 712057428765704192, 525860407676633108]:
            self.client.db["gifs"].delete_one({"name": gifname.lower()})
            await ctx.reply(f"Removed.")

    @commands.is_owner()
    @commands.command()
    async def change(self, ctx, *, player):
        doc = await self.client.find_player(player, ctx)
        if not doc: return
        fifa_card = doc["fifa"]
        new_fifa = fifa_card

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()

        for attribute in new_fifa:
            embed = discord.Embed(
                description=f"What is their new **{attribute}** stat? Their previous {attribute} was **{new_fifa[attribute]}**.",
                color=self.client.color)
            await ctx.reply(embed=embed)
            msg = await self.client.wait_for("message", check=check)
            new_fifa[attribute] = msg.content

        new_points = {"$set": {"fifa": new_fifa}}
        self.client.col.update_one({"name": doc["name"]}, new_points)
        await ctx.reply("Done.")

    @commands.is_owner()
    @commands.command()
    async def addplayer(self, ctx):
        new_dict = {'name': '', 'team': '', 'position': '', 'uid': 0, 'nationality': '',
                    'fifa': {},  'bio': {'title': 'Sorry...', 'content': "This player doesn't have a bio yet."},
                    'awards': {'golden boots': 0, 'golden gloves': 0, 'mvps': 0, 'all stars': 0, 'championships': [], 'opoys': 0, 'dpoys': 0, 'mips': 0, 'cotys': 0},
                    "bets": [], "money": 100}

        def check(m):
            return ctx.author == m.author and ctx.channel == m.channel

        def is_num(num):
            try:
                int(num)
                return True
            except ValueError:
                return False

        for attribute in new_dict:
            if attribute not in ["fifa", "bio", "awards", "bets"]:
                embed = discord.Embed(description=f"What is their **{attribute}**?", color=self.client.color)
                await ctx.reply(embed=embed)
                msg = await self.client.wait_for("message", check=check)
                if msg.content == "fwd":
                    new_dict[attribute] = msg.content
                    new_dict["fifa"] = {'overall': '0', 'shooting': '0', 'passing': '0', 'dribbling': '0',
                                        'corners': '0', 'positioning': '0', 'defense': '0'}
                elif msg.content == "gk":
                    new_dict[attribute] = msg.content
                    new_dict["fifa"] = {'overall': '0', 'reflexes': '0', 'passing': '0', 'positioning': '0',
                                        'dribbling': '0', "iq": "0", "offense": "0"}
                elif is_num(msg.content): new_dict[attribute] = int(msg.content)
                else: new_dict[attribute] = msg.content

        self.client.col.insert_one(new_dict)
        await ctx.reply("Done.")

    @commands.is_owner()
    @commands.command()
    async def removeplayer(self, ctx, *, uid):
        self.client.col.delete_one(self.client.col.find({"uid": int(uid)})[0])
        await ctx.reply(f"Removed <@{uid}> from the database.")

    @commands.command()
    @commands.is_owner()
    async def changeattribute(self, ctx, attribute, *, player):
        doc = await self.client.find_player(player, ctx)
        if not doc: return

        def check(m): return ctx.author == m.author and ctx.channel == m.channel

        await ctx.reply(f"What is their new **{attribute}** attribute?", mention_author=False)
        msg = await self.client.wait_for("message", check=check)

        if attribute == "position":
            if msg.content.strip() == "fwd":
                new_points = {"$set": {"fifa": {'overall': '0', 'shooting': '0', 'passing': '0', 'dribbling': '0',
                                                'corners': '0', 'positioning': '0', 'defense': '0'}}}
            else:
                new_points = {"$set": {"fifa": {'overall': '0', 'reflexes': '0', 'passing': '0', 'dribbling': '0',
                                                'positioning': '0', 'iq': '0', 'offense': '0'}}}

            self.client.col.update_one({"name": doc["name"]}, new_points)

        if msg.content.strip().isdigit():
            new_points = {"$set": {attribute: int(msg.content.strip())}}
        else:
            new_points = {"$set": {attribute: msg.content.strip()}}
        self.client.col.update_one({"name": doc["name"]}, new_points)
        await ctx.reply("Done.")

    @commands.is_owner()
    @commands.command()
    async def players(self, ctx):
        value = ""
        for x in self.client.col.find():
            value += f"{x['name']}\n"
        await ctx.reply(value)

    @commands.is_owner()
    @commands.command()
    async def bios(self, ctx):
        value = ""
        for x in self.client.col.find():
            if "Sorry..." != x['bio']['title']:
                value += f"{x['name']} ✅\n"
            else:
                value += f"{x['name']} :x:\n"
        await ctx.reply(value)

    @commands.is_owner()
    @commands.command()
    async def addbio(self, ctx, player):
        doc = await self.client.find_player(player, ctx)
        if not doc: return

        bio = {"title": "", "content": ""}
        for k in bio:
            await ctx.send(f"Send the {k} of the bio:")
            def check(m): return ctx.author == m.author and ctx.channel == m.channel

            msg = await self.client.wait_for("message", check=check)
            bio[k] = msg.content

        new_points = {"$set": {"bio": bio}}
        self.client.col.update_one({"name": doc["name"]}, new_points)
        await ctx.send(f"Done. Type `.bio {doc['name']}` to view the bio!")

    @commands.command()
    @commands.is_owner()
    async def prepare(self, ctx):
        embed = discord.Embed(title="Reaction Roles",
                              description="Click on one of the buttons below to be given/removed of a role!",
                              color=self.client.color)
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/850143026348556379.png?v=1")
        await ctx.send(embed=embed, view=ReactionRoles())

def setup(client):
    client.add_cog(OwnerCommands(client))