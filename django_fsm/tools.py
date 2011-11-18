# -*- coding: utf-8 -*-
"""
Various tools for the FSM

Created on 18/11/2011

@author: laur
"""
from django_fsm.db.fields.fsmfield import all_states

def write_png_graph(fname):
    """
    Make a graph of all available FSMs and save it in a PNG file

    @param fname: The file name of the image (.png)
    """
    try:
        import pydot
    except:
        return

    # Browse all tuples
    #
    nodes = {}
    graph = pydot.Dot(graph_type='digraph')
    uniq = []
    for src, dest in all_states:
        if src and not nodes.has_key(src):
            nodes[src] = pydot.Node(src, shape = "rect")
            graph.add_node(nodes[src])
        if dest and not nodes.has_key(dest):
            nodes[dest] = pydot.Node(dest, shape = "rect")
            graph.add_node(nodes[dest])

        # Add the connection between the two nodes
        #
        if not src or not dest:
            continue
        t = "__%s__:__%s__" % (src, dest)
        if t in uniq:
            continue
        uniq.append(t)
        graph.add_edge(pydot.Edge(nodes[src], nodes[dest]))

    graph.write_png(fname)
