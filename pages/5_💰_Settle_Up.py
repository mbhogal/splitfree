import streamlit as st
import sqlite3
from datetime import date
import pandas as pd
from database import DB_FILE, get_user_groups, get_group_members, get_group_expenses

if "user_id" not in st.session_state:
    st.switch_page("login.py")

st.title("💰 Settle Up")

st.write("See who needs to pay whom to make everything even — based on true equal sharing among all current members.")

groups = get_user_groups(st.session_state.user_id)

if groups.empty:
    st.info("You need to be in a group first.")
    st.stop()

group_name = st.selectbox("Select Group", groups["name"])
group_id = groups[groups["name"] == group_name]["id"].iloc[0]

# Get members and expenses
members = get_group_members(group_id)
if members.empty:
    st.error("No members in group.")
    st.stop()

expenses_df = get_group_expenses(group_id)
if expenses_df.empty:
    st.info("No expenses yet — nothing to settle!")
    st.stop()

# Unique expenses for accurate totals
unique_expenses = expenses_df.groupby('id').agg({
    'amount': 'first',
    'payer_id': 'first'
}).reset_index()

total_spent = unique_expenses['amount'].sum()
num_members = len(members)
fair_share = total_spent / num_members

# Calculate net for each member
paid_by = unique_expenses.groupby('payer_id')['amount'].sum().to_dict()

balances = []
for _, member in members.iterrows():
    user_id = member['id']
    name = member['name']
    paid = paid_by.get(user_id, 0.0)
    net = paid - fair_share
    rounded_net = round(net, 2)
    balances.append({"name": name, "net": rounded_net})

# Separate debtors (owe) and creditors (owed)
debtors = [b for b in balances if b["net"] < 0]
creditors = [b for b in balances if b["net"] > 0]
settled = [b for b in balances if b["net"] == 0]

# Current Fair Balances Summary
st.subheader("Current Fair Balances")

if not debtors and not creditors:
    st.success("🎉 Everyone is perfectly settled — no payments needed!")
else:
    # Show settled members
    if settled:
        for s in settled:
            st.info(f"✅ **{s['name']}** is all settled.")

    # Show who owes (debtors)
    if debtors:
        st.write("🔴 **Owes:**")
        for d in debtors:
            st.error(f"**{d['name']}** owes ${abs(d['net']):.2f}")

    # Show who is owed (creditors)
    if creditors:
        st.write("🟢 **Owed:**")
        for c in creditors:
            st.success(f"**{c['name']}** is owed ${c['net']:.2f}")

# Suggested Settlements (Minimize transfers)
st.markdown("---")
st.subheader("💡 Suggested Settlements")

if not debtors or not creditors:
    st.info("No settlements needed — all even!")
else:
    # Simple one-to-one suggestion (can be expanded later)
    st.write("To make everything even:")

    # Sort for consistent suggestion
    debtors.sort(key=lambda x: x["net"])
    creditors.sort(key=lambda x: x["net"], reverse=True)

    i = 0  # debtor index
    j = 0  # creditor index
    while i < len(debtors) and j < len(creditors):
        debtor = debtors[i]
        creditor = creditors[j]
        amount = min(abs(debtor["net"]), creditor["net"])

        st.warning(f"→ **{debtor['name']}** pays **{creditor['name']}** ${amount:.2f}")

        # Update remaining
        debtors[i]["net"] += amount
        creditors[j]["net"] -= amount

        if abs(debtors[i]["net"]) < 0.01:
            i += 1
        if abs(creditors[j]["net"]) < 0.01:
            j += 1

