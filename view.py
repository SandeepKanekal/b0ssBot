import discord
import random
import requests
from discord.ext import commands
from tools import send_error_embed, get_quote


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

        video_ids = self.items.get('video_ids')
        thumbnails = self.items.get('thumbnails')
        titles = self.items.get('titles')
        authors = self.items.get('authors')
        publish_dates = self.items.get('publish_dates')
        channel_ids = self.items.get('channel_ids')

        statistics = self.youtube.videos().list(part='statistics, contentDetails', id=video_ids[self.index]).execute()

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
        await interaction.response.defer()
        try:
            await self.ctx.invoke(self.bot.get_command('play'), query=self.items.get('titles')[self.index])
        except Exception as e:
            await send_error_embed(self.ctx, str(e))
        else:
            await interaction.followup.send('Audio added to queue!')

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
class RedditPostView(discord.ui.View):
    def __init__(self, ctx: commands.Context, submissions: list, embed: discord.Embed, timeout: float | None = None):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.submissions = submissions
        self.embed = embed
        self.index = 0

    def edit_embed(self):
        self.embed.title = self.submissions[self.index].title
        self.embed.description = self.submissions[self.index].selftext
        self.embed.url = f'https://reddit.com{self.submissions[self.index].permalink}'
        self.embed.set_footer(
            text=f'⬆️ {self.submissions[self.index].ups} | ⬇️ {self.submissions[self.index].downs} | 💬 {self.submissions[self.index].num_comments}\nPost {self.index + 1} out of {len(self.submissions)}')

        # Checking if the submission is text-only
        if self.submissions[self.index].is_self:
            self.embed.set_image(url=discord.Embed.Empty)

        elif self.submissions[self.index].is_video:
            self.embed.description += f'\n[Video Link]({self.submissions[self.index].url})'
            self.embed.set_image(url=self.submissions[self.index].thumbnail)

        else:
            self.embed.set_image(url=self.submissions[self.index].url)
            self.embed.description = ''

    @discord.ui.button(emoji='⏮️', style=discord.ButtonStyle.green)
    async def previous(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(f'This interaction is for {self.ctx.author.mention}',
                                                    ephemeral=True)
            return

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
                        button_three.style != discord.ButtonStyle.gray)):  # Check if the player has won
            return f'{self.turn.mention} has won!'

        elif not list(
                filter(lambda x: not x.disabled, [button for button in self.children if button.custom_id != 'cancel'])):
            return 'It\'s a draw!'

        self.turn = self.other_player if self.turn.id == self.initiator.id else self.initiator
        return None

    async def handle_board(self, interaction: discord.Interaction, content: str | None):
        if content:
            for button in self.children:
                button.disabled = True
            await interaction.followup.edit_message(content=content, view=self, message_id=interaction.message.id)
            self.stop()
        else:
            await interaction.followup.edit_message(content=f'It is {self.turn.mention}\'s turn!', view=self, message_id=interaction.message.id)

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
        await interaction.followup.send(
            f'{interaction.user.mention} would like to cancel this game. {response_player.mention}, respond with `yes` if you would like to cancel the game. Replying with anything other than yes will not cancel the game.')
        message = await self.bot.wait_for('message', check=lambda
            m: m.author.id == response_player.id and m.channel.id == interaction.channel.id, timeout=None)

        if message.content.lower() == 'yes':
            for item in self.children:
                item.disabled = True

            await interaction.followup.edit_message(content=f'{interaction.user.mention} has cancelled the game!',
                                                    view=self, message_id=interaction.message.id)
            self.stop()

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
    async def next(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(f'This interaction is for {self.ctx.author.mention}', ephemeral=True)
            return
        
        self.edit_embed()
        await interaction.response.edit_message(embed=self.embed)
    
    @discord.ui.button(emoji='❌', style=discord.ButtonStyle.gray)
    async def end(self, button: discord.Button, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(f'This interaction is for {self.ctx.author.mention}', ephemeral=True)
            return
        
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(view=self)
        self.stop()

class TruthOrDareView(discord.ui.View):
    def __init__(self, ctx: commands.Context, timeout: float | None = None):
        super().__init__(timeout=timeout)
        self.ctx = ctx

    @discord.ui.button(emoji='⏭️', style=discord.ButtonStyle.green)
    async def next(self, button: discord.Button, interaction: discord.Interaction):
        button.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

        await self.ctx.reinvoke()
