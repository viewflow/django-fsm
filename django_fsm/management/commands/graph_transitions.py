# -*- coding: utf-8; mode: django -*-
import graphviz
from optparse import make_option
from django.core.management.base import BaseCommand
from django.db.models import get_apps, get_app, get_models, get_model
from django_fsm import FSMFieldMixin


def all_fsm_fields_data(model):
    return [(field, model) for field in model._meta.fields
            if isinstance(field, FSMFieldMixin)]


def node_name(field, state):
    opts = field.model._meta
    return "%s.%s.%s.%s" % (opts.app_label, opts.verbose_name.replace(' ', '_'), field.name, state)


def generate_dot(fields_data):
    result = graphviz.Digraph()

    for field, model in fields_data:
        sources, targets, edges, any_targets = set(), set(), set(), set()

        # dump nodes and edges
        for transition in field.get_all_transitions(model):
            if transition.source == '*':
                any_targets.add((transition.target, transition.name))
            else:
                if transition.target is not None:
                    source_name = node_name(field, transition.source)
                    target_name = node_name(field, transition.target)
                    sources.add((source_name, transition.source))
                    targets.add((target_name, transition.target))
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

        # construct subgraph
        opts = field.model._meta
        subgraph = graphviz.Digraph(
            name="cluster_%s_%s" % (opts.app_label, opts.object_name),
            graph_attr={'label': "%s.%s" % (opts.app_label, opts.object_name)})

        final_states = targets - sources
        for name, label in final_states:
            subgraph.node(name, label=label, shape='doublecircle')
        for name, label in (sources | targets) - final_states:
            subgraph.node(name, label=label, shape='circle')
            if field.default:  # Adding initial state notation
                if label == field.default:
                    subgraph.node('.', shape='point')
                    subgraph.edge('.', name)
        for source_name, target_name, attrs in edges:
            subgraph.edge(source_name, target_name, **dict(attrs))

        result.subgraph(subgraph)

    return result


class Command(BaseCommand):
    requires_model_validation = True

    option_list = BaseCommand.option_list + (
        make_option('--output', '-o', action='store', dest='outputfile',
            help='Render output file. Type of output dependent on file extensions. Use png or jpg to render graph to image.'),  # NOQA
        make_option('--layout', '-l', action='store', dest='layout', default='dot',
            help='Layout to be used by GraphViz for visualization. Layouts: circo dot fdp neato nop nop1 nop2 twopi'),
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
                    app = get_app(field_spec[0])
                    models = get_models(app)
                    for model in models:
                        fields_data += all_fsm_fields_data(model)
                elif len(field_spec) == 2:
                    model = get_model(field_spec[0], field_spec[1])
                    fields_data += all_fsm_fields_data(model)
                elif len(field_spec) == 3:
                    model = get_model(field_spec[0], field_spec[1])
                    fields_data.append((model._meta.get_field_by_name(field_spec[2])[0], model))
        else:
            for app in get_apps():
                for model in get_models(app):
                    fields_data += all_fsm_fields_data(model)

        dotdata = generate_dot(fields_data)

        if options['outputfile']:
            self.render_output(dotdata, **options)
        else:
            print(dotdata)
