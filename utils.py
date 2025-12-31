import pandas as pd
from database import get_group_members, get_group_expenses, get_group_settlements

def calculate_balances(group_id):
    members = get_group_members(group_id)
    if members.empty:
        return pd.DataFrame(columns=["name", "balance"])

    expenses = get_group_expenses(group_id)

    # Total spent in the group (all expenses)
    total_spent = expenses['amount'].sum()

    # Current number of members
    num_members = len(members)
    if num_members == 0:
        return pd.DataFrame(columns=["name", "balance"])

    # Fair share per person (retroactive)
    fair_share = total_spent / num_members

    # How much each person actually paid
    paid_by = expenses.groupby('payer_id')['amount'].sum().to_dict()

    balance_data = []
    for _, member in members.iterrows():
        user_id = member['id']
        name = member['name']
        paid = paid_by.get(user_id, 0.0)
        net = paid - fair_share
        balance_data.append({"name": name, "balance": round(net, 2)})

    return pd.DataFrame(balance_data)
