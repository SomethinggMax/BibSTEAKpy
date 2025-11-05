import sys, time, threading, json, pprint
import networkx as nx
from objects import BibFile, Reference, String, GraphNode
from collections import defaultdict
from pyalex import Works, config
from nicegui import ui, app

stop_event = threading.Event()
RESET = "\033[0m"; RST = "\033[0m"
YELLOW = "\033[33m"

def show_status():
    dots = 0
    while not stop_event.is_set():
            sys.stdout.write(f"{YELLOW}\rLOADING GRAPH {'.' * dots}{(6 - dots) * ' '}{RESET}")
            sys.stdout.flush()
            time.sleep(0.5)
            dots = (dots + 1) % 6
    
    print("Graph loaded! - Check your browser")
    


# pyalex.config.email = "tabreafabian0@gmail.com"
config.max_retries = 0
config.retry_backoff_factor = 0.1
config.retry_http_codes = [429, 500, 503]


def generate_graph(bib_file: BibFile, k_regular: int):
    adjacency_list = defaultdict(list)
    base_nodes_titles = []
    
    t = threading.Thread(target=show_status, daemon=True)
    t.start()
    
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
                
                first_neighbours = update_adjacency_neighbours(adjacency_list, fetched_work, k_regular)
                
                for first_neighbour in first_neighbours:
                    second_neighbours = update_adjacency_neighbours(adjacency_list, first_neighbour, k_regular)
                    for second_neighbours in second_neighbours:
                        update_adjacency_neighbours(adjacency_list, second_neighbours, k_regular)
                        
            except Exception as e:
                print("Unexpected exception: ", e)

    Graph = nx.DiGraph()
    
    for base_node, neighbours in adjacency_list.items():
        for neighbour in neighbours:    
            Graph.add_edge(construct_node_description(base_node), construct_node_description(neighbour))
            
    try:
        stop_event.set()
        threading.Thread(target=run_server, args=(Graph, base_nodes_titles), daemon=True).start()
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
            ui.html('<div id="graph" style="width:100%; height:100vh"></div>', sanitize=True)
            ui.add_head_html('<script src="/static/graph.js"></script>', sanitize=True)
            ui.run_javascript(f'GraphWidget.init("#graph", {nodes_json}, {edges_json});')

        ui.run(port=8090, reload=False) 
        # ui.run(native=True, reload=False)  # opens a native window via PyWebView
        # s = socket.socket(); s.bind(('', 0)); port = s.getsockname()[1]; s.close()
        # ui.run(host='127.0.0.1', port=port, reload=False)
        
    except (KeyboardInterrupt):
        print(f"Graph Simulation Terminated!")
    except Exception as e:
        print(e)
        
        
def update_adjacency_neighbours(adjacency_list, base_work, max = 5):
    # Make this faster
    base_node = None
    is_key = False
    
    for node_object in adjacency_list.keys():
        if node_object.title == base_work.get("title", "N/A") and node_object.year == base_work.get("publication_year", "N/A"):
            base_node = node_object
            is_key = True
            break
        
    if is_key == False:
        base_node = GraphNode(base_work.get("title", "N/A"))
        base_node.authors = [author['author']['display_name'] for author in base_work.get("authorships", [])]
        base_node.year = base_work.get("publication_year", "N/A")
    
    neighbours_ids = base_work.get("referenced_works", [])[:10] # Improve this
    neighbours = []
    
    if len(neighbours_ids) > 0:
        try:
            joined = "|".join(neighbours_ids)
            neighbours = Works().filter(openalex=joined).sort(cited_by_count="desc").select(["id", "title", "publication_year", "authorships", "referenced_works"]).get(per_page=15)
            neighbours = neighbours[:max]
            
            for second_neighbour in neighbours:
                neighbour_node = GraphNode(second_neighbour.get("title", "N/A"))
                neighbour_node.authors = [author['author']['display_name'] for author in second_neighbour.get("authorships", [])]
                neighbour_node.year = second_neighbour.get("publication_year", "N/A")
                
                adjacency_list[base_node].append(neighbour_node)
                
        except Exception as e:
            print(e)
    else:
        adjacency_list[base_node] = []
        
    return neighbours

        
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
    


        





