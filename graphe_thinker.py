# -*- coding: utf-8 -*-
"""projet_tpe2_1.py

Application utilisant Tkinter pour visualiser les communautés d'un graphe de connaissances avec une fonctionnalité d'authentification.
"""
from rdflib import URIRef, BNode, Literal, Namespace, Graph
from rdflib.namespace import RDF
import networkx as nx
import matplotlib.pyplot as plt
import community.community_louvain as community_louvain
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, scrolledtext
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import csv
from datetime import datetime
import re
from PIL import Image, ImageTk

akg_file = "teaching_akg.ttl"

# Charger le graphe RDF
g = Graph()
G = nx.DiGraph()
akg_namespace = Namespace("http://sonfack.com/2023/12/tao/")
cao_namespace = Namespace("http://sonfack.com/2023/12/cao/")

try:
    g.parse(akg_file, format="ttl")
except Exception as e:
    messagebox.showerror("Erreur", f"Erreur lors du chargement du fichier RDF: {e}")
    exit()

# Fonctions pour manipuler le graphe
def lire_toutes_les_activites(akg: Graph, en_str=True) -> list:
    """Retourne toutes les activités d'un graphe de connaissances."""
    liste_activites = [extraire_nom_sans_identifiants(str(activite), "http://sonfack.com/2023/12/tao/") if en_str else activite for activite in akg.subjects(predicate=RDF.type, object=cao_namespace.Activity)]
    return liste_activites

def lire_noeud_akg(uri_noeud: str, akg: Graph, en_str=True) -> dict:
    """Retourne tous les éléments directement liés à un nœud du graphe."""
    infos_activite = {}
    for subj in akg.subjects(predicate=RDF.type, object=cao_namespace.Activity):
        if uri_noeud.lower() in str(subj).lower():
            uri_ref_activite = subj
            break
    else:
        return None

    for predicat_act, objet_act in akg.predicate_objects(subject=uri_ref_activite):
        pred = predicat_act
        obj = objet_act
        if en_str:
            pred = extraire_nom_sans_identifiants(str(predicat_act), "http://sonfack.com/2023/12/tao/")  # Simplifier l'affichage des prédicats
            obj = extraire_nom_sans_identifiants(str(objet_act), "http://sonfack.com/2023/12/tao/")  # Simplifier l'affichage des objets
        if pred in infos_activite:
            objets_existants = infos_activite[pred] + [obj]
            infos_activite[pred] = objets_existants
        else:
            infos_activite[pred] = [obj]
    return infos_activite

def ajouter_activite_au_graphe_nx(G, uri_activite, infos_activite):
    """Ajoute les activités et leurs relations au graphe NetworkX."""
    for pred, liste_obj in infos_activite.items():
        etiquette_pred = pred
        for obj in liste_obj:
            etiquette_obj = obj
            G.add_node(uri_activite, color='orange')
            G.add_node(etiquette_obj, color='blue')
            G.add_edge(uri_activite, etiquette_obj, label=etiquette_pred, width=2 if G.nodes[uri_activite]['color'] == 'orange' and G.nodes[etiquette_obj]['color'] == 'blue' else 3)

def visualiser_activite_3d(G):
    """Visualiser le graphe de connaissances en 3D."""
    from mpl_toolkits.mplot3d import Axes3D
    fig = plt.figure(figsize=(15, 15))  # Augmenter la taille de la figure pour qu'elle prenne toute la page
    ax = fig.add_subplot(111, projection='3d')

    pos = nx.spring_layout(G, dim=3, seed=42)  # Générer une position 3D pour chaque nœud
    for noeud, (x, y, z) in pos.items():
        ax.scatter(x, y, z, color=G.nodes[noeud]['color'], s=40)  # Ajuster la taille des points ici
        ax.text(x, y, z, noeud, fontsize=10)

    for arete in G.edges():
        x_coords, y_coords, z_coords = [], [], []
        for noeud in arete:
            x, y, z = pos[noeud]
            x_coords.append(x)
            y_coords.append(y)
            z_coords.append(z)
        ax.plot(x_coords, y_coords, z_coords, color='black')

    plt.title("Graphe de Connaissances 3D des Activités")
    plt.tight_layout()
    plt.show()

def visualiser_activite(G):
    """Visualiser le graphe de connaissances."""
    plt.figure(figsize=(6, 6))  # Réduire la taille du cercle
    pos = nx.spring_layout(G, seed=42, k=0.3)  # Ajuster la distance entre les nœuds pour 1 cm
    couleurs_noeuds = [data['color'] for _, data in G.nodes(data=True)]
    nx.draw(G, pos, with_labels=True, node_size=200, node_color=couleurs_noeuds, font_size=5, font_weight="bold", edge_color="black", width=[data.get('width', 2) for _, _, data in G.edges(data=True)])  # Diminuer la taille des nœuds et ajuster l'épaisseur des arêtes
    etiquettes_aretes = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=etiquettes_aretes, font_color='green', font_size=5)
    plt.title("Graphe de Connaissances des Activités")
    plt.legend(handles=[plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='orange', markersize=5, label='Activité'),
                        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', markersize=5, label='Ressource')],
               loc='upper right')
    plt.show()

def detecter_communautes(G):
    """Détection des communautés avec l'algorithme de Louvain."""
    partition = community_louvain.best_partition(G.to_undirected())
    return partition

def visualiser_communautes(G, partition):
    """Visualiser les communautés dans le graphe."""
    plt.figure(figsize=(6, 6))  # Réduire la taille du cercle
    pos = nx.spring_layout(G, seed=42, k=0.6)  # Ajuster la distance entre les nœuds pour une meilleure séparation (3 cm)
    couleurs_noeuds = ['orange' if partition[noeud] == partition[list(G.nodes())[0]] else 'blue' for noeud in G.nodes()]
    nx.draw(G, pos, node_color=couleurs_noeuds, with_labels=True, node_size=200, cmap=plt.cm.jet, font_size=5, font_weight="bold", edge_color="black", width=[data.get('width', 2) for _, _, data in G.edges(data=True)])  # Diminuer la taille des nœuds et ajuster l'épaisseur des arêtes
    etiquettes_aretes = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=etiquettes_aretes, font_color='red', font_size=5)
    plt.title("Communautés dans le Graphe de Connaissances des Activités")
    plt.legend(handles=[plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='orange', markersize=5, label='Activité'),
                        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', markersize=5, label='Ressource')],
               loc='upper right')
    plt.show()

# Extraction du nom sans identifiants
def extraire_nom_sans_identifiants(uri: str, namespace: str) -> str:
    """Extrait le nom de l'activité sans les identifiants de l'URI après le namespace."""
    match = re.match(f"{re.escape(namespace)}(.+?)(?:[-_].*)?$", uri)
    if match:
        nom_sans_identifiants = match.group(1).replace('-', ' ').replace('_', ' ').title()
        return nom_sans_identifiants
    return uri.split('/')[-1]  # Retourner uniquement le dernier segment sans l'URI

# Interface Tkinter
class ApplicationDetectionCommunautes:
    def __init__(self, root):
        self.root = root
        self.root.title("Application de Détection de Communautés")
        self.root.geometry("1400x800")

        # Variables pour l'authentification
        self.username = "admin"
        self.password = "password"

        self.creer_interface_authentification()

    def creer_interface_authentification(self):
        """Créer l'interface d'authentification."""
        self.root.configure(bg='#f0f8ff')  # Définir la couleur de fond

        self.frame_auth = tk.Frame(self.root, bg='#f0f8ff', padx=50, pady=50)
        self.frame_auth.pack(expand=True)

        self.label_icon = tk.Label(self.frame_auth, text="☺", font=("Helvetica", 40), bg='#f0f8ff')  # Icône de l'utilisateur
        self.label_icon.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        self.label_bienvenue = tk.Label(self.frame_auth, text="Bienvenue, veuillez vous connecter.", font=("Helvetica", 16), bg='#f0f8ff')
        self.label_bienvenue.grid(row=1, column=0, columnspan=2, pady=(0, 20))

        self.label_utilisateur = tk.Label(self.frame_auth, text="Nom d'utilisateur:", font=("Helvetica", 12), bg='#f0f8ff')
        self.label_utilisateur.grid(row=2, column=0, sticky='w', pady=5)
        self.entree_utilisateur = tk.Entry(self.frame_auth, font=("Helvetica", 12), width=30)
        self.entree_utilisateur.grid(row=2, column=1, pady=5)

        self.label_mot_de_passe = tk.Label(self.frame_auth, text="Mot de passe:", font=("Helvetica", 12), bg='#f0f8ff')
        self.label_mot_de_passe.grid(row=3, column=0, sticky='w', pady=5)
        self.entree_mot_de_passe = tk.Entry(self.frame_auth, show="*", font=("Helvetica", 12), width=30)
        self.entree_mot_de_passe.grid(row=3, column=1, pady=5)

        self.bouton_connexion = tk.Button(self.frame_auth, text="Se connecter", font=("Helvetica", 12), command=self.authentifier_utilisateur, bg='#007bff', fg='white', activebackground='#0056b3', activeforeground='white')
        self.bouton_connexion.grid(row=4, column=0, columnspan=2, pady=(20, 0))

    def authentifier_utilisateur(self):
        """Vérifier les informations d'identification de l'utilisateur."""
        if (self.entree_utilisateur.get() == self.username and self.entree_mot_de_passe.get() == self.password):
            self.creer_interface_principale()
        else:
            messagebox.showerror("Erreur d'authentification", "Nom d'utilisateur ou mot de passe incorrect.")

    def creer_interface_principale(self):
        """Créer l'interface principale de l'application après authentification."""
        for widget in self.root.winfo_children():
            widget.destroy()

        self.background_image = Image.open("C:/Users/Nael_Gaizka/Documents/projet_tpe/images.jpg")  # Chemin vers l'image téléchargée
        self.background_image = self.background_image.resize((self.root.winfo_screenwidth(), self.root.winfo_screenheight()), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(self.background_image)
        self.background_label = tk.Label(self.root, image=self.bg_photo)
        self.background_label.place(relwidth=1, relheight=1)

        self.label = ttk.Label(self.root, text="Détection de communautés sur le graphe de connaissances", font=("Helvetica", 16), background='#f0f8ff')
        self.label.pack(pady=10)

        # Ajouter une liste déroulante pour afficher les différentes tâches
        self.liste_taches = [
            "Visualiser le Graphe",
            "Visualiser une Communauté",
            "Visualiser Activités Sélectionnées",
            "Visualiser Communauté en Étoile",
            "Afficher le Journal Récapitulatif",
            "Visualiser Graphe Circulaire des Communautés",
            "Visualiser Graphe en 3D",
            "Afficher la Liste des Communautés"  # Nouvelle option ajoutée ici
        ]
        self.task_combobox = ttk.Combobox(self.root, values=self.liste_taches, state="readonly", width=80, font=("Helvetica", 12))
        self.task_combobox.set("Sélectionner une tâche")
        self.task_combobox.pack(pady=5)

        self.button_execute = ttk.Button(self.root, text="Exécuter la Tâche", command=self.execute_task)
        self.button_execute.pack(pady=5)

        self.canvas_frame = tk.Frame(self.root)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        self.canvas = None

        self.journal_text = None

    def ecrire_dans_journal(self, message):
        """Fonction pour écrire dans le fichier journal."""
        with open("journal.txt", "a") as fichier_journal:
            fichier_journal.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
            fichier_journal.flush()

    def execute_task(self):
        selected_task = self.task_combobox.get()
        self.ecrire_dans_journal(f"Exécution de la tâche: {selected_task}")

        if selected_task == "Visualiser le Graphe":
            self.visualiser_graphe()
        elif selected_task == "Visualiser une Communauté":
            self.visualiser_une_communaute()
        elif selected_task == "Visualiser Activités Sélectionnées":
            self.visualiser_activites_selectionnees()
        elif selected_task == "Visualiser Communauté en Étoile":
            self.visualiser_graphe_etoile()
        elif selected_task == "Afficher le Journal Récapitulatif":
            self.afficher_journal_recapitulatif()
        elif selected_task == "Visualiser Graphe Circulaire des Communautés":
            self.visualiser_communautes_circulaires()
        elif selected_task == "Visualiser Graphe en 3D":
            self.visualiser_graphe_3d()
        elif selected_task == "Afficher la Liste des Communautés":
            self.afficher_liste_communautes()

    def afficher_liste_communautes(self):
        """Affiche la liste des communautés sous forme de boîte de dialogue."""
        partition = detecter_communautes(G)
        texte_communautes = "Communautés:\n\n"
        communaute_dict = {}

        for noeud, id_communaute in partition.items():
            if id_communaute not in communaute_dict:
                communaute_dict[id_communaute] = []
            communaute_dict[id_communaute].append(noeud)

        for id_communaute, noeuds in communaute_dict.items():
            texte_communautes += f"Communauté {id_communaute}:\n"
            for noeud in noeuds:
                texte_communautes += f" - {noeud}\n"
                info_noeud = lire_noeud_akg(noeud, g, en_str=True)
                if info_noeud:
                    for pred, objs in info_noeud.items():
                        texte_communautes += f"   {pred}: {', '.join(objs)}\n"
            texte_communautes += "\n"

        # Afficher les informations dans une boîte de dialogue
        messagebox.showinfo("Liste des Communautés", texte_communautes)

        # Écrire dans le journal
        self.ecrire_dans_journal("Affichage de la liste des communautés détectées.")

    def visualiser_graphe(self):
        G.clear()
        activites = lire_toutes_les_activites(g, en_str=True)
        if not activites:
            messagebox.showerror("Erreur", "Aucune activité trouvée dans le graphe RDF.")
            self.ecrire_dans_journal("Erreur : Aucune activité trouvée dans le graphe RDF.")
            return
        for activite in activites:
            subj = activite.split('/')[-1]
            info_activite = lire_noeud_akg(subj, g, en_str=True)
            if info_activite:
                ajouter_activite_au_graphe_nx(G, activite, info_activite)
        visualiser_activite(G)

        # Écrire dans le journal
        self.ecrire_dans_journal("Visualisation du graphe des connaissances.")

    def visualiser_une_communaute(self):
        nom_activite = simpledialog.askstring("Entrer le nom de l'activité", "Nom de l'activité :")
        if not nom_activite:
            return
        G.clear()
        info_activite = lire_noeud_akg(nom_activite, g, en_str=True)
        if not info_activite:
            messagebox.showerror("Erreur", f"L'activité '{nom_activite}' n'a pas été trouvée dans le graphe RDF.")
            self.ecrire_dans_journal(f"Erreur : L'activité '{nom_activite}' n'a pas été trouvée dans le graphe RDF.")
            return
        ajouter_activite_au_graphe_nx(G, nom_activite, info_activite)
        visualiser_activite(G)

        # Écrire dans le journal
        self.ecrire_dans_journal(f"Visualisation de la communauté pour l'activité: {nom_activite}.")

    def visualiser_activites_selectionnees(self):
        activites = simpledialog.askstring("Sélectionner des activités", "Entrer les noms des activités séparés par des virgules :")
        if not activites:
            return
        G.clear()
        liste_activites = [activite.strip() for activite in activites.split(',')]
        for activite in liste_activites:
            info_activite = lire_noeud_akg(activite, g, en_str=True)
            if not info_activite:
                messagebox.showwarning("Attention", f"L'activité '{activite}' n'a pas été trouvée dans le graphe RDF.")
                self.ecrire_dans_journal(f"Attention : L'activité '{activite}' n'a pas été trouvée dans le graphe RDF.")
                continue
            ajouter_activite_au_graphe_nx(G, activite, info_activite)
        visualiser_activite(G)

        # Écrire dans le journal
        self.ecrire_dans_journal(f"Visualisation des activités sélectionnées: {', '.join(liste_activites)}.")

    def visualiser_graphe_etoile(self):
        type_propriete = simpledialog.askstring("Sélectionner une propriété", "Entrer le type de ressource que vous voulez détecter :")
        if not type_propriete:
            return
        G.clear()
        noeud_central = f"Centre-{type_propriete}"
        connexions_trouvees = False
        for sujet, pred, obj in g:
            nom_pred = extraire_nom_sans_identifiants(str(pred), "http://sonfack.com/2023/12/tao/")
            if type_propriete in nom_pred:
                nom_sujet = extraire_nom_sans_identifiants(str(sujet), "http://sonfack.com/2023/12/tao/")
                nom_objet = extraire_nom_sans_identifiants(str(obj), "http://sonfack.com/2023/12/tao/")

                if not connexions_trouvees:
                    G.add_node(noeud_central, color="red")
                    connexions_trouvees = True

                G.add_node(nom_sujet, color="orange")
                G.add_edge(noeud_central, nom_sujet, label=type_propriete)

                G.add_node(nom_objet, color="blue")
                G.add_edge(nom_sujet, nom_objet, label="element")

        if not connexions_trouvees:
            messagebox.showerror("Erreur", f"Aucune communauté trouvée pour la propriété '{type_propriete}' dans le graphe RDF.")
            self.ecrire_dans_journal(f"Erreur : Aucune communauté trouvée pour la propriété '{type_propriete}'.")
            return

        visualiser_activite(G)

        # Écrire dans le journal
        self.ecrire_dans_journal(f"Visualisation de la communauté en étoile pour la propriété: {type_propriete}.")

    def afficher_journal_recapitulatif(self):
        texte_recapitulatif = "Journal Récapitulatif:\n\n"
        activites = lire_toutes_les_activites(g, en_str=True)
        for activite in activites:
            info_activite = lire_noeud_akg(activite, g, en_str=True)
            if info_activite:
                texte_recapitulatif += f"Activité: {extraire_nom_sans_identifiants(activite, 'http://sonfack.com/2023/12/tao/')}\n"
                for pred, objs in info_activite.items():
                    texte_recapitulatif += f"  {pred}: {', '.join(objs)}\n"
                texte_recapitulatif += "\n"

        if self.journal_text:
            self.journal_text.pack_forget()
        self.journal_text = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=150, height=20, font=("Helvetica", 10))
        self.journal_text.insert(tk.INSERT, texte_recapitulatif)
        self.journal_text.pack(pady=10)

        # Ajouter un histogramme des activités en fonction des ressources
        compte_activites = [len(info_activite) for activite in activites if (info_activite := lire_noeud_akg(activite, g, en_str=True))]
        etiquettes_activites = [extraire_nom_sans_identifiants(activite, "http://sonfack.com/2023/12/tao/") for activite in activites]
        plt.figure(figsize=(24, 10))  # Augmenter la taille de la figure pour qu'elle prenne toute la page
        plt.bar(etiquettes_activites, compte_activites, color='skyblue')
        plt.xlabel("Activités")
        plt.ylabel("Nombre de Ressources")
        plt.xticks(rotation=90)
        plt.yticks(np.arange(0, 11, 1))  # Ajuster l'échelle pour commencer à 0 et aller jusqu'à 10
        plt.title("Histogramme des Activités en Fonction des Ressources")
        plt.tight_layout()
        plt.show()

        # Écrire dans le journal
        self.ecrire_dans_journal("Affichage du journal récapitulatif des activités et ressources.")

    def visualiser_communautes_circulaires(self):
        partition = detecter_communautes(G)
        communaute_dict = {}

        for noeud, id_communaute in partition.items():
            if id_communaute not in communaute_dict:
                communaute_dict[id_communaute] = []
            communaute_dict[id_communaute].append(noeud)

        # Calculer le nombre d'activités par communauté
        labels = []
        sizes = []
        for id_communaute, noeuds in communaute_dict.items():
            labels.append(extraire_nom_sans_identifiants(noeuds[0], "http://sonfack.com/2023/12/tao/"))
            sizes.append(len(noeuds))

        # Visualiser le diagramme circulaire
        fig, ax = plt.subplots(figsize=(10, 10))
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
        for text in texts:
            text.set_fontsize(10)  # Ajuster la taille des labels dans le diagramme
        plt.axis('equal')  # Assurer que le diagramme est un cercle
        plt.title("Répartition des Activités par Communauté")
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), fontsize=10)  # Positionner la légende en dessous du cercle

        def onclick(event):
            wedge_index = None
            for i, wedge in enumerate(wedges):
                if wedge.contains_point([event.x, event.y]):
                    wedge_index = i
                    break
            if wedge_index is not None:
                activite = labels[wedge_index]
                info_activite = lire_noeud_akg(activite, g, en_str=True)
                if info_activite:
                    texte_info = f"Informations sur l'activité: {activite}\n\n"
                    for pred, objs in info_activite.items():
                        texte_info += f"{pred}: {', '.join(objs)}\n"
                    messagebox.showinfo("Informations sur l'Activité", texte_info)

        fig.canvas.mpl_connect('button_press_event', onclick)
        plt.tight_layout()
        plt.show()

        # Écrire dans le journal
        self.ecrire_dans_journal("Visualisation des communautés avec un graphe circulaire.")

    def visualiser_graphe_3d(self):
        G.clear()
        activites = lire_toutes_les_activites(g, en_str=True)
        if not activites:
            messagebox.showerror("Erreur", "Aucune activité trouvée dans le graphe RDF.")
            self.ecrire_dans_journal("Erreur : Aucune activité trouvée dans le graphe RDF.")
            return
        for activite in activites:
            subj = activite.split('/')[-1]
            info_activite = lire_noeud_akg(subj, g, en_str=True)
            if info_activite:
                ajouter_activite_au_graphe_nx(G, activite, info_activite)
        visualiser_activite_3d(G)

        # Écrire dans le journal
        self.ecrire_dans_journal("Visualisation du graphe des connaissances en 3D.")

# Lancer l'application
if __name__ == "__main__":
    root = tk.Tk()
    app = ApplicationDetectionCommunautes(root)
    root.mainloop()
