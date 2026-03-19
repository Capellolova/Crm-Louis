
import os
import sqlite3
from datetime import datetime
import streamlit as st
import pandas as pd

APP_TITLE = "CRM Louis"
DB_PATH = "crm_louis.db"
DOCS_DIR = "documents_affaires"

GAMMES = ["GL", "VU", "REM"]
CARROSSERIES = ["FRIGO", "HYDRAU", "SEC", "TRR", "AUTRE"]
ENERGIES = ["B7", "B100", "B100 FLEXIBLE", "E-TECH"]
PRIORITES = ["🔥 Chaud", "⚠️ À suivre", "🧊 Froid"]
TYPES_OPP = ["Prospect", "Client existant", "Renouvellement", "AO / SAD"]
STATUTS = [
    "Définition du besoin", "Chiffrage en cours", "Rendez-vous", "Faire proposition",
    "Proposition envoyée", "Relance", "Contre-proposition",
    "Accord client", "Commande en cours", "Gagné", "Livré / Terminé", "Perdu", "Stand-by"
]
ACTIONS = [
    "Appeler", "Rendez-vous", "Relancer mail", "Envoyer proposition", "Refaire chiffrage",
    "Prendre RDV", "Attendre retour client", "Attendre validation interne",
    "Commander véhicule", "Signature contrat", "Récupération dépôt de garantie + SEPA",
    "Livraison", "Dossier terminé", "Clôturer gagné", "Clôturer perdu"
]
BLOCAGES = [
    "Prix", "Délais", "Pas de besoin immédiat", "Décision interne client",
    "Attente budget", "Concurrent en place", "Caractéristique véhicule",
    "Financement", "Validation hiérarchique", "Inconnu"
]
STATUTS_CLOTURES = {"Gagné", "Livré / Terminé", "Perdu"}

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
    os.makedirs(DOCS_DIR, exist_ok=True)
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
    cur.execute("""
    CREATE TABLE IF NOT EXISTS documents_affaires (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        affaire_id INTEGER NOT NULL,
        nom_document TEXT NOT NULL,
        type_document TEXT,
        chemin_fichier TEXT NOT NULL,
        created_at TEXT,
        FOREIGN KEY (affaire_id) REFERENCES affaires(id)
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


def fetch_documents_affaire(affaire_id):
    return fetch_df("""
        SELECT * FROM documents_affaires
        WHERE affaire_id = ?
        ORDER BY id DESC
    """, (affaire_id,))


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
        affaires = fetch_df("SELECT id FROM affaires WHERE client_id=?", (client_id,))
        for _, row in affaires.iterrows():
            delete_affaire(int(row["id"]))
    else:
        execute("UPDATE affaires SET client_id=NULL WHERE client_id=?", (client_id,))
    execute("DELETE FROM clients WHERE id=?", (client_id,))


def delete_affaire(affaire_id):
    docs = fetch_documents_affaire(affaire_id)
    for _, row in docs.iterrows():
        path = row.get("chemin_fichier")
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass
    execute("DELETE FROM documents_affaires WHERE affaire_id=?", (affaire_id,))
    execute("DELETE FROM affaires WHERE id=?", (affaire_id,))


def save_uploaded_document(affaire_id, uploaded_file, type_document):
    affaire_dir = os.path.join(DOCS_DIR, f"affaire_{affaire_id}")
    os.makedirs(affaire_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_name = uploaded_file.name
    safe_name = original_name.replace("/", "_").replace("\\", "_")
    filepath = os.path.join(affaire_dir, f"{timestamp}_{safe_name}")
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    execute("""
        INSERT INTO documents_affaires (affaire_id, nom_document, type_document, chemin_fichier, created_at)
        VALUES (?,?,?,?,?)
    """, (affaire_id, original_name, type_document, filepath, now_iso()))


def delete_document(doc_id):
    row = fetch_df("SELECT * FROM documents_affaires WHERE id=?", (doc_id,))
    if row.empty:
        return
    path = row.iloc[0]["chemin_fichier"]
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            pass
    execute("DELETE FROM documents_affaires WHERE id=?", (doc_id,))


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

    onglet_infos, onglet_notes = st.tabs(["Informations", "Notes"])
    with onglet_infos:
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

    with onglet_notes:
        notes = st.text_area("Notes de l'affaire", value=default.get("notes", ""), height=220, key=f"{key_prefix}_notes")

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


def section_documents(affaire_id, key_prefix="docs"):
    st.markdown("### Documents de l'affaire")
    st.caption("Tu peux y mettre ta proposition, le descriptif du VHL, ou tout autre document utile.")
    col1, col2 = st.columns([2, 1])
    with col1:
        uploaded = st.file_uploader("Ajouter un document", type=None, accept_multiple_files=False, key=f"{key_prefix}_uploader_{affaire_id}")
    with col2:
        type_doc = st.selectbox("Type de document", ["Proposition", "Descriptif VHL", "Bon de commande", "Autre"], key=f"{key_prefix}_type_{affaire_id}")

    if st.button("📎 Enregistrer le document", key=f"{key_prefix}_save_{affaire_id}", use_container_width=True):
        if uploaded is None:
            st.error("Ajoute d'abord un fichier.")
        else:
            save_uploaded_document(affaire_id, uploaded, type_doc)
            st.success("Document enregistré.")
            st.rerun()

    docs = fetch_documents_affaire(affaire_id)
    if docs.empty:
        st.info("Aucun document sur cette affaire.")
    else:
        for _, row in docs.iterrows():
            c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
            c1.write(f"**{row['nom_document']}**")
            c2.write(row["type_document"] or "—")
            c3.write(display_date(row["created_at"]))
            try:
                with open(row["chemin_fichier"], "rb") as f:
                    c4.download_button("Télécharger", data=f.read(), file_name=row["nom_document"], key=f"download_doc_{row['id']}")
            except Exception:
                c4.write("Fichier manquant")
            if st.button("🗑️ Supprimer", key=f"delete_doc_{row['id']}"):
                delete_document(int(row["id"]))
                st.success("Document supprimé.")
                st.rerun()


def page_actions_du_jour():
    st.title("Actions du jour")
    affaires = fetch_affaires()
    if affaires.empty:
        st.info("Aucune affaire pour le moment.")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    overdue = affaires[
        (affaires["date_prochaine_action"].notna()) &
        (affaires["date_prochaine_action"] < today) &
        (affaires["statut"] != "Perdu")
    ].copy()

    due_today = affaires[
        (affaires["date_prochaine_action"] == today) &
        (affaires["statut"] != "Perdu")
    ].copy()

    upcoming = affaires[
        (affaires["date_prochaine_action"].notna()) &
        (affaires["date_prochaine_action"] > today) &
        (affaires["statut"] != "Perdu")
    ].copy().sort_values("date_prochaine_action")

    c1, c2, c3 = st.columns(3)
    c1.metric("En retard", len(overdue))
    c2.metric("À faire aujourd'hui", len(due_today))
    c3.metric("À venir", len(upcoming))

    def render_actions(df, title):
        st.markdown(f"### {title}")
        if df.empty:
            st.info("Rien ici.")
            return
        for _, row in df.iterrows():
            st.markdown(f"""
            <div class="card">
                <b>#{row['id']} - {row.get('client_nom') or 'Sans client'}</b><br>
                {row.get('gamme','')} - {row.get('carrosserie','')} - {row.get('energie','')}<br>
                Statut : {row.get('statut','')}<br>
                Action : {row.get('action_suivante','')}<br>
                Date prochaine action : {display_date(row.get('date_prochaine_action'))}
            </div>
            """, unsafe_allow_html=True)

    render_actions(overdue.sort_values("date_prochaine_action"), "Actions en retard")
    render_actions(due_today.sort_values("id", ascending=False), "Actions du jour")
    render_actions(upcoming.head(15), "À venir")


def page_dashboard():
    st.title("Tableau de bord")
    affaires = fetch_affaires()
    today = datetime.now().strftime("%Y-%m-%d")
    en_cours = affaires[~affaires["statut"].isin(list(STATUTS_CLOTURES))].copy() if not affaires.empty else affaires
    ca_pipeline = 0.0 if en_cours.empty else float(en_cours["loyer_mensuel"].fillna(0).sum())
    affaires_chaudes = 0 if en_cours.empty else int((en_cours["priorite"] == "🔥 Chaud").sum())
    actions_du_jour = 0 if en_cours.empty else int((en_cours["date_prochaine_action"] == today).sum())
    retards = 0 if en_cours.empty else int(((en_cours["date_prochaine_action"].notna()) & (en_cours["date_prochaine_action"] < today)).sum())
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

        with st.form(f"form_client_create_edit_{current_id or 'new'}"):
            data = client_form(current, key_prefix=f"client_form_{current_id or 'new'}")
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
            delete_related = st.checkbox("Supprimer aussi ses affaires", key=f"delete_related_client_{current_id}")
            confirm = st.checkbox("Confirmer la suppression du client", key=f"confirm_delete_client_{current_id}")
            if st.button("🗑️ Supprimer le client", use_container_width=True, key=f"delete_client_btn_{current_id}", disabled=not confirm):
                delete_client(current_id, delete_related=delete_related)
                st.success("Client supprimé.")
                st.rerun()

    with onglet_suivi:
        clients_df = fetch_clients()
        if clients_df.empty:
            st.info("Aucun client pour le moment.")
            return

        filtre = st.text_input("Filtrer les clients", key="client_follow_filter")
        temp = clients_df.copy()
        if filtre.strip():
            temp = temp[temp["nom"].fillna("").str.contains(filtre, case=False)]

        st.markdown("### Liste des fiches clients")
        if temp.empty:
            st.info("Aucun client trouvé.")
            return

        labels = [f"{row['nom']} (#{row['id']})" for _, row in temp.iterrows()]
        selected = st.radio("Choisir un client", labels, key="follow_client_radio", label_visibility="collapsed")
        client_id = int(selected.split("#")[-1].replace(")", ""))
        current = clients_df[clients_df["id"] == client_id].iloc[0].to_dict()

        st.markdown("---")
        st.markdown(f"### Fiche client — {current['nom']}")
        st.caption(f"SIRET : {current.get('siret','') or '—'} | NAF : {current.get('naf','') or '—'}")

        with st.form(f"form_client_follow_{client_id}"):
            data = client_form(current, key_prefix=f"client_follow_form_{client_id}")
            save_follow = st.form_submit_button("💾 Enregistrer depuis le suivi", use_container_width=True)

        if save_follow:
            if not data["nom"]:
                st.error("Le nom client est obligatoire.")
            else:
                upsert_client(client_id, data)
                st.success("Client mis à jour.")
                st.rerun()

        delete_related2 = st.checkbox("Supprimer aussi ses affaires ", key=f"delete_related_client2_{client_id}")
        confirm2 = st.checkbox("Confirmer la suppression ", key=f"confirm_delete_client2_{client_id}")
        if st.button("🗑️ Supprimer cette fiche client", use_container_width=True, key=f"delete_client_follow_btn_{client_id}", disabled=not confirm2):
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

        with st.form(f"form_affaire_create_edit_{current_id or 'new'}"):
            data = affaire_form(clients_df, current, key_prefix=f"affaire_form_{current_id or 'new'}")
            save_affaire = st.form_submit_button("💾 Enregistrer l'affaire", use_container_width=True)

        if save_affaire:
            new_id = upsert_affaire(current_id, data)
            st.session_state["last_affaire_id"] = new_id
            st.success(f"Affaire enregistrée (ID #{new_id}).")
            st.rerun()

        if current_id is not None:
            section_documents(current_id, key_prefix=f"create_docs_{current_id}")
            confirm = st.checkbox("Confirmer la suppression de l'affaire", key=f"confirm_delete_affaire_{current_id}")
            if st.button("🗑️ Supprimer l'affaire", use_container_width=True, key=f"delete_affaire_btn_{current_id}", disabled=not confirm):
                delete_affaire(current_id)
                st.success("Affaire supprimée.")
                st.rerun()
        else:
            st.info("Enregistre d'abord l'affaire pour pouvoir ajouter des documents.")

    with onglet_suivi:
        affaires_df = fetch_affaires()
        if affaires_df.empty:
            st.info("Aucune affaire pour le moment.")
            return

        affaires_ouvertes_df = affaires_df[~affaires_df["statut"].isin(["Perdu", "Gagné", "Livré / Terminé"])].copy()
        affaires_gagnees_df = affaires_df[affaires_df["statut"] == "Gagné"].copy()
        affaires_terminees_df = affaires_df[affaires_df["statut"] == "Livré / Terminé"].copy()
        affaires_perdues_df = affaires_df[affaires_df["statut"] == "Perdu"].copy()

        filtre = st.text_input("Filtrer les dossiers (client / statut)", key="affaire_follow_filter")

        sous1, sous2, sous3, sous4 = st.tabs([
            f"Affaires en cours ({len(affaires_ouvertes_df)})",
            f"Affaires gagnées - suivi livraison / administratif ({len(affaires_gagnees_df)})",
            f"Affaires gagnées - dossiers terminés ({len(affaires_terminees_df)})",
            f"Affaires perdues archivées ({len(affaires_perdues_df)})"
        ])

        def apply_filter(df):
            temp = df.copy()
            if filtre.strip():
                mask = temp["client_nom"].fillna("").str.contains(filtre, case=False) | temp["statut"].fillna("").str.contains(filtre, case=False)
                temp = temp[mask]
            return temp





        def render_affaire_section(df, section_key, editable=True, show_documents=True):
            df = apply_filter(df)
            if df.empty:
                st.info("Aucun dossier ici.")
                return

            # Classement par date de prochaine action
            temp = df.copy()
            temp["_date_tri"] = pd.to_datetime(temp["date_prochaine_action"], errors="coerce")
            temp["_date_vide"] = temp["_date_tri"].isna()
            temp = temp.sort_values(by=["_date_vide", "_date_tri", "id"], ascending=[True, True, False])

            st.markdown("### Dossiers")
            selected_key = f"{section_key}_selected_affaire_id"

            for _, row in temp.iterrows():
                affaire_id = int(row["id"])
                total_est = safe_int(row.get("duree_mois"), 0) * safe_float(row.get("loyer_mensuel"), 0.0)

                st.markdown(f"""
                <div class="card">
                    <b>{row.get('client_nom') or 'Sans client'}</b><br>
                    {row.get('gamme','')} - {row.get('carrosserie','')} - {row.get('energie','')}<br>
                    Statut : {row.get('statut','')} | Priorité : {row.get('priorite','')}<br>
                    Total estimé : {total_est:,.0f} €<br>
                    Action : {row.get('action_suivante','')} | Prochaine action : {display_date(row.get('date_prochaine_action')) or '—'}
                </div>
                """.replace(",", " "), unsafe_allow_html=True)

                if st.button("Ouvrir la fiche", key=f"{section_key}_open_{affaire_id}", use_container_width=True):
                    current_selected = st.session_state.get(selected_key)
                    st.session_state[selected_key] = None if current_selected == affaire_id else affaire_id
                    st.rerun()

                if st.session_state.get(selected_key) == affaire_id:
                    current = row.to_dict()

                    st.markdown(f"#### Fiche dossier #{affaire_id} — {current.get('client_nom') or 'Sans client'}")
                    st.markdown(f"""
                    <div class="card">
                        <b>{current.get('client_nom') or 'Sans client'}</b><br>
                        {current.get('gamme','')} - {current.get('carrosserie','')} - {current.get('energie','')}<br>
                        Statut : {current.get('statut','')} | Priorité : {current.get('priorite','')}<br>
                        Action : {current.get('action_suivante','')} | Prochaine action : {display_date(current.get('date_prochaine_action')) or '—'}
                    </div>
                    """, unsafe_allow_html=True)

                    if editable:
                        with st.form(f"form_{section_key}_{affaire_id}"):
                            data = affaire_form(clients_df, current, key_prefix=f"{section_key}_form_{affaire_id}")
                            save_btn = st.form_submit_button("💾 Enregistrer les modifications", use_container_width=True)

                        if save_btn:
                            upsert_affaire(affaire_id, data)
                            st.success("Affaire mise à jour.")
                            st.rerun()

                        if show_documents:
                            section_documents(affaire_id, key_prefix=f"{section_key}_docs_{affaire_id}")

                        confirm = st.checkbox("Confirmer la suppression du dossier", key=f"{section_key}_delete_confirm_{affaire_id}")
                        if st.button("🗑️ Supprimer ce dossier", use_container_width=True, key=f"{section_key}_delete_btn_{affaire_id}", disabled=not confirm):
                            delete_affaire(affaire_id)
                            st.success("Affaire supprimée.")
                            st.rerun()
                    else:
                        st.markdown(f"""
                        <div class="card">
                            Concurrent : {current.get('concurrent','') or '—'}<br>
                            Contrat / BDC : {current.get('contrat_bdc','') or '—'}<br>
                            Notes : {current.get('notes','') or '—'}
                        </div>
                        """, unsafe_allow_html=True)

                    if st.button("❌ Fermer la fiche", key=f"{section_key}_close_{affaire_id}", use_container_width=True):
                        st.session_state[selected_key] = None
                        st.rerun()

                st.markdown("---")
        with sous1:
            render_affaire_section(affaires_ouvertes_df, "encours", editable=True, show_documents=True)
        with sous2:
            render_affaire_section(affaires_gagnees_df, "gagnees", editable=True, show_documents=True)
        with sous3:
            render_affaire_section(affaires_terminees_df, "terminees", editable=True, show_documents=True)
        with sous4:
            render_affaire_section(affaires_perdues_df, "perdues", editable=True, show_documents=True)

def page_stats():
    st.title("Statistiques & pilotage")
    affaires = fetch_affaires()
    if affaires.empty:
        st.info("Pas encore de données.")
        return

    affaires["total_estime"] = affaires["duree_mois"].fillna(0) * affaires["loyer_mensuel"].fillna(0)

    # Logique stats :
    # - Gagnées commercialement = Gagné + Livré / Terminé
    # - Perdues = Perdu
    # - Ouvertes = tout le reste
    affaires_gagnees_stats = affaires[affaires["statut"].isin(["Gagné", "Livré / Terminé"])].copy()
    affaires_gagnees_a_livrer = affaires[affaires["statut"] == "Gagné"].copy()
    affaires_gagnees_terminees = affaires[affaires["statut"] == "Livré / Terminé"].copy()
    affaires_perdues = affaires[affaires["statut"] == "Perdu"].copy()
    affaires_ouvertes = affaires[~affaires["statut"].isin(["Gagné", "Livré / Terminé", "Perdu"])].copy()

    # Montant total estimé = toutes les affaires sauf perdues
    affaires_en_cours = affaires[affaires["statut"] != "Perdu"].copy()

    taux_transfo = 0
    total_cloturees = len(affaires_gagnees_stats) + len(affaires_perdues)
    if total_cloturees > 0:
        taux_transfo = round((len(affaires_gagnees_stats) / total_cloturees) * 100, 1)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Affaires totales", int(len(affaires)))
    c2.metric("Affaires ouvertes", int(len(affaires_ouvertes)))
    c3.metric("Taux de transformation", f"{taux_transfo} %")
    c4.metric("Montant total estimé", f"{affaires_en_cours['total_estime'].sum():,.0f} €".replace(",", " "))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Montant moyen / affaire ouverte", f"{(affaires_ouvertes['total_estime'].mean() if not affaires_ouvertes.empty else 0):,.0f} €".replace(",", " "))
    c6.metric("Affaires perdues", int(len(affaires_perdues)))
    c7.metric("Affaires gagnées total", int(len(affaires_gagnees_stats)))
    c8.metric("AO / SAD", int((affaires["type_opportunite"] == "AO / SAD").sum()))

    c9, c10 = st.columns(2)
    c9.metric("Gagnées à livrer / suivre", int(len(affaires_gagnees_a_livrer)))
    c10.metric("Gagnées terminées", int(len(affaires_gagnees_terminees)))

    st.markdown("### Répartition par gamme")
    rep = affaires_ouvertes.groupby("gamme", dropna=False).agg(
        nombre=("id", "count"),
        montant_total=("total_estime", "sum")
    ).reset_index()
    rep.columns = ["Gamme", "Nombre", "Montant total"]
    st.dataframe(rep, use_container_width=True, hide_index=True)

    st.markdown("### Répartition par statut")
    rep2 = affaires.groupby("statut", dropna=False).agg(nombre=("id", "count")).reset_index()
    rep2.columns = ["Statut", "Nombre"]
    st.dataframe(rep2, use_container_width=True, hide_index=True)

    st.markdown("### Blocages principaux")
    rep3 = affaires_ouvertes.groupby("blocage_principal", dropna=False).agg(nombre=("id", "count")).reset_index()
    rep3.columns = ["Blocage principal", "Nombre"]
    rep3 = rep3.sort_values("Nombre", ascending=False)
    st.dataframe(rep3, use_container_width=True, hide_index=True)

    st.markdown("### Répartition par type d'opportunité")
    rep4 = affaires_ouvertes.groupby("type_opportunite", dropna=False).agg(
        nombre=("id", "count"),
        montant_total=("total_estime", "sum")
    ).reset_index()
    rep4.columns = ["Type opportunité", "Nombre", "Montant total"]
    st.dataframe(rep4, use_container_width=True, hide_index=True)

    st.markdown("### Top 10 affaires ouvertes")
    top10 = affaires_ouvertes.sort_values("total_estime", ascending=False).head(10)
    st.dataframe(
        top10[["id", "client_nom", "gamme", "carrosserie", "energie", "statut", "priorite", "total_estime"]]
        .rename(columns={
            "id":"ID", "client_nom":"Client", "gamme":"Gamme", "carrosserie":"Carrosserie",
            "energie":"Énergie", "statut":"Statut", "priorite":"Priorité", "total_estime":"Montant total"
        }),
        use_container_width=True,
        hide_index=True
    )

    st.caption("Les stats commerciales comptent comme gagnées : Gagné + Livré / Terminé. Le montant total estimé exclut uniquement les affaires perdues.")


def main():
    init_db()
    menu = st.sidebar.radio(
        "Navigation",
        ["🏠 Tableau de bord", "📅 Actions du jour", "📂 Affaires", "🏢 Clients", "📊 Statistiques"]
    )
    if menu == "🏠 Tableau de bord":
        page_dashboard()
    elif menu == "📅 Actions du jour":
        page_actions_du_jour()
    elif menu == "📂 Affaires":
        page_affaires()
    elif menu == "🏢 Clients":
        page_clients()
    else:
        page_stats()


if __name__ == "__main__":
    main()
