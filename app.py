import streamlit as st

st.set_page_config(page_title="CRM Louis", layout="wide")

# STYLE MOBILE
st.markdown("""
<style>
.block-container {
    padding: 1rem;
}

.card {
    background-color: #111827;
    padding: 1rem;
    border-radius: 12px;
    margin-bottom: 10px;
    color: white;
}

.big-button button {
    width: 100%;
    height: 50px;
    font-size: 16px;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# MENU
# -------------------------
menu = st.sidebar.radio(
    "Navigation",
    ["🏠 Accueil", "📂 Affaires", "🏢 Clients", "📊 Statistiques"]
)

# -------------------------
# ACCUEIL
# -------------------------
if menu == "🏠 Accueil":
    st.title("🏠 Aujourd’hui")

    st.markdown("### 🔥 Priorités")

    st.markdown('<div class="card">🔥 3 affaires chaudes</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">📞 2 relances à faire</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">📅 1 action aujourd’hui</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">⚠️ 1 affaire en retard</div>', unsafe_allow_html=True)

# -------------------------
# AFFAIRES
# -------------------------
elif menu == "📂 Affaires":
    st.title("📂 Affaires")

    # Exemple data (à remplacer par ta base)
    affaires = [
        {"client": "HANDY UP", "statut": "Proposition envoyée", "priorite": "🔥", "montant": "740€"},
        {"client": "YUDUM", "statut": "Relance", "priorite": "⚠️", "montant": "850€"},
    ]

    for a in affaires:
        st.markdown(f"""
        <div class="card">
            <b>{a['client']}</b><br>
            Statut : {a['statut']}<br>
            Priorité : {a['priorite']}<br>
            Montant : {a['montant']}
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📞 Appeler", key=a['client']+"call"):
                st.info("Appel lancé")

        with col2:
            if st.button("✉️ Relancer", key=a['client']+"mail"):
                st.info("Mail généré")

        with col3:
            if st.button("✏️ Modifier", key=a['client']+"edit"):
                st.info("Modification")

# -------------------------
# CLIENTS
# -------------------------
elif menu == "🏢 Clients":
    st.title("🏢 Clients")

    st.markdown("""
    <div class="card">
        <b>HANDY UP</b><br>
        Potentiel : Fort<br>
        Contact : Arnaud
    </div>
    """, unsafe_allow_html=True)

    st.button("📞 Appeler le contact", use_container_width=True)

# -------------------------
# STATS
# -------------------------
elif menu == "📊 Statistiques":
    st.title("📊 Statistiques & pilotage")

    col1, col2 = st.columns(2)

    col1.metric("💰 CA signé", "12 500 €")
    col2.metric("🔥 Affaires chaudes", "3")

    st.markdown("### Répartition par catégorie")
    st.write("Graphique à venir")
