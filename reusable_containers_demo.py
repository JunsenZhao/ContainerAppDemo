import streamlit as st
import pandas as pd
import os
import random
import ast

# ---------- CSV FILES ----------
USERS_FILE = "users.csv"
OPERATORS_FILE = "operators.csv"
CONTAINERS_FILE = "containers.csv"

# ---------- INITIALIZATION ----------
def init_csv():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([
            {"phone": "91234567", "password": "pass123", "points": 0},
            {"phone": "98765432", "password": "secret", "points": 0}
        ]).to_csv(USERS_FILE, index=False)
    if not os.path.exists(OPERATORS_FILE):
        pd.DataFrame([
            {"phone": "90001111", "password": "op123"},
            {"phone": "90002222", "password": "op456"}
        ]).to_csv(OPERATORS_FILE, index=False)
    if not os.path.exists(CONTAINERS_FILE):
        pd.DataFrame([
            {"id": "C001", "status": "CLEAN", "hoursInUse": 0, "timesUsed": 0,
             "owner": "", "deposit": 0.0, "history": "[]"}
        ]).to_csv(CONTAINERS_FILE, index=False)

init_csv()

# ---------- HELPERS ----------
def load_users():
    df = pd.read_csv(USERS_FILE, dtype=str).applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df["points"] = df["points"].astype(int)
    return df

def save_users(df):
    df.to_csv(USERS_FILE, index=False)

def load_operators():
    df = pd.read_csv(OPERATORS_FILE, dtype=str).applymap(lambda x: x.strip() if isinstance(x, str) else x)
    return df

def load_containers():
    df = pd.read_csv(CONTAINERS_FILE, dtype=str).applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df["hoursInUse"] = df["hoursInUse"].astype(int)
    df["timesUsed"] = df["timesUsed"].astype(int)
    df["deposit"] = df["deposit"].astype(float)
    df["history"] = df["history"].apply(lambda x: ast.literal_eval(x) if x else [])
    return df

def save_containers(df):
    df["history"] = df["history"].apply(str)
    df.to_csv(CONTAINERS_FILE, index=False)

def calc_points(hours, clean=True):
    base = max(0, (168 - hours) * 1000 / 168)
    return int(base if clean else base / 2)

# ---------- SESSION STATE ----------
if "role" not in st.session_state: st.session_state.role = None
if "phone" not in st.session_state: st.session_state.phone = None
if "selected_container" not in st.session_state: st.session_state.selected_container = None

# ---------- LOGIN ----------
if st.session_state.role is None:
    st.title("♻️ Reusable Container Demo")
    st.subheader("Login")
    with st.form("login_form"):
        phone = st.text_input("Phone").strip()
        password = st.text_input("Password", type="password").strip()
        role = st.radio("Login as", ["Customer", "Operator"])
        submitted = st.form_submit_button("Login")
        if submitted:
            if role == "Customer":
                users = load_users()
                match = users[(users["phone"] == phone) & (users["password"] == password)]
                if not match.empty:
                    st.session_state.role = "Customer"
                    st.session_state.phone = phone
                    st.rerun()
                else:
                    st.error("Invalid customer credentials")
            else:
                operators = load_operators()
                match = operators[(operators["phone"] == phone) & (operators["password"] == password)]
                if not match.empty:
                    st.session_state.role = "Operator"
                    st.session_state.phone = phone
                    st.rerun()
                else:
                    st.error("Invalid operator credentials")
    st.stop()

# ---------- CUSTOMER VIEW ----------
if st.session_state.role == "Customer":
    users = load_users()
    user = users[users["phone"] == st.session_state.phone].iloc[0]
    containers = load_containers()
    my_containers = containers[containers["owner"] == st.session_state.phone]

    st.header(f"Customer Home ({st.session_state.phone})")

    # Points
    st.subheader("💎 Points")
    st.metric("Current Points", user["points"])

    # Containers
    st.subheader("📦 Containers in Possession")
    if not my_containers.empty:
        for _, c in my_containers.iterrows():
            st.write(f"ID: {c['id']} | Status: {c['status']} | Hours: {c['hoursInUse']}")
    else:
        st.info("No containers in possession.")

    # New Order
    st.subheader("🛒 New Order")
    num = st.number_input("Number of containers", 1, 5, 1, key="num_order")
    if st.button("Place Order"):
        containers = load_containers()
        # Select clean containers
        available = containers[containers["status"] == "CLEAN"].head(num)
        if len(available) < num:
            st.error("Not enough clean containers available!")
        else:
            for idx in available.index:
                containers.at[idx, "status"] = "IN_USE"
                containers.at[idx, "owner"] = st.session_state.phone
                containers.at[idx, "deposit"] = 5.0
                history = containers.at[idx, "history"]
                history.append(st.session_state.phone)
                containers.at[idx, "history"] = history
            save_containers(containers)
            st.success("Order placed!")
            st.rerun()


    # Deposits
    st.subheader("💰 Deposits")
    if not my_containers.empty:
        deposits = my_containers[my_containers["deposit"] > 0]
        if not deposits.empty:
            st.write(deposits[["id", "deposit"]])
            st.write(f"Total deposit: ${deposits['deposit'].sum():.2f}")
        else:
            st.info("No active deposits.")
    else:
        st.info("No containers to show deposits.")

    # History
    st.subheader("📜 History")
    my_history = containers[containers["history"].apply(lambda h: st.session_state.phone in h)]
    st.write(my_history[["id"]])

    # Redeem Rewards
    st.subheader("🎁 Redeem Rewards")
    rewards = {"Free Coffee": 1000, "Discount $5": 2000, "Free Snack": 500}
    for r, cost in rewards.items():
        if st.button(f"Redeem {r} ({cost} pts)"):
            users = load_users()
            current_points = users.loc[users["phone"] == st.session_state.phone, "points"].values[0]
            if current_points >= cost:
                users.loc[users["phone"] == st.session_state.phone, "points"] -= cost
                save_users(users)
                st.success(f"Redeemed {r}!")
            else:
                st.error("Not enough points")

    # Logout
    if st.button("Logout"):
        st.session_state.role = None
        st.session_state.phone = None
        st.rerun()

# ---------- OPERATOR VIEW ----------
if st.session_state.role == "Operator":
    st.header(f"Operator Home ({st.session_state.phone})")
    containers = load_containers()
    search = st.text_input("Search Container ID")
    results = containers[containers["id"].str.contains(search)] if search else containers

    for _, c in results.iterrows():
        if st.button(f"{c['id']} | {c['status']}"):
            st.session_state.selected_container = c['id']
            st.rerun()

    # Container detail view
    if st.session_state.selected_container:
        cid = st.session_state.selected_container
        container = containers[containers["id"] == cid].iloc[0]
        st.subheader(f"Container {cid}")
        st.write(container)

        # Determine allowed next statuses
        current_status = container["status"]
        if current_status == "CLEAN":
            next_status_options = ["IN_USE"]
        elif current_status == "IN_USE":
            next_status_options = ["RETURNED"]
        elif current_status == "RETURNED":
            next_status_options = ["CLEAN"]

        next_status = st.selectbox("Next Status", next_status_options)

        # Show return option only if container is currently IN_USE
        returned_opt = None
        if current_status == "IN_USE":
            returned_opt = st.radio("Return Option", ["Returned Cleaned", "Returned Uncleaned"])

        if st.button("Update Status"):
            idx = containers[containers["id"] == cid].index[0]

            # Credit points only if moving to RETURNED and returned as cleaned
            if next_status == "RETURNED" and container["owner"]:
                if returned_opt == "Returned Cleaned":
                    users = load_users()
                    pts = calc_points(container["hoursInUse"], clean=True)
                    owner = container["owner"]
                    users.loc[users["phone"] == owner, "points"] += pts
                    save_users(users)

            # Reset container only when status is changed to CLEAN
            if next_status == "CLEAN":
                containers.at[idx, "owner"] = ""
                containers.at[idx, "deposit"] = 0.0
                containers.at[idx, "hoursInUse"] = 0
                containers.at[idx, "timesUsed"] += 1

            # Update status
            containers.at[idx, "status"] = next_status
            save_containers(containers)
            st.success("Status updated!")
            st.session_state.selected_container = None
            st.rerun()


    # Add container
    if st.button("Add Container"):
        new_id = f"C{random.randint(100,999)}"
        new = {"id": new_id, "status": "CLEAN", "hoursInUse": 0,
               "timesUsed": 0, "owner": "", "deposit": 0.0, "history": []}
        containers = pd.concat([containers, pd.DataFrame([new])], ignore_index=True)
        save_containers(containers)
        st.success(f"Added {new_id}")
        st.rerun()

    # Logout
    if st.button("Logout"):
        st.session_state.role = None
        st.session_state.phone = None
        st.session_state.selected_container = None
        st.rerun()