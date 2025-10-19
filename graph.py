from pyalex import Works, config
from nicegui import ui, app
from objects import BibFile, Reference, String, GraphNode
from collections import defaultdict
import pprint
import threading
import networkx as nx
import json

# pyalex.config.email = "tabreafabian0@gmail.com"
config.max_retries = 0
config.retry_backoff_factor = 0.1
config.retry_http_codes = [429, 500, 503]


def generate_graph(bib_file: BibFile):
    adjacency_list = defaultdict(list)
    base_nodes_titles = []
    
    for entry in bib_file.content:
        if isinstance(entry, Reference):

            fields = entry.get_fields()
            title = fields['title'].replace("{", "").replace("}", "")
            year = fields['year'].replace("{", "").replace("}", "")
            
            try:
                fetched_work = None
                results = Works().search(title).get() # Optimize this
                for w in results:
                    if w.get("title", "").strip().lower() == title.strip().lower() and str(w.get("publication_year", 0)) == str(year):
                        fetched_work = w
                        break
                        
                base_nodes_titles.append(construct_work_description(fetched_work))
                
                first_neighbours = update_adjacency_neighbours(adjacency_list, fetched_work)
                
                for first_neighbour in first_neighbours:
                    second_neighbours = update_adjacency_neighbours(adjacency_list, first_neighbour)
                    for second_neighbours in second_neighbours:
                        update_adjacency_neighbours(adjacency_list, second_neighbours, 5)
                        
            except Exception as e:
                print("Unexpected exception: ", e)

    Graph = nx.DiGraph()
    
    for base_node, neighbours in adjacency_list.items():
        for neighbour in neighbours:    
            Graph.add_edge(construct_node_description(base_node), construct_node_description(neighbour))
            
    try:
        threading.Thread(target=run_server(Graph, base_nodes_titles), daemon=True).start()
    except Exception as e:
        print("Unexpected exception: ", e)
        

def run_server(constructed_graph, base_nodes_titles = []):
    try:
        G = constructed_graph
        nodes = []
        
        base_set  = set(base_nodes_titles)
        first_set = {v for u, v in G.edges() if u in base_set}
        second_set = {v for u, v in G.edges() if u in first_set}
        
        for n in G.nodes():
            in_degree = G.in_degree(n)
            out_degree = G.out_degree(n)
            label = f"{n}\n(cited by: {in_degree}, cites: {out_degree})"
            
            if n in base_set:
                nodes.append({"id": str(n), "label": label, "color": "#c47e63"})
            
            elif n in first_set:
                nodes.append({"id": str(n), "label": label, "color": "#819a90"})
                
            elif n in second_set:
                nodes.append({"id": str(n), "label": label, "color": "#3c649f"})
                
            else:   
                nodes.append({"id": str(n), "label": label, "color": "#dccbb6"})
                
            # nodes.append({"id": str(n), "label": label, "color": "#dccbb6"})
            
        edges = [{"from": u, "to": v, "arrows": "to", "label": str(G[u][v].get('weight', '')), 
        "font": {
            "color": "red",        
            "background": "white", 
            "strokeWidth": 3,
            "strokeColor": "black"
            }} for u, v in G.edges()]
        
        nodes_json = json.dumps(nodes)
        edges_json = json.dumps(edges)

        @ui.page('/')
        def page():
            app.add_static_files('/static', 'static')  
            ui.html('<div id="graph" style="width:autodv; height:autodv"]></div>')
            ui.add_head_html('<script src="/static/graph.js"></script>')
            ui.run_javascript(f'GraphWidget.init("#graph", {nodes_json}, {edges_json});')

        ui.run(port=8090, reload=False) 
        # ui.run(native=True, reload=False)  # opens a native window via PyWebView
        # s = socket.socket(); s.bind(('', 0)); port = s.getsockname()[1]; s.close()
        # ui.run(host='127.0.0.1', port=port, reload=False)
        
    except (KeyboardInterrupt, SystemExit):
        print("some exception")
        
        
def update_adjacency_neighbours(adjacency_list, base_node, max = 5):
    # SOLVE THIS !!!!!!!!!!!
    neighbour_node = GraphNode(base_node.get("title", "N/A"))
    neighbour_node.authors = [author['author']['display_name'] for author in base_node.get("authorships", [])]
    neighbour_node.year = base_node.get("publication_year", "N/A")
    
    
    second_id_refs = base_node.get("referenced_works", [])
    second_neighbours = []
    
    if len(second_id_refs) > 0:
        joined = "|".join(second_id_refs)
        second_neighbours = Works().filter(openalex=joined).sort(cited_by_count="desc").select(["id", "title", "publication_year", "authorships", "referenced_works"]).get(per_page=15)
        second_neighbours = second_neighbours[:max]
        
        for second_neighbour in second_neighbours:
            node2 = GraphNode(second_neighbour.get("title", "N/A"))
            node2.authors = [author['author']['display_name'] for author in second_neighbour.get("authorships", [])]
            node2.year = second_neighbour.get("publication_year", "N/A")
            adjacency_list[neighbour_node].append(node2)
            
    else:
        adjacency_list[neighbour_node] = []
        
    return second_neighbours
        
def construct_node_description(base_node: GraphNode):
    title = base_node.title
    year =  str(base_node.year)
    authors = str(base_node.authors).replace("[", "").replace("]", "")
    
    return f"Title: {title} \n Publication Year: {year} \n Authors: {authors}" 

def construct_work_description(work):
    title = work.get("title", "N/A")
    year = str(work.get("publication_year", "N/A"))
    authors = str([author['author']['display_name'] for author in work.get("authorships", [])]).replace("[", "").replace("]", "")
    
    return f"Title: {title} \n Publication Year: {year} \n Authors: {authors}" 
    


        





