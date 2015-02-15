
class Command(object):
    tokens = None

    def __init__(self, tokens):
        self.tokens = tokens

    def _do_command(self, api):
        pass

    def __call__(self, api):
        return str(self._do_command(api))


class ShowTicket(Command):
    def __init__(self, tokens):
        Command.__init__(self, tokens=tokens)

    def _do_command(self, api):
        tokens = self.tokens

        ticket = api.tickets(id=tokens.ticket_id).item()
        format_params = dict()
        format_str = ""
        for attr in tokens.ticket_attribute:
            format_str += "%s: [%%(%s)s] " % (attr.capitalize(), attr)
            format_params.update({attr: getattr(ticket, attr)})

        format_params['url'] = "https://seqta.zendesk.com/agent/tickets/" + tokens.ticket_id
        format_str += ' %(url)s'
        print(format_str)
        return format_str % format_params


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


class CountTickets(Command):
    def __init__(self, tokens):
        Command.__init__(self, tokens=tokens)

    def _do_command(self, api):
        tokens = self.tokens
        format_str = "%(count)s tickets"
        print(tokens.keys())
        if len(tokens.keys()) == 2:
            if tokens.count and tokens.item == 'tickets':
                result = api.tickets()
                return format_str % {'count': result.count}

        if not isinstance(tokens.assignee, basestring):
            tokens['assignee'] = " ".join([n.capitalize() for n in tokens.assignee])
        elif tokens.assignee:
            tokens['assignee'] = tokens['assignee'].capitalize()

        search_params = dict()
        join_word = ' with'
        if tokens.priority:
            search_params.update({'priority': tokens.priority})
            format_str += join_word + " %(priority)s priority"
            join_word = ' and'

        if tokens.tags:
            search_params.update({'tags': tokens.tag_value})
            format_str += join_word + " %(tags)s %(tag_value)s"
            join_word = ' and'

        if tokens.status:
            if tokens.greater_than:
                key = 'status_greater_than'
            elif tokens.less_than:
                key = 'status_less_than'
            else:
                key = 'status'
            search_params.update({key: tokens.status})
            format_str += join_word + " %s %%(status)s" % " ".join(key.split('_'))
            join_word = ' and'

        if tokens.created or tokens.updated:
            if 'calculatedTime' in tokens:
                if tokens.created:
                    search_key = 'created'
                elif tokens.updated:
                    search_key = 'updated'
                else:
                    raise Exception("BAD THING HAP")

                api_time = tokens.calculatedTime.strftime("%Y-%m-%d")
                if tokens.before:
                    key = search_key + '_before'
                    search_params.update({key: api_time})

                elif tokens.after:
                    key = search_key + '_after'
                    search_params.update({key: api_time})
                else:
                    key = search_key
                    search_params.update({key: api_time})

                if 'with' in join_word:
                    format_str += " %s %%(calculatedTime)s" % " ".join(key.split('_'))
                else:
                    format_str += join_word + " %s %%(calculatedTime)s" % " ".join(key.split('_'))

        if tokens.assignee:
            search_params.update({'assignee': tokens.assignee})
            format_str += " for %(assignee)s"

        print(search_params)
        result = api.search(**search_params)
        if tokens.calculatedTime:
            tokens['calculatedTime'] = tokens.calculatedTime.strftime('%a, %b %Y')
        tokens['count'] = result.count

        return format_str % tokens