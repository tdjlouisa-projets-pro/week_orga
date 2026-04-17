import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Alors, on part où ?", page_icon="✈️", layout="centered")

# --- CONNEXION GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        data = conn.read(ttl=0)
        if data is not None:
            data = data.dropna(how='all')
            # --- CORRECTION DU TYPE ICI ---
            if "commentaires" in data.columns:
                data["commentaires"] = data["commentaires"].astype(str).replace('nan', '')
            return data
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame(columns=["id", "nom", "ville", "lien", "description", "budget", "votes", "commentaires", "date_debut", "date_fin"])

df = load_data()

if df.empty or "id" not in df.columns:
    df = pd.DataFrame(columns=["id", "nom", "ville", "lien", "description", "budget", "votes", "commentaires", "date_debut", "date_fin"])

# --- DESIGN ---
st.markdown("""
    <style>
    .stApp { background-color: #F7F9FC; }
    .hero-section { text-align: center; padding: 30px; background: white; border-radius: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 20px;}
    .proposal-card { background: white; padding: 20px; border-radius: 15px; border: 1px solid #E1E8F0; margin-bottom: 5px; }
    .stButton>button { border-radius: 50px; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)

# --- NAVIGATION ---
tab_home, tab_proposer, tab_liste, tab_top = st.tabs(["🏠 Accueil", "✍️ Proposer", "📋 Liste", "🏆 Top"])

# --- ACCUEIL ---
with tab_home:
    st.markdown('<div class="hero-section"><h1>Alors, on part où ?</h1><p>Partagez vos idées de sorties,votez,commentez !</p></div>', unsafe_allow_html=True)

with tab_proposer:
    with st.form("form_main", clear_on_submit=True):
        nom_user = st.text_input("Ton prénom *")
        ville = st.text_input("Ville*")
        lien = st.text_input("Lien URL")
        d_deb = st.text_input("Date début")
        d_fin = st.text_input("Date fin")
        desc = st.text_area("Description")
        budget = st.number_input("Budget (€)", min_value=0)
        submitted = st.form_submit_button("PUBLIER")
        
        if submitted and nom_user and ville:
            new_row = pd.DataFrame([{
                "id": str(datetime.now().strftime("%Y%m%d%H%M%S")),
                "nom": str(nom_user),
                "ville": str(ville),
                "lien": str(lien),
                "description": str(desc),
                "budget": int(budget),
                "votes": 0,
                "commentaires": "",
                "date_debut": str(d_deb),
                "date_fin": str(d_fin)
            }])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(worksheet="propositions", data=updated_df)
            st.cache_data.clear()
            st.rerun()
# --- PAGE LISTE ---
with tab_liste:
    if df.empty:
        st.info("Aucun projet pour le moment.")
    else:
        # On s'assure que la colonne commentaires accepte le texte
        if "commentaires" in df.columns:
            df["commentaires"] = df["commentaires"].astype(str).replace('nan', '')

        for i, row in df.iterrows():
            with st.container():
                # 1. AFFICHAGE DES INFOS DE BASE
                st.subheader(f"📍 {row['ville']}")
                st.caption(f"Proposé par {row['nom']}")
                st.write(row['description'])
                st.write(f"**Budget :** {int(row['budget'])} €")

                # 2. AFFICHAGE DU LIEN (Ajouté ici)
                url = row.get('lien', '')
                if url and str(url).startswith('http'):
                    st.link_button("🌐 Consulter le lien", url)

                # 3. AFFICHAGE DE L'HISTORIQUE DES COMMENTAIRES (Archivage)
                current_comments = str(row['commentaires']) if pd.notnull(row['commentaires']) else ""
                if current_comments.strip() and current_comments != "nan":
                    with st.expander("💬 Voir les avis précédents"):
                        # On sépare les commentaires par le délimiteur "|"
                        for c in current_comments.split(" | "):
                            if c.strip():
                                st.write(f"• {c}")

                # 4. BARRE D'ACTIONS (Vote, Nouveau Commentaire, Modif, Suppr)
                col_vote, col_comm, col_val_comm, col_edit, col_delete = st.columns([1, 2.5, 0.8, 0.5, 0.5])
                
                # --- BOUTON VOTER ---
                with col_vote:
                    if st.button(f"👍 ({int(row['votes'])})", key=f"v_{row['id']}", use_container_width=True):
                        df.at[i, 'votes'] = int(row['votes']) + 1
                        conn.update(worksheet="propositions", data=df)
                        st.cache_data.clear()
                        st.rerun()

                # --- CHAMP NOUVEAU COMMENTAIRE ---
                with col_comm:
                    input_key = f"new_c_{row['id']}"
                    # On laisse le champ vide pour une nouvelle saisie
                    new_txt = st.text_input("Ajouter un avis", key=input_key, label_visibility="collapsed", placeholder="Ton avis...")

                # --- BOUTON OK (VALIDER L'ARCHIVAGE) ---
                with col_val_comm:
                    if st.button("OK", key=f"btn_c_{row['id']}", use_container_width=True):
                        if new_txt:
                            # Récupération de l'ancien texte pour concaténer
                            old_txt = str(row['commentaires']) if pd.notnull(row['commentaires']) else ""
                            
                            # On ajoute le nouveau texte avec un séparateur
                            if old_txt.strip() and old_txt != "nan" and old_txt != "":
                                updated_comments = f"{old_txt} | {new_txt}"
                            else:
                                updated_comments = new_txt
                            
                            # Mise à jour sécurisée
                            df["commentaires"] = df["commentaires"].astype(object)
                            df.at[i, 'commentaires'] = updated_comments
                            
                            conn.update(worksheet="propositions", data=df)
                            st.cache_data.clear()
                            
                            # On vide le champ dans le session_state
                            st.session_state[input_key] = ""
                            st.toast("Avis ajouté !")
                            st.rerun()

                # --- BOUTON MODIFIER ---
                with col_edit:
                    with st.popover("📝"):
                        st.write("Modifier le projet")
                        new_v = st.text_input("Ville", value=row['ville'], key=f"ev_{row['id']}")
                        new_d = st.text_area("Description", value=row['description'], key=f"ed_{row['id']}")
                        new_b = st.number_input("Budget (€)", value=int(row['budget']), key=f"eb_{row['id']}")
                        if st.button("Enregistrer", key=f"es_{row['id']}"):
                            df.at[i, 'ville'] = new_v
                            df.at[i, 'description'] = new_d
                            df.at[i, 'budget'] = new_b
                            conn.update(worksheet="propositions", data=df)
                            st.cache_data.clear()
                            st.rerun()

                # --- BOUTON SUPPRIMER ---
                with col_delete:
                    if st.button("🗑️", key=f"del_{row['id']}", help="Supprimer"):
                        st.session_state[f"confirm_delete_{row['id']}"] = True

                # Zone de confirmation de suppression
                if st.session_state.get(f"confirm_delete_{row['id']}", False):
                    st.warning("Supprimer ?")
                    c1, c2 = st.columns(2)
                    if c1.button("OUI", key=f"ok_{row['id']}", type="primary"):
                        df = df.drop(i)
                        conn.update(worksheet="propositions", data=df)
                        st.cache_data.clear()
                        st.session_state[f"confirm_delete_{row['id']}"] = False
                        st.rerun()
                    if c2.button("NON", key=f"no_{row['id']}"):
                        st.session_state[f"confirm_delete_{row['id']}"] = False
                        st.rerun()

                st.divider()
# --- PAGE TOP ---
with tab_top:
    if not df.empty:
        st.subheader("Classement actuel")
        top_df = df.sort_values("votes", ascending=False)
        for rank, (i, row) in enumerate(top_df.iterrows()):
            st.write(f"{rank+1}. **{row['ville']}** — {int(row['votes'])} votes")
