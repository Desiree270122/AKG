import networkx as nx
import matplotlib.pyplot as plt
import random
from rdflib import Graph, Namespace
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go

# Charger les données RDF
akg_file = "teaching_akg.ttl"
g = Graph()
g.parse(akg_file, format='ttl')

# Définir les namespaces
akg_namespace = Namespace("http://sonfack.com/2023/12/tao/")
cao_namespace = Namespace("http://sonfack.com/2023/12/cao/")

# Nettoyer les noms pour qu'ils soient plus lisibles
def get_clean_name(uri):
    if not isinstance(uri, str):
        uri = str(uri)
    if '#' in uri:
        return uri.split('#')[-1]
    return uri.split('/')[-1].replace("%20", " ")

def read_akg_node(node, graph):
    """Récupérer les informations RDF d'un nœud donné."""
    activity_info = {}
    for s, p, o in graph.triples((node, None, None)):
        activity_info[str(p)] = str(o)
    return activity_info

def modified_louvain_algorithm(G, graph):
    # Initialisation : Chaque sommet forme sa propre communauté
    partition = {node: i for i, node in enumerate(G.nodes())}
    
    # Créer une liste initiale de communautés, chaque nœud est dans sa propre communauté
    initial_communities = [{v} for v in G.nodes()]
    Q = nx.algorithms.community.modularity(G, initial_communities)

    # Pour chaque sommet v, commencer la fusion
    for v in G.nodes():
        # Créer une liste triée aléatoirement des voisins de v
        L = list(G.neighbors(v))
        random.shuffle(L)

        # Pour chaque sommet voisin de v
        for n in L:
            # Initialisation de la variable de comparaison
            q_max = -float('inf')
            best_neighbor = None

            # Calculer la partition actuelle
            current_partition = [set() for _ in range(len(set(partition.values())))]
            for node, comm in partition.items():
                current_partition[comm].add(node)

            # Calculer la modularité avant la fusion
            q = nx.algorithms.community.modularity(G, current_partition)

            # Si la modularité après fusion est meilleure
            if q > q_max:
                best_neighbor = n
                q_max = q

            # Si la meilleure modularité après fusion est supérieure à Q
            if q_max > Q:
                # Fusionner les deux sommets dans la même communauté
                partition[v] = partition[best_neighbor]
                Q = q_max  # Mettre à jour la modularité courante
                break

    # Transformer le dictionnaire en liste de communautés
    communities = {}
    for node, comm in partition.items():
        if comm not in communities:
            communities[comm] = set()
        communities[comm].add(node)
    
    # Créer la liste des communautés
    final_partition = list(communities.values())

    # Créer un dictionnaire à partir de la partition pour que chaque nœud ait une communauté
    partition_dict = {}
    for i, community in enumerate(final_partition):
        for node in community:
            partition_dict[node] = i

    # Calculer la modularité finale avec la partition obtenue
    modularity_finale = nx.algorithms.community.modularity(G, final_partition)
    
    return partition_dict, modularity_finale

def extract_and_clean_labels(activity_info, activity_uri, graph):
    """Extraire et nettoyer les noms des nœuds en fonction de l'URI ou de hasName."""
    has_name = activity_info.get('http://sonfack.com/2023/12/tao/hasName', None)
    if has_name:
        central_node = has_name  # Utiliser le nom hasName
    else:
        central_node = get_clean_name(activity_uri)  # Utiliser l'URI nettoyée
    
    return central_node

def visualize_graph_with_communities(G, partition, graph):
    """Visualiser tout le graphe avec les communautés détectées et afficher les noms nettoyés ou hasName."""
    plt.figure(figsize=(10, 10))

    pos = nx.spring_layout(G, seed=42)  # Positionnement des nœuds

    # Générer une palette de couleurs pour chaque communauté
    unique_communities = len(set(partition.values()))
    color_map = [plt.cm.tab20(i) for i in range(unique_communities)]

    # Affichage des arêtes
    nx.draw_networkx_edges(G, pos, alpha=0.5, edge_color='gray')

    # Dessiner les nœuds en fonction de leurs communautés
    for i, community in enumerate(set(partition.values())):
        nodes_in_community = [node for node in G.nodes() if partition[node] == community]
        nx.draw_networkx_nodes(G, pos, nodelist=nodes_in_community, node_color=[color_map[i]], node_size=300)

    # Ajouter les labels des nœuds avec le nom (soit hasName soit l'URI nettoyée)
    labels = {}
    for node in G.nodes():
        activity_info = read_akg_node(node, graph)  # Récupère les informations de chaque nœud
        labels[node] = extract_and_clean_labels(activity_info, node, graph) + f"\nComm {partition[node]}"
    
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=10, font_color='black')

    plt.title("Visualisation des communautés (Louvain Modifié) avec nom et numéro de communauté")
    plt.show()

# Exemple d'utilisation avec un graphe
G = nx.karate_club_graph()  # Exemple de graphe
graph = g  # Utilisez le graphe RDF chargé précédemment

# Appliquer l'algorithme de Louvain modifié
partition, modularity = modified_louvain_algorithm(G, graph)

# Visualiser le graphe avec les communautés détectées
visualize_graph_with_communities(G, partition, graph)

# Créer l'application Dash
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Visualisation de Communautés"
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Page d'accueil
login_layout = html.Div([
    html.H2("Page d'Accueil - Connexion", style={'textAlign': 'center'}),
    html.Div([
        html.Label("Nom d'utilisateur:"),
        dcc.Input(id='username', type='text', placeholder='Entrez votre nom d\'utilisateur'),
        html.Label("Mot de passe:"),
        dcc.Input(id='password', type='password', placeholder='Entrez votre mot de passe'),
        html.Button('Se connecter', id='login-button', n_clicks=0)
    ], style={'width': '30%', 'margin': 'auto'}),
    html.Div(id='login-message', style={'textAlign': 'center', 'color': 'red'})
])

# Page de visualisation des communautés
visualization_layout = html.Div([
    html.H1("Visualisation du Graphe de Connaissances", style={'textAlign': 'center'}),
    dcc.Dropdown(
        id='centrality-choice',
        options=[
            {'label': 'Filtrer par centralité de degré', 'value': 'degree'},
            {'label': 'Filtrer par centralité de proximité', 'value': 'closeness'},
            {'label': "Filtrer par centralité d'intermédiarité", 'value': 'betweenness'},
            {'label': 'Aucune filtration', 'value': 'none'}
        ],
        value='none',
        placeholder="Choisissez une option pour filtrer les communautés",
        style={'width': '50%', 'margin': 'auto'}
    ),
    dcc.Graph(id='knowledge-graph', style={'height': '50vh'}),
    dcc.Graph(id='resource-bar-chart', style={'height': '50vh'}),
    dcc.Graph(id='dendrogram', style={'height': '100vh'})
])

# Page pour étudier les communautés
study_layout = html.Div([
    html.H1("Étude des Communautés", style={'textAlign': 'center'}),
    dcc.Dropdown(
        id='community-choice',
        options=[
            {'label': 'Visualiser toutes les communautés', 'value': 'all'},
            {'label': 'Visualiser une seule communauté par activité', 'value': 'single'},
            {'label': 'Sélectionner plusieurs activités', 'value': 'multiple'},
            {'label': 'Détection par ressources', 'value': 'resources'}
        ],
        value='all',
        placeholder="Choisissez une option pour visualiser les communautés",
        style={'width': '50%', 'margin': 'auto'}
    ),
    dcc.Input(id='activity-name', type='text', placeholder='Entrez le nom de l\'activité', style={'display': 'none', 'margin': '10px'}),
    dcc.Graph(id='study-graph', style={'height': '100vh'})
])

# Mise à jour de la disposition en fonction de l'URL
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/visualization':
        return visualization_layout
    elif pathname == '/study':
        return study_layout
    else:
        return login_layout

# Vérifier les informations de connexion et rediriger vers la page de visualisation
@app.callback(
    Output('url', 'pathname'),
    [Input('login-button', 'n_clicks')],
    [State('username', 'value'),
     State('password', 'value')]
)
def login(n_clicks, username, password):
    if n_clicks > 0:
        if username == 'admin' and password == 'password':  # Remplacez par votre logique d'authentification
            return '/visualization'
        else:
            return '/'
    return '/'

# Mise à jour du graphique de visualisation
@app.callback(
    [Output('knowledge-graph', 'figure'),
     Output('resource-bar-chart', 'figure'),
     Output('dendrogram', 'figure')],
    [Input('centrality-choice', 'value')]
)
def update_graphs(centrality_choice):
    if centrality_choice == 'none':
        filtered_G = G
    else:
        filtered_G = filter_by_centrality(G, centrality_choice)
    return create_activity_graph_figure(filtered_G), create_resource_bar_chart(filtered_G), create_dendrogram(filtered_G)

# Mise à jour du graphique pour l'étude des communautés
@app.callback(
    [Output('study-graph', 'figure'),
     Output('activity-name', 'style')],
    [Input('community-choice', 'value'),
     Input('activity-name', 'value')]
)
def update_study_graph(choice, activity_name):
    if choice == 'all':
        plotly_data = create_activity_graph_figure(G)
        input_style = {'display': 'none', 'margin': '10px'}
    elif choice == 'single':
        input_style = {'display': 'block', 'margin': '10px'}
        if activity_name:
            subgraph = G.subgraph([n for n in G.nodes if activity_name.lower() in n.lower()])
            plotly_data = create_activity_graph_figure(subgraph)
        else:
            plotly_data = go.Figure()
    elif choice == 'multiple':
        input_style = {'display': 'block', 'margin': '10px'}
        if activity_name:
            activities = [a.strip() for a in activity_name.split(',')]
            subgraph = G.subgraph([n for n in G.nodes if any(a.lower() in n.lower() for a in activities)])
            plotly_data = create_activity_graph_figure(subgraph)
        else:
            plotly_data = go.Figure()
    elif choice == 'resources':
        input_style = {'display': 'none', 'margin': '10px'}
        # Créer un sous-graphe basé sur les relations spécifiées
        subgraph = nx.DiGraph()
        for node in G.nodes:
            if any(relation in node.lower() for relation in ['hasobjective', 'activitydescription', 'hassubject', 'hasname', 'hasduration', 'hasbegintime', 'iscomposedof', 'haslocation', 'schema', 'hasbeneficialto', 'iscarriedoutwith']):
                subgraph.add_node(node)
                for neighbor in G.neighbors(node):
                    subgraph.add_edge(node, neighbor)
        plotly_data = create_activity_graph_figure(subgraph)
    else:
        plotly_data = go.Figure()
        input_style = {'display': 'none', 'margin': '10px'}

    return plotly_data, input_style

# Lancer l'application
if __name__ == '__main__':
    app.run_server(debug=True, port=8055)

print("Les données RDF ont été converties et sauvegardées dans graph_data.json")
