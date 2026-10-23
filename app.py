import base64
import calendar
from datetime import datetime
import json
import altair as alt
import pandas as pd
import requests
import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="Mon Planning Running",
    page_icon="🏃‍♂️",
    layout="wide"
)

# --- STYLE CSS ADAPTATIF (PC & MOBILE) ---
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    div.stButton > button {
        border-radius: 6px;
        font-weight: 600;
        height: 52px !important;
        padding: 0px !important;
        font-size: 11px !important;
        line-height: 1.1 !important;
    }

    /* Adaptation mobile (écrans <= 768px) */
    @media (max-width: 768px) {
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }
        div.stButton > button {
            height: 46px !important;
            font-size: 12px !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏃‍♂️ Mon Planning d'Entraînement Partagé")

# --- CONFIGURATION API GITHUB POUR LA PERSISTANCE ---
REPO_OWNER = "Robino8"
REPO_NAME = "planning-running"
BRANCH = "main"

def obtenir_token():
    return st.secrets.get("GITHUB_TOKEN", "")

def obtenir_fichier_sauvegarde():
    profil = st.session_state.get("profil", "Robin")
    return "planning_mathilde.json" if profil == "Mathilde" else "planning_robin.json"

def charger_seances():
    token = obtenir_token()
    fichier = obtenir_fichier_sauvegarde()

    if not token:
        st.error("Jeton GitHub manquant dans les Secrets Streamlit.")
        return {}

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{fichier}?ref={BRANCH}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data_json = response.json()
            contenu_decode = base64.b64decode(data_json["content"]).decode("utf-8")
            data_brute = json.loads(contenu_decode)
            seances_dict = {}
            for k, v in data_brute.items():
                parts = k.split("-")
                cle = (int(parts[0]), int(parts[1]), int(parts[2]))
                seances_dict[cle] = v
            return seances_dict
        return {}
    except Exception as e:
        st.warning(f"Erreur de lecture GitHub : {e}")
        return {}

def sauvegarder_seances(seances_dict):
    token = obtenir_token()
    fichier = obtenir_fichier_sauvegarde()

    if not token:
        st.error("Jeton GitHub manquant dans les Secrets Streamlit.")
        return False

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{fichier}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    data_brute = {}
    for (an, mo, j), seance_data in seances_dict.items():
        cle_str = f"{an}-{mo}-{j}"
        data_brute[cle_str] = seance_data

    contenu_chaine = json.dumps(data_brute, ensure_ascii=False, indent=4)
    contenu_b64 = base64.b64encode(contenu_chaine.encode("utf-8")).decode("utf-8")

    sha = None
    res_get = requests.get(f"{url}?ref={BRANCH}", headers=headers, timeout=10)
    if res_get.status_code == 200:
        sha = res_get.json().get("sha")

    payload = {
        "message": f"Mise à jour du planning {fichier} via l'application",
        "content": contenu_b64,
        "branch": BRANCH
    }
    if sha:
        payload["sha"] = sha

    res_put = requests.put(url, headers=headers, json=payload, timeout=10)
    return res_put.status_code in [200, 201]

# --- INITIALISATION DE LA SESSION ---
if "profil" not in st.session_state:
    st.session_state.profil = "Robin"
if "annee" not in st.session_state:
    st.session_state.annee = datetime.now().year
if "mois" not in st.session_state:
    st.session_state.mois = datetime.now().month
if "seances" not in st.session_state:
    st.session_state.seances = charger_seances()
if "jour_selectionne" not in st.session_state:
    st.session_state.jour_selectionne = datetime.now().day
if "mode_edition" not in st.session_state:
    st.session_state.mode_edition = False

mois_noms = {
    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
    5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
    9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"
}

couleurs_pastel = {
    "Footing": {"bg": "#B3E5FC", "border": "#0288D1"},
    "Sortie longue": {"bg": "#FFE0B2", "border": "#F57C00"},
    "VMA": {"bg": "#E1BEE7", "border": "#8E24AA"},
    "Seuil": {"bg": "#C8E6C9", "border": "#388E3C"},
    "Course": {"bg": "#FFCDD2", "border": "#D32F2F"},
    "Renforcement musculaire": {"bg": "#FFF9C4", "border": "#FBC02D"},
    "Repos": {"bg": "#EEEEEE", "border": "#BDBDBD"}
}

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

# ==========================================
# MISE EN PAGE EN 3 COLONNES
# ==========================================
col_nav, col_centre, col_droite = st.columns([0.8, 1.4, 1.3])

# --- 1. COLONNE GAUCHE : NAVIGATION ---
with col_nav:
    st.header("Profil")
    nouveau_profil = st.selectbox("Choisir le planning", ["Robin", "Mathilde"], key="select_profil")
    if nouveau_profil != st.session_state.profil:
        st.session_state.profil = nouveau_profil
        st.session_state.seances = charger_seances()
        st.session_state.mode_edition = False
        st.rerun()

    st.markdown("---")
    st.header("Navigation")
    col_n1, col_n2 = st.columns(2)
    with col_n1:
        if st.button("◀ Précéd", use_container_width=True):
            mois_precedent()
            st.rerun()
    with col_n2:
        if st.button("Suivant ▶", use_container_width=True):
            mois_suivant()
            st.rerun()

    st.markdown("---")
    choix_mois_nom = st.selectbox(
        "Aller au mois",
        list(mois_noms.values()),
        index=st.session_state.mois - 1
    )
    st.session_state.mois = [k for k, v in mois_noms.items() if v == choix_mois_nom][0]
    st.session_state.annee = st.number_input(
        "Année",
        min_value=2020,
        max_value=2030,
        value=st.session_state.annee,
        step=1
    )

# --- 2. COLONNE CENTRALE : PLANNING ---
with col_centre:
    mois_nom_courant = mois_noms[st.session_state.mois]
    if st.session_state.profil == "Robin":
        couleur_bandeau, bordure_bandeau, texte_couleur, icone_profil = "#E0F2FE", "#0288D1", "#0369A1", "🧢"
    else:
        couleur_bandeau, bordure_bandeau, texte_couleur, icone_profil = "#FCE7F3", "#DB2777", "#BE185D", "🌸"

    st.markdown(f"""
    <div style="background-color: {couleur_bandeau}; border: 2px solid {bordure_bandeau}; border-radius: 8px; padding: 10px; text-align: center; margin-bottom: 12px;">
        <span style="font-size: 16px; font-weight: 700; color: {texte_couleur};">
            {icone_profil} Planning d'entraînement de {st.session_state.profil}
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.subheader(f"📅 {mois_nom_courant} {st.session_state.annee}")

    cal = calendar.Calendar(firstweekday=0)
    mois_cal = cal.monthdatescalendar(st.session_state.annee, st.session_state.mois)

    jours_semaine = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    cols_entetes = st.columns(7)
    for i, j_nom in enumerate(jours_semaine):
        cols_entetes[i].markdown(f"<div style='text-align: center;'><b>{j_nom}</b></div>", unsafe_allow_html=True)

    for semaine in mois_cal:
        cols_semaine = st.columns(7)
        for i, date_jour in enumerate(semaine):
            with cols_semaine[i]:
                j_an, j_mo, j_jour = date_jour.year, date_jour.month, date_jour.day
                est_mois_courant = (j_mo == st.session_state.mois)
                cle = (j_an, j_mo, j_jour)
                opacite = "1.0" if est_mois_courant else "0.3"

                if cle in st.session_state.seances:
                    s_type = st.session_state.seances[cle]["type"]
                    s_realise = " ✅" if st.session_state.seances[cle].get("realise", False) else ""
                    mapping_labels = {
                        "Footing": f"J{j_jour}{s_realise}\n🏃 Footing",
                        "Sortie longue": f"J{j_jour}{s_realise}\n🔥 Sortie L.",
                        "Course": f"J{j_jour}{s_realise}\n🏁 {st.session_state.seances[cle]['details'].get('nom_course', 'Course')[:6]}",
                        "VMA": f"J{j_jour}{s_realise}\n⚡ VMA",
                        "Seuil": f"J{j_jour}{s_realise}\n⏱️ Seuil",
                        "Renforcement musculaire": f"J{j_jour}{s_realise}\n🏋️ Renfo",
                        "Repos": f"J{j_jour}{s_realise}\n🛋️ Repos"
                    }
                    label_btn = mapping_labels.get(s_type, f"J{j_jour}{s_realise}\n{s_type}")
                    style_data = couleurs_pastel.get(s_type, {"bg": "#FFFFFF", "border": "#CCCCCC"})
                    bg_color = style_data["bg"]
                    border_color = style_data["border"]
                else:
                    label_btn = f"J{j_jour}\n(-)"
                    bg_color = "#FFFFFF" if est_mois_courant else "#F5F5F5"
                    border_color = "#DDDDDD" if est_mois_courant else "#E0E0E0"

                st.markdown(f"""
                <div style="background-color: {bg_color}; opacity: {opacite}; padding: 1px; border-radius: 4px; border: 2px solid {border_color}; text-align: center; margin-bottom: -15px;">
                </div>
                """, unsafe_allow_html=True)

                if st.button(label_btn, key=f"btn_date_{j_an}_{j_mo}_{j_jour}", use_container_width=True):
                    st.session_state.annee = j_an
                    st.session_state.mois = j_mo
                    st.session_state.jour_selectionne = j_jour
                    st.session_state.mode_edition = False
                    st.rerun()

    st.markdown("")
    cols_leg = st.columns(7)
    legende_items = [
        ("Footing", couleurs_pastel["Footing"]["bg"]),
        ("Sortie L.", couleurs_pastel["Sortie longue"]["bg"]),
        ("Course", couleurs_pastel["Course"]["bg"]),
        ("VMA", couleurs_pastel["VMA"]["bg"]),
        ("Seuil", couleurs_pastel["Seuil"]["bg"]),
        ("Renfo", couleurs_pastel["Renforcement musculaire"]["bg"]),
        ("Repos", couleurs_pastel["Repos"]["bg"])
    ]
    for idx, (s_type, col) in enumerate(legende_items):
        cols_leg[idx].markdown(
            f"<div style='background-color: {col}; padding: 2px; border-radius: 3px; text-align: center; border: 1px solid #999; font-size: 8px; font-weight: 600;'>{s_type}</div>",
            unsafe_allow_html=True
        )

# --- 3. COLONNE DROITE : DÉTAILS, FORMULAIRE & STATS ---
with col_droite:
    jour_sel = st.session_state.jour_selectionne
    cle_actuelle = (st.session_state.annee, st.session_state.mois, jour_sel)

    existe_deja = cle_actuelle in st.session_state.seances
    seance_actuelle = st.session_state.seances.get(cle_actuelle, None)

    st.subheader(f"✍️ Séance du {jour_sel} {mois_noms[st.session_state.mois]}")

    if existe_deja and not st.session_state.mode_edition:
        s_type = seance_actuelle["type"]
        s_realise_bool = seance_actuelle.get("realise", False)
        details = seance_actuelle["details"]

        statut_str = "✅ Réalisée" if s_realise_bool else "⏳ Prévisionnelle"
        st.markdown(f"**Type : {s_type}** — *{statut_str}*")

        if s_type == "Footing":
            c1, c2, c3 = st.columns(3)
            c1.metric("Dist.", f"{details.get('distance', 0)} km")
            c2.metric("Durée", f"{details.get('duree', 0)} min")
            c3.metric("Allure", f"{details.get('allure', '-')}")
            if details.get("commentaire"):
                st.info(f"💬 {details.get('commentaire')}")
        elif s_type == "Sortie longue":
            c1, c2, c3 = st.columns(3)
            c1.metric("Dist.", f"{details.get('distance', 0)} km")
            c2.metric("Durée", f"{details.get('duree', 0)} min")
            c3.metric("D+ ", f"{details.get('denivele', 0)} m")
            if details.get("commentaire"):
                st.info(f"💬 {details.get('commentaire')}")
        elif s_type == "Course":
            st.markdown(f"🏁 **{details.get('nom_course', 'Course')}**")
            c1, c2 = st.columns(2)
            c1.metric("Dist.", f"{details.get('distance', 0)} km")
            c2.metric("D+ ", f"{details.get('denivele', 0)} m")
            if details.get("commentaire"):
                st.info(f"💬 {details.get('commentaire')}")
        elif s_type == "VMA":
            c1, c2, c3 = st.columns(3)
            c1.metric("Échau.", f"{details.get('echauffement', 0)}m")
            c2.metric("Séries", f"{details.get('series', '-')}")
            c3.metric("Effort", f"{details.get('effort', '-')}")
            c4, c5 = st.columns(2)
            c4.metric("Allure", f"{details.get('allure', '-')}")
            c5.metric("Récup", f"{details.get('recup', '-')}")
        elif s_type == "Seuil":
            c1, c2, c3 = st.columns(3)
            c1.metric("Échau.", f"{details.get('echauffement', 0)}m")
            c2.metric("Blocs", f"{details.get('blocs_nb', 0)}")
            c3.metric("Format", f"{details.get('blocs_duree', '-')}")
            c4, c5 = st.columns(2)
            c4.metric("Allure", f"{details.get('allure', '-')}")
            c5.metric("Récup", f"{details.get('recup', '-')}")
        elif s_type == "Renforcement musculaire":
            c1, c2 = st.columns(2)
            c1.metric("Zone", f"{details.get('zone', '-')}")
            c2.metric("Durée", f"{details.get('duree', 0)} min")
            if details.get("commentaire"):
                st.info(f"💬 {details.get('commentaire')}")
        else:
            st.info("Jour de repos complet 🛋️")

        st.markdown("")
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            if st.button("✏️ Modifier", use_container_width=True):
                st.session_state.mode_edition = True
                st.rerun()
        with col_act2:
            if st.button("🗑️ Supprimer", use_container_width=True):
                del st.session_state.seances[cle_actuelle]
                sauvegarder_seances(st.session_state.seances)
                st.rerun()

    else:
        seance_existante = seance_actuelle if existe_deja else {"type": "Footing", "details": {}}
        realise_defaut = seance_actuelle.get("realise", False) if existe_deja else False
        est_realise = st.checkbox("Séance réalisée ✅", value=realise_defaut, key="chk_realise")

        types_seances = ["Footing", "Sortie longue", "Course", "VMA", "Seuil", "Renforcement musculaire", "Repos"]
        type_index = types_seances.index(seance_existante["type"]) if seance_existante["type"] in types_seances else 0
        type_seance = st.selectbox("Type de séance", types_seances, index=type_index, key="select_type_seance")

        details = {}
        if type_seance == "Footing":
            col_d1, col_d2, col_d3 = st.columns(3)
            with col_d1:
                details["distance"] = st.number_input("Dist. (km)", min_value=0.0, value=float(seance_existante["details"].get("distance", 10.0)), step=0.5, key="f_dist")
            with col_d2:
                details["duree"] = st.number_input("Durée (min)", min_value=0, value=int(seance_existante["details"].get("duree", 50)), step=1, key="f_dur")
            with col_d3:
                details["allure"] = st.text_input("Allure", value=seance_existante["details"].get("allure", "5:15"), key="f_allure")
            details["commentaire"] = st.text_input("Commentaire", value=seance_existante["details"].get("commentaire", ""), key="f_comm")

        elif type_seance == "Sortie longue":
            col_d1, col_d2, col_d3 = st.columns(3)
            with col_d1:
                details["distance"] = st.number_input("Dist. (km)", min_value=0.0, value=float(seance_existante["details"].get("distance", 18.0)), step=0.5, key="sl_dist")
            with col_d2:
                details["duree"] = st.number_input("Durée (min)", min_value=0, value=int(seance_existante["details"].get("duree", 100)), step=1, key="sl_dur")
            with col_d3:
                details["denivele"] = st.number_input("D+ (m)", min_value=0, value=int(seance_existante["details"].get("denivele", 200)), step=10, key="sl_den")
            details["commentaire"] = st.text_input("Commentaire", value=seance_existante["details"].get("commentaire", ""), key="sl_comm")

        elif type_seance == "Course":
            details["nom_course"] = st.text_input("Nom", value=seance_existante["details"].get("nom_course", "10km"), key="c_nom")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                details["distance"] = st.number_input("Dist. (km)", min_value=0.0, value=float(seance_existante["details"].get("distance", 10.0)), step=0.5, key="c_dist")
            with col_d2:
                details["denivele"] = st.number_input("D+ (m)", min_value=0, value=int(seance_existante["details"].get("denivele", 100)), step=10, key="c_den")
            details["commentaire"] = st.text_input("Objectif", value=seance_existante["details"].get("commentaire", ""), key="c_comm")

        elif type_seance == "VMA":
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                details["echauffement"] = st.number_input("Échauff. (min)", min_value=0, value=int(seance_existante["details"].get("echauffement", 20)), step=5, key="vma_ech")
            with col_d2:
                details["series"] = st.text_input("Séries", value=seance_existante["details"].get("series", "2 x 8"), key="vma_ser")
            col_d3, col_d4 = st.columns(2)
            with col_d3:
                details["effort"] = st.text_input("Effort", value=seance_existante["details"].get("effort", "400m"), key="vma_eff")
            with col_d4:
                details["allure"] = st.text_input("Allure", value=seance_existante["details"].get("allure", "3:45"), key="vma_all")
            details["recup"] = st.text_input("Récup", value=seance_existante["details"].get("recup", "1 min"), key="vma_rec")

        elif type_seance == "Seuil":
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                details["echauffement"] = st.number_input("Échauff. (min)", min_value=0, value=int(seance_existante["details"].get("echauffement", 20)), step=5, key="seu_ech")
            with col_d2:
                details["blocs_nb"] = st.number_input("Nb blocs", min_value=1, value=int(seance_existante["details"].get("blocs_nb", 3)), step=1, key="seu_nb")
            col_d3, col_d4 = st.columns(2)
            with col_d3:
                details["blocs_duree"] = st.text_input("Format bloc", value=seance_existante["details"].get("blocs_duree", "8 min"), key="seu_dur")
            with col_d4:
                details["allure"] = st.text_input("Allure", value=seance_existante["details"].get("allure", "4:15"), key="seu_all")
            details["recup"] = st.text_input("Récup", value=seance_existante["details"].get("recup", "2 min"), key="seu_rec")

        elif type_seance == "Renforcement musculaire":
            details["zone"] = st.text_input("Zone ciblée", value=seance_existante["details"].get("zone", "Jambes / Abdos"), key="rm_zone")
            details["duree"] = st.number_input("Durée (min)", min_value=0, value=int(seance_existante["details"].get("duree", 30)), step=5, key="rm_dur")
            details["commentaire"] = st.text_input("Commentaire", value=seance_existante["details"].get("commentaire", ""), key="rm_comm")

        st.markdown("")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("💾 Enregistrer", type="primary", use_container_width=True):
                st.session_state.seances[cle_actuelle] = {
                    "type": type_seance,
                    "realise": est_realise,
                    "details": details
                }
                if sauvegarder_seances(st.session_state.seances):
                    st.session_state.mode_edition = False
                    st.success("Enregistré sur GitHub !")
                    st.rerun()
        with col_b2:
            if existe_deja and st.button("❌ Annuler", use_container_width=True):
                st.session_state.mode_edition = False
                st.rerun()

    # --- BILAN MENSUEL ---
    def estimer_distance(seance):
        t = seance["type"]
        d = seance["details"]
        if t in ["Footing", "Sortie longue", "Course"]:
            return float(d.get("distance", 0.0))
        elif t == "VMA":
            return float(d.get("echauffement", 20)) / 5.0 + 4.0
        elif t == "Seuil":
            return float(d.get("echauffement", 20)) / 5.0 + 6.0
        return 0.0

    total_km_mois = 0.0
    nb_seances_mois = 0
    compteur_types = {"Footing": 0, "Sortie longue": 0, "Course": 0, "VMA": 0, "Seuil": 0, "Renforcement musculaire": 0, "Repos": 0}

    for (an, mo, j), seance in st.session_state.seances.items():
        if an == st.session_state.annee and mo == st.session_state.mois:
            s_type = seance["type"]
            if s_type in compteur_types:
                compteur_types[s_type] += 1
            if s_type != "Repos":
                nb_seances_mois += 1
                total_km_mois += estimer_distance(seance)

    vma_seuil_total = compteur_types["VMA"] + compteur_types["Seuil"]

    st.markdown(f"""
    <div style="background-color: #f8fafc; border: 1.5px solid #cbd5e1; border-radius: 10px; padding: 12px; margin-top: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
        <div style="font-weight: 700; font-size: 14px; color: {texte_couleur}; margin-bottom: 8px; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px;">
            📈 Bilan de {mois_nom_courant} ({st.session_state.profil})
        </div>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; text-align: center;">
            <div style="background: white; padding: 6px; border-radius: 6px; border: 1px solid #e2e8f0;">
                <span style="font-size: 9px; color: #64748b; display: block; text-transform: uppercase; font-weight: 600;">Km totaux</span>
                <strong style="font-size: 14px; color: #0f172a;">{total_km_mois:.1f} km</strong>
            </div>
            <div style="background: white; padding: 6px; border-radius: 6px; border: 1px solid #e2e8f0;">
                <span style="font-size: 9px; color: #64748b; display: block; text-transform: uppercase; font-weight: 600;">Séances</span>
                <strong style="font-size: 14px; color: #0f172a;">{nb_seances_mois}</strong>
            </div>
            <div style="background: white; padding: 6px; border-radius: 6px; border: 1px solid #e2e8f0;">
                <span style="font-size: 9px; color: #64748b; display: block; text-transform: uppercase; font-weight: 600;">Footings</span>
                <strong style="font-size: 14px; color: #0f172a;">{compteur_types['Footing']}</strong>
            </div>
            <div style="background: white; padding: 6px; border-radius: 6px; border: 1px solid #e2e8f0;">
                <span style="font-size: 9px; color: #64748b; display: block; text-transform: uppercase; font-weight: 600;">Sorties long.</span>
                <strong style="font-size: 14px; color: #0f172a;">{compteur_types['Sortie longue']}</strong>
            </div>
            <div style="background: white; padding: 6px; border-radius: 6px; border: 1px solid #e2e8f0;">
                <span style="font-size: 9px; color: #64748b; display: block; text-transform: uppercase; font-weight: 600;">Courses 🏁</span>
                <strong style="font-size: 14px; color: #0f172a;">{compteur_types['Course']}</strong>
            </div>
            <div style="background: white; padding: 6px; border-radius: 6px; border: 1px solid #e2e8f0;">
                <span style="font-size: 9px; color: #64748b; display: block; text-transform: uppercase; font-weight: 600;">VMA / Seuil</span>
                <strong style="font-size: 14px; color: #0f172a;">{vma_seuil_total}</strong>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- GRAPHIQUE HEBDOMADAIRE ---
    st.markdown("---")
    st.markdown("#### 📊 Volume hebdomadaire (km)")

    data_hebdo = []
    for idx_sem, semaine in enumerate(mois_cal):
        km_semaine = 0.0
        for date_j in semaine:
            cle = (date_j.year, date_j.month, date_j.day)
            if cle in st.session_state.seances:
                s = st.session_state.seances[cle]
                if s["type"] != "Repos":
                    km_semaine += estimer_distance(s)

        debut_s = semaine[0].strftime("%d/%m")
        fin_s = semaine[-1].strftime("%d/%m")
        data_hebdo.append({
            "Semaine": f"S{idx_sem + 1} ({debut_s}-{fin_s})",
            "Volume": round(km_semaine, 1)
        })

    df_hebdo = pd.DataFrame(data_hebdo)

    chart = alt.Chart(df_hebdo).mark_bar(
        color="#2563EB",
        cornerRadiusTopLeft=6,
        cornerRadiusTopRight=6,
        width=28
    ).encode(
        x=alt.X("Semaine:N", sort=None, title=None, axis=alt.Axis(labelAngle=0, labelFontSize=10)),
        y=alt.Y("Volume:Q", title="Km", axis=alt.Axis(grid=True))
    )

    text = chart.mark_text(
        align="center",
        baseline="bottom",
        dy=-5,
        fontSize=11,
        fontWeight="bold",
        color="#1E293B"
    ).encode(
        text=alt.Text("Volume:Q", format=".1f")
    )

    st.altair_chart((chart + text).properties(height=160).configure_view(stroke=None), use_container_width=True)