from tempfile import NamedTemporaryFile

from django.core.management import call_command
from django.test import TestCase


class TestCommand(TestCase):
    def test_graph_transitions(self):
        with NamedTemporaryFile(suffix='.png') as tmpfile:
            call_command('graph_transitions', 'testapp.Application',
                         outputfile=tmpfile.name)

        # XXX: collects also all models from the tests, and breaks?!
        # call_command('graph_transitions', 'testapp')
        # Traceback (most recent call last):
        #   File "django-fsm/tests/testapp/tests/test_command.py", line 14, in test_graph_transitions
        #     call_command('graph_transitions', 'testapp')
        #   File "django-fsm/.tox/py35-dj18/lib/python3.5/site-packages/django/core/management/__init__.py", line 120, in call_command
        #     return command.execute(*args, **defaults)
        #   File "django-fsm/.tox/py35-dj18/lib/python3.5/site-packages/django/core/management/base.py", line 445, in execute
        #     output = self.handle(*args, **options)
        #   File "django-fsm/django_fsm/management/commands/graph_transitions.py", line 162, in handle
        #     dotdata = generate_dot(fields_data)
        #   File "django-fsm/django_fsm/management/commands/graph_transitions.py", line 85, in generate_dot
        #     subgraph.node(name, label=label, shape='doublecircle')
        #   File "django-fsm/.tox/py35-dj18/lib/python3.5/site-packages/graphviz/dot.py", line 104, in node
        #     attributes = self.attributes(label, attrs, _attributes)
        #   File "django-fsm/.tox/py35-dj18/lib/python3.5/site-packages/graphviz/lang.py", line 91, in attributes
        #     result = ['label=%s' % quote(label)]
        #   File "django-fsm/.tox/py35-dj18/lib/python3.5/site-packages/graphviz/lang.py", line 44, in quote
        #     if html(identifier):
        # TypeError: expected string or bytes-like object
