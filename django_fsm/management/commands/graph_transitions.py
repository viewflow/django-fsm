# -*- coding: utf-8; mode: django -*-
import graphviz
from optparse import make_option

from django.core.management.base import BaseCommand
from django.utils.encoding import smart_text

from django_fsm import FSMFieldMixin

try:
    from django.db.models import get_apps, get_app, get_models, get_model
    NEW_META_API = False
except ImportError:
    from django.apps import apps
    NEW_META_API = True


def all_fsm_fields_data(model):
    if NEW_META_API:
        return [(field, model) for field in model._meta.get_fields()
                if isinstance(field, FSMFieldMixin)]
    else:
        return [(field, model) for field in model._meta.fields
                if isinstance(field, FSMFieldMixin)]


def node_name(field, state):
    opts = field.model._meta
    return "%s.%s.%s.%s" % (opts.app_label, opts.verbose_name.replace(' ', '_'), field.name, state)


def generate_dot(fields_data):
    result = graphviz.Digraph()

    for field, model in fields_data:
        sources, targets, edges, any_targets, any_except_targets = set(), set(), set(), set(), set()

        # dump nodes and edges
        for transition in field.get_all_transitions(model):
            if transition.source == '*':
                any_targets.add((transition.target, transition.name))
            elif transition.source == '+':
                any_except_targets.add((transition.target, transition.name))
            else:
                source_name = node_name(field, transition.source)
                if transition.target is not None:
                    target_name = node_name(field, transition.target)
                    if isinstance(transition.source, int):
                        source_label = [smart_text(name[1]) for name in field.choices if name[0] == transition.source][0]
                    else:
                        source_label = transition.source
                    sources.add((source_name, source_label))
                    if isinstance(transition.target, int):
                        target_label = [smart_text(name[1]) for name in field.choices if name[0] == transition.target][0]
                    else:
                        target_label = transition.target
                    targets.add((target_name, target_label))
                    edges.add((source_name, target_name, (('label', transition.name),)))
            if transition.on_error:
                on_error_name = node_name(field, transition.on_error)
                targets.add((on_error_name, transition.on_error))
                edges.add((source_name, on_error_name, (('style', 'dotted'),)))

        for target, name in any_targets:
            target_name = node_name(field, target)
            targets.add((target_name, target))
            for source_name, label in sources:
                edges.add((source_name, target_name, (('label', name),)))

        for target, name in any_except_targets:
            target_name = node_name(field, target)
            targets.add((target_name, target))
            for source_name, label in sources:
                if target_name == source_name:
                    continue
                edges.add((source_name, target_name, (('label', name),)))

        # construct subgraph
        opts = field.model._meta
        subgraph = graphviz.Digraph(
            name="cluster_%s_%s_%s" % (opts.app_label, opts.object_name, field.name),
            graph_attr={'label': "%s.%s.%s" % (opts.app_label, opts.object_name, field.name)})

        final_states = targets - sources
        for name, label in final_states:
            subgraph.node(name, label=label, shape='doublecircle')
        for name, label in (sources | targets) - final_states:
            subgraph.node(name, label=label, shape='circle')
            if field.default:  # Adding initial state notation
                if label == field.default:
                    initial_name = node_name(field, '_initial')
                    subgraph.node(name=initial_name, label='', shape='point')
                    subgraph.edge(initial_name, name)
        for source_name, target_name, attrs in edges:
            subgraph.edge(source_name, target_name, **dict(attrs))

        result.subgraph(subgraph)

    return result


class Command(BaseCommand):
    requires_system_checks = True

    option_list = BaseCommand.option_list + (
        make_option('--output', '-o', action='store', dest='outputfile',
                    help=('Render output file. Type of output dependent on file extensions. '
                          'Use png or jpg to render graph to image.')),
        # NOQA
        make_option('--layout', '-l', action='store', dest='layout', default='dot',
                    help=('Layout to be used by GraphViz for visualization. '
                          'Layouts: circo dot fdp neato nop nop1 nop2 twopi')),
    )

    help = ("Creates a GraphViz dot file with transitions for selected fields")
    args = "[appname[.model[.field]]]"

    def render_output(self, graph, **options):
        filename, format = options['outputfile'].rsplit('.', 1)

        graph.engine = options['layout']
        graph.format = format
        graph.render(filename)

    def handle(self, *args, **options):
        fields_data = []
        if len(args) != 0:
            for arg in args:
                field_spec = arg.split('.')

                if len(field_spec) == 1:
                    if NEW_META_API:
                        app = apps.get_app(field_spec[0])
                        models = apps.get_models(app)
                    else:
                        app = get_app(field_spec[0])
                        models = get_models(app)
                    for model in models:
                        fields_data += all_fsm_fields_data(model)
                elif len(field_spec) == 2:
                    if NEW_META_API:
                        model = apps.get_model(field_spec[0], field_spec[1])
                    else:
                        model = get_model(field_spec[0], field_spec[1])
                    fields_data += all_fsm_fields_data(model)
                elif len(field_spec) == 3:
                    if NEW_META_API:
                        model = apps.get_model(field_spec[0], field_spec[1])
                        fields_data.append((model._meta.get_field(field_spec[2])[0], model))
                    else:
                        model = get_model(field_spec[0], field_spec[1])
                        fields_data.append((model._meta.get_field_by_name(field_spec[2])[0], model))
        else:
            if NEW_META_API:
                for model in apps.get_models():
                    fields_data += all_fsm_fields_data(model)
            else:
                for app in get_apps():
                    for model in get_models(app):
                        fields_data += all_fsm_fields_data(model)

        dotdata = generate_dot(fields_data)

        if options['outputfile']:
            self.render_output(dotdata, **options)
        else:
            print(dotdata)
