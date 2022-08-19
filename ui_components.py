# Copyright (c) 2022 Sandeep Kanekal
# Subclasses of discord UI components
import discord
import random
import requests
import contextlib
import datetime
from discord.ext import commands
from tools import send_error_embed, get_quote
from asyncpraw.reddit import Submission


class AuthorNotConnectedToVoiceChannel(commands.CommandError):
    pass


class AuthorInDifferentVoiceChannel(commands.CommandError):
    pass


class PlayerNotConnectedToVoiceChannel(commands.CommandError):
    pass


class NoAudioPlaying(commands.CommandError):
    pass


class PlayerPaused(commands.CommandError):
    pass


class PlayerPlaying(commands.CommandError):
    pass


# noinspection PyUnusedLocal
class YouTubeSearchView(discord.ui.View):
    def __init__(self, ctx: commands.Context, items: dict[str, list[str | int]], youtube, embed: discord.Embed,
                 bot: commands.Bot, timeout: float | None = None):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.items = items
        self.index = 0
        self.youtube = youtube
        self.embed = embed
        self.bot = bot

    def edit_embed(self):
        self.embed.clear_fields()

        # Get details
        video_ids = self.items.get('video_ids')
        thumbnails = self.items.get('thumbnails')
        titles = self.items.get('titles')
        authors = self.items.get('authors')
        publish_dates = self.items.get('publish_dates')
        channel_ids = self.items.get('channel_ids')
        statistics = self.youtube.videos().list(part='statistics, contentDetails', id=video_ids[self.index]).execute()

        # Edit embed
        self.embed.add_field(name='Result:',
                             value=f'[{titles[self.index]}](https://www.youtube.com/watch?v={video_ids[self.index]})')
        self.embed.add_field(name='Video Author:',
                             value=f'[{authors[self.index]}](https://youtube.com/channel/{channel_ids[self.index]})')
        self.embed.add_field(name='Publish Date:', value=f'{publish_dates[self.index]}')
        self.embed.set_image(url=thumbnails[self.index])
        self.embed.set_footer(
            text=f'Duration: {statistics["items"][0]["contentDetails"]["duration"].strip("PT")}, 🎥: {statistics["items"][0]["statistics"]["viewCount"]}, 👍: {statistics["items"][0]["statistics"]["likeCount"]}\nResult {self.index + 1} out of 50')

    @discord.ui.button(emoji='⏮️', style=discord.ButtonStyle.green)
    async def previous(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(f'This interaction is for {self.ctx.author.mention}',
                                                    ephemeral=True)
            return

        # Edit index accordingly
        if self.index == 0:
            self.index = len(self.items.get('video_ids')) - 1
        else:
            self.index -= 1

        self.edit_embed()
        await interaction.response.edit_message(embed=self.embed)

    @discord.ui.button(emoji='⏭️', style=discord.ButtonStyle.green)
    async def next(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(f'This interaction is for {self.ctx.author.mention}',
                                                    ephemeral=True)
            return

        # Edit index accordingly
        if self.index == len(self.items.get('video_ids')) - 1:
            self.index = 0
        else:
            self.index += 1

        self.edit_embed()
        await interaction.response.edit_message(embed=self.embed)

    @discord.ui.button(label='Watch Video', style=discord.ButtonStyle.green)
    async def watch(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                f'https://youtube.com/watch?v={self.items.get("video_ids")[self.index]}', ephemeral=True)
        else:
            await interaction.response.send_message(
                f'https://youtube.com/watch?v={self.items.get("video_ids")[self.index]}')

    @discord.ui.button(label='Play Audio in VC', style=discord.ButtonStyle.green)
    async def play(self, button: discord.Button, interaction: discord.Interaction):
        try:
            await self.ctx.invoke(self.bot.get_command('play'), query=self.items.get('titles')[self.index])
        except Exception as e:
            await send_error_embed(self.ctx, str(e))
        finally:
            await interaction.response.edit_message(view=self)

    @discord.ui.button(label='End Interaction', style=discord.ButtonStyle.red)
    async def end(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(f'This interaction is for {self.ctx.author.mention}',
                                                    ephemeral=True)
            return

        # Disable items
        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(view=self)

        self.stop()


# noinspection PyUnusedLocal
class RedditPostView(discord.ui.View):
    def __init__(self, ctx: commands.Context, submissions: list[Submission], embed: discord.Embed,
                 timeout: float | None = None):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.submissions = submissions
        self.embed = embed
        self.index = 0

    def edit_embed(self):
        # Edit embed
        self.embed.title = self.submissions[self.index].title
        self.embed.description = self.submissions[self.index].selftext
        self.embed.url = f'https://reddit.com{self.submissions[self.index].permalink}'
        self.embed.set_footer(
            text=f'⬆️ {self.submissions[self.index].ups} | ⬇️ {self.submissions[self.index].downs} | 💬 {self.submissions[self.index].num_comments}\nPost {self.index + 1} out of {len(self.submissions)}')

        # Checking if the submission is text-only
        if self.submissions[self.index].is_self:
            self.embed.set_image(url=discord.Embed.Empty)

        # Set thumbnail as image
        elif self.submissions[self.index].is_video:
            self.embed.description += f'\n[Video Link]({self.submissions[self.index].url})'
            self.embed.set_image(url=self.submissions[self.index].thumbnail)

        # Set image
        else:
            self.embed.set_image(url=self.submissions[self.index].url)
            self.embed.description = ''

    @discord.ui.button(emoji='⏮️', style=discord.ButtonStyle.green)
    async def previous(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(f'This interaction is for {self.ctx.author.mention}',
                                                    ephemeral=True)
            return

        # Edit index accordingly
        if self.index == 0:
            self.index = len(self.submissions) - 1
        else:
            self.index -= 1

        self.edit_embed()
        await interaction.response.edit_message(embed=self.embed)

    @discord.ui.button(emoji='⏭️', style=discord.ButtonStyle.green)
    async def next(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(f'This interaction is for {self.ctx.author.mention}',
                                                    ephemeral=True)
            return

        # Edit index accordingly
        if self.index == len(self.submissions) - 1:
            self.index = 0
        else:
            self.index += 1

        self.edit_embed()
        await interaction.response.edit_message(embed=self.embed)

    @discord.ui.button(label='End Interaction', style=discord.ButtonStyle.red)
    async def end(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(f'This interaction is for {self.ctx.author.mention}',
                                                    ephemeral=True)
            return

        # Disable items
        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(view=self)

        self.stop()


# noinspection PyUnusedLocal
class QuoteView(discord.ui.View):
    def __init__(self, ctx: commands.Context, url: str, embed: discord.Embed, timeout: float | None = None):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.url = url
        self.embed = embed

    @discord.ui.button(emoji='⏭️', style=discord.ButtonStyle.green)
    async def next(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(f'This interaction is for {self.ctx.author.mention}',
                                                    ephemeral=True)
            return

        quote_data = get_quote()

        if quote_data[0]['a'] == 'zenquotes.io':
            await interaction.response.send_message(content='Please wait for a few seconds!', ephemeral=True)
            return

        self.embed.description = f'> {quote_data[0]["q"]}'
        self.embed.set_author(name=quote_data[0]["a"])

        await interaction.response.edit_message(embed=self.embed)

    @discord.ui.button(emoji='❌', style=discord.ButtonStyle.gray)
    async def end(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(f'This interaction is for {self.ctx.author.mention}',
                                                    ephemeral=True)
            return

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(view=self)

        self.stop()


# noinspection PyUnusedLocal
class TriviaView(discord.ui.View):
    def __init__(self, ctx: commands.Context, items: dict[str, int | list[dict[str, str]]], embed: discord.Embed,
                 timeout: float | None = None):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.items = items
        self.embed = embed
        self.index = 0

    def edit_embed(self):
        question = self.items['results'][self.index]['question'].replace('&quot;', '"').replace('&#039;', "'")
        answer = self.items['results'][self.index]['correct_answer'].replace('&quot;', '"').replace('&#039;', "'")

        self.embed.title = question
        self.embed.description = f"**Answer:** ||**{answer}**||"
        self.embed.set_footer(text=f'Question {self.index + 1} out of {len(self.items["results"])}')

    @discord.ui.button(emoji='⏮️', style=discord.ButtonStyle.green)
    async def previous(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(f'This interaction is for {self.ctx.author.mention}',
                                                    ephemeral=True)
            return

        if self.index == 0:
            self.index = len(self.items['results']) - 1
        else:
            self.index -= 1

        self.edit_embed()
        await interaction.response.edit_message(embed=self.embed)

    @discord.ui.button(emoji='⏭️', style=discord.ButtonStyle.green)
    async def next(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(f'This interaction is for {self.ctx.author.mention}',
                                                    ephemeral=True)
            return

        if self.index == len(self.items['results']) - 1:
            self.index = 0
        else:
            self.index += 1

        self.edit_embed()
        await interaction.response.edit_message(embed=self.embed)

    @discord.ui.button(label='End Interaction', style=discord.ButtonStyle.red)
    async def end(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(f'This interaction is for {self.ctx.author.mention}',
                                                    ephemeral=True)
            return

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(view=self)

        self.stop()


# noinspection PyUnusedLocal
class ImgurView(discord.ui.View):
    def __init__(self, ctx: commands.Context, items: list, timeout: float | None = None):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.items = items
        self.index = 0

    @discord.ui.button(emoji='⏮️', style=discord.ButtonStyle.green)
    async def previous(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(f'This interaction is for {self.ctx.author.mention}',
                                                    ephemeral=True)
            return

        if self.index == 0:
            self.index = len(self.items) - 1
        else:
            self.index -= 1

        await interaction.response.edit_message(
            content=f'Image {self.index + 1} out of {len(self.items)}\n{self.items[self.index].link}')

    @discord.ui.button(emoji='⏭️', style=discord.ButtonStyle.green)
    async def next(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(f'This interaction is for {self.ctx.author.mention}',
                                                    ephemeral=True)
            return

        if self.index == len(self.items) - 1:
            self.index = 0
        else:
            self.index += 1

        await interaction.response.edit_message(
            content=f'Image {self.index + 1} out of {len(self.items)}\n{self.items[self.index].link}')

    @discord.ui.button(label='End Interaction', style=discord.ButtonStyle.red)
    async def end(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(f'This interaction is for {self.ctx.author.mention}',
                                                    ephemeral=True)
            return

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(view=self)

        self.stop()


# noinspection PyUnusedLocal
class FlipView(discord.ui.View):
    def __init__(self, ctx: commands.Context, message_id: int, timeout: float | None = None):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.message_id = message_id

    @discord.ui.button(label='Flip Again', style=discord.ButtonStyle.green)
    async def again(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:  # Prevent foreign users from interacting with the button
            await interaction.response.send_message(content=f'This interaction is for {self.ctx.author.mention}',
                                                    ephemeral=True)
            return

        await interaction.response.edit_message(content='**Flipping**')
        await interaction.followup.edit_message(content='**Flipping.**', message_id=self.message_id)
        await interaction.followup.edit_message(content='**Flipping..**', message_id=self.message_id)
        await interaction.followup.edit_message(content='**Flipping...**', message_id=self.message_id)
        await interaction.followup.edit_message(
            content=f'**You flipped a {random.choice(["Heads", "Tails"])}!** :coin:',
            message_id=self.message_id)

    @discord.ui.button(label='End Interaction', style=discord.ButtonStyle.red)
    async def end(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(f'This interaction is for {self.ctx.author.mention}',
                                                    ephemeral=True)
            return

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(view=self)

        self.stop()


# noinspection PyUnusedLocal
class RollView(discord.ui.View):
    def __init__(self, ctx: commands.Context, message_id: int, timeout: float | None = None):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.message_id = message_id

    @discord.ui.button(label='Roll Again', style=discord.ButtonStyle.green)
    async def again(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:  # Prevent foreign users from interacting with the button
            await interaction.response.send_message(content=f'This interaction is for {self.ctx.author.mention}',
                                                    ephemeral=True)
            return

        await interaction.response.edit_message(content='**Rolling**')
        await interaction.followup.edit_message(content='**Rolling.**', message_id=self.message_id)
        await interaction.followup.edit_message(content='**Rolling..**', message_id=self.message_id)
        await interaction.followup.edit_message(content='**Rolling...**', message_id=self.message_id)
        await interaction.followup.edit_message(content=f'**You rolled a {random.randint(1, 6)}!** :game_die:',
                                                message_id=self.message_id)

    @discord.ui.button(label='End Interaction', style=discord.ButtonStyle.red)
    async def end(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(f'This interaction is for {self.ctx.author.mention}',
                                                    ephemeral=True)
            return

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(view=self)

        self.stop()


# noinspection PyUnusedLocal
class TicTacToeView(discord.ui.View):
    def __init__(self, ctx: commands.Context, initiator: discord.Member, other_player: discord.Member,
                 turn: discord.Member, bot: commands.Bot, timeout: float | None = None):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.initiator = initiator
        self.other_player = other_player
        self.turn = turn
        self.first_turn = turn
        self.bot = bot

    def edit_button(self, button: discord.Button, turn: discord.Member) -> discord.Button:
        button.emoji = '<:TTTX:980118345774923838>' if turn.id == self.first_turn.id else '<:TTTO:980118346144038942>'
        button.label = None
        button.disabled = True
        button.style = discord.ButtonStyle.blurple if self.turn.id == self.first_turn.id else discord.ButtonStyle.red
        return button

    def check(self) -> str | None:
        button_one, button_two, button_three, button_four, button_five, button_six, button_seven, button_eight, button_nine = [
            button for button in self.children if button.custom_id != 'cancel']

        # Check if 3 consecutive buttons have the same style other than discord.ButtonStyle.gray
        if ((button_one.style == button_two.style == button_three.style) and (
                button_one.style != discord.ButtonStyle.gray) or
                (button_four.style == button_five.style == button_six.style) and (
                        button_four.style != discord.ButtonStyle.gray) or
                (button_seven.style == button_eight.style == button_nine.style) and (
                        button_seven.style != discord.ButtonStyle.gray) or
                (button_one.style == button_four.style == button_seven.style) and (
                        button_one.style != discord.ButtonStyle.gray) or
                (button_two.style == button_five.style == button_eight.style) and (
                        button_two.style != discord.ButtonStyle.gray) or
                (button_three.style == button_six.style == button_nine.style) and (
                        button_three.style != discord.ButtonStyle.gray) or
                (button_one.style == button_five.style == button_nine.style) and (
                        button_one.style != discord.ButtonStyle.gray) or
                (button_three.style == button_five.style == button_seven.style) and (
                        button_three.style != discord.ButtonStyle.gray)):
            return f'{self.turn.mention} has won!'

        elif not list(
                filter(lambda x: not x.disabled, [button for button in self.children if button.custom_id != 'cancel'])):
            return 'It\'s a draw!'

        # Exchange turn
        self.turn = self.other_player if self.turn.id == self.initiator.id else self.initiator
        return None

    async def handle_board(self, interaction: discord.Interaction, content: str | None):
        # Edit the message that the game has ended
        if content:
            for button in self.children:
                button.disabled = True
            await interaction.followup.edit_message(content=content, view=self, message_id=interaction.message.id)
            self.stop()
        # Edit the message that the turn has changed
        else:
            await interaction.followup.edit_message(content=f'It is {self.turn.mention}\'s turn!', view=self,
                                                    message_id=interaction.message.id)

    @discord.ui.button(label=' ', style=discord.ButtonStyle.gray, row=0, custom_id='one')
    async def one(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.id != self.turn.id:
            await interaction.followup.send(f'This interaction is for {self.turn.mention}', ephemeral=True)
            return
        button = self.edit_button(button, self.turn)
        await self.handle_board(interaction, self.check())

    @discord.ui.button(label=' ', style=discord.ButtonStyle.gray, row=0, custom_id='two')
    async def two(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.id != self.turn.id:
            await interaction.followup.send(f'This interaction is for {self.turn.mention}', ephemeral=True)
            return
        button = self.edit_button(button, self.turn)
        await self.handle_board(interaction, self.check())

    @discord.ui.button(label=' ', style=discord.ButtonStyle.gray, row=0, custom_id='three')
    async def three(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.id != self.turn.id:
            await interaction.followup.send(f'This interaction is for {self.turn.mention}', ephemeral=True)
            return
        button = self.edit_button(button, self.turn)
        await self.handle_board(interaction, self.check())

    @discord.ui.button(label=' ', style=discord.ButtonStyle.gray, row=1, custom_id='four')
    async def four(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.id != self.turn.id:
            await interaction.followup.send(f'This interaction is for {self.turn.mention}', ephemeral=True)
            return
        button = self.edit_button(button, self.turn)
        await self.handle_board(interaction, self.check())

    @discord.ui.button(label=' ', style=discord.ButtonStyle.gray, row=1, custom_id='five')
    async def five(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.id != self.turn.id:
            await interaction.followup.send(f'This interaction is for {self.turn.mention}', ephemeral=True)
            return
        button = self.edit_button(button, self.turn)
        await self.handle_board(interaction, self.check())

    @discord.ui.button(label=' ', style=discord.ButtonStyle.gray, row=1, custom_id='six')
    async def six(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.id != self.turn.id:
            await interaction.followup.send(f'This interaction is for {self.turn.mention}', ephemeral=True)
            return
        button = self.edit_button(button, self.turn)
        await self.handle_board(interaction, self.check())

    @discord.ui.button(label=' ', style=discord.ButtonStyle.gray, row=2, custom_id='seven')
    async def seven(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.id != self.turn.id:
            await interaction.followup.send(f'This interaction is for {self.turn.mention}', ephemeral=True)
            return
        button = self.edit_button(button, self.turn)
        await self.handle_board(interaction, self.check())

    @discord.ui.button(label=' ', style=discord.ButtonStyle.gray, row=2, custom_id='eight')
    async def eight(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.id != self.turn.id:
            await interaction.followup.send(f'This interaction is for {self.turn.mention}', ephemeral=True)
            return
        button = self.edit_button(button, self.turn)
        await self.handle_board(interaction, self.check())

    @discord.ui.button(label=' ', style=discord.ButtonStyle.gray, row=2, custom_id='nine')
    async def nine(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.id != self.turn.id:
            await interaction.followup.send(f'This interaction is for {self.turn.mention}', ephemeral=True)
            return
        button = self.edit_button(button, self.turn)
        await self.handle_board(interaction, self.check())

    @discord.ui.button(label='Cancel Game', style=discord.ButtonStyle.red, row=3, custom_id='cancel')
    async def cancel(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        if interaction.user.id not in (self.initiator.id, self.other_player.id):
            await interaction.followup.send('This interaction is not for you', ephemeral=True)
            return

        response_player = self.initiator if interaction.user.id != self.initiator.id else self.other_player

        # Send confirmation message
        await interaction.followup.send(
            f'{interaction.user.mention} would like to cancel this game. {response_player.mention}, respond with `yes` if you would like to cancel the game. Replying with anything other than yes will not cancel the game.')

        message = await self.bot.wait_for(
            'message',
            check=lambda m: m.author.id == response_player.id and m.channel.id == interaction.channel.id,
            timeout=None
        )

        if message.content.lower() == 'yes':
            # Disable items
            for item in self.children:
                item.disabled = True

            # Send `game cancelled` message
            await interaction.followup.edit_message(content=f'{interaction.user.mention} has cancelled the game!',
                                                    view=self, message_id=interaction.message.id)
            self.stop()

        # Continue with the game
        else:
            await interaction.followup.edit_message(view=self, message_id=interaction.message.id)

        await message.delete()
        await interaction.delete_original_message()


# noinspection PyUnusedLocal
class FunView(discord.ui.View):
    def __init__(self, ctx: commands.Context, url: str, embed: discord.Embed, timeout: float | None = None):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.url = url
        self.embed = embed

    def edit_embed(self):
        # Edit the embed accordingly
        if self.url.startswith('https://dog.ceo'):
            response = requests.get(self.url).json()
            self.embed.url = response['message']
            self.embed.set_image(url=response['message'])

        elif self.url.startswith('https://api.thecatapi.com'):
            response = requests.get(self.url).json()
            self.embed.url = response[0]['url']
            self.embed.set_image(url=response[0]['url'])

        elif self.url.startswith('https://icanhazdadjoke.com'):
            response = requests.get(self.url, headers={'Accept': 'application/json'}).json()
            self.embed.description = response['joke']

        else:
            response = requests.get(self.url, verify=False).json()
            self.embed.description = response['activity']
            self.embed.set_footer(text=f'Type: {response["type"].upper()}')

    @discord.ui.button(emoji='⏭️', style=discord.ButtonStyle.green)
    async def next_(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(f'This interaction is for {self.ctx.author.mention}',
                                                    ephemeral=True)
            return

        self.edit_embed()
        await interaction.response.edit_message(embed=self.embed)

    @discord.ui.button(emoji='❌', style=discord.ButtonStyle.gray)
    async def end_(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(f'This interaction is for {self.ctx.author.mention}',
                                                    ephemeral=True)
            return

        # Disable items
        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(view=self)
        self.stop()


class TruthOrDareView(discord.ui.View):
    def __init__(self, ctx: commands.Context, timeout: float | None = None):
        super().__init__(timeout=timeout)
        self.ctx = ctx

    @discord.ui.button(emoji='⏭️', style=discord.ButtonStyle.green)
    async def next_(self, button: discord.Button, interaction: discord.Interaction):
        button.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

        # Re-invoke the command
        await self.ctx.reinvoke()


class MusicChecks:
    def __init__(self, author: discord.Member, vc: discord.VoiceClient):
        self.author = author
        self.vc = vc

    def skip_check(self):
        if not self.author.voice:
            raise AuthorNotConnectedToVoiceChannel('You are not connected to a voice channel')

        if self.vc is None:
            raise PlayerNotConnectedToVoiceChannel('The player is not connected to a voice channel')

        if not self.vc.is_playing():
            raise NoAudioPlaying('No audio is playing')

        if self.author.voice.channel != self.vc.channel:
            raise AuthorInDifferentVoiceChannel('You are not in the same voice channel as the player')

    stop_check = skip_check

    def pause_check(self):
        if not self.author.voice:
            raise AuthorNotConnectedToVoiceChannel('You are not connected to a voice channel')

        if self.vc is None:
            raise PlayerNotConnectedToVoiceChannel('The player is not connected to a voice channel')

        if self.vc.is_paused():
            raise PlayerPaused('Player is already paused')

        if not self.vc.is_playing():
            raise NoAudioPlaying('No audio is playing')

        if self.author.voice.channel != self.vc.channel:
            raise AuthorInDifferentVoiceChannel('You are not in the same voice channel as the player')

    def resume_check(self):
        if not self.author.voice:
            raise AuthorNotConnectedToVoiceChannel('You are not connected to a voice channel')

        if self.vc is None:
            raise PlayerNotConnectedToVoiceChannel('The player is not connected to a voice channel')

        if self.vc.is_playing():
            raise PlayerPlaying('Player is already playing')

        if self.author.voice.channel != self.vc.channel:
            raise AuthorInDifferentVoiceChannel('You are not in the same voice channel as the player')

    def play_check(self):
        if self.author.voice is None:
            raise AuthorNotConnectedToVoiceChannel('You are not connected to a voice channel')

        if self.vc.is_connected() and self.vc.channel != self.author.voice.channel:
            raise AuthorInDifferentVoiceChannel('You are in a different voice channel')

    def loop_check(self):
        if not self.author.voice:
            raise AuthorNotConnectedToVoiceChannel('You are not connected to a voice channel')

        if self.vc is None:
            raise PlayerNotConnectedToVoiceChannel('The player is not connected to a voice channel')

        if not self.vc.is_playing():
            raise NoAudioPlaying('No audio is being played')

        if self.author.voice.channel != self.vc.channel:
            raise AuthorInDifferentVoiceChannel('You are not connected to the same voice channel as the player')


class LoopModal(discord.ui.Modal):
    def __init__(self, ctx: commands.Context, title: str, timeout: float | None = None):
        super().__init__(title=title, timeout=timeout)

        self.add_item(
            discord.ui.InputText(
                label='Enter the number of times to loop',
                style=discord.InputTextStyle.short,
                placeholder='Leave blank for infinite loop',
                required=False
            )
        )

        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        limit = None
        try:
            limit = int(self.children[0].value)
        except ValueError:
            limit = None
        finally:
            await self.ctx.invoke(self.ctx.bot.get_command('loop'), limit=limit)
            self.stop()
            await interaction.response.edit_message(embed=interaction.message.embeds[0])


# noinspection PyUnusedLocal
class MusicView(discord.ui.View):
    def __init__(self, ctx: commands.Context, bot: commands.Bot, vc: discord.VoiceClient, query: str,
                 timeout: float | None = None):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.bot = bot
        self.vc = vc
        self.query = query

    @discord.ui.button(emoji='⏭️', style=discord.ButtonStyle.green)
    async def skip(self, button: discord.Button, interaction: discord.Interaction):
        checks = MusicChecks(interaction.user, self.vc)
        try:
            checks.skip_check()
            await self.ctx.invoke(self.bot.get_command('skip'))
        except Exception as e:
            await interaction.response.send_message(f'Error: {e}', ephemeral=True)
        else:
            # Disable items
            for item in self.children:
                item.disabled = True
            self.stop()
            # Respond
            with contextlib.suppress(discord.NotFound):
                await interaction.response.edit_message(view=self)

    @discord.ui.button(emoji='❌', style=discord.ButtonStyle.gray)
    async def end(self, button: discord.Button, interaction: discord.Interaction):
        checks = MusicChecks(interaction.user, self.vc)
        try:
            checks.stop_check()
            await self.ctx.invoke(self.bot.get_command('stop'))
        except Exception as e:
            await interaction.response.send_message(f'Error: {e}', ephemeral=True)
        else:
            # Disable items
            for item in self.children:
                item.disabled = True
            self.stop()
            # Respond
            with contextlib.suppress(discord.NotFound):
                await interaction.response.edit_message(view=self)

    @discord.ui.button(emoji='⏯️', style=discord.ButtonStyle.red)
    async def pause(self, button: discord.Button, interaction: discord.Interaction):
        checks = MusicChecks(interaction.user, self.vc)
        try:
            if self.vc.is_playing():
                checks.pause_check()
                await self.ctx.invoke(self.bot.get_command('pause'))
            else:
                checks.resume_check()
                await self.ctx.invoke(self.bot.get_command('resume'))
        except Exception as e:
            await interaction.response.send_message(f'Error: {e}', ephemeral=True)
        else:
            # Respond
            with contextlib.suppress(discord.NotFound):
                await interaction.response.edit_message(view=self)

    @discord.ui.button(emoji='🔁', style=discord.ButtonStyle.blurple)
    async def loop(self, button: discord.Button, interaction: discord.Interaction):
        checks = MusicChecks(interaction.user, self.vc)
        try:
            checks.loop_check()
            await interaction.response.send_modal(LoopModal(self.ctx, 'Loop Options', timeout=None))
        except Exception as e:
            await interaction.response.send_message(f'Error: {e}', ephemeral=True)
        else:
            # Respond
            with contextlib.suppress(discord.NotFound):
                await interaction.followup.edit_message(interaction.message.id, view=self)

    @discord.ui.button(label='Lyrics', style=discord.ButtonStyle.blurple, row=1)
    async def lyrics(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            await self.ctx.invoke(self.bot.get_command('lyrics'), query=self.query)
        except Exception as e:
            await interaction.followup.send(f'Error: {e}', ephemeral=True)
        else:
            # Respond
            with contextlib.suppress(discord.NotFound):
                await interaction.followup.edit_message(interaction.message.id, view=self)

    @discord.ui.button(label='Add to queue', style=discord.ButtonStyle.blurple, row=1)
    async def add(self, button: discord.Button, interaction: discord.Interaction):
        checks = MusicChecks(interaction.user, self.vc)
        await interaction.response.defer()
        try:
            checks.play_check()
            await self.ctx.invoke(self.bot.get_command('play'), query=self.query)
        except Exception as e:
            await interaction.followup.send(f'Error: {e}', ephemeral=True)
        else:
            # Respond
            with contextlib.suppress(discord.NotFound):
                await interaction.followup.edit_message(interaction.message.id, view=self)


# noinspection PyUnusedLocal
class EmbedViewModal(discord.ui.Modal):
    def __init__(self, embed: discord.Embed, edit_type: str, title: str,
                 input_data: list[dict[str, str | discord.InputTextStyle | bool]] | None, timeout: float | None = None):
        super().__init__(title=title, timeout=timeout)
        self.embed = embed
        self.edit_type = edit_type

        for item_data in input_data:
            self.add_item(discord.ui.InputText(label=item_data['label'], style=item_data['style'],
                                               placeholder=item_data['placeholder'],
                                               required=item_data['required']))

    async def callback(self, interaction: discord.Interaction):
        # sourcery skip: low-code-quality
        # Edit the embed accordingly
        if self.edit_type == 'title':
            self.embed.title = self.children[0].value

        elif self.edit_type == 'url':
            self.embed.url = self.children[0].value

        elif self.edit_type == 'description':
            self.embed.description = self.children[0].value

        elif self.edit_type == 'footer':
            self.embed.set_footer(text=self.children[0].value, icon_url=self.children[1].value or discord.Embed.Empty)

        elif self.edit_type == 'author':
            self.embed.set_author(
                name=self.children[0].value,
                icon_url=self.children[1].value or discord.Embed.Empty,
                url=self.children[2].value or discord.Embed.Empty
            )

        elif self.edit_type == 'thumbnail':
            if not self.children[0].value.startswith('http'):
                await interaction.response.send_message('Invalid URL!', ephemeral=True)
                self.stop()
                return
            self.embed.set_thumbnail(url=self.children[0].value)

        elif self.edit_type == 'image':
            if not self.children[0].value.startswith('http'):
                await interaction.response.send_message('Invalid URL!', ephemeral=True)
                self.stop()
                return
            self.embed.set_image(url=self.children[0].value)

        elif self.edit_type == 'colour':
            try:
                self.embed.colour = int(self.children[0].value, 16)
            except ValueError:
                await interaction.response.send_message('Invalid colour!', ephemeral=True)
                self.stop()
                return

        elif self.edit_type == 'add field':
            inline = self.children[2].value.lower() == 'true' if self.children[2].value else False
            self.embed.add_field(name=self.children[0].value, value=self.children[1].value, inline=inline)

        elif self.edit_type == 'remove field':
            try:
                self.embed.remove_field(int(self.children[0].value - 1))
            except ValueError:
                await interaction.response.send_message('Enter an integer!', ephemeral=True)
                self.stop()
                return

        await interaction.response.edit_message(embed=self.embed)
        self.stop()


# noinspection PyUnusedLocal
class EmbedView(discord.ui.View):
    def __init__(self, author_: discord.Member, embed: discord.Embed, channel: discord.TextChannel,
                 timeout: float | None = None):
        super().__init__(timeout=timeout)
        self.author_ = author_
        self.embed = embed
        self.channel = channel

    @discord.ui.button(label='Title', style=discord.ButtonStyle.blurple)
    async def title(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.author_.id:
            await interaction.response.send_message(f'This interaction is for {self.author_.mention}',
                                                    ephemeral=True)
        input_data = [
            {'label': 'Title', 'style': discord.InputTextStyle.long, 'placeholder': 'Title', 'required': True}]
        await interaction.response.send_modal(
            EmbedViewModal(self.embed, 'title', 'Edit title', input_data, timeout=self.timeout))

    @discord.ui.button(label='URL', style=discord.ButtonStyle.blurple)
    async def url(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.author_.id:
            await interaction.response.send_message(f'This interaction is for {self.author_.mention}',
                                                    ephemeral=True)
        input_data = [{'label': 'URL', 'style': discord.InputTextStyle.long, 'placeholder': 'URL', 'required': True}]
        await interaction.response.send_modal(
            EmbedViewModal(self.embed, 'url', 'Edit URL', input_data, timeout=self.timeout))

    @discord.ui.button(label='Description', style=discord.ButtonStyle.blurple)
    async def description(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.author_.id:
            await interaction.response.send_message(f'This interaction is for {self.author_.mention}',
                                                    ephemeral=True)
        input_data = [{'label': 'Description', 'style': discord.InputTextStyle.long, 'placeholder': 'Description',
                       'required': True}]
        await interaction.response.send_modal(
            EmbedViewModal(self.embed, 'description', 'Edit description', input_data, timeout=self.timeout))

    @discord.ui.button(label='Footer', style=discord.ButtonStyle.blurple)
    async def footer(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.author_.id:
            await interaction.response.send_message(f'This interaction is for {self.author_.mention}',
                                                    ephemeral=True)
        input_data = [
            {'label': 'Footer', 'style': discord.InputTextStyle.long, 'placeholder': 'Footer', 'required': True},
            {'label': 'Icon URL', 'style': discord.InputTextStyle.long, 'placeholder': 'Icon URL', 'required': False}]
        await interaction.response.send_modal(
            EmbedViewModal(self.embed, 'footer', 'Edit footer', input_data, timeout=self.timeout))

    @discord.ui.button(label='Author', style=discord.ButtonStyle.blurple)
    async def author(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.author_.id:
            await interaction.response.send_message(f'This interaction is for {self.author_.mention}',
                                                    ephemeral=True)
        input_data = [{'label': 'Text', 'style': discord.InputTextStyle.short, 'placeholder': 'This field is required',
                       'required': True},
                      {'label': 'Icon URL', 'style': discord.InputTextStyle.short,
                       'placeholder': 'This field is optional',
                       'required': False},
                      {'label': 'URL', 'style': discord.InputTextStyle.short, 'placeholder': 'This field is optional',
                       'required': False}]
        await interaction.response.send_modal(
            EmbedViewModal(self.embed, 'author', 'Edit author', input_data, timeout=self.timeout))

    @discord.ui.button(label='Thumbnail', style=discord.ButtonStyle.blurple)
    async def thumbnail(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.author_.id:
            await interaction.response.send_message(f'This interaction is for {self.author_.mention}',
                                                    ephemeral=True)
        input_data = [{'label': 'URL', 'style': discord.InputTextStyle.long, 'placeholder': 'URL', 'required': True}]
        await interaction.response.send_modal(
            EmbedViewModal(self.embed, 'thumbnail', 'Edit thumbnail', input_data, timeout=self.timeout))

    @discord.ui.button(label='Image', style=discord.ButtonStyle.blurple)
    async def image(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.author_.id:
            await interaction.response.send_message(f'This interaction is for {self.author_.mention}',
                                                    ephemeral=True)
        input_data = [{'label': 'URL', 'style': discord.InputTextStyle.long, 'placeholder': 'URL', 'required': True}]
        await interaction.response.send_modal(
            EmbedViewModal(self.embed, 'image', 'Edit image', input_data, timeout=self.timeout))

    @discord.ui.button(label='Colour', style=discord.ButtonStyle.blurple)
    async def colour(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.author_.id:
            await interaction.response.send_message(f'This interaction is for {self.author_.mention}',
                                                    ephemeral=True)
        input_data = [
            {'label': 'Colour', 'style': discord.InputTextStyle.short, 'placeholder': 'Colour', 'required': True}]
        await interaction.response.send_modal(
            EmbedViewModal(self.embed, 'colour', 'Edit colour', input_data, timeout=self.timeout))

    @discord.ui.button(label='Timestamp', style=discord.ButtonStyle.blurple)
    async def timestamp(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.author_.id:
            await interaction.response.send_message(f'This interaction is for {self.author_.mention}',
                                                    ephemeral=True)
        self.embed.timestamp = discord.Embed.Empty if self.embed.timestamp else datetime.datetime.now()
        await interaction.response.edit_message(embed=self.embed)

    @discord.ui.button(label='Add Field', style=discord.ButtonStyle.gray)
    async def add_field(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.author_.id:
            await interaction.response.send_message(f'This interaction is for {self.author_.mention}',
                                                    ephemeral=True)
        input_data = [{'label': 'Name', 'style': discord.InputTextStyle.short, 'placeholder': 'This field is required',
                       'required': True},
                      {'label': 'Value', 'style': discord.InputTextStyle.short, 'placeholder': 'This field is required',
                       'required': True},
                      {'label': 'Inline', 'style': discord.InputTextStyle.short,
                       'placeholder': 'This field is optional. Reply with True or False only.',
                       'required': False}]
        await interaction.response.send_modal(
            EmbedViewModal(self.embed, 'add field', 'Add a field', input_data, timeout=self.timeout))

    @discord.ui.button(label='Remove Field', style=discord.ButtonStyle.gray)
    async def remove_field(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.author_.id:
            await interaction.response.send_message(f'This interaction is for {self.author_.mention}',
                                                    ephemeral=True)
        input_data = [
            {'label': 'Index', 'style': discord.InputTextStyle.short, 'placeholder': 'Index', 'required': True}]
        await interaction.response.send_modal(
            EmbedViewModal(self.embed, 'remove field', 'Enter the position of the field to remove',
                           input_data, timeout=self.timeout))

    @discord.ui.button(label='Send Embed', style=discord.ButtonStyle.green)
    async def send(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.author_.id:
            await interaction.response.send_message(f'This interaction is for {self.author_.mention}',
                                                    ephemeral=True)
        await self.channel.send(embed=self.embed)

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(view=self)
        self.stop()

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
    async def cancel(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.author_.id:
            await interaction.response.send_message(f'This interaction is for {self.author_.mention}',
                                                    ephemeral=True)
        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(view=self)
        self.stop()


# noinspection PyUnusedLocal
class HelpView(discord.ui.View):
    def __init__(self, command: str, bot: commands.Bot, prefix: str, timeout: float | None = None):
        super().__init__(timeout=timeout)
        self.command = command
        self.bot = bot
        self.prefix = prefix

    @discord.ui.button(label='Prefix Command', style=discord.ButtonStyle.blurple)
    async def prefix_command(self, button: discord.Button, interaction: discord.Interaction):
        cmd = self.bot.get_command(self.command)

        # Create and add details to the embed
        embed = discord.Embed(
            title=f'Help - {cmd}',
            description=cmd.description,
            colour=discord.Colour.blurple(),
            timestamp=datetime.datetime.now()
        )
        embed.set_footer(text=f'Help for {cmd}', icon_url=self.bot.user.avatar)

        embed.add_field(name='Aliases', value=f"`{', '.join(cmd.aliases)}`",
                        inline=False) if cmd.aliases else embed.add_field(name='Aliases', value='`None`', inline=False)
        param_str = ''.join(f'`{param}` ' for param in cmd.clean_params)
        param_str = param_str[:-1]
        embed.add_field(name='Parameters', value=param_str or '`None`', inline=False)
        embed.add_field(name='Usage', value=f'`{self.prefix}{cmd.usage}`', inline=False)

        await interaction.response.edit_message(content=None, embed=embed, view=None)
        self.stop()

    @discord.ui.button(label='Application Command', style=discord.ButtonStyle.blurple)
    async def application_command(self, button: discord.Button, interaction: discord.Interaction):
        cmd = self.bot.get_application_command(self.command, type=discord.ApplicationCommand)

        # Create and add details to the embed
        embed = discord.Embed(
            title=f'Help - {cmd}',
            description=cmd.description,
            colour=discord.Colour.blurple(),
            timestamp=datetime.datetime.now()
        )
        embed.set_footer(text=f'Help for {cmd}', icon_url=self.bot.user.avatar)

        if isinstance(cmd, discord.SlashCommand):
            param_str = ''.join(f'`{param.name}` ' for param in cmd.options)
            param_str = param_str[:-1]
            embed.add_field(name='Parameters', value=param_str, inline=False)
            embed.add_field(name='Usage', value='This is a slash command. Type / to get the command', inline=False)
        elif isinstance(cmd, discord.SlashCommandGroup):
            embed.add_field(name='Subcommands', value=f'{" ".join(f"`{subcmd.name}`" for subcmd in cmd.walk_commands())}', inline=False)
            embed.add_field(name='Usage', value=f'This is a Slash Command Group. Type /{cmd.name} to get the subcommands')
        else:
            embed.add_field(name='Usage', value='This is an application command. Right click on a message/user to get the command', inline=False)

        await interaction.response.edit_message(content=None, embed=embed, view=None)
        self.stop()


class FeatureViewModal(discord.ui.Modal):
    def __init__(self, suggestor: discord.User, type_: str, title: str,
                 timeout: float | None = None):
        super().__init__(title=title, timeout=timeout)

        self.suggestor = suggestor
        self.type_ = type_

        self.add_item(discord.ui.InputText(label='Comments', style=discord.InputTextStyle.long, placeholder='Comments',
                                           required=False))

    async def callback(self, interaction: discord.Interaction):
        with contextlib.suppress(discord.Forbidden):
            await self.suggestor.send(
                f'Your suggestion has been {self.type_}ed.\nComments by owner: {self.children[0].value}')

        if self.type_ == 'Reject':
            await interaction.response.edit_message(content=None)
            await interaction.delete_original_message()
        else:
            await interaction.response.edit_message(content=None, view=None)


# noinspection PyUnusedLocal
class FeatureView(discord.ui.View):
    def __init__(self, suggestor: discord.User, timeout: float | None = None):
        super().__init__(timeout=timeout)
        self.suggestor = suggestor

    @discord.ui.button(label='Accept', style=discord.ButtonStyle.green)
    async def accept(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(
            FeatureViewModal(self.suggestor, 'Accept', 'Add a comment', timeout=None))

    @discord.ui.button(label='Reject', style=discord.ButtonStyle.red)
    async def reject(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(
            FeatureViewModal(self.suggestor, 'Reject', 'Add a comment', timeout=None))
