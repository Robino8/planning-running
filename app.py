calendar_mod = __import__("calendar")
from datetime import datetime
import pandas as pd
import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="Mon Planning Running", page_icon="🏃‍♂️", layout="wide"
)

st.title("🏃‍♂️ Mon Planning d'Entraînement")

# --- INITIALISATION DE LA MÉMOIRE ---
if "annee" not in st.session_state:
  st.session_state.annee = datetime.now().year
if "mois" not in st.session_state:
  st.session_state.mois = datetime.now().month
if "seances" not in st.session_state:
  st.session_state.seances = {}
if "jour_selectionne" not in st.session_state:
  st.session_state.jour_selectionne = 1
if "mode_edition" not in st.session_state:
  st.session_state.mode_edition = False

mois_noms = {
    1: "Janvier",
    2: "Février",
    3: "Mars",
    4: "Avril",
    5: "Mai",
    6: "Juin",
    7: "Juillet",
    8: "Août",
    9: "Septembre",
    10: "Octobre",
    11: "Novembre",
    12: "Décembre",
}

# Dictionnaire des couleurs pastel par type de séance
couleurs_pastel = {
    "Footing": "#E1F5FE",  # Bleu clair
    "Sortie longue": "#FFE0B2",  # Orange clair
    "VMA": "#F3E5F5",  # Violet clair
    "Seuil": "#E8F5E9",  # Vert clair
    "Course": "#FFEBEE",  # Rouge clair
    "Repos": "#F5F5F5",  # Gris clair
}


# --- FONCTIONS DE NAVIGATION ---
def mois_precedent():
  if st.session_state.mois == 1:
    st.session_state.mois = 12
    st.session_state.annee -= 1
  else:
    st.session_state.mois -= 1
  st.session_state.jour_selectionne = 1
  st.session_state.mode_edition = False


def mois_suivant():
  if st.session_state.mois == 12:
    st.session_state.mois = 1
    st.session_state.annee += 1
  else:
    st.session_state.mois += 1
  st.session_state.jour_selectionne = 1
  st.session_state.mode_edition = False


# --- BARRE LATÉRALE (NAVIGATION) ---
st.sidebar.header("Navigation")
col1, col2 = st.sidebar.columns(2)
with col1:
  if st.button("◀ Précéd", use_container_width=True):
    mois_precedent()
    st.rerun()
with col2:
  if st.button("Suivant ▶", use_container_width=True):
    mois_suivant()
    st.rerun()

st.sidebar.markdown("---")
choix_mois_nom = st.sidebar.selectbox(
    "Aller au mois",
    list(mois_noms.values()),
    index=st.session_state.mois - 1,
)
st.session_state.mois = [
    k for k, v in mois_noms.items() if v == choix_mois_nom
][0]
st.session_state.annee = st.sidebar.number_input(
    "Année",
    min_value=2020,
    max_value=2030,
    value=st.session_state.annee,
    step=1,
)


# --- AFFICHAGE DU CALENDRIER INTERACTIF ---
mois_nom_courant = mois_noms[st.session_state.mois]
st.subheader(f"Planning de {mois_nom_courant} {st.session_state.annee}")
st.info(
    "💡 Clique sur un jour ci-dessous pour voir ou modifier sa séance. Les"
    " couleurs indiquent le type de séance."
)

cal = calendar_mod.Calendar(firstweekday=0)  # Lundi = 0
mois_cal = cal.monthdayscalendar(st.session_state.annee, st.session_state.mois)

jours_semaine = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

# Affichage des en-têtes des jours de la semaine
cols_entetes = st.columns(7)
for i, j_nom in enumerate(jours_semaine):
  cols_entetes[i].markdown(f"**{j_nom}**")

# Affichage des semaines
for semaine in mois_cal:
  cols_semaine = st.columns(7)
  for i, jour in enumerate(semaine):
    with cols_semaine[i]:
      if jour == 0:
        st.markdown("")
      else:
        cle = (st.session_state.annee, st.session_state.mois, jour)

        # Détermination du texte et de la couleur du bouton
        if cle in st.session_state.seances:
          s_type = st.session_state.seances[cle]["type"]
          icone = (
              "🏃"
              if s_type == "Footing"
              else (
                  "🔥"
                  if s_type == "Sortie longue"
                  else (
                      "⚡"
                      if s_type == "VMA"
                      else "⏱️" if s_type == "Seuil" else "🏁" if s_type == "Course" else "🛋️"
                  )
              )
          )
          if s_type == "Course" and st.session_state.seances[cle]["details"].get(
              "nom_course"
          ):
            nom_c = st.session_state.seances[cle]["details"]["nom_course"]
            label_btn = f"J{jour} : {nom_c}"
          else:
            label_btn = f"J{jour} : {s_type}"

          bg_color = couleurs_pastel.get(s_type, "#FFFFFF")
        else:
          label_btn = f"J{jour} (-)"
          bg_color = "#FFFFFF"

        # Application propre de la couleur via un bloc HTML stylisé englobant le bouton
        st.markdown(
            f"""
            <div style="background-color: {bg_color}; padding: 4px; border-radius: 6px; border: 1px solid #ddd; text-align: center; margin-bottom: -15px;">
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(label_btn, key=f"btn_j_{jour}", use_container_width=True):
          st.session_state.jour_selectionne = jour
          st.session_state.mode_edition = False
          st.rerun()

# --- LÉGENDE DES COULEURS ---
st.markdown("---")
cols_leg = st.columns(6)
idx = 0
for s_type, col in couleurs_pastel.items():
  cols_leg[idx].markdown(
      f"<div style='background-color: {col}; padding: 5px; border-radius: 4px;"
      f" text-align: center; border: 1px solid #ccc; font-weight: 500;"
      f" font-size: 13px;'>{s_type}</div>",
      unsafe_allow_html=True,
  )
  idx += 1


# --- SECTION : CONSULTATION / GESTION DU JOUR SÉLECTIONNÉ ---
st.markdown("---")
jour_sel = st.session_state.jour_selectionne
cle_actuelle = (st.session_state.annee, st.session_state.mois, jour_sel)

existe_deja = cle_actuelle in st.session_state.seances
seance_actuelle = st.session_state.seances.get(cle_actuelle, None)

st.subheader(f"📅 Détails pour le {jour_sel} {mois_nom_courant}")

if existe_deja and not st.session_state.mode_edition:
  s_type = seance_actuelle["type"]
  details = seance_actuelle["details"]

  st.markdown(f"### Type de séance : **{s_type}**")

  if s_type == "Footing":
    col1, col2, col3 = st.columns(3)
    col1.metric("Distance", f"{details.get('distance', 0)} km")
    col2.metric("Durée estimée", f"{details.get('duree', 0)} min")
    col3.metric("Allure cible", f"{details.get('allure', '-')}")
    if details.get("commentaire"):
      st.info(f"💬 Commentaire : {details.get('commentaire')}")

  elif s_type == "Sortie longue":
    col1, col2, col3 = st.columns(3)
    col1.metric("Distance", f"{details.get('distance', 0)} km")
    col2.metric("Durée", f"{details.get('duree', 0)} min")
    col3.metric("Dénivelé", f"{details.get('denivele', 0)} m D+")
    if details.get("commentaire"):
      st.info(f"💬 Commentaire / Bloc : {details.get('commentaire')}")

  elif s_type == "Course":
    st.markdown(f"### 🏁 **{details.get('nom_course', 'Course')}**")
    col1, col2 = st.columns(2)
    col1.metric("Distance", f"{details.get('distance', 0)} km")
    col2.metric("Dénivelé", f"{details.get('denivele', 0)} m D+")
    if details.get("commentaire"):
      st.info(f"💬 Objectif / Remarque : {details.get('commentaire')}")

  elif s_type == "VMA":
    col1, col2, col3 = st.columns(3)
    col1.metric("Échauffement", f"{details.get('echauffement', 0)} min")
    col2.metric("Blocs / Séries", f"{details.get('series', '-')}")
    col3.metric("Format effort", f"{details.get('effort', '-')}")

    col4, col5 = st.columns(2)
    col4.metric("Allure cible", f"{details.get('allure', '-')}")
    col5.metric("Récupération", f"{details.get('recup', '-')}")

  elif s_type == "Seuil":
    col1, col2, col3 = st.columns(3)
    col1.metric("Échauffement", f"{details.get('echauffement', 0)} min")
    col2.metric("Nb de blocs", f"{details.get('blocs_nb', 0)}")
    col3.metric("Format bloc", f"{details.get('blocs_duree', '-')}")

    col4, col5 = st.columns(2)
    col4.metric("Allure seuil", f"{details.get('allure', '-')}")
    col5.metric("Récupération", f"{details.get('recup', '-')}")

  else:
    st.info("Jour de repos complet 🛋️")

  st.markdown("")
  col_act1, col_act2 = st.columns(2)
  with col_act1:
    if st.button("✏️ Modifier cette séance", use_container_width=True):
      st.session_state.mode_edition = True
      st.rerun()
  with col_act2:
    if st.button("🗑️ Supprimer cette séance", use_container_width=True):
      del st.session_state.seances[cle_actuelle]
      st.warning(f"Séance du {jour_sel} {mois_nom_courant} supprimée.")
      st.rerun()

else:
  if not existe_deja:
    st.info(
        f"Aucune séance enregistrée le {jour_sel} {mois_nom_courant}. Remplis"
        " les champs ci-dessous pour en créer une."
    )
  else:
    st.warning("Mode modification en cours...")

  seance_existante = (
      seance_actuelle if existe_deja else {"type": "Footing", "details": {}}
  )

  col_s1, col_s2 = st.columns([1, 2])

  with col_s1:
    types_seances = [
        "Footing",
        "Sortie longue",
        "Course",
        "VMA",
        "Seuil",
        "Repos",
    ]
    type_index = (
        types_seances.index(seance_existante["type"])
        if seance_existante["type"] in types_seances
        else 0
    )
    type_seance = st.selectbox(
        "Type de séance", types_seances, index=type_index, key="select_type_seance"
    )

  with col_s2:
    details = {}

    if type_seance == "Footing":
      col_d1, col_d2, col_d3 = st.columns(3)
      with col_d1:
        details["distance"] = st.number_input(
            "Distance (km)",
            min_value=0.0,
            value=float(seance_existante["details"].get("distance", 10.0)),
            step=0.5,
            key="f_dist",
        )
      with col_d2:
        details["duree"] = st.number_input(
            "Durée estimée (min)",
            min_value=0,
            value=int(seance_existante["details"].get("duree", 50)),
            step=1,
            key="f_dur",
        )
      with col_d3:
        details["allure"] = st.text_input(
            "Allure cible (ex: 5:15)",
            value=seance_existante["details"].get("allure", "5:15"),
            key="f_allure",
        )
      details["commentaire"] = st.text_input(
          "Commentaire",
          value=seance_existante["details"].get("commentaire", ""),
          key="f_comm",
      )

    elif type_seance == "Sortie longue":
      col_d1, col_d2, col_d3 = st.columns(3)
      with col_d1:
        details["distance"] = st.number_input(
            "Distance (km)",
            min_value=0.0,
            value=float(seance_existante["details"].get("distance", 18.0)),
            step=0.5,
            key="sl_dist",
        )
      with col_d2:
        details["duree"] = st.number_input(
            "Durée (min)",
            min_value=0,
            value=int(seance_existante["details"].get("duree", 100)),
            step=1,
            key="sl_dur",
        )
      with col_d3:
        details["denivele"] = st.number_input(
            "Dénivelé D+ (m)",
            min_value=0,
            value=int(seance_existante["details"].get("denivele", 200)),
            step=10,
            key="sl_den",
        )
      details["commentaire"] = st.text_input(
          "Commentaire / Bloc spécifique",
          value=seance_existante["details"].get("commentaire", ""),
          key="sl_comm",
      )

    elif type_seance == "Course":
      details["nom_course"] = st.text_input(
          "Nom de la course (ex: Semi de Paris)",
          value=seance_existante["details"].get("nom_course", "10km de la ville"),
          key="c_nom",
      )
      col_d1, col_d2 = st.columns(2)
      with col_d1:
        details["distance"] = st.number_input(
            "Distance (km)",
            min_value=0.0,
            value=float(seance_existante["details"].get("distance", 10.0)),
            step=0.5,
            key="c_dist",
        )
      with col_d2:
        details["denivele"] = st.number_input(
            "Dénivelé D+ (m)",
            min_value=0,
            value=int(seance_existante["details"].get("denivele", 100)),
            step=10,
            key="c_den",
        )
      details["commentaire"] = st.text_input(
          "Objectif / Remarque",
          value=seance_existante["details"].get("commentaire", ""),
          key="c_comm",
      )

    elif type_seance == "VMA":
      col_d1, col_d2, col_d3 = st.columns(3)
      with col_d1:
        details["echauffement"] = st.number_input(
            "Échauffement (min)",
            min_value=0,
            value=int(seance_existante["details"].get("echauffement", 20)),
            step=5,
            key="vma_ech",
        )
      with col_d2:
        details["series"] = st.text_input(
            "Blocs / Séries (ex: 2 x 8)",
            value=seance_existante["details"].get("series", "2 x 8"),
            key="vma_ser",
        )
      with col_d3:
        details["effort"] = st.text_input(
            "Format effort (ex: 400m)",
            value=seance_existante["details"].get("effort", "400m"),
            key="vma_eff",
        )

      col_d4, col_d5 = st.columns(2)
      with col_d4:
        details["allure"] = st.text_input(
            "Allure / Vitesse cible",
            value=seance_existante["details"].get("allure", "3:45 /km"),
            key="vma_all",
        )
      with col_d5:
        details["recup"] = st.text_input(
            "Récupération",
            value=seance_existante["details"].get("recup", "1 min trot"),
            key="vma_rec",
        )

    elif type_seance == "Seuil":
      col_d1, col_d2, col_d3 = st.columns(3)
      with col_d1:
        details["echauffement"] = st.number_input(
            "Échauffement (min)",
            min_value=0,
            value=int(seance_existante["details"].get("echauffement", 20)),
            step=5,
            key="seu_ech",
        )
      with col_d2:
        details["blocs_nb"] = st.number_input(
            "Nombre de blocs",
            min_value=1,
            value=int(seance_existante["details"].get("blocs_nb", 3)),
            step=1,
            key="seu_nb",
        )
      with col_d3:
        details["blocs_duree"] = st.text_input(
            "Durée/Distance par bloc",
            value=seance_existante["details"].get("blocs_duree", "8 min"),
            key="seu_dur",
        )

      col_d4, col_d5 = st.columns(2)
      with col_d4:
        details["allure"] = st.text_input(
            "Allure seuil cible",
            value=seance_existante["details"].get("allure", "4:15 /km"),
            key="seu_all",
        )
      with col_d5:
        details["recup"] = st.text_input(
            "Récupération entre blocs",
            value=seance_existante["details"].get("recup", "2 min trot"),
            key="seu_rec",
        )

    else:
      st.info("Jour de repos complet.")

    col_b1, col_b2 = st.columns(2)
    with col_b1:
      if st.button(
          "💾 Enregistrer la séance", type="primary", use_container_width=True
      ):
        st.session_state.seances[cle_actuelle] = {
            "type": type_seance,
            "details": details,
        }
        st.session_state.mode_edition = False
        st.success(f"Séance du {jour_sel} {mois_nom_courant} enregistrée !")
        st.rerun()

    with col_b2:
      if existe_deja:
        if st.button("❌ Annuler", use_container_width=True):
          st.session_state.mode_edition = False
          st.rerun()


# --- SECTION : SYNTHÈSES ---
st.markdown("---")
st.subheader(
    f"📊 Synthèse et Statistiques - {mois_nom_courant} {st.session_state.annee}"
)


def estimer_distance(seance):
  t = seance["type"]
  d = seance["details"]
  if t in ["Footing", "Sortie longue", "Course"]:
    return float(d.get("distance", 0.0))
  elif t == "VMA":
    ech_km = float(d.get("echauffement", 20)) / 5.0
    return ech_km + 4.0
  elif t == "Seuil":
    ech_km = float(d.get("echauffement", 20)) / 5.0
    return ech_km + 6.0
  return 0.0


total_km_mois = 0.0
nb_seances_mois = 0
compteur_types = {
    "Footing": 0,
    "Sortie longue": 0,
    "Course": 0,
    "VMA": 0,
    "Seuil": 0,
    "Repos": 0,
}

for (an, mo, j), seance in st.session_state.seances.items():
  if an == st.session_state.annee and mo == st.session_state.mois:
    s_type = seance["type"]
    if s_type in compteur_types:
      compteur_types[s_type] += 1
    if s_type != "Repos":
      nb_seances_mois += 1
      total_km_mois += estimer_distance(seance)

m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Km totaux", f"{total_km_mois:.1f} km")
m2.metric("Séances", f"{nb_seances_mois}")
m3.metric("Footings", f"{compteur_types['Footing']}")
m4.metric("Sorties long.", f"{compteur_types['Sortie longue']}")
m5.metric("Courses 🏁", f"{compteur_types['Course']}")
m6.metric("VMA / Seuil", f"{compteur_types['VMA'] + compteur_types['Seuil']}")

# --- SYNTHÈSE HEBDOMADAIRE ---
st.markdown("#### 📅 Détail par Semaine")
data_hebdo = []
for idx_sem, semaine in enumerate(mois_cal):
  km_semaine = 0.0
  seances_semaine = 0
  for jour in semaine:
    if jour != 0:
      cle = (st.session_state.annee, st.session_state.mois, jour)
      if cle in st.session_state.seances:
        s = st.session_state.seances[cle]
        if s["type"] != "Repos":
          seances_semaine += 1
          km_semaine += estimer_distance(s)

  jours_valides_semaine = [j for j in semaine if j != 0]
  if jours_valides_semaine:
    debut_s = jours_valides_semaine[0]
    fin_s = jours_valides_semaine[-1]
    data_hebdo.append({
        "Semaine": (
            f"Semaine {idx_sem + 1} (Du {debut_s} au {fin_s}"
            f" {mois_nom_courant})"
        ),
        "Nombre de séances": seances_semaine,
        "Volume estimé (km)": round(km_semaine, 1),
    })

df_hebdo = pd.DataFrame(data_hebdo)
st.dataframe(df_hebdo, use_container_width=True)