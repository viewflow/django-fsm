# -*- coding: utf-8; mode: django -*-
import pygraphviz
from optparse import make_option
from django.core.management.base import BaseCommand
from django.db.models import get_apps, get_app, get_models, get_model
from django_fsm import FSMFieldMixin


def all_fsm_fields_data(model):
    return [(field, model) for field in model._meta.fields
            if isinstance(field, FSMFieldMixin)]


def node_name(field, state):
    opts = field.model._meta
    return "%s.%s.%s.%s" % (opts.app_label, opts.verbose_name, field.name, state)


def generate_dot(fields_data):
    result = pygraphviz.AGraph(directed=True)
    model_graphs = {}

    for field, model in fields_data:
        sources, any_targets = [], []

        for transition in field.get_all_transitions(model):
            opts = field.model._meta
            if field.model in model_graphs:
                model_graph = model_graphs[field.model]
            else:
                model_graph = result.subgraph(name="cluster_%s_%s" % (opts.app_label, opts.object_name),
                                              label="%s.%s" % (opts.app_label, opts.object_name))

            if transition.source == '*':
                any_targets.append(transition.target)
            else:
                if transition.target is not None:
                    source_node = node_name(field, transition.source)
                    target_node = node_name(field, transition.target)
                    if source_node not in model_graph:
                        model_graph.add_node(source_node, label=transition.source)
                    if target_node not in model_graph:
                        model_graph.add_node(target_node, label=transition.target)
                    model_graph.add_edge(source_node, target_node)
                    sources.append(transition.source)

        for target in any_targets:
            target_node = node_name(field, target)
            model_graph.add_node(target_node, label=target)
            for source in sources:
                model_graph.add_edge(node_name(field, source), target_node)

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
        graph.layout(prog=options['layout'])
        graph.draw(options['outputfile'])

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
