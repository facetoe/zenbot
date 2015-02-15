import json
from pyparsing import Word, alphas, Regex, oneOf, Optional, LineEnd, OneOrMore, Each
import re
from zenpy import Zenpy
from commands import ShowTicket, ShowUser, CountTickets
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
        bot_name = Word(self.bot_name)
        person_name = (Word(alphas) + Word(alphas)).setResultsName("assignee") | Word(alphas).setResultsName("assignee")

        tags = oneOf("tag tags", caseless=True).setResultsName('tags')
        status = oneOf("new open pending hold solved closed", caseless=True).setResultsName('status')
        priority = oneOf('low normal high urgent', caseless=True).setResultsName('priority')
        created = oneOf('created', caseless=True).setResultsName('created')
        updated = oneOf('updated', caseless=True).setResultsName('updated')


        count = oneOf("count", caseless=True).setResultsName('count')
        show = oneOf("show", caseless=True).setResultsName('show')

        item = oneOf('tickets ticket', caseless=True).setResultsName("item")
        specifier = oneOf('with and', caseless=True)
        user_specifier = oneOf('for', caseless=True)

        comparison = Word('<').setResultsName('less_than') | Word('>').setResultsName("greater_than")

        time_comparison = ( oneOf("after >").setResultsName("after") | oneOf("before <").setResultsName(
            'before') + nlTimeExpression).setResultsName("time_comparison")

        priority_extra = Optional(specifier + Each(priority + Word('priority')))
        status_extra = Optional(specifier + Word('status') + Optional(comparison) + status)
        tags_extra = Optional(specifier + tags + Regex(r'(?P<tag_value>\*?\w+\*?)'))
        created_extra = Optional(Optional(specifier) + created + Optional(time_comparison) + Optional(dayTimeSpec))
        updated_extra = Optional(Optional(specifier) + updated + Optional(time_comparison) + Optional(dayTimeSpec))
        person_extra = Optional(user_specifier + person_name)

        ticket = Regex(r'#(?P<ticket_id>\d+)').setResultsName('ticket')

        person_attribute = OneOrMore(
            Regex("email|phone|signature|details|notes|role"), re.IGNORECASE
        ).setResultsName('person_attribute')

        ticket_attribute = OneOrMore(
            Regex(
                r"due_at|updated_at|created_at|subject|status|subject|raw_subject|url"
                r"|assignee|type|priority|description|recipient|requester"
                r"|submitter|assignee|collaborators",
                re.IGNORECASE)) \
            .setResultsName('ticket_attribute')

        count_tickets = (bot_name +
                         count +
                         Optional(status) +
                         item +
                         Each(priority_extra +
                              tags_extra +
                              status_extra +
                              created_extra +
                                updated_extra +
                              person_extra) +
                         LineEnd())

        count_tickets.setParseAction(self.get_command_parse_action(CountTickets))

        show_user_info = bot_name + show + Optional(person_attribute) + user_specifier + person_name + LineEnd()
        show_user_info.setParseAction(self.get_command_parse_action(ShowUser))

        show_ticket = bot_name + show + ticket + Optional(ticket_attribute) + LineEnd()
        show_ticket.setParseAction(self.get_command_parse_action(ShowTicket))

        show_ticket_unprompted = Optional(OneOrMore(Word(alphas))) + ticket + Optional(OneOrMore(Word(alphas)))
        show_ticket_unprompted.setParseAction(self.get_command_parse_action(ShowTicket))

        return (count_tickets |
                show_ticket |
                show_user_info |
                show_ticket_unprompted)


if __name__ == '__main__':
    api_credentials = json.load(open('/home/facetoe/zendeskapi_creds.json', 'r'))
    api = Zenpy(api_credentials['domain'], api_credentials['email'], api_credentials['token'])
    grammar = ZenbotGrammar(".zenbot").get_grammar()
    result = grammar.parseString(".zenbot count tickets updated today")
    print(result[0](api))


