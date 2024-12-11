from dash import Dash, html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import pandas as pd
from rdflib import Graph

# Charger les données RDF à partir du fichier .ttl
rdf_file_path = "C:/Users/Nael_Gaizka/Documents/projet_tpe/teaching_akg.ttl"
g = Graph()
g.parse(rdf_file_path, format="turtle")

# Extraire les données pertinentes du graphe RDF
data_activities = []
data_teachers = []

# Extraire les activités et leurs descriptions
for subj, pred, obj in g.triples((None, None, None)):
    if str(pred).endswith("hasName"):
        activity_name = str(obj)
        data_activities.append({"activity": str(subj), "name": activity_name})
    elif str(pred).endswith("isCarriedOutBy"):
        data_teachers.append({"activity": str(subj), "teacher": str(obj)})

# Convertir les données en DataFrame pour faciliter la manipulation
df_activities = pd.DataFrame(data_activities)
df_teachers = pd.DataFrame(data_teachers)

# Fusionner les DataFrames pour obtenir les informations complètes sur les activités et leurs enseignants
df = pd.merge(df_activities, df_teachers, on="activity", how="left")

# Initialiser l'application Dash
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Mise en page de l'application Dash
app.layout = dbc.Container(
    [
        # En-tête
        dbc.Row(
            dbc.Col(html.H1("Tableau de Bord des Activités d'Enseignement", className="text-center mt-4 mb-4"),
                    width=12)
        ),

        # Statistiques rapides
        dbc.Row(
            [
                dbc.Col(dbc.Card(
                    [
                        dbc.CardHeader("Nombre Total d'Activités"),
                        dbc.CardBody(html.H4(f"{len(df_activities)}", className="card-title")),
                    ], color="info", inverse=True), width=4
                ),
                dbc.Col(dbc.Card(
                    [
                        dbc.CardHeader("Nombre Total d'Enseignants"),
                        dbc.CardBody(html.H4(f"{df_teachers['teacher'].nunique()}", className="card-title")),
                    ], color="success", inverse=True), width=4
                ),
                dbc.Col(dbc.Card(
                    [
                        dbc.CardHeader("Nombre Total de Salles"),
                        dbc.CardBody(html.H4("Non déterminé", className="card-title")),
                    ], color="warning", inverse=True), width=4
                ),
            ],
            className="mb-4",
        ),

        # Graphique récapitulatif des activités par enseignant
        dbc.Row(
            dbc.Col(
                dcc.Graph(
                    id='activities-graph',
                    figure={
                        'data': [
                            go.Bar(
                                x=df['teacher'].value_counts().index,
                                y=df['teacher'].value_counts().values,
                                name='Nombre d\'activités par enseignant'
                            )
                        ],
                        'layout': go.Layout(
                            title='Nombre d\'activités par enseignant',
                            xaxis={'title': 'Enseignant'},
                            yaxis={'title': 'Nombre d\'Activités'},
                        )
                    }
                ), width=12
            )
        ),

        # Liste des activités
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H4("Liste des Activités d'Enseignement", className="card-title"),
                            html.Ul([html.Li(f"{row['name']} - Enseignant: {row['teacher'] if row['teacher'] else 'Non attribué'}") for index, row in df.iterrows()])
                        ]
                    )
                ), width=12
            ),
            className="mt-4"
        )
    ],
    fluid=True,
)

# Exécuter l'application
if __name__ == "__main__":
    app.run_server(debug=True)
