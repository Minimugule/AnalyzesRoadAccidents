import pandas as pd
import numpy as np
from bokeh.io import output_notebook
from bokeh.plotting import figure, show, ColumnDataSource, output_file
from bokeh.models import Dropdown, CustomJS, BasicTicker, PrintfTickFormatter, TabPanel, Tabs, Div, Select, HoverTool, FactorRange, Switch
from bokeh.layouts import row, column
from datetime import datetime
from bokeh.palettes import Category20c, Reds8
from bokeh.transform import cumsum, linear_cmap
from math import pi
from shapely.geometry import Point, Polygon

##### Importation des données #####
accident = pd.read_csv("accidents_corporels.csv", sep = ";", decimal = ".")
# accident.head()

# Séparer la date en annee et mois : 
accident[['annee', 'mois']] = accident['date'].str.split('-', expand=True)[[0, 1]]

# Séparer la colonne heure en heure et minute
accident[["heure", "minute"]] = accident.heure.str.split(":", expand = True)


# Ordonner par année croissante :
accident = accident.sort_values(by = 'date')

# Modification des classes d'accident : 
def map_classes(classe_specifique):
    if classe_specifique in ['VL', 'Véhicule de tourisme (VT)', 'Voiturette']:
        return 'Voiture'
    elif classe_specifique in ['cyclomoteur', 'Scooter <= 50 cm3', 'motocyclette > 125 cm3', 'motocyclette >50<=125 cm3', 'Scooter  > 50 <= 125 cm3', 'Scooter > 125 cm3', 'Moto ou sidecar > 125 cm3', 'Moto ou sidecar  > 50 <= 125 cm3', 'Cyclomoteur <=50 cm3', '3 RM > 125 cm3', '3 RM  > 50 <= 125 cm3']:
        return 'Deux-roues motorisé'
    elif classe_specifique in ['Autobus', 'Autocar']:
        return 'Transport en commun'
    elif classe_specifique in ['VU seul 1,5T < PTAC <=3,5T', 'PL seul PTAC > 7,5T', 'PL + remorque(s)', 'PL seul 3,5 < PTAC <=7,5t', 'Tracteur routier + semi-remorque', 'tracteur routier seul', 'PL > 3,5T + remorque']:
        return 'Poids lourd'
    elif classe_specifique in ['Bicyclette', 'Vélo par assistance électrique']:
        return 'Vélo'
    elif classe_specifique in ['Tracteur agricole', 'Autre engin de déplacement personnel (EDP) sans moteur', 'Indéterminable', 'Autre véhicule']:
        return 'Autre'
    elif classe_specifique in ['quad léger <=50 cm3', 'Nouvel engin de déplacement personnel (EDP) à moteur', 'voiturette / quad à moteur carrossé', 'quad lourd > 50 cm3']:
        return 'Engin personnel motorisé'
    elif classe_specifique == 'Engin spécial':
        return 'Engin spécial'
    else:
        return 'Non spécifié'

# Appliquer la fonction de mapping pour créer une nouvelle colonne 'classe_generale'
for i in range(1, 7):
    col_name = f'classe_vehicule{i}'
    veh_col_name = f'vehicule{i}'
    accident[col_name] = accident[veh_col_name].apply(map_classes)



# Nom des colonnes à sélectionner
colonnes_selectionnees = accident.filter(regex=r'^classe_vehicule', axis=1).columns.tolist()
type_vehicule = ['Deux-roues motorisé', 'Non spécifié', 'Voiture', 'Vélo', 'Poids lourd', 'Transport en commun', 'Engin personnel motorisé', 'Autre', 'Engin spécial']
# Calculer le nombre total d'accidents par type de vehicule
d_accidents = dict()
for col in colonnes_selectionnees:
    for vehicule in accident[col]:
        d_accidents[vehicule] = d_accidents.get(vehicule, 0) + 1

# On supprime les non specifies du dictionnaire car trop nombreux et mauvaise visualisation des resultats par la suite
d_accidents.pop('Non spécifié')

# Convertir le dictionnaire en un DataFrame
data = pd.Series(d_accidents).reset_index(name='nb_accident').rename(columns={'index': 'type_vehicule'})


#############################################################################################################################################
################################################################# PIE CHART #################################################################
#############################################################################################################################################

#####################
##### PIE CHART #####
#####################

# Calculer les angles et les couleurs
data['angle'] = data['nb_accident'] / data['nb_accident'].sum() * 2 * pi
data['color'] = Reds8

# Créer un graphique en secteurs (pie chart)
p_pie = figure(title = "Accidents en fonction du véhicule", 
               x_range=(-0.5, 1.0),
               height = 500, 
               toolbar_location = None,
               tools = "hover", 
               tooltips = "@type_vehicule: @nb_accident")

# Dessiner les secteurs
p_pie.wedge(x = 0, y = 1, radius = 0.4,
        start_angle = cumsum('angle', include_zero=True), end_angle = cumsum('angle'),
        line_color = "white", fill_color = 'color', legend_field = 'type_vehicule', source = data)

# Paramètres du graphique
p_pie.axis.axis_label = None
p_pie.axis.visible = False
p_pie.grid.grid_line_color = None

####################
##### BARPLOT #####
###################

# Créer un graphique en barplot
p_barre = figure(title = "Accidents en fonction du véhicule", 
            x_range = data['type_vehicule'], y_axis_label = 'Nombre d\'accidents', 
            height = 500,
            toolbar_location = None, 
            tools = "")

# Ajouter les barres
p_barre.vbar(x = 'type_vehicule', top = 'nb_accident', width = 0.9, color = '#922B21', source=data)

#Création de l'outil
outilsurvol = HoverTool(tooltips = [('Véhicule','@type_vehicule'), ( 'Nombre', '@nb_accident' )])
p_barre.add_tools(outilsurvol)

# Paramètres du graphique
p_barre.xgrid.grid_line_color = None
p_barre.y_range.start = 0
p_barre.y_range.end = 10000

# Modifier l'orientation des noms sur l'axe des x
p_barre.xaxis.major_label_orientation = 45  # Angle de 45 degrés

################################################
##### Pouvoir choisir le type de graphique #####
################################################

# Masquer le barplot par défaut
p_barre.visible = False

# Créer un Select pour choisir entre pie chart et barplot
select = Select(title="Choisir le type de graphique", options=["Pie Chart", "Barplot"], value="Pie Chart")

# Callback JavaScript pour changer le type de graphique en fonction de la sélection
callback = CustomJS(args=dict(p_pie=p_pie, p_barre=p_barre), code="""
    if (cb_obj.value === "Pie Chart") {
        p_pie.visible = true;
        p_barre.visible = false;
    } else {
        p_pie.visible = false;
        p_barre.visible = true;
    }
""")

# Associer la fonction JavaScript à la sélection du Select
select.js_on_change('value', callback)

# Afficher les graphiques et le Select dans une mise en page
pie_barre = column(select, p_pie, p_barre)

#### Commentaire

## Commentaire graphique croisières ---
text_p_barre = Div(text="""<h1> Analyse </h1> 
        <p> Les voitures sont le type de véhicule le plus impliqué dans les accidents à Rennes, avec une partition de 60% des accuidents globaux.
            Elles sont ensuite suivies des deux-roues motorisés et des vélos qui sont impliqués dans 20% des accidents.
            Les autres types de véhicules sont beaucoup moins impliqués dans les accidents.<br><br>
           
            En revanche, le graphique ne montre pas la gravité des accidents ni les facteurs qui y contribuent.
            Il est possible que les accidents impliquant des deux-roues motorisés soient plus graves que les accidents impliquant des voitures.
            Ou que les véhicules soient plus susceptibles d'être impliqués dans des accidents en raison de facteurs tels
            que la vitesse, la distraction au volant ou l'état des routes.
        </p>""", styles={'text-align':'justify','color':'black','background-color':'lavender','padding':'15px','border-radius':'10px', 'max-width':'500px'})



##########################################################################################################################################
################################################################ HEAT MAP ################################################################
##########################################################################################################################################
# Regroupez les données par 'jsem' et 'heure' et comptez le nombre d'accidents
heatmap_data = accident.groupby(['jsem', 'heure']).size().reset_index(name='nb')

# Convertir en ColumnDataSource
heatmap_data_cvs = ColumnDataSource(heatmap_data)

# Définir l'ordre des jours de la semaine selon votre préférence
ordre_jours_semaine = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']

# Utiliser FactorRange pour spécifier l'ordre des jours de la semaine sur l'axe Y
x_range = FactorRange(factors=ordre_jours_semaine)

# Créer une palette de couleurs
colors = ["#75968f", "#a5bab7", "#c9d9d3", "#e2e2e2", "#dfccce", "#ddb7b1", "#cc7878", "#933b41", "#550b1d"]

# Liste des outils
TOOLS = "hover,save,pan,box_zoom,reset,wheel_zoom"

# Créer un graphique de type heatmap
heat_map = figure(title="Accident de la route par jour de la semaine et heure",
        x_range = x_range, 
        y_range = list(reversed(np.unique(heatmap_data.heure))),
        x_axis_location="above", width=600, height=600,
        tools=TOOLS, toolbar_location='below',
        tooltips=[('Heure/Jour', '@heure @jsem'), ('Nombre', '@nb')])

# Supprimer les axes
heat_map.grid.grid_line_color = None
heat_map.axis.axis_line_color = None
heat_map.axis.major_tick_line_color = None
heat_map.axis.major_label_text_font_size = "7px"
heat_map.axis.major_label_standoff = 0
heat_map.xaxis.major_label_orientation = 0

# Réalisation de la heatmap avec les axes inversés
r = heat_map.rect(x="jsem", y="heure", width=1, height=1, source=heatmap_data_cvs,
        fill_color=linear_cmap("nb", colors, low=heatmap_data.nb.min(), high=heatmap_data.nb.max()),
        line_color=None)

# Ajouter une légende
heat_map.add_layout(r.construct_color_bar(
    major_label_text_font_size="7px",
    ticker=BasicTicker(desired_num_ticks=len(colors)),
    formatter=PrintfTickFormatter(format="%d"),
    label_standoff=6,
    border_line_color=None,
    padding=5,), 'right')
 

#### Commentaire
text_t_map = Div(text=""" <h1> Analyse du heat map </h1> 
        <p> Le heat map présenté met en lumière une tendance claire concernant les accidents de la route : les journées les plus accidentogènes sont les vendredis,
                  avec un pic notable à 8h du matin. Cette observation s'accompagne d'une corrélation avec les heures de pointe, indiquant une concentration des
                  accidents durant les trajets domicile-travail. En revanche, les week-ends sont globalement moins marqués par les accidents, avec une absence totale
                  d'incidents sur certains créneaux horaires du dimanche. <br><br>
                 
                 Ces informations précieuses pourraient servir à cibler des campagnes de sensibilisation et des mesures préventives en vue de réduire le nombre d'accidents,
                  en particulier durant les heures et les jours identifiés comme les plus à risque.

Ces informations précieuses pourraient servir à cibler des campagnes de sensibilisation et des mesures préventives en vue de réduire le nombre d'accidents, en particulier durant les heures et les jours identifiés comme les plus à risque.
        </p>""",styles={'text-align':'justify','color':'black','background-color':'lavender','padding':'15px','border-radius':'10px', 'max-width':'600px'})



########################################################################################################################
############################################### CARTE ##################################################################
########################################################################################################################

# Converts decimal longitude/latitude to Web Mercator format
def coor_wgs84_to_web_mercator(lon, lat):
    k = 6378137
    x = lon * (k * np.pi/180.0)
    y = np.log(np.tan((90 + lat) * np.pi/360.0)) * k
    return (x,y)

x_rennes,y_rennes = coor_wgs84_to_web_mercator(-1.6742900,48.1119800)


# Séparer la colonne Geo Point en longitude et latitude
accident[["latitude", "longitude"]] = accident["Geo Point"].str.split(",", expand = True)

# Supprimer les espaces éventuels dans les colonnes de latitude et de longitude
accident["latitude"] = accident["latitude"].str.strip()
accident["longitude"] = accident["longitude"].str.strip()

# Créer un df pour les vélo
data_accident_velo = accident[accident.velo == "Oui"]

# Créer un df pour les piétons
data_accident_pieton = accident[accident.pieton == "Oui"]

################################
##### Carte pour les vélos #####
################################

# Appliquer la fonction de conversion à toutes les coordonnées de latitude et de longitude
data_accident_velo['x'], data_accident_velo['y'] = coor_wgs84_to_web_mercator(data_accident_velo['longitude'].astype(float), data_accident_velo['latitude'].astype(float))

# Créer une source de données pour les points d'accident
source_velo = ColumnDataSource(data=dict(
    x = data_accident_velo['x'],
    y = data_accident_velo['y'],
    annee = data_accident_velo['annee'],
))

# Création de la figure avec axes géographiques
p_carte_velo = figure(title = "Cartographie des accidents de vélo à Rennes", 
           x_axis_type = "mercator",
           y_axis_type = "mercator",
           x_range=(x_rennes - 10000, x_rennes + 10000),
           y_range=(y_rennes - 10000, y_rennes + 10000),
           active_scroll = "wheel_zoom")

#Ajout d'un arrière plan de carte
p_carte_velo.add_tile("CartoDB Positron")

# Ajouter les points d'accident à la carte
p_carte_velo.circle(x='x', y='y', size=5, color='#922B21', alpha=1, source=source_velo)

p_carte_velo.visible = True

##################################
##### Carte pour les piétons #####
##################################

# Appliquer la fonction de conversion à toutes les coordonnées de latitude et de longitude
data_accident_pieton['x'], data_accident_pieton['y'] = coor_wgs84_to_web_mercator(data_accident_pieton['longitude'].astype(float), data_accident_pieton['latitude'].astype(float))

# Créer une source de données pour les points d'accident
source_pieton = ColumnDataSource(data=dict(
    x = data_accident_pieton['x'],
    y = data_accident_pieton['y'],
    annee = data_accident_pieton['annee'],
))

# Création de la figure avec axes géographiques
p_carte_pieton = figure(title = "Cartographie des accidents de piéton à Rennes", 
           x_axis_type = "mercator",
           y_axis_type = "mercator",
           x_range=(x_rennes - 10000, x_rennes + 10000),
           y_range=(y_rennes - 10000, y_rennes + 10000),
           active_scroll = "wheel_zoom")

#Ajout d'un arrière plan de carte
p_carte_pieton.add_tile("CartoDB Positron")

# Ajouter les points d'accident à la carte
p_carte_pieton.circle(x='x', y='y', size=5, color='#922B21', alpha=1, source=source_pieton)

p_carte_pieton.visible = False

#############################################
##### Pouvoir switch entre les 2 cartes #####
#############################################

# Texte d'information
info_text = Div(text="<b>Pouvoir switch entre les cartes des vélos et des piétons</b>")

# Création du widget Switch
switch = Switch(active=True)

# Définition de la fonction de rappel JavaScript pour basculer entre les cartes
callback = CustomJS(args=dict(p_carte_velo=p_carte_velo, p_carte_pieton=p_carte_pieton), code="""
    if (this.active) {
        p_carte_velo.visible = true;
        p_carte_pieton.visible = false;
    } else {
        p_carte_velo.visible = false;
        p_carte_pieton.visible = true;
    }
""")
switch.js_on_change("active", callback)

##### Menu pour choisir l'année #####

# Labels pour les années
LABELS = ["Total", "2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022"]

# Création du menu déroulant pour choisir l'année
annee_menu = Dropdown(label="Choix de l'année", menu=[(str(year), str(year)) for year in LABELS])

# Définition de la fonction de rappel JavaScript pour sélectionner l'année
callback_annee = CustomJS(args=dict(source_velo=source_velo, source_pieton=source_pieton, p_carte_velo=p_carte_velo, p_carte_pieton=p_carte_pieton, annee_menu=annee_menu), code="""
    const selected_year = cb_obj.item;
    const data_velo = source_velo.data;
    const data_pieton = source_pieton.data;
                          
    // Filtrer les données pour l'année sélectionnée
    const indices_velo = [];
    const indices_pieton = [];
    
    // Vérifier si "Total" est sélectionné
    if (selected_year === "Total") {
        for (let i = 0; i < data_velo['annee'].length; i++) {
            indices_velo.push(i);
        }
        
        for (let i = 0; i < data_pieton['annee'].length; i++) {
            indices_pieton.push(i);
        }
    } else {
        for (let i = 0; i < data_velo['annee'].length; i++) {
            if (data_velo['annee'][i] === selected_year) {
                indices_velo.push(i);
            }
        }
        
        for (let i = 0; i < data_pieton['annee'].length; i++) {
            if (data_pieton['annee'][i] === selected_year) {
                indices_pieton.push(i);
            }
        }
    }

    // Mettre à jour les sources de données pour les points d'accident
    source_velo.selected.indices = indices_velo;
    source_pieton.selected.indices = indices_pieton;
    
    // Mettre à jour les sources de données
    source_velo.change.emit();
    source_pieton.change.emit();

    // Mettre à jour le titre de la carte
    if (selected_year === "Total") {
        p_carte_velo.title.text = "Cartographie des accidents de vélo à Rennes (Total)";
        p_carte_pieton.title.text = "Cartographie des accidents de piéton à Rennes (Total)";
    } else {
        p_carte_velo.title.text = "Cartographie des accidents de vélo à Rennes en " + selected_year;
        p_carte_pieton.title.text = "Cartographie des accidents de piéton à Rennes en " + selected_year;
    }
""")



# Liaison du callback JavaScript à l'événement de sélection d'année dans le menu déroulant
annee_menu.js_on_event('menu_item_click', callback_annee)

# Affichage de la mise en page
cartes = column(row(switch, info_text), row(p_carte_velo, p_carte_pieton, annee_menu))


#### Commentaire
text_carte = Div(text=""" <h1> Analyse cartographique </h1> 
        <p> L'analyse de la carte des accidents de la route à Rennes, complétée par une étude des données statistiques, permet d'identifier plusieurs facteurs contribuant
                  à la concentration d'accidents dans certaines zones :
            <br>
                 <ul>
                 <li> Sur la rocade
                    <ul>
                        <li> Vitesse excessive : La vitesse élevée combinée à un sentiment de sécurité trompeur incite au dépassement des limitations et augmente les risques d'accidents graves.</li>
                        <li> Fatigue au volant : La monotonie des trajets et la longueur des parcours favorisent la fatigue, diminuant les réflexes et la vigilance.</li>
                        <li> Trafic dense : Le trafic congestionné génère du stress et incite aux comportements à risque (queues de poisson, dépassements dangereux).</li>
                    </ul>
                </li>
                <li> En centre-ville
                    <ul>
                        <li> Mixité des usages : La cohabitation de piétons, cyclistes, voitures et transports en commun crée des interactions complexes et des points de conflit potentiels.</li>
                        <li> Réseau routier complexe : La présence d'un réseau ancien, peu lisible, avec de nombreuses intersections et une signalisation parfois confuse, augmente les risques d'accidents.</li>
                        <li> Manque de visibilité : Des éléments urbains (bâtiments, végétation) peuvent limiter la visibilité des piétons et cyclistes, augmentant les risques d'accidents.</li>
                
        </p>""",styles={'text-align':'justify','color':'black','background-color':'lavender','padding':'15px','border-radius':'10px', 'max-width':'750px'})



#################################################################################################################################################
################################################################### EVOLUTION ###################################################################
#################################################################################################################################################
# Ajout d'une colonne 'id' :
accident["id"] = range(len(accident))

# Passer en ColumnDataSource :
accident_cds = ColumnDataSource(accident)

# Agréger les données par année et compter le nombre d'occurrences de chaque colonne pour chaque année
accidents_par_annee = accident.groupby('annee').agg({'id': 'count', 'ntu': 'sum', 'nbh': 'sum', 'nbnh': 'sum'}).reset_index()

# Utiliser cette nouvelle DataFrame comme source de données pour y
donnees_ligne = ColumnDataSource({'x': accidents_par_annee['annee'],
                                  'y': accidents_par_annee['id'],
                                  'Tué': accidents_par_annee['ntu'],
                                  'Blessés hospitalisés': accidents_par_annee['nbh'],
                                  'Blessés': accidents_par_annee['nbnh'], 
                                  'Nombre d\'accidents': accidents_par_annee['id']})

# Evolution du nombre d'accident dans Rennes (menu pour sélectionner nbtu, nbh, nbnh)
p_ligne = figure(title="Evolution des accidents à Rennes au cours du temps", x_axis_label = 'Année', y_axis_label = 'Nombre')
ligne_accidents = p_ligne.line(x = 'x', y = 'y', source=donnees_ligne, line_color = '#922B21', line_width = 3)

# Ajouter un survol pour afficher les valeurs
outilsurvol = HoverTool(tooltips = [( 'Année', '@x'), ( 'Nombre', '@y' )])
p_ligne.add_tools(outilsurvol)

# Ajouter un menu déroulant pour choisir l'ordonnée
menu = Dropdown(label = "Choix des ordonnées", menu = [('Nombre d\'accidents', 'Nombre d\'accidents'),
                                                       ('Tué', 'Tué'),
                                                       ('Blessés hospitalisés', 'Blessés hospitalisés'),
                                                       ('Blessés', 'Blessés')])

callback = CustomJS(args = dict(p = p_ligne, source = donnees_ligne), code = """
    const data = source.data;
    const val = cb_obj.item;
    const y = data['y'];
    const ynew = data[val];
    const graph_title = val + " à Rennes au cours du temps";
    for (let i = 0; i < y.length; i++) {
        y[i] = ynew[i];
    }
    source.change.emit();
    p.title.text = graph_title;
""")

menu.js_on_event('menu_item_click', callback)

evolution = row(p_ligne, menu)

#### Commentaire
text_evolution = Div(text=""" <h1> Analyse de l'évolution </h1> 
        <p> Analyse des graphiques d'accidents à Rennes

        Les quatre graphiques présentés illustrent l'évolution des accidents de la route à Rennes sur une période de 10 ans (2014-2023).
        <br>
        <ul>
            <li> <b> Nombre d'accidents </b> : on peut voir sur ce graphique qu'il y a un pique du nombre d'accidents en 2016 à plus de 600 accidents. Par la suite le nombre d'accidents diminue pour atteindre un minimum en 2020 à un peu plus de 400 accidents. </li>
                     
            <li> <b> Tués </b> : ce graphique met en évidence un pique en 2016 avec 16 personnes mortes du à des accidents routiers cette année, ce pique est pourtant précédé du plus petit nombre de mort, 2 tués, en 2015.</li>

            <li> <b> Blessés hospitalisés </b> : Le nombre d'accidents à Rennes est en baisse sur 10 ans, diminuant de 25%. On observe cependant des variations d'une année à l'autre. La baisse la plus forte a eu lieu entre 2020 et 2022. Tandis que le plus haut pique a été enregistré en 2017, avec 152 personnes bléssées</li>
                     
            <li> <b> Blessés </b> : ce graphique indique le nombre de blessés au court du temps. On constate que après 2016 où le pique de blessés a été de 630, une diminution se laisse entrevoir. Pour atteindre son plus bas en 2020, et par la suite remonter subitement.</li>
        </ul>
                     
        <br>
        <b> Conclusion</b>
                     
        <br>
        L'analyse de ces graphiques permet de dresser un constat global de la situation des accidents de la route à Rennes. 
        Si la tendance générale est à la baisse du à la pandémie de COVID-19, des points d'attention subsistent, notamment les accidents corporels graves et mortels.
        Des actions ciblées de prévention et d'aménagement pourraient être mises en œuvre pour réduire encore le nombre d'accidents et améliorer la sécurité routière à Rennes.


        </p>""",styles={'text-align':'justify','color':'black','background-color':'lavender','padding':'15px','border-radius':'10px', 'max-width':'700px'})



#############################################################################################################################################
################################################################# INTERFACE #################################################################
#############################################################################################################################################

tab1 = TabPanel(child=row(text_p_barre, column(pie_barre)), title="Nombre d'accidents en fonction du type de véhicule")
tab2 = TabPanel(child=row(text_t_map, column(heat_map)), title="Accident de la route par jour et heure de la semaine")
tab3 = TabPanel(child=row(cartes, column(text_carte)), title="Cartographie des accidents")
tab4 = TabPanel(child=row(evolution, column(text_evolution)), title="Evolution des accidents")
tabs_graphique = Tabs(tabs = [tab1, tab4, tab2, tab3])





#################################################################################################################################################
################################################################### AFFICHAGE ###################################################################
#################################################################################################################################################
text_presentation = Div(text=""" <h1> Analyse des accidents dans la ville de Rennes </h1>  

        <div style="display:flex; align-items:center;">
            <p> 
            Notre projet s'est concentré sur l'analyse des données d'accidents routiers survenus à Rennes entre 2012 et 2022. 
            Nous avons examiné l'évolution des incidents impliquant des blessés, des décès, etc., ainsi que leur répartition géographique à l'aide
            d'une carte des lieux d'accidents. De plus, nous avons étudié la répartition des accidents selon les types de véhicules impliqués, ainsi
            que les horaires et les jours où les accidents sont les plus fréquents. 
            Ces analyses fournissent un aperçu pour informer les politiques de sécurité routière et les efforts de prévention des
            accidents dans la région de Rennes.</p>
            
            <img src="Projet/accident.jpeg" alt="photo_accident" style="width:400px; height:auto; margin-left:20px;">
        </div>
        """,styles={'text-align':'justify','color':'black','background-color':'lavender','padding':'0px','border-radius':'10px', 'max-width':'1500px'})





output_file("Projet_Visualisation_Accidents_Rennes.html")
show(column(row(text_presentation),row(tabs_graphique)))




