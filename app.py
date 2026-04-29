import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import plotly.express as px
from datetime import datetime
import re

# --- CONFIGURATION ---
st.set_page_config(page_title="Fit-Collect Pro", page_icon="🏋️‍♂️", layout="wide")

# --- LISTE DES EXERCICES (Ajout de 18 exercices + Option Personnalisée) ---
EXERCICES_LIST = {
    "Pectoraux": ["Développé couché", "Développé incliné", "Écartés couchés", "Dips", "Pompes", "Chest Press", "Pec Deck", "Pull-over", "Écartés poulie"],
    "Dos": ["Tractions", "Tirage horizontal", "Tirage vertical", "Rowing barre", "Lumberjack", "Deadlift", "Facepull", "Rowing haltère", "Good Morning"],
    "Jambes": ["Squat", "Presse à cuisses", "Fentes", "Leg Extension", "Leg Curl", "Hack Squat", "Mollets debout", "Fentes bulgares", "Hip Thrust", "Soulevé de terre jambes tendues"],
    "Épaules": ["Développé militaire", "Élévations latérales", "Oiseau", "Arnold Press", "Shrugs", "Développé haltères", "Élévations frontales"],
    "Bras": ["Curl barre", "Hammer Curl", "Extension poulie", "Barre au front", "Curl Larry Scott", "Dips banc", "Kickback haltère", "Curl incliné"],
    "Abdos": ["Crunch", "Gainage", "Lying Leg Raise", "Russian Twist", "Mountain Climbers", "Relevé de jambes suspendu", "Roulette abdo"],
    "Cardio & HIIT": ["Burpees", "Jump Squats", "Corde à sauter", "Box Jumps", "Kettlebell Swing", "Battle Rope"],
    "Autre": ["EXERCICE PERSONNALISÉ"]
}

PAYS_DATA = {
    "Cameroun": {"code": "+237", "regex": r"^\d{9}$"},
    "France": {"code": "+33", "regex": r"^\d{9}$"},
    "Côte d'Ivoire": {"code": "+225", "regex": r"^\d{10}$"},
    "Sénégal": {"code": "+221", "regex": r"^\d{9}$"},
    "Canada": {"code": "+1", "regex": r"^\d{10}$"}
}

# --- CSS : DESIGN & FIX MOBILE ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stApp {
        background-image: url("https://images.unsplash.com/photo-1534438327276-14e5300c3a48?q=80&w=2070&auto=format&fit=crop");
        background-attachment: fixed; background-size: cover;
    }
    [data-testid="stSidebarCollapsedControl"] {
        display: block !important; background-color: #e67e22 !important;
        color: white !important; border-radius: 8px !important;
        left: 10px !important; top: 10px !important;
    }
    .stTabs, .stForm, .stDataFrame {
        background-color: rgba(255, 255, 255, 0.95) !important;
        padding: 20px; border-radius: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('fit_pro_v4.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY, nom TEXT, prenom TEXT, 
                phone TEXT, password TEXT, sex TEXT, pays TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS entrainements (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, 
                date TEXT, exercice TEXT, series INTEGER, reps INTEGER, 
                poids REAL, repos INTEGER, intensite TEXT, notes TEXT, volume REAL)''')
    conn.commit()
    return conn, c

conn, c = init_db()

def hash_pwd(pwd):
    return hashlib.sha256(str.encode(pwd)).hexdigest()

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_info = None

def main():
    if not st.session_state.authenticated:
        st.title("🏋️‍♂️ Fit-Collect Pro")
        tab_login, tab_signup = st.tabs(["Connexion", "S'inscrire"])

        with tab_login:
            with st.form("form_login"):
                l_nom = st.text_input("Nom")
                l_prenom = st.text_input("Prénom")
                l_pw = st.text_input("Mot de passe", type='password')
                if st.form_submit_button("Se connecter"):
                    c.execute('SELECT * FROM users WHERE nom=? AND prenom=? AND password=?', (l_nom, l_prenom, hash_pwd(l_pw)))
                    user = c.fetchone()
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user_info = list(user)
                        st.rerun()
                    else: st.error("Identifiants incorrects.")

        with tab_signup:
            with st.form("form_signup"):
                col1, col2 = st.columns(2)
                with col1:
                    s_nom, s_prenom = st.text_input("Nom"), st.text_input("Prénom")
                    s_email, s_sex = st.text_input("Email"), st.selectbox("Sexe", ["Masculin", "Féminin"])
                with col2:
                    s_pays = st.selectbox("Nationalité", list(PAYS_DATA.keys()))
                    s_phone = st.text_input(f"Téléphone ({PAYS_DATA[s_pays]['code']})")
                    s_pw = st.text_input("Mot de passe", type='password')
                if st.form_submit_button("S'inscrire"):
                    if re.match(PAYS_DATA[s_pays]["regex"], s_phone):
                        try:
                            c.execute('INSERT INTO users VALUES (?,?,?,?,?,?,?)', 
                                     (s_email, s_nom, s_prenom, f"{PAYS_DATA[s_pays]['code']} {s_phone}", hash_pwd(s_pw), s_sex, s_pays))
                            conn.commit()
                            st.success("Compte créé ! Connectez-vous.")
                        except: st.error("Email déjà utilisé.")
                    else: st.error("Format numéro invalide.")

    else:
        u_email = st.session_state.user_info[0]
        st.sidebar.title(f"💪 {st.session_state.user_info[2]}")
        menu = st.sidebar.selectbox("Navigation", ["Journal d'entraînement", "Mon Profil", "Déconnexion"])

        if menu == "Déconnexion":
            st.session_state.authenticated = False
            st.rerun()

        elif menu == "Mon Profil":
            st.header("⚙️ Paramètres du Profil")
            with st.form("edit_user"):
                u_nom = st.text_input("Nom", value=st.session_state.user_info[1])
                u_pre = st.text_input("Prénom", value=st.session_state.user_info[2])
                u_tel = st.text_input("Téléphone", value=st.session_state.user_info[3])
                u_pass = st.text_input("Nouveau mot de passe (laisser vide pour garder)", type="password")
                if st.form_submit_button("Mettre à jour mon profil"):
                    if u_pass:
                        c.execute('UPDATE users SET nom=?, prenom=?, phone=?, password=? WHERE email=?', (u_nom, u_pre, u_tel, hash_pwd(u_pass), u_email))
                    else:
                        c.execute('UPDATE users SET nom=?, prenom=?, phone=? WHERE email=?', (u_nom, u_pre, u_tel, u_email))
                    conn.commit()
                    st.success("Profil mis à jour !")

        elif menu == "Journal d'entraînement":
            st.header("📝 Journal des Séances")
            t_saisie, t_analyse, t_modif = st.tabs(["📥 Saisie", "🥧 Analyse", "🛠️ Modifier / Supprimer"])

            with t_saisie:
                with st.form("add_workout"):
                    cat = st.selectbox("Groupe Musculaire", list(EXERCICES_LIST.keys()))
                    ex_choice = st.selectbox("Exercice", EXERCICES_LIST[cat])
                    
                    # Possibilité de saisir soi-même l'exercice
                    custom_ex = st.text_input("Nom de l'exercice personnalisé (si non listé)") if ex_choice == "EXERCICE PERSONNALISÉ" else ""
                    final_ex = custom_ex if ex_choice == "EXERCICE PERSONNALISÉ" else ex_choice
                    
                    colA, colB, colC = st.columns(3)
                    with colA:
                        ser = st.number_input("Séries", 1, 20, 4)
                        pds = st.number_input("Poids (kg)", 0.0, 500.0, 50.0)
                    with colB:
                        rep = st.number_input("Répétitions", 1, 100, 10)
                        repo = st.number_input("Repos (sec)", 0, 600, 90)
                    with colC:
                        intense = st.select_slider("Intensité (RPE)", options=["Facile", "Modéré", "Difficile", "Échec"])
                    
                    note = st.text_area("Notes")
                    if st.form_submit_button("Enregistrer"):
                        if ex_choice == "EXERCICE PERSONNALISÉ" and not custom_ex:
                            st.error("Veuillez entrer un nom pour votre exercice personnalisé.")
                        else:
                            vol = ser * rep * pds
                            c.execute('''INSERT INTO entrainements 
                                        (user_email, date, exercice, series, reps, poids, repos, intensite, notes, volume) 
                                        VALUES (?,?,?,?,?,?,?,?,?,?)''',
                                     (u_email, datetime.now().strftime("%d/%m/%Y %H:%M"), final_ex, ser, rep, pds, repo, intense, note, vol))
                            conn.commit()
                            st.success("Séance ajoutée !")

            with t_analyse:
                c.execute('SELECT date, exercice, series, reps, poids, repos, intensite, volume, notes FROM entrainements WHERE user_email=?', (u_email,))
                data = c.fetchall()
                if data:
                    df = pd.DataFrame(data, columns=["Date", "Exercice", "Séries", "Reps", "Poids (kg)", "Repos (s)", "Intensité", "Volume", "Notes"])
                    
                    # Graphique
                    st.subheader("Répartition du Volume")
                    st.plotly_chart(px.pie(df, values='Volume', names='Exercice', hole=0.4), use_container_width=True)
                    
                    # TABLEAU DE TOUTES LES DONNÉES SAISIES
                    st.subheader("Historique Complet des Données")
                    st.dataframe(df, use_container_width=True)
                else: st.info("Aucune donnée.")

            with t_modif:
                c.execute('SELECT id, date, exercice, series, reps, poids, repos, intensite, notes FROM entrainements WHERE user_email=?', (u_email,))
                items = c.fetchall()
                if items:
                    options = {f"ID:{i[0]} | {i[2]} ({i[1]})": i for i in items}
                    sel_key = st.selectbox("Sélectionnez la séance à modifier", list(options.keys()))
                    curr = options[sel_key]
                    
                    st.write("---")
                    with st.form("edit_entry"):
                        col1, col2 = st.columns(2)
                        with col1:
                            e_ser = st.number_input("Séries", value=curr[3])
                            e_rep = st.number_input("Répétitions", value=curr[4])
                            e_pds = st.number_input("Poids (kg)", value=curr[5])
                        with col2:
                            e_repo = st.number_input("Repos (sec)", value=curr[6])
                            e_intense = st.select_slider("Intensité", options=["Facile", "Modéré", "Difficile", "Échec"], value=curr[7])
                        
                        e_note = st.text_area("Notes", value=curr[8])
                        
                        if st.form_submit_button("💾 Mettre à jour"):
                            new_vol = e_ser * e_rep * e_pds
                            c.execute('''UPDATE entrainements SET series=?, reps=?, poids=?, repos=?, intensite=?, notes=?, volume=? 
                                         WHERE id=?''', (e_ser, e_rep, e_pds, e_repo, e_intense, e_note, new_vol, curr[0]))
                            conn.commit()
                            st.success("Mise à jour réussie !")
                            st.rerun()
                    
                    if st.button("🗑️ Supprimer"):
                        c.execute('DELETE FROM entrainements WHERE id=?', (curr[0],))
                        conn.commit()
                        st.rerun()
                else: st.info("Aucune séance.")

if __name__ == '__main__':
    main()