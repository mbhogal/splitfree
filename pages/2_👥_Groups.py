import streamlit as st
import sqlite3
import random
import string
import pandas as pd
from database import DB_FILE, get_user_groups

if "user_id" not in st.session_state:
    st.switch_page("login.py")

st.title("👥 Groups")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🆕 Create New Group")
    with st.form("create_group"):
        group_name = st.text_input("Group Name")
        if st.form_submit_button("Create"):
            if not group_name.strip():
                st.error("Enter a name!")
            else:
                invite_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("INSERT INTO groups (name, creator_id, invite_code) VALUES (?, ?, ?)",
                          (group_name, st.session_state.user_id, invite_code))
                group_id = c.lastrowid
                c.execute("INSERT OR IGNORE INTO group_members (group_id, user_id) VALUES (?, ?)",
                          (group_id, st.session_state.user_id))
                conn.commit()
                conn.close()
                st.success(f"Created **{group_name}**!")
                st.info(f"Invite Code: `{invite_code}`")
                st.balloons()
                st.rerun()  # Refresh to show new group immediately

with col2:
    st.subheader("🔑 Join Group")
    with st.form("join_group"):
        invite_code = st.text_input("Invite Code").strip().upper()
        if st.form_submit_button("Join"):
            if not invite_code:
                st.error("Enter code")
            else:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("SELECT id, name FROM groups WHERE invite_code = ?", (invite_code,))
                row = c.fetchone()
                if row:
                    group_id, g_name = row
                    try:
                        c.execute("INSERT OR IGNORE INTO group_members (group_id, user_id) VALUES (?, ?)",
                                  (group_id, st.session_state.user_id))
                        conn.commit()
                        st.success(f"Joined **{g_name}**!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.info("Already in this group")
                else:
                    st.error("Invalid code")
                conn.close()

# --- Your Groups with Group Code ---
st.markdown("---")
st.subheader("Your Groups")

groups = get_user_groups(st.session_state.user_id)

if groups.empty:
    st.info("No groups yet — create one or join using a code!")
else:
    # Fetch invite codes
    conn = sqlite3.connect(DB_FILE)
    codes_df = pd.read_sql("SELECT id, invite_code FROM groups", conn)
    conn.close()

    # Merge with groups
    groups_with_code = groups.merge(codes_df, on="id", how="left")

    # Display table
    display_df = groups_with_code[["name", "invite_code"]].copy()
    display_df = display_df.rename(columns={
        "name": "Group Name",
        "invite_code": "Group Code"
    })

    st.dataframe(display_df, use_container_width=True, hide_index=True)

# --- Invite Members Section ---
st.markdown("---")
st.subheader("📩 Invite Members to a Group")

if not groups.empty:
    # Use the same groups_with_code DataFrame for consistency
    selected_group_name = st.selectbox("Choose group to invite to", groups_with_code["name"], key="invite_group_select")
    
    # Get the row for the selected group
    selected_row = groups_with_code[groups_with_code["name"] == selected_group_name].iloc[0]
    current_invite_code = selected_row["invite_code"]

    # Show code
    st.code(current_invite_code, language=None)
    st.caption("Share this code — anyone with the app can join instantly")

    # Simulated email invite
    email_input = st.text_input("Or invite by email", placeholder="friend@example.com", key="email_input")
    if st.button("Send Invite Email"):
        email = email_input.strip()
        if email:
            st.success(f"Invite sent to **{email}**!")
            st.info(f"Message includes Group Code: `{current_invite_code}`")
            st.caption("In a full version, this would send a real email with a join link.")
        else:
            st.error("Please enter an email address")
else:
    st.info("Create a group first to start inviting members!")

st.caption("Group codes are permanent and unique — safe to share freely!")