from typing import *

import discord
from discord.ext import commands

class Command:
    "A command wrapper for commands.Context and discord.Interaction"

    def __init__(self, command: Union[commands.Context, discord.Interaction]):
        if not isinstance(command, commands.Context) and not isinstance(command, discord.Interaction):
            raise Exception("Can't convert to command, please check the original command type")
        
        self._command = command

    def is_response(self):
        return self._command.response.is_done()

    @property
    def command_type(self):
        if isinstance(self._command, commands.Context):
            return 'Context'
        if isinstance(self._command, discord.Interaction):
            return 'Interaction'

    @property
    def guild(self) -> Optional[discord.Guild]:
        '''
        This function returns converted discord.Guild
        '''
        return self._command.guild

    @property
    def channel(self) -> Union[discord.PartialMessageable, None]:
        '''
        This function returns converted 
        MessageableChannel or InteractionChannel
        '''
        return self._command.channel

    @property
    def author(self) -> Union[discord.User, discord.Member, None]:
        '''
        This function returns converted
        discord.User or discord.Member
        from "interaction.message.author"
        or "ctx.author"
        '''
        if isinstance(self._command, commands.Context):
            return self._command.author
        if isinstance(self._command, discord.Interaction):
            return self._command.user

    @property
    def send(self):
        '''
        This function returns converted
        send function either
        "interaction.response.send_message" or
        "ctx.send"
        '''
        if isinstance(self._command, commands.Context):
            return self._command.send
        if isinstance(self._command, discord.Interaction):
            return self._command.response.send_message

    @property
    def message(self) -> discord.Message:
        '''
        This function returns converted
        discord.Message or InteractionMessage from
        "interaction.message()" or
        "ctx.message"
        '''
        return self._command.message

    @property
    def reply(self):
        '''
        This function returns converted
        send function either
        "interaction.message.reply" or
        "ctx.reply"

        Notice:
        It must pong back (interaction.response.pong()) 
        if use with interaction
        otherwise interaction will failed
        '''
        if isinstance(self._command, commands.Context):
            return self._command.reply
        if isinstance(self._command, discord.Interaction):
            return self._command.message.reply

    @property
    def pong(self):
        '''
        This function returns converted function from
        "interaction.pong"
        '''
        if isinstance(self._command, commands.Context):
            return None
        if isinstance(self._command, discord.Interaction):
            return self._command.response.pong

    @property
    def original_response(self):
        if isinstance(self._command, commands.Context):
            return None
        if isinstance(self._command, discord.Interaction):
            return self._command.original_response