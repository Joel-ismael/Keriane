import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import plotly.express as px
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Fit-Collect Pro", page_icon="🏋️‍♂️", layout="wide")

# --- CSS : ARRIÈRE-PLAN & FIX NAVIGATION MOBILE ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    .stApp {
        background-image: url("https://images.unsplash.com/photo-1534438327276-14e5300c3a48?q=80&w=2070&auto=format&fit=crop");
        background-attachment: fixed;
        background-size: cover;
    }
    
    [data-testid="stSidebarCollapsedControl"] {
        display: block !important;
        background-color: #e67e22 !important; /* Orange Sport */
        color: white !important;
        border-radius: 8px !important;
        left: 10px !important;
        top: 10px !important;
    }

    .stTabs, .stForm, [data-testid="stMetric"], .stDataFrame {
        background-color: rgba(255, 255, 255, 0.9) !important;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('fit_data_v1.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY, nom TEXT, prenom TEXT, 
                password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS entrainements (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, 
                date TEXT, exercice TEXT, series INTEGER, reps INTEGER, poids REAL, volume REAL)''')
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
        choix = st.sidebar.radio("Menu", ["Connexion", "Inscription"])
        
        if choix == "Inscription":
            with st.form("inscription"):
                n, p, e, pw = st.text_input("Nom"), st.text_input("Prénom"), st.text_input("Email"), st.text_input("Mot de passe", type='password')
                if st.form_submit_button("Créer mon compte"):
                    try:
                        c.execute('INSERT INTO users VALUES (?,?,?,?)', (e, n, p, hash_pwd(pw)))
                        conn.commit()
                        st.success("Compte fitness créé !")
                    except: st.error("Cet email est déjà utilisé.")
        else:
            with st.form("login"):
                email_log = st.text_input("Email")
                pw_log = st.text_input("Mot de passe", type='password')
                if st.form_submit_button("Se connecter"):
                    c.execute('SELECT * FROM users WHERE email=? AND password=?', (email_log, hash_pwd(pw_log)))
                    user = c.fetchone()
                    if user:
                        st.session_state.authenticated, st.session_state.user_info = True, list(user)
                        st.rerun()
                    else: st.error("Email ou mot de passe incorrect.")

    else:
        u_email = st.session_state.user_info[0]
        st.sidebar.title(f"💪 Coach {st.session_state.user_info[2]}")
        menu = st.sidebar.selectbox("Navigation", ["Journal d'entraînement", "Profil & Sécurité", "Déconnexion"])

        if menu == "Déconnexion":
            st.session_state.authenticated = False
            st.rerun()

        elif menu == "Profil & Sécurité":
            st.header("⚙️ Gestion du profil")
            with st.form("edit_profile"):
                new_nom = st.text_input("Nom", value=st.session_state.user_info[1])
                new_prenom = st.text_input("Prénom", value=st.session_state.user_info[2])
                new_pw = st.text_input("Nouveau mot de passe (optionnel)", type='password')
                if st.form_submit_button("Mettre à jour"):
                    if new_pw:
                        c.execute('UPDATE users SET nom=?, prenom=?, password=? WHERE email=?', (new_nom, new_prenom, hash_pwd(new_pw), u_email))
                    else:
                        c.execute('UPDATE users SET nom=?, prenom=? WHERE email=?', (new_nom, new_prenom, u_email))
                    conn.commit()
                    st.session_state.user_info[1], st.session_state.user_info[2] = new_nom, new_prenom
                    st.success("Profil mis à jour !")
                    st.rerun()

        elif menu == "Journal d'entraînement":
            st.header("📝 Suivi des performances")
            t1, t2, t3 = st.tabs(["📥 Ajouter une séance", "📈 Analyse", "🛠️ Modifier"])

            with t1:
                with st.form("add_workout"):
                    ex = st.selectbox("Exercice", ["Squat", "Développé couché", "Soulevé de terre", "Tractions"])
                    ser = st.number_input("Séries", 1, 10, 4)
                    rep = st.number_input("Répétitions", 1, 50, 10)
                    pds = st.number_input("Poids (kg)", 0.0, 500.0, 60.0)
                    if st.form_submit_button("Enregistrer"):
                        vol = ser * rep * pds # Calcul automatique du volume
                        c.execute('INSERT INTO entrainements (user_email, date, exercice, series, reps, poids, volume) VALUES (?,?,?,?,?,?,?)',
                                 (u_email, datetime.now().strftime("%d/%m/%Y"), ex, ser, rep, pds, vol))
                        conn.commit()
                        st.success(f"Séance de {ex} enregistrée ! Volume total : {vol} kg")

            with t2:
                c.execute('SELECT date, exercice, volume FROM entrainements WHERE user_email=?', (u_email,))
                data = c.fetchall()
                if data:
                    df = pd.DataFrame(data, columns=["Date", "Exercice", "Volume Total"])
                    st.dataframe(df, use_container_width=True)
                    fig = px.bar(df, x="Date", y="Volume Total", color="Exercice", title="Progression du Volume par Séance")
                    st.plotly_chart(fig, use_container_width=True)
                else: st.info("Aucune donnée enregistrée.")

            with t3:
                c.execute('SELECT id, date, exercice FROM entrainements WHERE user_email=?', (u_email,))
                rows = c.fetchall()
                if rows:
                    options = {f"{r[1]} - {r[2]} (ID:{r[0]})": r[0] for r in rows}
                    sel = st.selectbox("Sélectionner une séance", list(options.keys()))
                    if st.button("🗑️ Supprimer cette séance"):
                        c.execute('DELETE FROM entrainements WHERE id=?', (options[sel],))
                        conn.commit()
                        st.warning("Séance supprimée.")
                        st.rerun()

if __name__ == '__main__':
    main()