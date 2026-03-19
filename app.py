# VERSION V6 - EDIT INLINE (simplifiée stable)

import streamlit as st

st.set_page_config(page_title="CRM Louis", layout="wide")

if "affaires" not in st.session_state:
    st.session_state.affaires = [
        {"client": "HANDY UP", "statut": "Relance", "montant": 740, "gamme":"VU","carrosserie":"FRIGO","energie":"B7"},
        {"client": "CRISTEL", "statut": "Proposition", "montant": 1200, "gamme":"GL","carrosserie":"SEC","energie":"B100"}
    ]

if "clients" not in st.session_state:
    st.session_state.clients = [
        {"nom":"CRISTEL","siret":"","naf":""},
        {"nom":"HANDY UP","siret":"","naf":""}
    ]

menu = st.sidebar.radio("Menu",["Suivi affaires","Suivi clients"])

# ---------------- AFFAIRES ----------------
if menu == "Suivi affaires":
    st.title("Suivi des affaires")

    noms = [a["client"] for a in st.session_state.affaires]
    choix = st.selectbox("Choisir une affaire", noms)

    affaire = next(a for a in st.session_state.affaires if a["client"] == choix)

    st.subheader("Modifier l'affaire")

    client = st.text_input("Client", valeur:=affaire["client"])
    statut = st.selectbox("Statut", ["Définition","Proposition","Relance","Gagné","Perdu"], index=0)
    montant = st.number_input("Montant", value=int(affaire["montant"]))

    gamme = st.selectbox("Gamme", ["GL","VU","REM"])
    carrosserie = st.selectbox("Carrosserie", ["FRIGO","HYDRAU","SEC","TRR","AUTRE"])
    energie = st.selectbox("Énergie", ["B7","B100","B100 FLEXIBLE","E-TECH"])

    if st.button("💾 Enregistrer modifications"):
        affaire["client"] = client
        affaire["statut"] = statut
        affaire["montant"] = montant
        affaire["gamme"] = gamme
        affaire["carrosserie"] = carrosserie
        affaire["energie"] = energie
        st.success("Modifié")

# ---------------- CLIENTS ----------------
if menu == "Suivi clients":
    st.title("Suivi des clients")

    noms = sorted([c["nom"] for c in st.session_state.clients])
    choix = st.selectbox("Choisir un client", noms)

    client_data = next(c for c in st.session_state.clients if c["nom"] == choix)

    st.subheader("Modifier le client")

    nom = st.text_input("Nom", value=client_data["nom"])
    siret = st.text_input("SIRET", value=client_data["siret"])
    naf = st.text_input("Code NAF", value=client_data["naf"])

    if st.button("💾 Enregistrer client"):
        client_data["nom"] = nom
        client_data["siret"] = siret
        client_data["naf"] = naf
        st.success("Client modifié")
