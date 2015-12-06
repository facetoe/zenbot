#!/usr/bin/env python2.7

import time
import sys
import requests
from zenpy.lib.exception import RecordNotFoundException

from lib.lang import ZenbotGrammar
from zenpy import log as logger, ZenpyException
from optparse import OptionParser
from pyparsing import ParseException
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from HTMLParser import HTMLParser
from zenpy import Zenpy


class ZenBot(irc.IRCClient):

    zendesk = None
    channels = None
    grammar = None
    nickname = "zenbot"

    def __init__(self, domain, email, token, channels):
            self.zendesk = self.zendesk = Zenpy(domain, email, token, debug=True)
            self.grammar = ZenbotGrammar('.' + self.nickname).get_grammar()
            self.channels = channels

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        logger.info("[connected at %s]" %
                        time.asctime(time.localtime(time.time())))

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        logger.info("[disconnected at %s]" %
                        time.asctime(time.localtime(time.time())))

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        logger.info("[Signed on server]")
        for channel in self.channels:
            self.join(channel)

    def joined(self, channel):
        """This will get called when the bot joins the channel."""
        logger.info("[Joined %s]" % channel)

    def parse_message(self, msg):
        try:
            command_method = self.grammar.parseString(msg)[0]
            return command_method(self.zendesk)
        except ParseException:
            pass
        except RecordNotFoundException:
            pass

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        user = user.split('!', 1)[0]
        logger.debug("[privmsg called with: %s]" % msg)

        if msg.startswith(".%s" % self.nickname):
            output = self.parse_message(msg)
            if output:
                self.say_channel(channel, output)
            else:
                self.say_channel(channel, self.get_error(user))
        else:
            self.say_channel(channel, self.parse_message(msg))


        # Check to see if they're sending me a private message
        if channel == self.nickname:
            msg = "It isn't nice to whisper!  Play nice with the group."
            self.msg(user, msg)
            return

    def get_error(self, user):
        url = 'http://api.icndb.com/jokes/random?escape=html&limitTo=[nerdy]'
        response = requests.get(url)
        if response.ok:
            return "%s, %s" % (user, HTMLParser().unescape(response.json()['value']['joke']))

    def say_channel(self, channel, message):
        if message:
            self.say(channel, message.encode('utf-8'))


    def action(self, user, channel, msg):
        """This will get called when the bot sees someone do an action."""
        user = user.split('!', 1)[0]
        logger.debug("* %s %s" % (user, msg))

    # irc callbacks

    def irc_NICK(self, prefix, params):
        """Called when an IRC user changes their nickname."""
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        logger.debug("%s is now known as %s" % (old_nick, new_nick))


    # For fun, override the method that determines how a nickname is changed on
    # collisions. The default method appends an underscore.
    def alterCollidedNick(self, nickname):
        """
        Generate an altered version of a nickname that caused a collision in an
        effort to create an unused related name for subsequent registration.
        """
        return nickname + '^'


class ZenBotFactory(protocol.ClientFactory):
    domain = None
    email = None
    api_token = None

    def __init__(self, channels, domain, email, api_token):
        self.domain = domain
        self.email = email
        self.api_token = api_token
        self.channels = channels

    def buildProtocol(self, addr):
        p = ZenBot(self.domain, self.email, self.api_token, self.channels)
        p.factory = self
        return p

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        reactor.stop()


if __name__ == '__main__':
    # initialize logging

    parser = OptionParser()
    parser.add_option("-d", "--domain", dest="domain",
                      help="Domain for your Zendesk", metavar="DOMAIN")
    parser.add_option("-e", "--email", dest="email",
                      help="Email for Zendesk user", metavar="EMAIL")
    parser.add_option("-t", "--token", dest="token",
                      help="API token", metavar="TOKEN")
    parser.add_option("-s", "--server", dest="server",
                      help="Server for bot to connect to", metavar="SERVER")
    parser.add_option("-c", "--channels", dest="channels",
                      help="Comma seperated list of channels for the bot to join", metavar="CHANNELS")
    parser.add_option("-p", "--port", dest="port", default=6667,
                      help="Port to connect to", metavar="PORT")

    (options, args) = parser.parse_args()

    for key, value in options.__dict__.iteritems():
        if not value:
            print("** %s is required! **" % key)
            sys.exit()

    # create factory protocol and application
    f = ZenBotFactory(options.channels.split(','), options.domain, options.email, options.token)
    reactor.connectTCP(options.server, options.port, f)

    # run bot
    reactor.run()
