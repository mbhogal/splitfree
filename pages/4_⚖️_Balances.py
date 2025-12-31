import streamlit as st
import pandas as pd
from database import get_user_groups, get_group_expenses, get_group_members

if "user_id" not in st.session_state:
    st.switch_page("login.py")

st.title("⚖️ Group Balances")

groups = get_user_groups(st.session_state.user_id)

if groups.empty:
    st.info("You haven't joined any groups yet.")
    st.stop()

group_name = st.selectbox("Select Group", groups["name"])
group_id = groups[groups["name"] == group_name]["id"].iloc[0]

# Get all expenses in the group
expenses_df = get_group_expenses(group_id)

if expenses_df.empty:
    st.info("No expenses in this group yet — add some on the Add Expense page!")
    st.stop()

# Get unique expenses (groupby to avoid duplicates from splits)
unique_expenses = expenses_df.groupby('id').agg({
    'amount': 'first',
    'payer_id': 'first'
}).reset_index()

# Total spent
total_spent = unique_expenses['amount'].sum()

# Current number of members
members = get_group_members(group_id)
num_members = len(members)

fair_share = total_spent / num_members if num_members > 0 else 0

# How much each person paid (using unique)
paid_by = unique_expenses.groupby('payer_id')['amount'].sum().to_dict()

# Build balances for all members
balance_data = []
for _, member in members.iterrows():
    user_id = member['id']
    name = member['name']
    paid = paid_by.get(user_id, 0.0)
    net = paid - fair_share
    rounded_net = round(net, 2)
    balance_data.append({
        "Member": name,
        "Paid": f"${round(paid, 2):.2f}",
        "Fair Share": f"${round(fair_share, 2):.2f}",
        "Net Balance": rounded_net
    })

balances_df = pd.DataFrame(balance_data)

# Display styled table
st.subheader(f"Balances in **{group_name}** (Equal Sharing Among All {num_members} Members)")

def color_net(val):
    if val > 0:
        return "color: green; font-weight: bold"
    elif val < 0:
        return "color: red; font-weight: bold"
    else:
        return "color: gray; font-weight: bold"

styled = balances_df.style.format({"Net Balance": "${:.2f}"}).applymap(color_net, subset=['Net Balance'])

st.dataframe(styled, use_container_width=True, hide_index=True)

# Your personal summary
your_row = balances_df[balances_df["Member"] == st.session_state.name]
if not your_row.empty:
    your_net = your_row["Net Balance"].iloc[0]
    if your_net > 0:
        st.success(f"You are owed ${your_net:.2f} in this group")
    elif your_net < 0:
        st.warning(f"You owe ${abs(your_net):.2f} in this group")
    else:
        st.success("You're all settled in this group!")

st.caption("All balances are calculated with true equal sharing — everyone contributes the same total amount, regardless of when they joined.")