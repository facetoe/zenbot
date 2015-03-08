from datetime import datetime


class Command(object):
    tokens = None

    @staticmethod
    def convert_datetimes(format_params):
        for param, value in format_params.iteritems():
            if isinstance(value, datetime):
                format_params[param] = value.strftime("%I:%M %p - %a %m %b %Y")
        return format_params

    def __init__(self, tokens):
        self.tokens = tokens

    def _do_command(self, api):
        pass

    @staticmethod
    def get_help():
        raise NotImplementedError("Implement Help")

    def __call__(self, api):
        return str(self._do_command(api))


class ShowTicket(Command):
    def __init__(self, tokens):
        Command.__init__(self, tokens=tokens)

    def _do_command(self, api):
        tokens = self.tokens
        ticket_attributes = set(list(tokens.pop('ticket_attributes', [])) + ['subject'])

        result = api.tickets(**tokens)
        if not result:
            return "No Result"

        format_params = dict()
        format_str = ""
        ticket = result.one()
        for attr in ticket_attributes:
            format_str += "%s: [%%(%s)s] " % (attr.capitalize(), attr)
            format_params.update({attr: getattr(ticket, attr)})

        format_params['url'] = "https://seqta.zendesk.com/agent/tickets/" + tokens.id
        format_str += ' - %(url)s'
        print(format_str)
        return format_str % self.convert_datetimes(format_params)


    @staticmethod
    def get_help():
        return "usage: .zenbot show TICKET_ID [via|updated_at|submitter|assignee|id|subject|collaborators|priority|type|status|description|tags|forum_topic|organization|requester|recipient|problem|due_at|created_at|raw_subject|url|has_incidents|group|external]"


class HelpCommand(Command):
    def __init__(self, tokens):
        Command.__init__(self, tokens=tokens)

    def _do_command(self, api):
        commands = {
            'show': ShowTicket,
            'help': self,
        }

        for token in self.tokens:
            if token in commands:
                return commands[token].get_help()

        return "usage: .zenbot help [%s]" % "|".join(sorted(commands.keys()))

    @staticmethod
    def get_help():
        return "Yo dog..."

    def __call__(self, api):
        return self._do_command(None)


class ShowUser(Command):
    def __init__(self, tokens):
        Command.__init__(self, tokens=tokens)

    def _do_command(self, api):
        tokens = self.tokens
        search_params = dict(type='user')

        if not isinstance(tokens.assignee, basestring):
            tokens['assignee'] = " ".join([n.capitalize() for n in tokens.assignee])
        elif tokens.assignee:
            tokens['assignee'] = tokens['assignee'].capitalize()

        if tokens.assignee:
            search_params['name'] = tokens.assignee

        user = api.search(**search_params).item()
        print(tokens.keys())
        format_params = dict()
        format_str = ""
        tokens.person_attribute.insert(0, 'name')
        for attr in tokens.person_attribute:
            if hasattr(user, attr):
                format_str += "%s: [%%(%s)s] " % (attr.capitalize(), attr)
                format_params.update({attr: getattr(user, attr)})

        return format_str % format_params

    @staticmethod
    def get_help():
        return 'omg'


class CountTickets(Command):
    def __init__(self, tokens):
        Command.__init__(self, tokens=tokens)

    def _do_command(self, api):
        tokens = self.tokens
        format_str = "%s"
        search_params = dict()
        for key in tokens.keys():
            if key in ('updated', 'updated_before', 'updated_after'):
                search_params[key] = tokens.calculatedTime.strftime("%Y-%m-%d")

        result = api.search(**search_params)
        print result.count
        print format_str
        return format_str % result.count