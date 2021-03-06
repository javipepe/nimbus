#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging

"""
Plugin Definitions
"""

log = logging.getLogger()


class Plugin(object):
    """
    Generic Plugin:

    Activated when the specified slack event is triggered. Useful for plugins that are not
    triggered by a certain keyword rather than a command. For example: expanding links

    """

    def __init__(self, bot):
        # Nimbus bot instance
        self.bot = bot

        # Shows up on the '!help' list
        self.short_help = ''

        # Detailed help that shows up on '!help plugin'
        self.help = ''

        # Syntax example that shows up on '!help plugin'
        self.help_example = []

        # Slack event type to listen to. Defaults to regular messages
        self.event_type = 'message'

        # Generic Plugins don't show up in '!help'
        self.hidden = True

    def on_event(self, event, response):
        """
        Called when a matching slack event is thrown

        Do what you want with the event here.
        Post a reply: self.bot.sc.api_call('chat.postMessage', **response)
        """
        pass


class CommandPlugin(Plugin):
    """
    Command Plugin:

    Activated when a slack 'message' type event is throw that starts with a command prefix and
    contains any matching triggers. For example '!echo test' where '!' is the command prefix and
    'echo' is the command trigger.

    Command Plugin does all the commmand parsing for you. When defining a command plugin
    don't override on_event() instead put your logic in on_command() which is called automatically
    when the event text matches the command requirements.

    The 'text' key in the slack message contains only the arguments of the command (with the
    command and command prefix stripped away).


    """

    def __init__(self, bot):
        Plugin.__init__(self, bot)
        # Triggers to match in order to call on_event()
        self.triggers = []

        # Commands default to showing up on '!help'
        self.hidden = False

        # Direct message the sender of the message back the response
        self.dm_sender = False

        # Only allow Slack admins and owners to run this command
        self.admin_command = False

    def on_event(self, event, response):
        """
        Called on 'message' events
        """
        # Strip command prefix and split at first space
        if event['text'].startswith(self.bot.command_prefix):
            split = event['text'][len(self.bot.command_prefix):].split(' ', 1)

            # If command matches a trigger, parse arguments and continue
            command = split[0]
            if command in self.triggers:
                if len(split) > 1:
                    args = split[1]
                else:
                    args = ''

                # Replace text component of slack message to just command arguments
                # (Strip out command and prefix)
                event['text'] = args

                # Replace the channel with the sender if dm setting is on
                if self.dm_sender:
                    # Open a IM channel
                    # For some reason we have to do this otherwise the message will come from
                    # Slack's slackbot instead of our bot
                    result = json.loads(self.bot.sc.api_call('im.open', **{'user': event['user']}))
                    if result.get('ok'):
                        response['channel'] = result['channel']['id']
                    # Fallback for when IM open call fails. This will send through Slack's Slackbot
                    # Which isn't ideal but it works and won't spam a specific channel
                    else:
                        response['channel'] = event['user']

                if self.admin_command:
                    user = json.loads(self.bot.sc.api_call('users.info', **{'user': event['user']}))
                    if user.get('ok'):
                        user = user['user']
                        if not user.get('is_admin') and not user.get('is_owner'):
                            raise PluginException('No Permission to run this command!')
                    # Fallback when user info fails. We don't want a non-admin user running an admin bot command
                    else:
                        raise PluginException('Failed to lookup user permissions. Try command again.')

                log.info('%s invoked command \'%s\' with arguments \'%s\'' % (event['user'], command, args))
                self.on_command(event, response)

    def on_command(self, event, response):
        """
        Called when a message event matches the command triggers

        Override this in your plugin to provide command functionality.
        """
        pass


class PluginException(Exception):
    """
    Errors throw by Nimbus Plugins with a message
    """
    pass
