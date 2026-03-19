
import sqlite3
from datetime import datetime
import streamlit as st
import pandas as pd

APP_TITLE = "CRM Louis"
DB_PATH = "crm_louis.db"

GAMMES = ["GL", "VU", "REM"]
CARROSSERIES = ["FRIGO", "HYDRAU", "SEC", "TRR", "AUTRE"]
ENERGIES = ["B7", "B100", "B100 FLEXIBLE", "E-TECH"]
PRIORITES = ["🔥 Chaud", "⚠️ À suivre", "🧊 Froid"]
TYPES_OPP = ["Prospect", "Client existant", "Renouvellement", "AO / SAD"]
STATUTS = [
    "Définition du besoin", "Chiffrage en cours", "Faire proposition",
    "Proposition envoyée", "Relance", "Contre-proposition",
    "Accord client", "Commande en cours", "Gagné", "Perdu", "Stand-by"
]
ACTIONS = [
    "Appeler", "Relancer mail", "Envoyer proposition", "Refaire chiffrage",
    "Prendre RDV", "Attendre retour client", "Attendre validation interne",
    "Commander véhicule", "Clôturer gagné", "Clôturer perdu"
]
BLOCAGES = [
    "Prix", "Délais", "Pas de besoin immédiat", "Décision interne client",
    "Attente budget", "Concurrent en place", "Caractéristique véhicule",
    "Financement", "Validation hiérarchique", "Inconnu"
]
STATUTS_CLOTURES = {"Gagné", "Perdu"}

st.set_page_config(page_title=APP_TITLE, layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1rem; padding-bottom: 2rem;}
.card {
    border: 1px solid rgba(120,120,120,.25);
    border-radius: 14px;
    padding: 14px 16px;
    margin-bottom: 10px;
    background: rgba(255,255,255,.03);
}
.small-muted {opacity: .75; font-size: .9rem;}
</style>
""", unsafe_allow_html=True)


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        secteur TEXT,
        type_compte TEXT,
        adresse TEXT,
        ville TEXT,
        code_postal TEXT,
        telephone TEXT,
        email TEXT,
        statut_client TEXT,
        potentiel TEXT,
        concurrent_en_place TEXT,
        siret TEXT,
        naf TEXT,
        notes TEXT,
        contact1_nom TEXT,
        contact1_fonction TEXT,
        contact1_telephone TEXT,
        contact1_email TEXT,
        contact2_nom TEXT,
        contact2_fonction TEXT,
        contact2_telephone TEXT,
        contact2_email TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS affaires (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        priorite TEXT,
        date_creation TEXT,
        commercial_assigne TEXT,
        type_opportunite TEXT,
        gamme TEXT,
        carrosserie TEXT,
        energie TEXT,
        vn_parc TEXT,
        duree_mois INTEGER,
        km_an INTEGER,
        loyer_mensuel REAL,
        statut TEXT,
        action_suivante TEXT,
        date_envoi_proposition TEXT,
        blocage_principal TEXT,
        deadline_ao TEXT,
        date_prochaine_action TEXT,
        concurrent TEXT,
        contrat_bdc TEXT,
        notes TEXT,
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY (client_id) REFERENCES clients(id)
    )
    """)
    conn.commit()
    conn.close()


def now_iso():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def parse_optional_date_str(value: str):
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


def display_date(value):
    if not value:
        return ""
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return str(value)


def safe_int(v, default=0):
    try:
        if v in (None, "", "None"):
            return default
        return int(float(v))
    except Exception:
        return default


def safe_float(v, default=0.0):
    try:
        if v in (None, "", "None"):
            return default
        return float(v)
    except Exception:
        return default


def fetch_df(query, params=()):
    conn = get_conn()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def execute(query, params=()):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id


def fetch_clients():
    return fetch_df("SELECT * FROM clients ORDER BY UPPER(nom) ASC")


def fetch_affaires():
    return fetch_df("""
        SELECT a.*, c.nom AS client_nom
        FROM affaires a
        LEFT JOIN clients c ON c.id = a.client_id
        ORDER BY a.id DESC
    """)


def upsert_client(client_id, data):
    ts = now_iso()
    if client_id is None:
        return execute("""
            INSERT INTO clients (
                nom, secteur, type_compte, adresse, ville, code_postal, telephone, email,
                statut_client, potentiel, concurrent_en_place, siret, naf, notes,
                contact1_nom, contact1_fonction, contact1_telephone, contact1_email,
                contact2_nom, contact2_fonction, contact2_telephone, contact2_email,
                created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            data["nom"], data["secteur"], data["type_compte"], data["adresse"], data["ville"], data["code_postal"],
            data["telephone"], data["email"], data["statut_client"], data["potentiel"], data["concurrent_en_place"],
            data["siret"], data["naf"], data["notes"], data["contact1_nom"], data["contact1_fonction"],
            data["contact1_telephone"], data["contact1_email"], data["contact2_nom"], data["contact2_fonction"],
            data["contact2_telephone"], data["contact2_email"], ts, ts
        ))
    execute("""
        UPDATE clients SET
            nom=?, secteur=?, type_compte=?, adresse=?, ville=?, code_postal=?, telephone=?, email=?,
            statut_client=?, potentiel=?, concurrent_en_place=?, siret=?, naf=?, notes=?,
            contact1_nom=?, contact1_fonction=?, contact1_telephone=?, contact1_email=?,
            contact2_nom=?, contact2_fonction=?, contact2_telephone=?, contact2_email=?, updated_at=?
        WHERE id=?
    """, (
        data["nom"], data["secteur"], data["type_compte"], data["adresse"], data["ville"], data["code_postal"],
        data["telephone"], data["email"], data["statut_client"], data["potentiel"], data["concurrent_en_place"],
        data["siret"], data["naf"], data["notes"], data["contact1_nom"], data["contact1_fonction"],
        data["contact1_telephone"], data["contact1_email"], data["contact2_nom"], data["contact2_fonction"],
        data["contact2_telephone"], data["contact2_email"], ts, client_id
    ))
    return client_id


def upsert_affaire(affaire_id, data):
    ts = now_iso()
    if affaire_id is None:
        return execute("""
            INSERT INTO affaires (
                client_id, priorite, date_creation, commercial_assigne, type_opportunite,
                gamme, carrosserie, energie, vn_parc, duree_mois, km_an, loyer_mensuel,
                statut, action_suivante, date_envoi_proposition, blocage_principal,
                deadline_ao, date_prochaine_action, concurrent, contrat_bdc, notes,
                created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            data["client_id"], data["priorite"], data["date_creation"], data["commercial_assigne"],
            data["type_opportunite"], data["gamme"], data["carrosserie"], data["energie"], data["vn_parc"],
            data["duree_mois"], data["km_an"], data["loyer_mensuel"], data["statut"], data["action_suivante"],
            data["date_envoi_proposition"], data["blocage_principal"], data["deadline_ao"],
            data["date_prochaine_action"], data["concurrent"], data["contrat_bdc"], data["notes"], ts, ts
        ))
    execute("""
        UPDATE affaires SET
            client_id=?, priorite=?, date_creation=?, commercial_assigne=?, type_opportunite=?,
            gamme=?, carrosserie=?, energie=?, vn_parc=?, duree_mois=?, km_an=?, loyer_mensuel=?,
            statut=?, action_suivante=?, date_envoi_proposition=?, blocage_principal=?,
            deadline_ao=?, date_prochaine_action=?, concurrent=?, contrat_bdc=?, notes=?, updated_at=?
        WHERE id=?
    """, (
        data["client_id"], data["priorite"], data["date_creation"], data["commercial_assigne"],
        data["type_opportunite"], data["gamme"], data["carrosserie"], data["energie"], data["vn_parc"],
        data["duree_mois"], data["km_an"], data["loyer_mensuel"], data["statut"], data["action_suivante"],
        data["date_envoi_proposition"], data["blocage_principal"], data["deadline_ao"],
        data["date_prochaine_action"], data["concurrent"], data["contrat_bdc"], data["notes"], ts, affaire_id
    ))
    return affaire_id


def delete_client(client_id, delete_related=False):
    if delete_related:
        execute("DELETE FROM affaires WHERE client_id=?", (client_id,))
    else:
        execute("UPDATE affaires SET client_id=NULL WHERE client_id=?", (client_id,))
    execute("DELETE FROM clients WHERE id=?", (client_id,))


def delete_affaire(affaire_id):
    execute("DELETE FROM affaires WHERE id=?", (affaire_id,))


def idx(options, value, default=0):
    return options.index(value) if value in options else default


def client_form(default=None, key_prefix="client"):
    default = default or {}
    col1, col2 = st.columns(2)
    with col1:
        nom = st.text_input("Nom client", value=default.get("nom", ""), key=f"{key_prefix}_nom")
        secteur = st.text_input("Secteur / département", value=default.get("secteur", ""), key=f"{key_prefix}_secteur")
        type_compte = st.selectbox("Type de compte",
            ["Prospect", "Client", "Ancien client", "Grand compte", "AO / public"],
            index=idx(["Prospect", "Client", "Ancien client", "Grand compte", "AO / public"], default.get("type_compte", "Prospect")),
            key=f"{key_prefix}_type")
        telephone = st.text_input("Téléphone", value=default.get("telephone", ""), key=f"{key_prefix}_tel")
        email = st.text_input("Email", value=default.get("email", ""), key=f"{key_prefix}_mail")
        siret = st.text_input("SIRET", value=default.get("siret", ""), key=f"{key_prefix}_siret")
        naf = st.text_input("Code NAF", value=default.get("naf", ""), key=f"{key_prefix}_naf")
    with col2:
        adresse = st.text_input("Adresse", value=default.get("adresse", ""), key=f"{key_prefix}_adresse")
        ville = st.text_input("Ville", value=default.get("ville", ""), key=f"{key_prefix}_ville")
        code_postal = st.text_input("Code postal", value=default.get("code_postal", ""), key=f"{key_prefix}_cp")
        statut_client = st.selectbox("Statut client", ["Actif", "À relancer", "En sommeil"],
            index=idx(["Actif", "À relancer", "En sommeil"], default.get("statut_client", "Actif")), key=f"{key_prefix}_statut")
        potentiel = st.selectbox("Potentiel", ["Faible", "Moyen", "Fort"],
            index=idx(["Faible", "Moyen", "Fort"], default.get("potentiel", "Moyen"), 1), key=f"{key_prefix}_potentiel")
        concurrent_en_place = st.text_input("Concurrent en place", value=default.get("concurrent_en_place", ""), key=f"{key_prefix}_concurrent")
    st.markdown("#### Contacts clés")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Contact 1**")
        contact1_nom = st.text_input("Nom", value=default.get("contact1_nom", ""), key=f"{key_prefix}_c1_nom")
        contact1_fonction = st.text_input("Fonction", value=default.get("contact1_fonction", ""), key=f"{key_prefix}_c1_fonction")
        contact1_telephone = st.text_input("Téléphone", value=default.get("contact1_telephone", ""), key=f"{key_prefix}_c1_tel")
        contact1_email = st.text_input("Email", value=default.get("contact1_email", ""), key=f"{key_prefix}_c1_mail")
    with c2:
        st.markdown("**Contact 2**")
        contact2_nom = st.text_input("Nom ", value=default.get("contact2_nom", ""), key=f"{key_prefix}_c2_nom")
        contact2_fonction = st.text_input("Fonction ", value=default.get("contact2_fonction", ""), key=f"{key_prefix}_c2_fonction")
        contact2_telephone = st.text_input("Téléphone ", value=default.get("contact2_telephone", ""), key=f"{key_prefix}_c2_tel")
        contact2_email = st.text_input("Email ", value=default.get("contact2_email", ""), key=f"{key_prefix}_c2_mail")
    notes = st.text_area("Notes", value=default.get("notes", ""), height=120, key=f"{key_prefix}_notes")
    return {
        "nom": nom.strip(), "secteur": secteur, "type_compte": type_compte, "adresse": adresse, "ville": ville,
        "code_postal": code_postal, "telephone": telephone, "email": email, "statut_client": statut_client,
        "potentiel": potentiel, "concurrent_en_place": concurrent_en_place, "siret": siret, "naf": naf,
        "notes": notes, "contact1_nom": contact1_nom, "contact1_fonction": contact1_fonction,
        "contact1_telephone": contact1_telephone, "contact1_email": contact1_email, "contact2_nom": contact2_nom,
        "contact2_fonction": contact2_fonction, "contact2_telephone": contact2_telephone, "contact2_email": contact2_email
    }


def affaire_form(clients_df, default=None, key_prefix="affaire"):
    default = default or {}
    client_labels = ["— Aucun client —"] + [f"{row['nom']} (#{row['id']})" for _, row in clients_df.iterrows()]
    default_client_index = 0
    if default.get("client_id") not in (None, "", float("nan")):
        for pos, (_, row) in enumerate(clients_df.iterrows(), start=1):
            if int(row["id"]) == safe_int(default.get("client_id"), -1):
                default_client_index = pos
                break

    col1, col2, col3 = st.columns(3)
    with col1:
        client_choice = st.selectbox("Client lié", client_labels, index=default_client_index, key=f"{key_prefix}_client")
        priorite = st.selectbox("Priorité", PRIORITES, index=idx(PRIORITES, default.get("priorite", PRIORITES[1]), 1), key=f"{key_prefix}_priorite")
        date_creation = st.text_input("Date de création (vide = aujourd'hui)", value=display_date(default.get("date_creation")) or datetime.now().strftime("%d/%m/%Y"), key=f"{key_prefix}_date_creation")
        commercial_assigne = st.text_input("Commercial assigné", value=default.get("commercial_assigne", "Louis"), key=f"{key_prefix}_commercial")
        type_opportunite = st.selectbox("Type opportunité", TYPES_OPP, index=idx(TYPES_OPP, default.get("type_opportunite", TYPES_OPP[0])), key=f"{key_prefix}_type")
        statut = st.selectbox("Statut", STATUTS, index=idx(STATUTS, default.get("statut", STATUTS[0])), key=f"{key_prefix}_statut")
    with col2:
        gamme = st.selectbox("Gamme", GAMMES, index=idx(GAMMES, default.get("gamme", GAMMES[0])), key=f"{key_prefix}_gamme")
        carrosserie = st.selectbox("Carrosserie", CARROSSERIES, index=idx(CARROSSERIES, default.get("carrosserie", CARROSSERIES[0])), key=f"{key_prefix}_carrosserie")
        energie = st.selectbox("Énergie", ENERGIES, index=idx(ENERGIES, default.get("energie", ENERGIES[0])), key=f"{key_prefix}_energie")
        action_suivante = st.selectbox("Action suivante", ACTIONS, index=idx(ACTIONS, default.get("action_suivante", ACTIONS[0])), key=f"{key_prefix}_action")
        blocage_principal = st.selectbox("Blocage principal", BLOCAGES, index=idx(BLOCAGES, default.get("blocage_principal", BLOCAGES[0])), key=f"{key_prefix}_blocage")
        concurrent = st.text_input("Concurrent", value=default.get("concurrent", ""), key=f"{key_prefix}_concurrent")
    with col3:
        vn_parc = st.text_input("VN / Parc", value=default.get("vn_parc", ""), key=f"{key_prefix}_vnparc")
        duree_mois = st.number_input("Durée (mois)", min_value=0, step=1, value=safe_int(default.get("duree_mois"), 0), key=f"{key_prefix}_duree")
        km_an = st.number_input("Km/an", min_value=0, step=1000, value=safe_int(default.get("km_an"), 0), key=f"{key_prefix}_km")
        loyer_mensuel = st.number_input("Loyer mensuel €", min_value=0.0, step=10.0, value=safe_float(default.get("loyer_mensuel"), 0.0), key=f"{key_prefix}_loyer")
        contrat_bdc = st.text_input("Contrat / BDC", value=default.get("contrat_bdc", ""), key=f"{key_prefix}_contrat")

    st.markdown("#### Dates facultatives")
    d1, d2, d3 = st.columns(3)
    with d1:
        date_envoi_proposition = st.text_input("Date envoi proposition", value=display_date(default.get("date_envoi_proposition")), key=f"{key_prefix}_date_envoi")
    with d2:
        date_prochaine_action = st.text_input("Date prochaine action", value=display_date(default.get("date_prochaine_action")), key=f"{key_prefix}_date_action")
    with d3:
        deadline_ao = st.text_input("Deadline AO", value=display_date(default.get("deadline_ao")), key=f"{key_prefix}_deadline")

    notes = st.text_area("Notes", value=default.get("notes", ""), height=140, key=f"{key_prefix}_notes")

    selected_client_id = None
    if client_choice != "— Aucun client —":
        selected_client_id = int(client_choice.split("#")[-1].replace(")", ""))

    return {
        "client_id": selected_client_id,
        "priorite": priorite,
        "date_creation": parse_optional_date_str(date_creation) or datetime.now().strftime("%Y-%m-%d"),
        "commercial_assigne": commercial_assigne,
        "type_opportunite": type_opportunite,
        "gamme": gamme,
        "carrosserie": carrosserie,
        "energie": energie,
        "vn_parc": vn_parc,
        "duree_mois": safe_int(duree_mois, 0),
        "km_an": safe_int(km_an, 0),
        "loyer_mensuel": safe_float(loyer_mensuel, 0.0),
        "statut": statut,
        "action_suivante": action_suivante,
        "date_envoi_proposition": parse_optional_date_str(date_envoi_proposition),
        "blocage_principal": blocage_principal,
        "deadline_ao": parse_optional_date_str(deadline_ao),
        "date_prochaine_action": parse_optional_date_str(date_prochaine_action),
        "concurrent": concurrent,
        "contrat_bdc": contrat_bdc,
        "notes": notes
    }


def page_dashboard():
    st.title("Tableau de bord")
    affaires = fetch_affaires()
    today = datetime.now().strftime("%Y-%m-%d")
    ca_pipeline = 0.0 if affaires.empty else float(affaires["loyer_mensuel"].fillna(0).sum())
    affaires_chaudes = 0 if affaires.empty else int(((affaires["priorite"] == "🔥 Chaud") & (~affaires["statut"].isin(list(STATUTS_CLOTURES)))).sum())
    actions_du_jour = 0 if affaires.empty else int((affaires["date_prochaine_action"] == today).sum())
    retards = 0 if affaires.empty else int(((affaires["date_prochaine_action"].notna()) & (affaires["date_prochaine_action"] < today) & (~affaires["statut"].isin(list(STATUTS_CLOTURES)))).sum())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("CA pipeline mensuel", f"{ca_pipeline:,.0f} €".replace(",", " "))
    c2.metric("Affaires chaudes", affaires_chaudes)
    c3.metric("Actions du jour", actions_du_jour)
    c4.metric("Retards", retards)


def page_clients():
    st.title("Clients")
    onglet_creation, onglet_suivi = st.tabs(["Créer / modifier un client", "Suivi clients"])
    with onglet_creation:
        clients_df = fetch_clients()
        options = ["Nouveau client"] + [f"{row['nom']} (#{row['id']})" for _, row in clients_df.iterrows()]
        selected = st.selectbox("Choisir une fiche client", options, key="client_edit_select")
        current = None
        current_id = None
        if selected != "Nouveau client":
            current_id = int(selected.split("#")[-1].replace(")", ""))
            current = clients_df[clients_df["id"] == current_id].iloc[0].to_dict()

        with st.form("form_client_create_edit"):
            data = client_form(current, key_prefix="client_form")
            save_client = st.form_submit_button("💾 Enregistrer le client", use_container_width=True)

        if save_client:
            if not data["nom"]:
                st.error("Le nom client est obligatoire.")
            else:
                new_id = upsert_client(current_id, data)
                st.session_state["last_client_id"] = new_id
                st.success("Client enregistré.")
                st.rerun()

        if current_id is not None:
            delete_related = st.checkbox("Supprimer aussi ses affaires", key="delete_related_client")
            confirm = st.checkbox("Confirmer la suppression du client", key="confirm_delete_client")
            if st.button("🗑️ Supprimer le client", use_container_width=True, key="delete_client_btn", disabled=not confirm):
                delete_client(current_id, delete_related=delete_related)
                st.success("Client supprimé.")
                st.rerun()

    with onglet_suivi:
        clients_df = fetch_clients()
        if clients_df.empty:
            st.info("Aucun client pour le moment.")
            return
        labels = [f"{row['nom']} (#{row['id']})" for _, row in clients_df.iterrows()]
        choice = st.selectbox("Ouvrir une fiche client", labels, key="follow_client_select")
        client_id = int(choice.split("#")[-1].replace(")", ""))
        current = clients_df[clients_df["id"] == client_id].iloc[0].to_dict()

        with st.form("form_client_follow"):
            data = client_form(current, key_prefix="client_follow_form")
            save_follow = st.form_submit_button("💾 Enregistrer depuis le suivi", use_container_width=True)

        if save_follow:
            if not data["nom"]:
                st.error("Le nom client est obligatoire.")
            else:
                upsert_client(client_id, data)
                st.success("Client mis à jour.")
                st.rerun()

        delete_related2 = st.checkbox("Supprimer aussi ses affaires ", key="delete_related_client2")
        confirm2 = st.checkbox("Confirmer la suppression ", key="confirm_delete_client2")
        if st.button("🗑️ Supprimer cette fiche client", use_container_width=True, key="delete_client_follow_btn", disabled=not confirm2):
            delete_client(client_id, delete_related=delete_related2)
            st.success("Client supprimé.")
            st.rerun()


def page_affaires():
    st.title("Affaires")
    clients_df = fetch_clients()
    onglet_creation, onglet_suivi = st.tabs(["Créer / modifier une affaire", "Suivi affaires"])

    with onglet_creation:
        affaires_df = fetch_affaires()
        options = ["Nouvelle affaire"] + [f"#{row['id']} - {(row.get('client_nom') or 'Sans client')} - {row.get('statut')}" for _, row in affaires_df.iterrows()]
        selected = st.selectbox("Choisir un dossier affaire", options, key="affaire_edit_select")
        current = None
        current_id = None
        if selected != "Nouvelle affaire":
            current_id = int(selected.split(" - ")[0].replace("#", ""))
            current = affaires_df[affaires_df["id"] == current_id].iloc[0].to_dict()

        with st.form("form_affaire_create_edit"):
            data = affaire_form(clients_df, current, key_prefix="affaire_form")
            save_affaire = st.form_submit_button("💾 Enregistrer l'affaire", use_container_width=True)

        if save_affaire:
            new_id = upsert_affaire(current_id, data)
            st.session_state["last_affaire_id"] = new_id
            st.success(f"Affaire enregistrée (ID #{new_id}).")
            st.rerun()

        if current_id is not None:
            confirm = st.checkbox("Confirmer la suppression de l'affaire", key="confirm_delete_affaire")
            if st.button("🗑️ Supprimer l'affaire", use_container_width=True, key="delete_affaire_btn", disabled=not confirm):
                delete_affaire(current_id)
                st.success("Affaire supprimée.")
                st.rerun()

    with onglet_suivi:
        affaires_df = fetch_affaires()
        if affaires_df.empty:
            st.info("Aucune affaire pour le moment.")
            return

        if "last_affaire_id" in st.session_state:
            last_id = st.session_state["last_affaire_id"]
            default_index = 0
            label_list = [f"#{row['id']} - {(row.get('client_nom') or 'Sans client')} - {row.get('statut')}" for _, row in affaires_df.iterrows()]
            for i, (_, row) in enumerate(affaires_df.iterrows()):
                if int(row["id"]) == int(last_id):
                    default_index = i
                    break
        else:
            default_index = 0
            label_list = [f"#{row['id']} - {(row.get('client_nom') or 'Sans client')} - {row.get('statut')}" for _, row in affaires_df.iterrows()]

        selected = st.selectbox("Ouvrir un dossier affaire", label_list, index=default_index, key="follow_affaire_select")
        affaire_id = int(selected.split(" - ")[0].replace("#", ""))
        current = affaires_df[affaires_df["id"] == affaire_id].iloc[0].to_dict()

        st.markdown(f"""
        <div class="card">
            <b>{current.get('client_nom') or 'Sans client'}</b><br>
            {current.get('gamme','')} - {current.get('carrosserie','')} - {current.get('energie','')}<br>
            Statut : {current.get('statut','')}<br>
            Priorité : {current.get('priorite','')}
        </div>
        """, unsafe_allow_html=True)

        with st.form("form_affaire_follow"):
            data = affaire_form(clients_df, current, key_prefix="affaire_follow_form")
            save_follow_affaire = st.form_submit_button("💾 Enregistrer depuis le suivi", use_container_width=True)

        if save_follow_affaire:
            upsert_affaire(affaire_id, data)
            st.success("Affaire mise à jour.")
            st.rerun()

        confirm = st.checkbox("Confirmer la suppression du dossier", key="confirm_delete_affaire_follow")
        if st.button("🗑️ Supprimer ce dossier", use_container_width=True, key="delete_follow_affaire_btn", disabled=not confirm):
            delete_affaire(affaire_id)
            st.success("Affaire supprimée.")
            st.rerun()

        st.markdown("### Liste rapide")
        filtre = st.text_input("Filtrer les affaires (client / statut)", key="affaire_filter")
        temp = affaires_df.copy()
        if filtre.strip():
            mask = temp["client_nom"].fillna("").str.contains(filtre, case=False) | temp["statut"].fillna("").str.contains(filtre, case=False)
            temp = temp[mask]
        for _, row in temp.head(20).iterrows():
            total_est = safe_int(row.get("duree_mois"), 0) * safe_float(row.get("loyer_mensuel"), 0.0)
            st.markdown(f"""
            <div class="card">
                <b>#{row['id']} - {row.get('client_nom') or 'Sans client'}</b><br>
                {row.get('gamme','')} - {row.get('carrosserie','')} - {row.get('energie','')}<br>
                Statut : {row.get('statut','')} | Priorité : {row.get('priorite','')}<br>
                Total estimé : {total_est:,.0f} € | Prochaine action : {display_date(row.get('date_prochaine_action'))}
            </div>
            """.replace(",", " "), unsafe_allow_html=True)


def page_stats():
    st.title("Statistiques & pilotage")
    affaires = fetch_affaires()
    if affaires.empty:
        st.info("Pas encore de données.")
        return
    affaires["total_estime"] = affaires["duree_mois"].fillna(0) * affaires["loyer_mensuel"].fillna(0)
    c1, c2, c3 = st.columns(3)
    c1.metric("Affaires totales", int(len(affaires)))
    c2.metric("Affaires gagnées", int((affaires["statut"] == "Gagné").sum()))
    c3.metric("Montant total estimé", f"{affaires['total_estime'].sum():,.0f} €".replace(",", " "))
    st.dataframe(
        affaires[["id", "client_nom", "gamme", "carrosserie", "energie", "statut", "total_estime"]]
        .rename(columns={"id":"ID", "client_nom":"Client", "gamme":"Gamme", "carrosserie":"Carrosserie", "energie":"Énergie", "statut":"Statut", "total_estime":"Montant total"}),
        use_container_width=True,
        hide_index=True
    )


def main():
    init_db()
    menu = st.sidebar.radio("Navigation", ["🏠 Tableau de bord", "📂 Affaires", "🏢 Clients", "📊 Statistiques"])
    if menu == "🏠 Tableau de bord":
        page_dashboard()
    elif menu == "📂 Affaires":
        page_affaires()
    elif menu == "🏢 Clients":
        page_clients()
    else:
        page_stats()


if __name__ == "__main__":
    main()
