import discord
from discord.ext import commands
from dotenv import load_dotenv
from enum import Enum
import os

load_dotenv(verbose=True)

class Stage(Enum):
    STARTING = 0
    RUNNING = 1
    ENDED = 2

class ConnectFour:
    pieces = [':black_circle:', ':joy:', ':rage:', ':nauseated_face:', ':smiling_imp:']
    columns = ['\u0030\u20E3', '\u0031\u20E3', '\u0032\u20E3', '\u0033\u20E3', '\u0034\u20E3', '\u0035\u20E3', '\u0036\u20E3', '\u0037\u20E3', '\u0038\u20E3', '\u0039\u20E3', '\U0001f51f']

    async def remove_user_reactions(message):
        for reaction in message.reactions:
            if reaction.emoji in ConnectFour.columns:
                async for user in reaction.users():
                    if user != message.author:
                        await reaction.remove(user)


    def __init__(self, bot, players):
        """Constructs a Connect Four game between the provided players."""

        self.bot = bot

        self.stage = Stage.STARTING

        # Constructs a 6x7 board, where all spots are zero-initialized (empty)
        self.board = list([0] * 11 for i in range(10))
        self.players = players
        # `turn` is the index of the player whose turn it currently is
        self.turn = 0

        # Initialize `message` to None so GameBot#on_reaction_add can detect
        # the existence of the game message
        self.message = None

    def __str__(self):
        """Builds a string used to display the current state of this Connect Four game."""

        # Display whose turn it is
        if self.stage == Stage.RUNNING:
            message = 'It\'s ' + self.players[self.turn].mention + '\'s turn.\n\n'
        elif self.stage == Stage.ENDED:
            message = self.players[self.turn].mention + ' has won!\n\n'

        message += '**Connect Four**\n'
        # Put the list of players in the string in the format: 1 vs. 2 vs. ...
        # message += ' vs. '.join(list(map(lambda player: player.name, self.players))) + '\n\n'
        for i in range(len(self.players)):
            if i > 0:
                message += ' vs. '
            message += ConnectFour.pieces[i + 1] + ' ' + self.players[i].name
        message += '\n\n'

        # Print the game board by a row-major iteration and using constant
        # game-piece arrays for the emojis
        message += ''.join(ConnectFour.columns) + '\n'
        for row in self.board:
            for piece in row:
                message += ConnectFour.pieces[piece]
            message += '\n'
        return message

    async def start(self, channel=None):
        """Begins this Connect Four game in the provided channel."""
        self.stage = Stage.RUNNING

        # Send a message which displays the game (implicitly uses __str__)
        self.message = await channel.send(self)
        # Add column reactions, used by the user to interactively select the
        # column where they would like to drop their next piece
        for column in ConnectFour.columns:
            await self.message.add_reaction(column)

    async def on_reaction_add(self, reaction, user):
        """Executes when a player reacts to the game message, which is how a turn is taken."""

        # The reacting user must be the user whose turn it is
        if self.stage == Stage.RUNNING and self.players[self.turn] == user:
            # Initialize column to None so there is a way to determine if any
            # of the column emojis matched or not
            column = None
            for i, emoji in enumerate(ConnectFour.columns):
                if reaction.emoji == emoji:
                    column = i
                    break
            # If the column is still None after iterating, then the emoji does
            # not match that of any of the columns
            if column is None:
                return

            row = 0
            if self.board[row][column] != 0:
                return
            while row + 1 < len(self.board) and self.board[row + 1][column] == 0:
                row += 1
            self.board[row][column] = self.turn + 1
            if row == 0:
                await self.message.remove_reaction(ConnectFour.columns[column], self.message.author)

            winner = self.has_winner()
            if winner:
                self.stage = Stage.ENDED
                self.bot.end_game('ConnectFour')
                
                await self.message.edit(content=str(self))
                await self.message.clear_reactions()
                return
            
            self.turn = (self.turn + 1) % len(self.players)

            await self.message.edit(content=str(self))
            await ConnectFour.remove_user_reactions(reaction.message)

    def has_line(self, row, col, row_step, col_step, length):
        player = self.board[row][col]
        if player == 0:
            return 0
        for piece in range(length - 1):
            row += row_step
            col += col_step
            if self.board[row][col] != player:
                return 0
        return player

    def has_winner(self):
        for row in range(len(self.board)):
            for col in range(len(self.board[0]) - 3):
                winner = self.has_line(row, col, 0, 1, 4)
                if winner:
                    return winner

                if row - 3 >= 0:
                    winner = self.has_line(row, col, -1, 1, 4)
                    if winner:
                        return winner

                if row + 3 < len(self.board):
                    winner = self.has_line(row, col, 1, 1, 4)
                    if winner:
                        return winner
        return 0

class GameBot(commands.Bot):
    def __init__(self):
        commands.Bot.__init__(self, '!')
        self.games = {}

    async def on_ready(self):
        print('GameBot has launched successfully')

    async def on_reaction_add(self, reaction, user):
        if 'ConnectFour' in self.games:
            connect_four = self.games['ConnectFour']
            if connect_four.message.id == reaction.message.id:
                await connect_four.on_reaction_add(reaction, user)

    def end_game(self, game):
        self.games.pop(game, None)

gamebot = GameBot()

@gamebot.command()
async def connectfour(context, name):
    if "ConnectFour" in gamebot.games:
        await context.send(':warning: A Connect Four game is already in progress')
        return

    opponent = None
    for member in context.message.channel.members:
        if member.name.startswith(name):
            opponent = member
            break
    if opponent is None:
        await context.send(':warning: No users matched name "' + name + '"')
        return

    await context.send('Starting a Connect Four game against ' + opponent.mention)
    gamebot.games['ConnectFour'] = ConnectFour(gamebot, [context.message.author, opponent])
    await gamebot.games['ConnectFour'].start(context.message.channel)

@gamebot.command()
async def debug(context, game):
    await context.send(gamebot.games[game])

gamebot.run(os.getenv('TOKEN'))
