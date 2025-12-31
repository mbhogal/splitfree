import streamlit as st
from auth import register, login
from database import init_db

init_db()  # Ensure DB ready

st.set_page_config(page_title="SplitFree", layout="centered")

if "user_id" in st.session_state:
    st.switch_page("pages/1_📊_Dashboard.py")  # Redirect if already logged in

st.title("💸 SplitFree")
st.subheader("Split expenses with friends/roommates — free forever!")

tab1, tab2 = st.tabs(["Login", "Register"])

with tab1:
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            user = login(username, password)
            if user:
                st.session_state.user_id = user[0]
                st.session_state.name = user[1]
                st.session_state.username = username
                st.success(f"Welcome, {user[1]}!")
                st.switch_page("pages/1_📊_Dashboard.py")
            else:
                st.error("Invalid username/password")

with tab2:
    with st.form("register_form"):
        new_name = st.text_input("Your Name")
        new_username = st.text_input("Username")
        new_email = st.text_input("Email", placeholder="you@example.com")
        new_password = st.text_input("Password", type="password")
        if st.form_submit_button("Register"):
            if not new_name.strip() or not new_username.strip() or not new_email.strip() or not new_password:
                st.error("All fields are required!")
            elif register(new_username, new_name, new_email, new_password):
                st.success("Registered successfully! Please login.")
            else:
                st.error("Username or email already taken")