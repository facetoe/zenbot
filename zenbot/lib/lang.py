import json
from string import digits
from pyparsing import Word, alphas, Regex, oneOf, Optional, LineEnd, OneOrMore, Each
import re
from zenpy import Zenpy
from commands import ShowTicket, ShowUser, CountTickets, HelpCommand
from natural_time import nlTimeExpression, dayTimeSpec


class ZenbotGrammar(object):
    bot_name = None

    def __init__(self, bot_name):
        self.bot_name = bot_name

    def get_command_parse_action(self, cls):
        def cmd_parse_action(s, l, tokens):
            return cls(tokens)

        return cmd_parse_action

    def get_grammar(self):
        bot_name = Word(self.bot_name).suppress()

        show = oneOf('show', caseless=True).suppress()
        help = oneOf('help', caseless=True).suppress()

        ticket = Regex(r'#(?P<id>\d+)')
        ticket_attribute = OneOrMore(
            Regex(
                r"via|updated_at|submitter|assignee|id|subject|collaborators|priority|type|"
                r"status|description|tags|forum_topic|organization|requester|recipient|problem|"
                r"due_at|created_at|raw_subject|url|has_incidents|group|external",
                re.IGNORECASE)) \
            .setResultsName('ticket_attributes')

        show_ticket_command = bot_name + show + (ticket | Word(digits)('id')) + Optional(ticket_attribute) + LineEnd()
        show_ticket_command.setParseAction(self.get_command_parse_action(ShowTicket))

        ticket_unprompted_command = Optional(OneOrMore(Word(alphas))).suppress() + ticket + Optional(
            OneOrMore(Word(alphas))).suppress()
        ticket_unprompted_command.setParseAction(self.get_command_parse_action(ShowTicket))

        help_command = bot_name + help + Optional(Word(alphas))
        help_command.setParseAction(self.get_command_parse_action(HelpCommand))

        return (show_ticket_command |
                help_command |
                ticket_unprompted_command)


if __name__ == '__main__':
    api_credentials = json.load(open('/home/facetoe/zendeskapi_creds.json', 'r'))
    api = Zenpy(api_credentials['domain'], api_credentials['email'], api_credentials['token'])
    grammar = ZenbotGrammar(".zenbot").get_grammar()
    result = grammar.parseString(".zenbot show 3223 assignee")
    print result[0](api)


