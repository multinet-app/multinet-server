# Recommender
"""Flask blueprint for Multinet REST API."""
from flasgger import swag_from
from flask import Blueprint, request
from webargs import fields
from webargs.flaskparser import use_kwargs

from typing import Any, Optional, List
from multinet.types import EdgeDirection, TableType
from multinet.validation import ValidationFailure, UndefinedKeys, UndefinedTable

from multinet import db, util
from multinet.errors import (
    ValidationFailed,
    BadQueryArgument,
    MalformedRequestBody,
    AlreadyExists,
    RequiredParamsMissing,
)

bp = Blueprint("multinet-recommender", __name__)
bp.before_request(util.require_db)


@bp.route("/workspace/<workspace>/graph/<graph>", methods=["GET"])
# @swag_from("swagger/workspaces.yaml")
def get_stats(workspace:str, graph:str) -> Any:
    """Retrieve summary statistics of graph."""
    table_dict = db.workspace_graph(workspace, graph)
    node_tables = table_dict['nodeTables']
    edge_table = table_dict['edgeTable']

    gs = GraphStatistics(workspace, node_table_paths = node_tables, link_table_paths = [edge_table])
    stats = {'network_size': gs.get_network_size()
            , 'nr_node_attributes': gs.get_amount_node_attributes()
            , 'nr_edge_attributes': gs.get_amount_edge_attributes()
            , 'is_homogeneous_network': gs.is_homogeneous_network()
            , 'is_tree': gs.is_tree()
            , 'degree_statistics': gs.get_degree_statistics()
            }
    
    return stats


import numpy as np
import pandas as pd
import networkx as nx

class GraphStatistics:
    
    def __init__(self, workspace, node_table_paths = ["data/openflights/airports.csv"], node_table_names = ["airports"], node_key = ["_key"], link_table_paths = ["data/openflights/routes.csv"], link_table_names = ["routes"], link_from = ["_from"], link_to = ["_to"]):
        
        self.node_table_paths = node_table_paths
        self.node_table_names = node_table_names
        self.node_key = node_key
        
        self.link_table_paths = link_table_paths
        self.link_table_names = link_table_names
        self.link_from = link_from
        self.link_to = link_to

        self.workspace = workspace
        
        self.load_data()
        self.build_graph()
    
    def load_data(self):
        self.data_map = {}

        for i in range(len(self.node_table_paths)):
            #pd_table = pd.read_csv(self.node_table_paths[i])
            rows = db.workspace_table_no_limit(self.workspace, self.node_table_paths[i])
            pd_table = pd.DataFrame(rows)
            key = self.node_key[i]
            name = self.node_table_names[i]
            #print(pd_table)

            # add tablename prefix to key
            # pd_table[key] = pd_table[key].astype(str).str.replace(name + '/', '')
            # pd_table[key] = name + '/' + pd_table[key].astype(str)
            self.data_map[self.node_table_names[i]] = pd_table

        for i in range(len(self.link_table_paths)):
            # link tables should have keys to nodes with the corresponding tablename as prefix
            rows = db.workspace_table_no_limit(self.workspace, self.link_table_paths[i])
            self.data_map[self.link_table_names[i]] = pd.DataFrame(rows)
            
            
            
    def build_graph(self):
        self.graph = nx.MultiDiGraph()

        # add nodes to the graph
        for i in range(len(self.node_table_names)):
            table_name = self.node_table_names[i]
            key = self.node_key[i]
            self.graph.add_nodes_from(self.data_map[table_name][key])

        for i in range(len(self.link_table_names)):
            table_name = self.link_table_names[i]
            source = self.link_from[i]
            target = self.link_to[i]
            pd_table = self.data_map[table_name]
            temp = nx.from_pandas_edgelist(pd_table, source=source, target=target, create_using=nx.MultiDiGraph)
            self.graph = nx.compose(self.graph, temp)
        
    def get_network_size(self):
        return nx.number_of_nodes(self.graph)
    
    def get_amount_node_attributes(self):
        # this amount includes the key!
        nr_attributes = []
        for table_name in self.node_table_names:
            nr_attributes.append(len(self.data_map[table_name].columns))
        return max(nr_attributes) # for several tables, we could take some aggregation funktion e.g. max(...)
        
    def get_amount_edge_attributes(self):
        nr_attributes = []
        for table_name in self.link_table_names:
            nr_attributes.append(len(self.data_map[table_name].columns))
        return max(nr_attributes) # for several tables, we could take some aggregation funktion e.g. max(...)
    
    def is_homogeneous_network(self):
        return len(self.node_table_names) <= 1 and len(self.link_table_names) <= 1
    
    def is_tree(self):
        return nx.is_tree(self.graph)
    
    def get_degree_statistics(self):
        dv = self.graph.degree()
        degrees = [degree for node, degree in dv]
        degrees = np.array(degrees)
        
        stats = ( ('min degree', int(np.min(degrees)))
                , ('max degree', int(np.max(degrees)))
                , ('mean degree', np.mean(degrees))
                , ('std degree', np.std(degrees))
                , ('median0 degree', int(np.median(degrees))) # median degree is 0, which means that there are lots of isolated nodes...
                , ('mean no 0 degree', np.mean(degrees[degrees > 0])) # mean without 0s
                , ('std no 0 degree', np.std(degrees[degrees > 0])) # std without 0s
                )

        # stats = {}
        # stats['min degree'] = int(np.min(degrees))
        # stats['max degree'] = int(np.max(degrees))
        # stats['mean degree'] = np.mean(degrees)
        # stats['std degree'] = np.std(degrees)
        # stats['median degree'] = int(np.median(degrees)) # median degree is 0, which means that there are lots of isolated nodes...
        # stats['mean no 0 degree'] = np.mean(degrees[degrees > 0]) # mean without 0s
        # stats['std no 0 degree'] = np.std(degrees[degrees > 0]) # std without 0s
        return stats
