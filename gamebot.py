import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

from connectfour import ConnectFour

load_dotenv(verbose=True)

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
