import streamlit as st
import sqlite3
from datetime import date
import pandas as pd
from database import DB_FILE, get_user_groups, get_group_members, get_group_expenses

# Security
if "user_id" not in st.session_state:
    st.switch_page("login.py")

st.title("➕ Add Expense")

groups = get_user_groups(st.session_state.user_id)
if groups.empty:
    st.warning("You need to be in a group to add expenses. Go to the Groups page first!")
    st.stop()

# Select group
group_name = st.selectbox("Select Group", options=groups["name"].tolist())
group_id = groups[groups["name"] == group_name]["id"].iloc[0]

# Safety net: Ensure current user is member
conn = sqlite3.connect(DB_FILE)
conn.execute("INSERT OR IGNORE INTO group_members (group_id, user_id) VALUES (?, ?)",
             (group_id, st.session_state.user_id))
conn.commit()
conn.close()

# Get current members
members = get_group_members(group_id)
if members.empty:
    st.error("No members in group — something went wrong.")
    st.stop()

member_names = members["name"].tolist()
id_to_name = dict(zip(members['id'], members['name']))
name_to_id = dict(zip(members['name'], members['id']))

# ADD EXPENSE FORM
with st.form("add_expense_form", clear_on_submit=True):
    col1, col2 = st.columns([2, 1])
    with col1:
        description = st.text_input("Description", placeholder="e.g., Beer, Dinner, Uber")
    with col2:
        amount = st.number_input("Amount ($)", min_value=0.01, step=0.01, format="%.2f")
    col3, col4 = st.columns(2)
    with col3:
        payer_name = st.selectbox("Who paid?", options=member_names,
                                  index=member_names.index(st.session_state.name) if st.session_state.name in member_names else 0)
    with col4:
        expense_date = st.date_input("Date", value=date.today())
    submitted = st.form_submit_button("➕ Add Expense", use_container_width=True)
    if submitted:
        if not description.strip():
            st.error("Add a description!")
        elif amount <= 0:
            st.error("Amount must be positive")
        else:
            payer_id = name_to_id[payer_name]
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("""
                INSERT INTO expenses (group_id, description, amount, payer_id, date)
                VALUES (?, ?, ?, ?, ?)
            """, (group_id, description, amount, payer_id, expense_date.isoformat()))
            expense_id = c.lastrowid
            num_members = len(members)
            if num_members > 1:
                share = round(amount / num_members, 2)
                for _, member in members.iterrows():
                    if member["id"] != payer_id:
                        c.execute("INSERT INTO splits (expense_id, user_id, owed) VALUES (?, ?, ?)",
                                  (expense_id, member["id"], share))
            conn.commit()
            conn.close()
            st.success(f"Added **{description}** – ${amount:.2f}")
            st.balloons()
            st.rerun()

# EXPENSES HISTORY TABLE
st.markdown("---")
st.subheader(f"📜 Expenses in **{group_name}** (Equal Sharing Among All Current Members)")

expenses_df = get_group_expenses(group_id)
if expenses_df.empty:
    st.info("No expenses yet. Add one above!")
else:
    # One row per expense
    expenses_clean = expenses_df.groupby('id').agg({
        'date': 'first',
        'description': 'first',
        'amount': 'first',
        'payer_id': 'first'
    }).reset_index()

    expenses_clean['paid_by'] = expenses_clean['payer_id'].map(id_to_name)

    current_num_members = len(members)
    expenses_clean['fair_share'] = (expenses_clean['amount'] / current_num_members).round(2)

    current_user_id = st.session_state.user_id
    expenses_clean['your_fair_net'] = expenses_clean.apply(
        lambda row: row['amount'] - row['fair_share'] if row['payer_id'] == current_user_id else -row['fair_share'],
        axis=1
    )

    display_df = expenses_clean[['date', 'description', 'amount', 'paid_by', 'your_fair_net']].copy()
    display_df = display_df.rename(columns={
        'date': 'Date',
        'description': 'Expense',
        'amount': 'Total Spent',
        'paid_by': 'Paid By',
        'your_fair_net': 'Your Fair Share'
    })
    display_df['Total Spent'] = display_df['Total Spent'].map("${:.2f}".format)
    display_df['Your Fair Share'] = display_df['Your Fair Share'].map(
        lambda x: f"**+${x:.2f}** (Lent)" if x > 0 else f"**${x:.2f}** (Borrowed)" if x < 0 else "$0.00"
    )
    display_df['Date'] = pd.to_datetime(display_df['Date']).dt.strftime('%m/%d/%Y')
    display_df = display_df.sort_values("Date", ascending=False)

    def color_share(val):
        if "(Lent)" in val:
            return "color: green; font-weight: bold"
        elif "(Borrowed)" in val:
            return "color: red; font-weight: bold"
        return ""

    styled = display_df.style.applymap(color_share, subset=['Your Fair Share'])
    st.dataframe(styled, use_container_width=True, hide_index=True)

    # === ACTIONS SECTION BELOW THE TABLE ===
    st.markdown("---")
    st.subheader("✏️ Actions (Edit / Delete)")

    # Show each expense with edit/delete buttons if user is the payer
    for _, exp in expenses_clean.iterrows():
        expense_id = exp['id']
        if exp['payer_id'] == st.session_state.user_id:  # Only payer can act
            with st.expander(f"📝 {exp['description']} – ${exp['amount']:.2f} (Paid by you on {exp['date']})"):
                col_edit, col_delete = st.columns([3, 1])

                with col_edit:
                    with st.form(key=f"edit_form_{expense_id}"):
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            new_desc = st.text_input("Description", value=exp['description'])
                        with col2:
                            new_amount = st.number_input("Amount ($)", min_value=0.01, step=0.01,
                                              value=float(exp['amount']), format="%.2f")
                        col3, col4 = st.columns(2)
                        with col3:
                            new_payer_name = st.selectbox("Who paid?", options=member_names,
                                                          index=member_names.index(id_to_name[exp['payer_id']]))
                        with col4:
                            new_date = st.date_input("Date", value=pd.to_datetime(exp['date']))

                        if st.form_submit_button("💾 Save Changes", use_container_width=True):
                            if not new_desc.strip():
                                st.error("Description required")
                            elif new_amount <= 0:
                                st.error("Amount must be positive")
                            else:
                                new_payer_id = name_to_id[new_payer_name]
                                conn = sqlite3.connect(DB_FILE)
                                c = conn.cursor()
                                # Update expense
                                c.execute("""
                                    UPDATE expenses 
                                    SET description = ?, amount = ?, payer_id = ?, date = ?
                                    WHERE id = ?
                                """, (new_desc, new_amount, new_payer_id, new_date.isoformat(), expense_id))
                                # Delete old splits
                                c.execute("DELETE FROM splits WHERE expense_id = ?", (expense_id,))
                                # Recreate splits (equal among current members)
                                num_members = len(members)
                                if num_members > 1:
                                    share = round(new_amount / num_members, 2)
                                    for _, member in members.iterrows():
                                        if member["id"] != new_payer_id:
                                            c.execute("INSERT INTO splits (expense_id, user_id, owed) VALUES (?, ?, ?)",
                                                      (expense_id, member["id"], share))
                                conn.commit()
                                conn.close()
                                st.success("Expense updated!")
                                st.rerun()

                with col_delete:
                    st.write("")  # spacing
                    if st.button("🗑️ Delete", key=f"delete_btn_{expense_id}", type="primary"):
                        st.warning("Are you sure you want to delete this expense?")
                        if st.button("Yes, delete permanently", key=f"confirm_delete_{expense_id}"):
                            conn = sqlite3.connect(DB_FILE)
                            c = conn.cursor()
                            c.execute("DELETE FROM splits WHERE expense_id = ?", (expense_id,))
                            c.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
                            conn.commit()
                            conn.close()
                            st.success("Expense deleted")
                            st.rerun()

# Overall fair balance summary
if not expenses_df.empty:
    total_spent = expenses_clean['amount'].sum()
    current_num_members = len(members)
    fair_share = total_spent / current_num_members
    user_paid = expenses_clean[expenses_clean['payer_id'] == st.session_state.user_id]['amount'].sum()
    your_balance = round(user_paid - fair_share, 2)

    if your_balance > 0:
        st.success(f"Overall: You are owed ${your_balance:.2f} in this group")
    elif your_balance < 0:
        st.warning(f"Overall: You owe ${abs(your_balance):.2f} in this group")
    else:
        st.success("🎉 All settled — perfect equal sharing! You owe nothing.")
        
