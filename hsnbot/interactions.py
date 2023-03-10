import discord
import pandas

class UpvoteCounter(discord.ui.View):
    def __init__(self, gif_col, gif):
        super().__init__(timeout=20)
        self.gif_col = gif_col
        self.gif = gif
        self.upvoted = gif["upvotes"]
        self.message = None

    @discord.ui.button(label="Upvote", style=discord.ButtonStyle.green)
    async def count(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id not in self.upvoted:
            self.upvoted.append(interaction.user.id)
            new_points = {"$set": {"upvotes": self.upvoted}}
            self.gif_col.update_one({"name": self.gif["name"]}, new_points)
            await interaction.response.edit_message(content=f"<:upvote:850242364404793364> **Upvotes:** `{len(self.upvoted)}`\n{self.gif['gif']}")
        else:
            await interaction.response.send_message("You have already upvoted!", ephemeral=True)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

        await self.message.edit(self.message.content, view=self)

class StandingsButton(discord.ui.View):
    def __init__(self, ctx, values):
        super().__init__(timeout=10)
        self.ctx = ctx
        self.values = values
        self.message = None

    @discord.ui.button(label="Pretty View", style=discord.ButtonStyle.blurple)
    async def pretty(self, button: discord.ui.Button, interaction: discord.Interaction):
        embed = discord.Embed(title="NFLCHL Standings", description="", color=self.ctx.bot.color)
        for i, team in enumerate(self.values):
            embed.description += f"**{i + 1}. {self.ctx.bot.emoji_dict[team[0].lower()]} {team[0]}** `{team[1]}-{team[3]}` (`{team[-1]}` PTS)\n"
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="Detailed View", style=discord.ButtonStyle.blurple)
    async def detailed(self, button: discord.ui.Button, interaction: discord.Interaction):
        df = pandas.DataFrame(self.values, columns=["TEAM", "W", "OTL", "L", "GF", "GA", "GD", "PTS"]).to_string(index=False)
        embed = discord.Embed(title="NFLCHL Standings", description=f"```py\n{df}\n```", color=self.ctx.bot.color)
        await interaction.response.edit_message(embed=embed)

    async def interaction_check(self, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("You can't interact with this!", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

        await self.message.edit(self.message.content, view=self)

class Paginator(discord.ui.View):
    def __init__(self, ctx, value, max_value, choice, message_list=None):
        super().__init__(timeout=10)
        self.ctx = ctx
        self.value = value
        self.max_value = max_value
        self.message = None
        self.choice = choice

        self.message_list = message_list

        if value == 0: self.children[0].disabled = True
        if value == self.max_value: self.children[1].disabled = True

    async def edit_response_message(self, interaction):
        if self.choice == "podcast":
            embed = discord.Embed(title="Podcast", description=self.message_list[self.value], color=self.ctx.bot.color)
        else: return
        await interaction.response.edit_message(embed=embed, view=self)


    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple)
    async def previous(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value -= 1

        if self.value == 0: button.disabled = True
        if self.children[1].disabled: self.children[1].disabled = False

        await self.edit_response_message(interaction)


    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple)
    async def next(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value += 1

        if self.value == self.max_value: button.disabled = True
        if self.children[0].disabled: self.children[0].disabled = False

        await self.edit_response_message(interaction)


    async def interaction_check(self, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("You can't interact with this!", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

        await self.message.edit(self.message.content, view=self)


class ReactionRoles(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Announcement Pings", style=discord.ButtonStyle.blurple, custom_id="rr:announcements")
    async def announcements(self, button: discord.ui.Button, interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, id=938625149043884062)
        if role in interaction.user.roles: await interaction.user.remove_roles(role)
        else: await interaction.user.add_roles(role)

    @discord.ui.button(label="Pubs", style=discord.ButtonStyle.blurple, custom_id="rr:pubs")
    async def pubs(self, button: discord.ui.Button, interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, id=850073020647473202)
        if role in interaction.user.roles: await interaction.user.remove_roles(role)
        else: await interaction.user.add_roles(role)

    @discord.ui.button(label="Fun Time", style=discord.ButtonStyle.blurple, custom_id="rr:funtime")
    async def funtime(self, button: discord.ui.Button, interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, id=849442855910244374)
        if role in interaction.user.roles: await interaction.user.remove_roles(role)
        else: await interaction.user.add_roles(role)

    @discord.ui.button(label="Haxball Pings", style=discord.ButtonStyle.blurple, custom_id="rr:haxupdates")
    async def haxballupdates(self, button: discord.ui.Button, interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, id=889185844492132443)
        if role in interaction.user.roles: await interaction.user.remove_roles(role)
        else: await interaction.user.add_roles(role)