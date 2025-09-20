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
REQUESTS_FILE = "requests.csv"   # new file for restaurant container requests

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
    if not os.path.exists(RESTAURANTS_FILE):
        # If restaurants.csv already exists in your workspace, this won't overwrite.
        pd.DataFrame([
            {"phone": "80001111", "password": "restA", "name": "Restaurant A"},
            {"phone": "80002222", "password": "restB", "name": "Restaurant B"}
        ]).to_csv(RESTAURANTS_FILE, index=False)
    if not os.path.exists(CONTAINERS_FILE):
        pd.DataFrame([
            {"id": "C001", "status": "CLEAN", "hoursInUse": 0, "timesUsed": 0,
             "owner": "", "deposit": 0.0, "history": "[]"}
        ]).to_csv(CONTAINERS_FILE, index=False)
    if not os.path.exists(ORDERS_FILE):
        pd.DataFrame(columns=["customer_phone", "restaurant_phone", "order_text", "status", "containers"]) \
          .to_csv(ORDERS_FILE, index=False)
    if not os.path.exists(REQUESTS_FILE):
        # requests: restaurant_phone, num_requested, status (OPEN / FULFILLED), created_at
        pd.DataFrame(columns=["restaurant_phone", "num_requested", "status", "created_at"]).to_csv(REQUESTS_FILE, index=False)

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
    if not os.path.exists(ORDERS_FILE):
        pd.DataFrame(columns=["customer_phone", "restaurant_phone", "order_text", "status", "containers"]).to_csv(ORDERS_FILE, index=False)
    return pd.read_csv(ORDERS_FILE, dtype=str)

def save_orders(df):
    df.to_csv(ORDERS_FILE, index=False)

def load_requests():
    if not os.path.exists(REQUESTS_FILE):
        pd.DataFrame(columns=["restaurant_phone", "num_requested", "status", "created_at"]).to_csv(REQUESTS_FILE, index=False)
    df = pd.read_csv(REQUESTS_FILE, dtype=str).applymap(lambda x: x.strip() if isinstance(x, str) else x)
    return df

def save_requests(df):
    df.to_csv(REQUESTS_FILE, index=False)

def load_containers():
    df = pd.read_csv(CONTAINERS_FILE, dtype=str).applymap(lambda x: x.strip() if isinstance(x, str) else x)
    # ensure columns types
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
# page state used for simple multi-page navigation
if "page" not in st.session_state: st.session_state.page = "home"

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
                    st.session_state.page = "home"
                    st.rerun()
                else:
                    st.error("Invalid customer credentials")
            elif role == "Operator":
                operators = load_operators()
                match = operators[(operators["phone"] == phone) & (operators["password"] == password)]
                if not match.empty:
                    st.session_state.role = "Operator"
                    st.session_state.phone = phone
                    st.session_state.page = "home"
                    st.rerun()
                else:
                    st.error("Invalid operator credentials")
            else:  # Restaurant
                restaurants = load_restaurants()
                match = restaurants[(restaurants["phone"] == phone) & (restaurants["password"] == password)]
                if not match.empty:
                    st.session_state.role = "Restaurant"
                    st.session_state.phone = phone
                    st.session_state.page = "home"
                    st.rerun()
                else:
                    st.error("Invalid restaurant credentials")
    st.stop()

# -----------------------
# ---------- CUSTOMER VIEW ----------
# -----------------------
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
            st.session_state.page = "home"
            st.rerun()

    st.markdown(f"## 👤 Customer Home - `{st.session_state.phone}`")

    # Points + Rewards button
    col1, col2 = st.columns([2, 1])
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

        # Spin wheel simplified (directly apply points or voucher)
        st.subheader("🎡 Spin the Wheel")
        spin_cost = 100
        wheel_segments = [
            "+10 Points", "Restaurant Voucher", "+20 Points", "Restaurant Voucher", "+50 Points",
            "Restaurant Voucher", "+100 Points", "Restaurant Voucher", "+200 Points", "Restaurant Voucher"
        ]

        if st.button(f"🎰 Spin Now! (cost {spin_cost} pts)"):
            current_points = users.loc[users["phone"] == st.session_state.phone, "points"].values[0]
            if current_points >= spin_cost:
                # Deduct cost
                users.loc[users["phone"] == st.session_state.phone, "points"] -= spin_cost
                save_users(users)

                prize = random.choice(wheel_segments)
                if "Points" in prize:
                    amount = int(prize.replace("+", "").replace(" Points", ""))
                    users.loc[users["phone"] == st.session_state.phone, "points"] += amount
                    save_users(users)
                    st.success(f"🎉 You won {amount} points! They’ve been added to your balance.")
                else:
                    st.success("🎉 You won a Restaurant Voucher! (voucher not tracked in this demo)")
            else:
                st.error("Not enough points to spin ❌")

        st.divider()
        st.button("⬅️ Back to Home", on_click=lambda: st.session_state.update({"page":"home"}))
        st.stop()

    if st.session_state.get("page", "home") == "home":
        # Big button to go to order page (visual centered)
        col_l, col_c, col_r = st.columns([1, 3, 1])
        with col_c:
            if st.button("🛒 Place New Order", key="new_order_button", help="Place a new order"):
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
    orders = load_orders()  # reload to ensure fresh
    customer_orders = orders[orders["customer_phone"]==st.session_state.phone]
    restaurants = load_restaurants()

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

    # Full history in expander (latest first)
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


# -----------------------
# ---------- OPERATOR VIEW ----------
# -----------------------
if st.session_state.role == "Operator":
    st.header(f"Operator Home ({st.session_state.phone})")
    containers = load_containers()


    # Redistribute button -> opens redistribute page
    if st.button("🔁 Redistribute Containers"):
        st.session_state.page = "redistribute_page"
        st.rerun()

    # Redistribute page
    if st.session_state.get("page") == "redistribute_page":
        st.header("Redistribute Requests")
        requests = load_requests()
        open_requests = requests[requests["status"] == "OPEN"].iloc[::-1]  # latest first
        if not open_requests.empty:
            for idx, req in open_requests.iterrows():
                rest_phone = req["restaurant_phone"]
                rest_name = req["restaurant_name"]
                num_req = num_req = int(float(req["num_requested"]))

                with st.container(border=True):
                    st.write(f"**Restaurant:** {rest_name} ({rest_phone})")
                    st.write(f"**Requested:** {num_req} containers")
                    if st.button(f"Distribute to {rest_name} (req {idx})"):
                        containers = load_containers()
                        available = containers[containers["status"] == "CLEAN"].head(num_req)
                        if len(available) < num_req:
                            st.error("Not enough clean containers available to fulfill request.")
                        else:
                            for cidx in available.index:
                                containers.at[cidx, "status"] = "DISTRIBUTED"
                                containers.at[cidx, "owner"] = rest_phone
                                # record history
                                history = containers.at[cidx, "history"]
                                history.append(rest_phone)
                                containers.at[cidx, "history"] = history
                            save_containers(containers)
                            # mark request fulfilled
                            requests.at[idx, "status"] = "FULFILLED"
                            save_requests(requests)
                            st.success(f"Distributed {num_req} containers to {rest_name}")
                            st.rerun()
        else:
            st.info("No open redistribute requests.")

        st.button("⬅️ Back to Operator Home", on_click=lambda: st.session_state.update({"page": "home"}))
        st.stop()

    search = st.text_input("Search Container ID")
    results = containers[containers["id"].str.contains(search)] if search else containers
    # normal operator view (container list + detail)
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
        # include DISTRIBUTED in status transitions
        if current_status == "CLEAN":
            next_status_options = ["DISTRIBUTED", "IN_USE"]
        elif current_status == "DISTRIBUTED":
            next_status_options = ["IN_USE", "CLEAN"]
        elif current_status == "IN_USE":
            next_status_options = ["RETURNED"]
        elif current_status == "RETURNED":
            next_status_options = ["CLEAN"]
        else:
            next_status_options = ["CLEAN", "IN_USE", "RETURNED"]

        next_status = st.selectbox("Next Status", next_status_options)
        returned_opt = None
        if current_status == "IN_USE":
            returned_opt = st.radio("Return Option", ["Returned Cleaned", "Returned Uncleaned"])

        if st.button("Update Status"):
            idx = containers[containers["id"] == cid].index[0]
            # credit points only if moving to RETURNED and returned as cleaned
            if next_status == "RETURNED" and container["owner"]:
                if returned_opt == "Returned Cleaned":
                    users = load_users()
                    pts = calc_points(container["hoursInUse"], clean=True)
                    owner = container["owner"]
                    if owner in users["phone"].values:
                        users.loc[users["phone"] == owner, "points"] += pts
                        save_users(users)
            # reset container only when setting to CLEAN
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
        st.session_state.page = "home"
        st.rerun()



# ---------- RESTAURANT VIEW ----------
if st.session_state.role == "Restaurant":
    restaurants = load_restaurants()
    my_rest = restaurants[restaurants["phone"] == st.session_state.phone].iloc[0]
    st.header(f"🍴 Restaurant Home - {my_rest['name']}")

    containers = load_containers()

    # Show restaurant's container stock (distributed containers)
    my_stock = containers[(containers["status"] == "DISTRIBUTED") & (containers["owner"] == st.session_state.phone)]
    st.metric("📦 Containers Available", len(my_stock))

    # Request more containers button
    if st.session_state.get("page") == "request_page":
        st.subheader("➕ Request More Containers")
        num_req = st.number_input("Enter number of containers needed", min_value=1, step=1)
        if st.button("📤 Submit Request"):
            if "requests.csv" not in os.listdir():
                pd.DataFrame(columns=["restaurant_phone", "restaurant_name", "num"]).to_csv("requests.csv", index=False)
            requests = pd.read_csv("requests.csv")
            new_req = pd.DataFrame([{
                "restaurant_phone": st.session_state.phone,
                "restaurant_name": my_rest["name"],
                "num": int(num_req)
            }])
            requests = pd.concat([requests, new_req], ignore_index=True)
            requests.to_csv("requests.csv", index=False)
            st.session_state.page = "request_sent"
            st.rerun()
        st.button("⬅️ Back to Home", on_click=lambda: st.session_state.update({"page":"home"}))
        st.stop()

    if st.session_state.get("page") == "request_sent":
        st.markdown("## ✅ Your request has been sent!")
        st.markdown("Operator will distribute containers to you soon.")
        st.button("⬅️ Back to Home", on_click=lambda: st.session_state.update({"page":"home"}))
        st.stop()

    if st.button("📦 Request More", key="req_btn"):
        st.session_state.page = "request_page"
        st.rerun()

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
                    available = containers[(containers["status"] == "DISTRIBUTED") & 
                                           (containers["owner"] == st.session_state.phone)].head(num)

                    if len(available) < num:
                        st.error("Not enough distributed containers in your stock!")
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
                        st.success("Order delivered using your distributed containers!")
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
