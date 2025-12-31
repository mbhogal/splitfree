import streamlit as st
from database import get_user_groups
from utils import calculate_balances

# Security: Redirect to login if not logged in
if "user_id" not in st.session_state:
    st.switch_page("login.py")

# Sidebar with user info and logout
st.sidebar.title(f"Hi, {st.session_state.name}! 👋")
st.sidebar.write(f"Logged in as {st.session_state.username}")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.switch_page("login.py")

st.title("📊 Dashboard")

# Fetch user's groups
groups = get_user_groups(st.session_state.user_id)

if groups.empty:
    st.info("👋 Welcome! You don't have any groups yet.")
    st.write("Go to the **Groups** page to create your first group or join one with an invite code.")
else:
    st.success(f"You are in {len(groups)} group(s)!")
    total_balance = 0.0

    for _, group in groups.iterrows():
        with st.expander(f"🏠 {group['name']}", expanded=False):
            balances = calculate_balances(group['id'])
            if balances.empty:
                st.write("No expenses yet in this group.")
            else:
                # Show balances table
                styled = balances.style.format({"balance": "${:.2f}"})
                st.dataframe(styled)

                # Your personal balance in this group
                your_row = balances[balances['name'] == st.session_state.name]
                if not your_row.empty:
                    your_balance = your_row['balance'].iloc[0]
                    total_balance += your_balance
                    if your_balance > 0:
                        st.success(f"You are owed ${your_balance:.2f} in this group")
                    elif your_balance < 0:
                        st.error(f"You owe ${abs(your_balance):.2f} in this group")
                    else:
                        st.info("You're all settled in this group!")

    # Overall total
    st.markdown("---")
    if total_balance > 0:
        st.success(f"🎉 Overall: You are owed ${total_balance:.2f} across all groups")
    elif total_balance < 0:
        st.warning(f"Overall: You owe ${abs(total_balance):.2f} across all groups")
    else:
        st.balloons()
        st.success("🎊 You're perfectly settled across all groups!")

st.markdown("---")
st.caption("Next steps: Create a group → Invite friends → Add expenses → Settle up!")