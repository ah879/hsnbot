import asyncio

import discord
from discord.ext import commands

class Betting(commands.Cog, name="Betting"):
    def __init__(self, client):
        self.client = client
        self.games_db = self.client.db["games"]

    @commands.command(hidden=True)
    @commands.is_owner()
    async def cleargames(self, ctx):
        for x in self.games_db.find():
            self.games_db.delete_one(x)
        await ctx.send("Done.")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def clearbets(self, ctx):
        for x in self.client.col.find():
            new_points = {"$set": {"bets": []}}
            self.client.col.update_one({"name": x["name"]}, new_points)

        await ctx.send("Done.")


    @commands.command(hidden=True)
    @commands.is_owner()
    async def addgame(self, ctx):
        embed = discord.Embed(title="Who's Playing, and what are the Odds?", description="2 teams, names and odds (moneyline), separated by a comma.", color=self.client.color)
        embed.add_field(name="Example", value="`wolves -110, owls +150`")
        await ctx.reply(embed=embed)

        game_dict = {"game_id": 0 if len(list(self.games_db.find())) == 0 else list(self.games_db.find())[-1]["game_id"]+1, "team1": [], "team2": [], "matchday": 0, "completed": False}

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        msg = await self.client.wait_for("message", check=check)
        try:
            team1, team2 = [x.strip() for x in msg.content.split(",")]
            game_dict["team1"].append(team1.split()[0])
            game_dict["team1"].append(team1.split()[1])

            game_dict["team2"].append(team2.split()[0])
            game_dict["team2"].append(team2.split()[1])
        except:
            return await ctx.reply("Error.")

        await ctx.reply("What's the matchday? E.G. `6`.")
        msg = await self.client.wait_for("message", check=check)
        game_dict["matchday"] = int(msg.content)

        self.games_db.insert_one(game_dict)

        await ctx.reply("Done.")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def submit(self, ctx, game_id: int, team):
        doc = self.games_db.find({"game_id": game_id})[0]
        if doc["completed"]:
            return await ctx.reply("You can't submit a game that's already been completed!")

        if team.lower() not in [doc["team1"][0], doc["team2"][0]]:
            return await ctx.reply(f"{team} isn't one of the teams!")

        new_points = {"$set": {"completed": True}}
        self.games_db.update_one({"game_id": game_id}, new_points)

        won = []
        lost = []
        for x in self.client.col.find():
            for bet in x["bets"].copy():
                if bet["game_id"] == game_id:
                    if bet["team"] == team.lower():
                        won.append((x['name'], bet['payout']))
                        new_points = {"$set": {"money": x["money"] + bet["payout"]}}
                        self.client.col.update_one({"name": x["name"]}, new_points)

                        player_bets = x["bets"]
                        player_bets.remove(bet)
                        new_points = {"$set": {"bets": player_bets}}
                        self.client.col.update_one({"name": x["name"]}, new_points)

                    else:
                        lost.append((x['name'], bet['bet']))

        win_string = "\n".join(f"**{x}** won `${y}`" for x, y in won) if len(won) > 0 else "No winners."
        loss_string = "\n".join(f"**{x}** lost `${y}`" for x, y in lost) if len(lost) > 0 else "No losers."

        embed = discord.Embed(title=f"{team.title()} beat the {doc['team1'][0].title() if team.lower() != doc['team1'][0] else doc['team2'][0].title()}",
                              color=self.client.color)
        embed.add_field(name="Winners", value=win_string)
        embed.add_field(name="Losers", value=loss_string)
        await ctx.reply(embed=embed)

    @commands.is_owner()
    @commands.command(hidden=True)
    async def addmoney(self, ctx, money: int, *, player):
        player_doc = await self.client.find_player(player, ctx)
        if not player_doc: return

        new_points = {"$set": {"money": player_doc["money"] + money}}
        self.client.col.update_one({"name": player_doc["name"]}, new_points)

        await ctx.send("Done.")

    @commands.command(description="See available games to bet on!")
    async def games(self, ctx):
        embed = discord.Embed(title="Game Betting Odds", description="To bet on a game, type `.bet <id>`", color=self.client.color)
        matchdays = {}
        for game in self.games_db.find():
            if game["completed"]: continue
            match_string = f"**{game['team1'][0].title()}** (`{game['team1'][1]}`) vs. **{game['team2'][0].title()}** (`{game['team2'][1]}`) *ID:* `{game['game_id']}`\n"
            if game["matchday"] not in matchdays:
                matchdays[game["matchday"]] = match_string
            else:
                matchdays[game["matchday"]] += match_string

        for k, v in matchdays.items():
            embed.add_field(name=f"Matchday {k}", value=v, inline=False)

        if len(embed.fields) == 0: embed.description = "There are no matches to bet on!"

        await ctx.reply(embed=embed)

    @commands.command(description="Bet on a game!")
    async def bet(self, ctx, game_id: int):
        player_doc = await self.client.find_player(None, ctx)
        if not player_doc: return

        if game_id in [x["game_id"] for x in player_doc["bets"]]:
            return await ctx.reply("You've already bet on this game! Type `.bets` to view your bets.'")

        try: doc = self.games_db.find({"game_id": game_id})[0]
        except IndexError: return await ctx.reply("Not a valid game ID! Type `.games` for valid IDs.")

        if doc["completed"]:
            return await ctx.reply("That game is already completed!")

        embed = discord.Embed(title="Place your bet", description=f"E.G. `{doc['team1'][0]} 100` or `{doc['team2'][0]} 50`.",
                              color=self.client.color)
        for team in [doc["team1"], doc["team2"]]:
            if int(team[1]) < 0:
                payout = f"`$100` -> `${round(100+((100/abs(int(team[1])))*100))}`"
            else:
                payout = f"`$100` -> `${100+int(team[1])}`"

            embed.add_field(name=f"Payout if {team[0].title()} win", value=payout)

        await ctx.reply(embed=embed)
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        try:
            msg = await self.client.wait_for("message", timeout=30, check=check)
            if len(msg.content.split()) != 2:  return await msg.reply(f"Separate the team and the bet with a space! E.G. `{doc['team1'][0]} 100`.")
            team, bet = msg.content.split()
            if team.lower() not in [doc["team1"][0], doc["team2"][0]]: return await msg.reply(f"`{team}` is not a valid team! It's either `{doc['team1'][0]}` or `{doc['team2'][0]}`.")
            if not bet.isdigit(): return await msg.reply(f"`{bet}` is not a valid bet! Please choose a whole number, no decimals.")

            if int(bet) > player_doc["money"]:
                return await msg.reply(f"You only have `${player_doc['money']}` in your balance, therefore you cannot bet `${bet}`!")

            team_doc = doc["team1"] if team.lower() == doc["team1"][0] else doc["team2"]
            win = (int(bet) / abs(int(team_doc[1]))) * 100 if int(team_doc[1]) < 0 else (int(bet)*int(team_doc[1]))/100
            opponent = doc["team1"][0] if team.lower() == doc["team2"][0] else doc["team2"][0]
            bet_dict = {"game_id": game_id, "team": team.lower(), "bet": int(bet), "payout": int(bet)+round(win), "opponent": opponent}
            player_bets = player_doc["bets"]
            player_bets.append(bet_dict)

            new_points = {"$set": {"bets": player_bets}}
            self.client.col.update_one({"name": player_doc["name"]}, new_points)

            new_points = {"$set": {"money": player_doc["money"]-int(bet)}}
            self.client.col.update_one({"name": player_doc["name"]}, new_points)

            await ctx.reply("Bet added. Type `.bets` to view your bets!")

        except asyncio.TimeoutError:
            await ctx.reply("Timed out.")

    @commands.command(description="See your (or someone elses') bets!")
    async def bets(self, ctx, player=None):
        doc = await self.client.find_player(player, ctx)
        if not doc: return

        if len(doc["bets"]) == 0: return await ctx.send(f"{doc['name']} has no bets placed!")

        embed = discord.Embed(title=f"{doc['name']}'s Bets", color=self.client.color, description="")
        for bet in doc["bets"]:
            embed.description += f"**{bet['team'].title()}:** `${bet['bet']}` -> `${bet['payout']}` (playing {bet['opponent'].title()}) *ID:* `{bet['game_id']}`\n"

        embed.add_field(name="Balance", value=f"`${doc['money']}`")
        embed.set_footer(text="To remove a bet, type `.rbet <id>`")
        await ctx.reply(embed=embed)

    @commands.command(aliases=["bal"], description="See your (or someone elses') betting balance!")
    async def balance(self, ctx, player=None):
        doc = await self.client.find_player(player, ctx)
        if not doc: return
        embed = discord.Embed(title=f"{doc['name']}'s Balance", description=f"`${doc['money']}`", color=self.client.color)
        await ctx.reply(embed=embed)

    @commands.command()
    async def rbet(self, ctx, game_id: int):
        doc = await self.client.find_player(None, ctx)
        if not doc: return

        if len(doc["bets"]) == 0: return await ctx.send(f"You have no bets placed!")

        player_bets = doc["bets"]

        for x in player_bets:
            if x["game_id"] == game_id:
                player_bets.remove(x)
                new_points = {"$set": {"bets": player_bets}}
                self.client.col.update_one({"name": doc["name"]}, new_points)

                new_points = {"$set": {"money": doc["money"]+x["bet"]}}
                self.client.col.update_one({"name": doc["name"]}, new_points)
                return await ctx.reply(f"Removed bet.")

        await ctx.reply(f"You did not place a bet for that game! Type `.bets` to view your bets, and provide the game ID!")


def setup(client):
    client.add_cog(Betting(client))