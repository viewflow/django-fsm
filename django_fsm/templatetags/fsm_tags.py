# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import template
from django.template.base import kwarg_re, Node, TemplateSyntaxError
from django.utils.encoding import smart_text

register = template.Library()


class GetAvailableTransitionsNode(Node):
    def __init__(self, obj, field_name, args, kwargs, asvar):
        self.obj = obj
        self.field_name = field_name
        self.args = args
        self.kwargs = kwargs
        self.asvar = asvar

    def render(self, context):
        obj = self.obj.resolve(context)
        field_name = self.field_name.resolve(context)
        args = [arg.resolve(context) for arg in self.args]
        kwargs = dict([(smart_text(k, 'ascii'), v.resolve(context))
                       for k, v in self.kwargs.items()])

        func = getattr(obj, 'get_available_%s_transitions' % field_name)
        context[self.asvar] = func(*args, **kwargs)
        return ''


@register.tag
def get_available_transitions(parser, token):
    """
    Usage:

        {% get_available_transitions <object> <field_name> [<args>] [<kwargs>] as state_transitions %}

    Example:

        {% get_available_transitions purchase "state" as state_transitions %}
        {% for new_state, transition_function in state_transitions %}
            <button class="btn" type="submit" data-action="{{ transition_function.func_name }}">
                Transition to {{ new_state }}
            </button>
        {% endfor %}

    If the transition and condition functions take arguments you can pass these as well:

        {% get_available_transitions purchase "state" request.user as state_transitions %}

    In fact if the transition and condition functions don't take any arguments you can just call the
    get_available_FIELD_transitions method directly:

        {% for new_state, transition_function in purchase.get_available_state_transitions %}

    This template tag is necessary only if there are any arguments to pass to the transition
    and condition functions.
    """

    bits = token.split_contents()
    tag_name = bits[0]
    AS, asvar = bits[-2:]

    if len(bits) < 5 or AS != 'as':
        raise TemplateSyntaxError("'%s' takes at least 4 arguments like this:\n"
                                  "<object> <field_name> [args] [kwargs] as <as_var>"
                                  % tag_name)

    obj = parser.compile_filter(bits[1])
    field_name = parser.compile_filter(bits[2])
    bits = bits[3:-2]

    args = []
    kwargs = {}

    for bit in bits:
        match = kwarg_re.match(bit)
        if not match:
            raise TemplateSyntaxError("Malformed arguments to '%s' tag" % tag_name)
        name, value = match.groups()
        if name:
            kwargs[name] = parser.compile_filter(value)
        else:
            args.append(parser.compile_filter(value))

    return GetAvailableTransitionsNode(obj, field_name, args, kwargs, asvar)
