from pyalex import Works, config
from objects import BibFile, Reference, String, GraphNode
from collections import defaultdict
import pprint
import threading
import networkx as nx
import json
from nicegui import ui

# pyalex.config.email = "tabreafabian0@gmail.com"
config.max_retries = 0
config.retry_backoff_factor = 0.1
config.retry_http_codes = [429, 500, 503]

def run_server(constructed_graph, base_nodes_titles = [], first_neighbours_titles = []):
    print("here")
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
                
                
            
            # if "marie" in str(n).lower() or "marie" in label.lower():
            #     n["color"] = {"background": "#2ecc71", "border": "#1e824c"}

        # nodes = [{"id": str(n), "label": str(n)} for n in G.nodes()]
        # edges = [{"from": str(u), "to": str(v)} for u, v in G.edges()]
        edges = [{"from": u, "to": v, "arrows": "to", "label": str(G[u][v].get('weight', '')), "font": {
            "color": "red",        # color of the label text
            # optional extras:
            "background": "white", # rectangle background behind text
            "strokeWidth": 3,
            "strokeColor": "black"
        }} for u, v in G.edges()]
        
        nodes_json = json.dumps(nodes)
        edges_json = json.dumps(edges)

        @ui.page('/')
        def page():

            ui.html('<div id="graph" style="width:autodv; height:autodv"]></div>')
            
            ui.run_javascript(f"""
            (function () {{
            function truncateLabel(s, n) {{
                if (!s) return s;
                if (s.length <= n) return s;
                return s.slice(0, n - 1) + "…";
            }}

            function wrapByWords(text, maxPerLine) {{
                if (!text) return "";
                const words = String(text).split(/\\s+/);
                let line = "", out = [];
                for (const w of words) {{
                if ((line + " " + w).trim().length > maxPerLine) {{
                    out.push(line.trim());
                    line = w;
                }} else {{
                    line += " " + w;
                }}
                }}
                if (line.trim()) out.push(line.trim());
                return out.join("\\n"); // vis-network uses \\n for new lines
            }}

            // Prepare datasets with short/long labels and tooltips
            const rawNodes = {nodes_json};
            const nodes = rawNodes.map(n => {{
                const titleOnly   = String(n.id);                    // your academic title is in n.id (or use another field if needed)
                const statsLine   = n.label.split("\\n").slice(1).join("\\n"); // keep your (cited by, cites) part
                const wrappedFull = wrapByWords(titleOnly, 32);      // multi-line full label
                const shortTitle  = truncateLabel(titleOnly, 48);    // short, single-line + …
                const shortLabel  = shortTitle + (statsLine ? "\\n" + statsLine : "");
                const longLabel   = wrappedFull + (statsLine ? "\\n" + statsLine : "");
                
                return {{
                id: n.id,
                label: shortLabel,          // start collapsed
                title: titleOnly,           // full on hover
                _shortLabel: shortLabel,    // custom fields we will toggle
                _longLabel:  longLabel,
                _isShort: true,
                shape: "ellipse",                // box allows wrapping nicely with widthConstraint
                color:  n.color || {{ background: '#27AE60', border: '#66BB6A' }}
                }};
            }});

            const edges = {edges_json};

            function render() {{
                const container = document.getElementById('graph');
                const data = {{
                nodes: new vis.DataSet(nodes),
                edges: new vis.DataSet(edges)
                }};
                
            const options = {{
                physics: {{ 
                enabled: true,
                stabilization: false,
                solver: 'repulsion',
                repulsion: {{
                    nodeDistance: 1500,     // push components apart
                    springLength: 300,
                    springConstant: 0.03,
                    damping: 0.09,
                    centralGravity: 0.0    // avoid pulling everything to the center
                }}

                }},
                interaction: {{ hover: true, dragNodes: true, zoomView: true, zoomSpeed: 0.6, navigationButtons: true, dragView: true}},
                // edges: {{ length: 250,width: 15}},
                edges: {{width: 15}},
                
                nodes: {{
                    shape: "ellipse",
                    shadow: {{ enabled: true, size: 15, x: 7, y: 7 }},
                    margin: 6,
                    size: 30,
                    widthConstraint: {{ maximum: 180 }},   // wrap to this width
                    font: {{
                    // 'multi' isn't required for wrapping; \\n handles new lines
                    // you can tweak size or face if you want
                    size: 20,
     
                    }}
                }}
                }};
                
                const network = new vis.Network(container, data, options);

                // Toggle expand/collapse on double-click
                network.on("doubleClick", params => {{
                if (!params.nodes || !params.nodes.length) return;
                const id = params.nodes[0];
                const n = data.nodes.get(id);
                if (!n) return;
                if (n._isShort) {{
                    data.nodes.update({{ id, label: n._longLabel, _isShort: false }});
                }} else {{
                    data.nodes.update({{ id, label: n._shortLabel, _isShort: true }});
                }}
                }});
            }}

            if (window.vis) {{ render(); }}
            else {{
                const s = document.createElement('script');
                s.src = 'https://unpkg.com/vis-network/standalone/umd/vis-network.min.js';
                s.onload = render;
                document.head.appendChild(s);
            }}
            }})();
            """)

        ui.run(port=8090, reload=False) 
        # ui.run(native=True, reload=False)  # opens a native window via PyWebView
        # s = socket.socket(); s.bind(('', 0)); port = s.getsockname()[1]; s.close()
        # ui.run(host='127.0.0.1', port=port, reload=False)
        
    except (KeyboardInterrupt, SystemExit):
        print("some exception")
        
        
def update_adjacency_neighbours(adjacency_list, base_node, max = 5):
    # SOLVE THIS
    neighbour_node = GraphNode(base_node.get("title", "No known title"))
    neighbour_node.authors = [author['author']['display_name'] for author in base_node.get("authorships", [])]
    neighbour_node.year = base_node.get("publication_year", "No known year")
    
    
    second_id_refs = base_node.get("referenced_works", [])
    second_neighbours = None
    
    if len(second_id_refs) > 0:
        joined = "|".join(second_id_refs)
        second_neighbours = Works().filter(openalex=joined).sort(cited_by_count="desc").select(["id", "title", "publication_year", "authorships", "referenced_works"]).get(per_page=15)
        second_neighbours = second_neighbours[:max]
        
        for second_neighbour in second_neighbours:
            authors = [author['author']['display_name'] for author in second_neighbour.get("authorships", [])]
            node2 = GraphNode(second_neighbour.get("title", "No known title"))
            node2.authors = authors
            adjacency_list[neighbour_node].append(node2)
            
    else:
        adjacency_list[neighbour_node] = []
        
    return second_neighbours
        


def generate_graph(bib_file: BibFile):
    adjacency_list = defaultdict(list)
    keys = []
    base_nodes_titles = []
    first_neighbours_titles = []
    
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
                        
                base_nodes_titles.append(fetched_work.get("title", "No known title"))
                first_neighbours = update_adjacency_neighbours(adjacency_list, fetched_work)
                
                for neighbour in first_neighbours:
                    first_neighbours_titles.append(neighbour.get("title", "No known title"))
                    second_neighbours = update_adjacency_neighbours(adjacency_list, neighbour)
                    for sec_neighbour in second_neighbours:
                        update_adjacency_neighbours(adjacency_list, sec_neighbour, 3)
                        
                        
            except Exception as e:
                print(e)

    G = nx.DiGraph([("(John, 2024)","(Marie et al., 2017)")])
    for base_node, neighbours in adjacency_list.items():
        for neighbour in neighbours:    
            G.add_edge(base_node.title, neighbour.title)
        
    try:
        threading.Thread(target=run_server(G, base_nodes_titles, first_neighbours_titles), daemon=True).start()
    # run_server()
    except Exception:
        pass
        





