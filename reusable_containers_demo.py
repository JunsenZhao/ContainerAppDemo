import streamlit as st
import pandas as pd
import os
import random
import ast

# ---------- CSV FILES ----------
USERS_FILE = "users.csv"
OPERATORS_FILE = "operators.csv"
RESTAURANTS_FILE = "restaurants.csv"
CONTAINERS_FILE = "containers.csv"
ORDERS_FILE = "orders.csv"

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
    if not os.path.exists(ORDERS_FILE):
        pd.DataFrame(columns=["customer_phone", "restaurant_phone", "order_text", "status", "containers"]) \
          .to_csv(ORDERS_FILE, index=False)

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

def load_restaurants():
    df = pd.read_csv(RESTAURANTS_FILE, dtype=str).applymap(lambda x: x.strip() if isinstance(x, str) else x)
    return df

def load_orders():
    return pd.read_csv(ORDERS_FILE, dtype=str)

def save_orders(df):
    df.to_csv(ORDERS_FILE, index=False)

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
    st.title("♻️ Reusable Container App")
    st.subheader("Login")
    with st.form("login_form"):
        phone = st.text_input("Phone").strip()
        password = st.text_input("Password", type="password").strip()
        role = st.radio("Login as", ["Customer", "Operator", "Restaurant"])
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
            elif role == "Operator":
                operators = load_operators()
                match = operators[(operators["phone"] == phone) & (operators["password"] == password)]
                if not match.empty:
                    st.session_state.role = "Operator"
                    st.session_state.phone = phone
                    st.rerun()
                else:
                    st.error("Invalid operator credentials")
            else:  # Restaurant
                restaurants = load_restaurants()
                match = restaurants[(restaurants["phone"] == phone) & (restaurants["password"] == password)]
                if not match.empty:
                    st.session_state.role = "Restaurant"
                    st.session_state.phone = phone
                    st.rerun()
                else:
                    st.error("Invalid restaurant credentials")
    st.stop()

# ---------- CUSTOMER VIEW ----------
if st.session_state.role == "Customer":
    users = load_users()
    user = users[users["phone"] == st.session_state.phone].iloc[0]
    containers = load_containers()
    my_containers = containers[containers["owner"] == st.session_state.phone]
    orders = load_orders()
    restaurants = load_restaurants()

    # ---------- CUSTOMER HEADER ----------
    with st.sidebar:
        st.markdown("## 👤 Customer Info")
        st.markdown(f"**Phone:** `{st.session_state.phone}`")
        if st.button("🚪 Logout", key="logout_sidebar"):
            st.session_state.role = None
            st.session_state.phone = None
            st.rerun()

    st.markdown(f"## 👤 Customer Home - `{st.session_state.phone}`")

    # Points + Rewards button
    col1, col2 = st.columns([1, 1])
    with col1:
        st.metric("💎 Available Points", user["points"])
    with col2:
        if st.button("🎁 Rewards"):
            st.session_state.page = "rewards_page"

    # ---------- Page Navigation ----------
    if st.session_state.get("page", "home") == "rewards_page":
        st.markdown("## 🎁 Rewards")
        rewards = {"Free Coffee": 1000, "Discount $5": 2000, "Free Snack": 500}
        cols = st.columns(len(rewards))
        for i, (r, cost) in enumerate(rewards.items()):
            with cols[i]:
                if st.button(f"Redeem {r} ({cost} pts)", key=f"reward_{i}"):
                    current_points = users.loc[users["phone"] == st.session_state.phone, "points"].values[0]
                    if current_points >= cost:
                        users.loc[users["phone"] == st.session_state.phone, "points"] -= cost
                        save_users(users)
                        st.success(f"🎉 You redeemed {r}!")
                    else:
                        st.error("Not enough points ❌")
        st.divider()

        st.button("⬅️ Back to Home", on_click=lambda: st.session_state.update({"page":"home"}))
        st.stop()

    if st.session_state.get("page", "home") == "home":
        # Big button to go to order page
        if st.button("🛒 Place New Order", key="new_order_button"):
            st.session_state.page = "order_page"
            st.rerun()

    if st.session_state.get("page") == "order_page":
        st.markdown("## 📝 New Order")
        order_text = st.text_area("Enter your order instructions here", height=200)
        restaurant_selection = st.selectbox("Select restaurant", restaurants["name"])
        if st.button("✅ Submit Order"):
            restaurant_phone = restaurants[restaurants["name"] == restaurant_selection]["phone"].values[0]
            new_order = pd.DataFrame([{
                "customer_phone": st.session_state.phone,
                "restaurant_phone": restaurant_phone,
                "order_text": order_text,
                "status": "PENDING",
                "containers": ""
            }])
            orders = pd.concat([orders, new_order], ignore_index=True)
            save_orders(orders)
            st.session_state.page = "order_sent_page"
            st.rerun()
        st.button("⬅️ Back to Home", on_click=lambda: st.session_state.update({"page":"home"}))
        st.stop()

    if st.session_state.get("page") == "order_sent_page":
        st.markdown("## ✅ Your order has been sent!")
        st.markdown("You will be notified when the restaurant delivers it.")
        st.button("⬅️ Back to Home", on_click=lambda: st.session_state.update({"page":"home"}))
        st.stop()

    # ---------- Order History ----------
    st.divider()
    st.markdown("### 📜 Order History")
    # --- Pending Orders as cards ---
    customer_orders = orders[orders["customer_phone"]==st.session_state.phone]

    pending_orders = customer_orders[customer_orders["status"] == "PENDING"]
    if not pending_orders.empty:
        st.markdown("#### 🕒 Pending Orders")
        # Sort latest first
        pending_orders = pending_orders.iloc[::-1]
        for idx, order in pending_orders.iterrows():
            with st.container(border=True):
                rest_name = restaurants.loc[restaurants["phone"] == order["restaurant_phone"], "name"].values[0]
                st.write(f"**Restaurant:** {rest_name}")
                st.write(f"**Order:** {order['order_text']}")
    else:
        st.info("No pending orders.")


    if not customer_orders.empty:
        customer_orders = customer_orders.iloc[::-1]
        with st.expander("View all orders"):
            display_orders = []
            for _, row in customer_orders.iterrows():
                restaurant_name = restaurants[restaurants['phone']==row['restaurant_phone']]['name'].values[0]
                display_orders.append({
                    "Order": row['order_text'],
                    "Restaurant": restaurant_name,
                    "Containers": row['containers'] if row['containers'] else "-",
                    "Status": row['status']
                })
            st.table(pd.DataFrame(display_orders))
    else:
        st.info("No order history yet.")

    # Containers in Possession (unchanged)
    st.divider()
    st.markdown("### 📦 My Containers")
    my_containers_active = my_containers[my_containers["status"] != "RETURNED"]
    if not my_containers_active.empty:
        cols = st.columns(2)
        for i, (_, c) in enumerate(my_containers_active.iterrows()):
            with cols[i % 2]:
                with st.container(border=True):
                    st.subheader(f"ID: {c['id']}")
                    st.write(f"**Status:** {c['status']}")
                    st.write(f"**Hours in use:** {c['hoursInUse']}")
                    st.write(f"**Deposit:** ${c['deposit']:.2f}")
    else:
        st.info("You don’t have any containers right now.")

    # Deposits (unchanged)
    st.divider()
    st.markdown("### 💰 My Deposits")
    deposits = my_containers_active[my_containers_active["deposit"] > 0]
    if not deposits.empty:
        total = deposits["deposit"].sum()
        st.metric("Total Deposit", f"${total:.2f}")
        with st.expander("See details"):
            for _, c in deposits.iterrows():
                st.write(f"🆔 {c['id']} → ${c['deposit']:.2f}")
    else:
        st.info("No active deposits at the moment.")


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

    if st.session_state.selected_container:
        cid = st.session_state.selected_container
        container = containers[containers["id"] == cid].iloc[0]
        st.subheader(f"Container {cid}")
        st.write(container)

        current_status = container["status"]
        if current_status == "CLEAN":
            next_status_options = ["IN_USE"]
        elif current_status == "IN_USE":
            next_status_options = ["RETURNED"]
        elif current_status == "RETURNED":
            next_status_options = ["CLEAN"]

        next_status = st.selectbox("Next Status", next_status_options)
        returned_opt = None
        if current_status == "IN_USE":
            returned_opt = st.radio("Return Option", ["Returned Cleaned", "Returned Uncleaned"])

        if st.button("Update Status"):
            idx = containers[containers["id"] == cid].index[0]
            if next_status == "RETURNED" and container["owner"]:
                if returned_opt == "Returned Cleaned":
                    users = load_users()
                    pts = calc_points(container["hoursInUse"], clean=True)
                    owner = container["owner"]
                    users.loc[users["phone"] == owner, "points"] += pts
                    save_users(users)
            if next_status == "CLEAN":
                containers.at[idx, "owner"] = ""
                containers.at[idx, "deposit"] = 0.0
                containers.at[idx, "hoursInUse"] = 0
                containers.at[idx, "timesUsed"] += 1
            containers.at[idx, "status"] = next_status
            save_containers(containers)
            st.success("Status updated!")
            st.session_state.selected_container = None
            st.rerun()

    if st.button("Add Container"):
        new_id = f"C{random.randint(100,999)}"
        new = {"id": new_id, "status": "CLEAN", "hoursInUse": 0,
               "timesUsed": 0, "owner": "", "deposit": 0.0, "history": []}
        containers = pd.concat([containers, pd.DataFrame([new])], ignore_index=True)
        save_containers(containers)
        st.success(f"Added {new_id}")
        st.rerun()

    if st.button("Logout"):
        st.session_state.role = None
        st.session_state.phone = None
        st.session_state.selected_container = None
        st.rerun()
# ---------- RESTAURANT VIEW ----------
if st.session_state.role == "Restaurant":
    restaurants = load_restaurants()
    my_rest = restaurants[restaurants["phone"] == st.session_state.phone].iloc[0]
    st.header(f"🍴 Restaurant Home - {my_rest['name']}")

    orders = load_orders()
    my_orders = orders[(orders["restaurant_phone"] == st.session_state.phone)].iloc[::-1]  # latest first

    # ---------- Active Orders Cards (latest 5) ----------
    st.subheader("📥 Pending Orders")
    pending_orders = my_orders[my_orders["status"] == "PENDING"]
    if not pending_orders.empty:
        for idx, order in pending_orders.head(5).iterrows():
            with st.container(border=True):
                st.write(f"**Customer:** {order['customer_phone']}")
                st.write(f"**Order:** {order['order_text']}")
                num = st.number_input(f"Containers for order {idx}", 1, 5, 1, key=f"cont_{idx}")
                if st.button(f"✅ Mark Delivered (Order {idx})"):
                    containers = load_containers()
                    available = containers[containers["status"] == "CLEAN"].head(num)
                    if len(available) < num:
                        st.error("Not enough clean containers available!")
                    else:
                        for cidx in available.index:
                            containers.at[cidx, "status"] = "IN_USE"
                            containers.at[cidx, "owner"] = order["customer_phone"]
                            containers.at[cidx, "deposit"] = 5.0
                            history = containers.at[cidx, "history"]
                            history.append(order["customer_phone"])
                            containers.at[cidx, "history"] = history
                        save_containers(containers)
                        orders.at[idx, "status"] = "DELIVERED"
                        orders.at[idx, "containers"] = str(num)
                        save_orders(orders)
                        st.success("Order delivered and containers assigned!")
                        st.rerun()
    else:
        st.info("No pending orders.")

    # ---------- Full Order History Table ----------
    st.subheader("📜 Full Order History")
    with st.expander("Show all orders"):
        if not my_orders.empty:
            st.table(my_orders[["customer_phone", "order_text", "status", "containers"]])
        else:
            st.info("No orders yet.")

    if st.button("🚪 Logout"):
        st.session_state.role = None
        st.session_state.phone = None
        st.rerun()
