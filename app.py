# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import re
import urllib.parse
import random
import string
from supabase import create_client, Client
from datetime import datetime, date, timedelta

# The Invisibility Cloak: Hides Streamlit branding and menus
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            .stDeployButton {display:none;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# SETUP & CONFIG
st.set_page_config(page_title="Washh | Silent Partner", layout="wide", initial_sidebar_state="collapsed")

@st.cache_resource
def init_connection() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = init_connection()

# SESSION STATES
if "auth" not in st.session_state: st.session_state.auth = False
if "is_master" not in st.session_state: st.session_state.is_master = False
if "shop_info" not in st.session_state: st.session_state.shop_info = None
if "vault_unlocked" not in st.session_state: st.session_state.vault_unlocked = False
if "trainer_wheels" not in st.session_state: st.session_state.trainer_wheels = True

# ADMIN WHATSAPP NUMBER
ADMIN_WA_NUMBER = "2348058535372" 

# LOGIN GATE & SELF-SERVICE
def login_gate():
    st.title("Washh: Access Portal")
    
    tab_login, tab_signup = st.tabs(["🚪 Shop Login", "🚀 Start 7-Day Free Trial"])

    # --- SPRINT 6: SHOP NAME LOGIN & AUTO-LOCK PAYWALL ---
    with tab_login:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.container(border=True):
                # Swapped Shop Code for Shop Name
                shop_input_name = st.text_input("Laundry Shop Name", key="gate_shop_name", placeholder="e.g. Clean & Sharp").strip()
                pin = st.text_input("Staff PIN", type="password", key="gate_staff_pin")

                if st.button("Enter Workspace", use_container_width=True):
                    # Master Backdoor (Uses the name field to enter secret code)
                    if shop_input_name == st.secrets["auth"]["master_code"] and pin == st.secrets["auth"]["master_pin"]:
                        st.session_state.auth = True
                        st.session_state.is_master = True
                        st.rerun()

                    # Tenant Verification via Shop Name (ilike handles case-insensitivity)
                    res = supabase.table("shops").select("*").ilike("shop_name", shop_input_name).execute()
                    
                    if res.data:
                        shop = res.data[0] # Grabs the exact match
                        expiry = datetime.strptime(shop["expiry_date"], "%Y-%m-%d").date()
                        
                        is_expired = date.today() > expiry
                        is_disabled = not shop.get("is_active", True)

                        # Check if trial has ended or account is manually disabled
                        if is_expired or is_disabled:
                            # Auto-lock the database if they expired but it still says 'True'
                            if is_expired and shop.get("is_active", True):
                                supabase.table("shops").update({"is_active": False}).eq("id", shop["id"]).execute()
                            
                            st.error("🚨 Your Washh access has expired or is suspended.")
                            
                            # The Contact Admin Button
                            msg = f"Hello Washh Admin, my shop '{shop['shop_name']}' has expired. I am ready to subscribe and unlock my account!"
                            safe_msg = urllib.parse.quote(msg)
                            wa_link = f"https://wa.me/{ADMIN_WA_NUMBER}?text={safe_msg}"
                            
                            st.link_button("📲 Click Here to Contact Admin & Subscribe", wa_link, use_container_width=True)
                        else:
                            # Active and within timeframe
                            staff = supabase.table("staff").select("*").eq("shop_id", shop["id"]).eq("pin", pin).execute()
                            if staff.data:
                                st.session_state.auth = True
                                st.session_state.shop_info = shop
                                st.rerun()
                            else:
                                st.error("Invalid Staff PIN.")
                    else:
                        st.error("Shop Name not found. Check your spelling.")

    # --- SPRINT 3: AUTOPILOT ONBOARDING ---
    with tab_signup:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.container(border=True):
                st.markdown("### Create Your Washh Account")
                st.caption("Setup takes exactly 2 minutes.")
                
                with st.form("signup_form"):
                    new_shop_name = st.text_input("Laundry Shop Name", placeholder="e.g. Clean & Sharp Laundry").strip()
                    new_phone = st.text_input("Shop Phone Number", placeholder="080...").strip()
                    manager_name = st.text_input("Manager/Staff Name", placeholder="e.g. Chidi").strip()
                    
                    st.markdown("**Create Your Shop PIN**")
                    st.caption("Must be at least 7 characters. Must contain letters, numbers, and a symbol (e.g., @, #, $).")
                    new_pin = st.text_input("Shop Access PIN", type="password")
                    
                    submitted = st.form_submit_button("Launch My Shop", use_container_width=True)

                    if submitted:
                        if not new_shop_name or not new_phone or not manager_name or not new_pin:
                            st.error("Boss, please fill all fields to continue.")
                        else:
                            # 1. PIN Logic Check
                            if len(new_pin) < 7 or not re.search(r"[a-zA-Z]", new_pin) or not re.search(r"\d", new_pin) or not re.search(r"[\W_]", new_pin):
                                st.error("PIN is too weak. Make sure it has 7+ characters, letters, numbers, and a symbol.")
                            else:
                                # 2. Check if Shop Name exists (Case Insensitive)
                                name_check = supabase.table("shops").select("shop_name").ilike("shop_name", new_shop_name).execute()
                                if name_check.data:
                                    st.error(f"The name '{new_shop_name}' is already taken. Try adding your location, like '{new_shop_name} Lekki'.")
                                else:
                                    # 3. Check if Phone Number exists
                                    phone_check = supabase.table("shops").select("owner_phone").eq("owner_phone", new_phone).execute()
                                    if phone_check.data:
                                        st.error("This phone number is already registered to another shop.")
                                    else:
                                        # 4. Generate Unique Shop Code & Dates (Code stays invisible to user)
                                        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
                                        auto_code = f"WASHH-{random_str}"
                                        trial_expiry = str(date.today() + timedelta(days=7))
                                        
                                        # 5. Create the Shop Profile (ACTIVE)
                                        new_shop = supabase.table("shops").insert({
                                            "shop_name": new_shop_name, 
                                            "owner_phone": new_phone,
                                            "shop_code": auto_code,
                                            "is_active": True, 
                                            "expiry_date": trial_expiry, 
                                            "owner_pin": "0000" # Default Vault PIN
                                        }).execute()
                                        
                                        shop_record = new_shop.data[0]
                                        
                                        # 6. Create the Staff Profile
                                        supabase.table("staff").insert({
                                            "shop_id": shop_record["id"],
                                            "staff_name": manager_name,
                                            "pin": new_pin
                                        }).execute()

                                        # 7. Log them in automatically!
                                        st.success(f"Shop created! You will use your Shop Name ('{new_shop_name}') and PIN to log in.")
                                        st.session_state.auth = True
                                        st.session_state.shop_info = shop_record
                                        st.rerun()

# OPERATIONS & VAULT
def shop_workspace():
    shop = st.session_state.shop_info
    shop_id = shop["id"]

    st.sidebar.title(shop["shop_name"])
    menu = st.sidebar.radio("Navigation", ["Drop-off", "Shop Floor", "Owner Vault"])

    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    if menu == "Drop-off":
        st.subheader("New Order")
        
        # SPRINT 5: Trainer Wheels Implementation
        if st.session_state.trainer_wheels:
            st.info("💡 **Trainer Wheels:** Enter the customer's phone number first. If they are a returning customer, their details will pop up automatically!")
            
        phone = st.text_input("Customer Phone Number", key="cust_search_input")

        c_name, c_loc = "", ""
        if phone and len(phone) > 7:
            existing = supabase.table("orders").select("cust_name, location").eq("shop_id", shop_id).eq("cust_phone", phone).limit(1).execute()
            if existing.data:
                c_name, c_loc = existing.data[0]["cust_name"], existing.data[0]["location"]
                st.info(f"Existing Client: {c_name}")

        with st.form("order_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            name = col1.text_input("Customer Name", value=c_name)
            phone_val = col1.text_input("Phone Number", value=phone)
            loc = col1.text_input("Address", value=c_loc)
            items = col1.number_input("Total Items", min_value=1)

            total = col2.number_input("Total Bill", min_value=0)
            paid = col2.number_input("Amount Paid", min_value=0)
            target = col2.date_input("Due Date")
            notes = st.text_area("Special Instructions")

            if st.form_submit_button("Log Order"):
                if not name or not phone_val:
                    st.error("Missing credentials.")
                else:
                    supabase.table("orders").insert({
                        "shop_id": shop_id, "cust_name": name, "cust_phone": phone_val,
                        "location": loc, "items_count": items, "total_price": total,
                        "amount_paid": paid, "delivery_target": str(target), "notes": notes, "status": "Pickup"
                    }).execute()
                    st.success("Order logged.")
                    st.rerun()

    elif menu == "Shop Floor":
        st.subheader("Active Jobs")
        res = supabase.table("orders").select("*").eq("shop_id", shop_id).neq("status", "Delivered").execute()

        if res.data:
            df = pd.DataFrame(res.data)
            stages = ["Pickup", "Washing", "Ironing", "Ready"]
            cols = st.columns(len(stages))

            for i, stage in enumerate(stages):
                with cols[i]:
                    st.markdown(f"**{stage}**")
                    stage_items = df[df["status"] == stage]

                    for _, r in stage_items.iterrows():
                        with st.container(border=True):
                            st.write(f"**{r['cust_name']}**")
                            st.caption(f"{r['items_count']} pcs | Due: {r['delivery_target']}")

                            with st.expander("View Details"):
                                st.write(f"Phone: {r['cust_phone']}")
                                bal = r['total_price'] - r['amount_paid']
                                st.write(f"Balance: N{bal}")
                                st.write(f"Loc: {r['location']}")
                                if r['notes']: st.info(r['notes'])

                            if stage == "Ready":
                                raw_phone = str(r['cust_phone']).strip().replace(" ", "").replace("+", "").replace("-", "")
                                if raw_phone.startswith("0"):
                                    c_phone = "234" + raw_phone[1:] 
                                else:
                                    c_phone = raw_phone

                                bal_ready = r['total_price'] - r['amount_paid']
                                bal_text = f" Your balance is N{bal_ready:,.0f}." if bal_ready > 0 else ""
                                
                                msg = f"Hello {r['cust_name']}, your clothes are ready and looking sharp at {shop['shop_name']}!{bal_text} You can pick them up anytime or let us know if you prefer delivery."
                                
                                safe_msg = urllib.parse.quote(msg)
                                wa_link = f"https://wa.me/{c_phone}?text={safe_msg}"
                                
                                st.link_button("WhatsApp Nudge", wa_link, use_container_width=True)

                            if st.button("Move", key=f"move_{r['id']}"):
                                next_s = stages[i+1] if i < len(stages)-1 else "Delivered"
                                supabase.table("orders").update({"status": next_s}).eq("id", r["id"]).execute()
                                st.rerun()
        else:
            st.write("Floor is clear.")

    elif menu == "Owner Vault":
        current_pin = shop.get("owner_pin", "0000")
        if not st.session_state.vault_unlocked:
            st.info("Vault Locked. Authorized Personnel Only.")
            st.caption("Hint: Default PIN for new shops is 0000")
            v_pin = st.text_input("Enter Vault PIN", type="password", key="vault_unlock_field")
            if st.button("Unlock"):
                if v_pin == current_pin:
                    st.session_state.vault_unlocked = True
                    st.rerun()
                else: st.error("Access Denied.")
        else:
            col_h, col_l = st.columns([0.8, 0.2])
            col_h.subheader("The Strong Room")
            if col_l.button("Lock Vault", use_container_width=True):
                st.session_state.vault_unlocked = False
                st.rerun()

            res = supabase.table("orders").select("*").eq("shop_id", shop_id).execute()
            
            # --- EXPANDER 1: BUSINESS COMMAND CENTER ---
            with st.expander("📊 Business Command Center", expanded=True):
                if res.data:
                    dfv = pd.DataFrame(res.data)
                    dfv['total_price'] = pd.to_numeric(dfv['total_price']).fillna(0)
                    dfv['amount_paid'] = pd.to_numeric(dfv['amount_paid']).fillna(0)
                    dfv['balance'] = dfv['total_price'] - dfv['amount_paid']

                    if 'created_at' in dfv.columns:
                        dfv['created_at'] = pd.to_datetime(dfv['created_at'])
                    else:
                        dfv['created_at'] = pd.Timestamp.now()

                    st.write("**Revenue & Receivables**")
                    tabs = st.tabs(["Today", "This Week", "This Month", "All Time"])

                    now = pd.Timestamp.now(tz=dfv['created_at'].dt.tz if hasattr(dfv['created_at'].dt, 'tz') else None)
                    today_start = now.normalize()
                    week_start = today_start - pd.Timedelta(days=today_start.weekday())
                    month_start = today_start.replace(day=1)

                    def render_metrics(filtered_df):
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Expected Value", f"N {filtered_df['total_price'].sum():,.0f}")
                        c2.metric("Revenue Collected", f"N {filtered_df['amount_paid'].sum():,.0f}")
                        c3.metric("Outstanding Debt", f"N {filtered_df['balance'].sum():,.0f}")

                    with tabs[0]: render_metrics(dfv[dfv['created_at'] >= today_start])
                    with tabs[1]: render_metrics(dfv[dfv['created_at'] >= week_start])
                    with tabs[2]: render_metrics(dfv[dfv['created_at'] >= month_start])
                    with tabs[3]: render_metrics(dfv)

                    st.divider()

                    st.write("**Total Debt Ledger**")
                    debts_all = dfv[dfv['balance'] > 0].copy()
                    if not debts_all.empty:
                        for _, r in debts_all.iterrows():
                            with st.container(border=True):
                                dc1, dc2, dc3 = st.columns([2, 1, 1])
                                dc1.write(f"**{r['cust_name']}** | {r['cust_phone']}")
                                dc2.write(f"Owes: **N{r['balance']:,.0f}**")
                                if dc3.button("Clear Debt", key=f"clear_debt_{r['id']}"):
                                    supabase.table("orders").update({"amount_paid": r['total_price']}).eq("id", r['id']).execute()
                                    st.success(f"Debt cleared for {r['cust_name']}! Revenue updated.")
                                    st.rerun()
                    else:
                        st.success("No outstanding debts. The book is clean.")

                    st.divider()

                    st.write("**Customer Growth Engine**")
                    g_col1, g_col2 = st.columns(2)

                    customer_stats = dfv.groupby(['cust_name', 'cust_phone']).agg(
                        total_spent=('total_price', 'sum'),
                        last_visit=('created_at', 'max')
                    ).reset_index()

                    with g_col1:
                        with st.container(border=True):
                            st.markdown("**Loyalty Board (Top Spenders)**")
                            top_5 = customer_stats.sort_values('total_spent', ascending=False).head(5)
                            for _, row in top_5.iterrows():
                                st.write(f"{row['cust_name']} (N {row['total_spent']:,.0f})")
                                msg = f"Hello {row['cust_name']}, we were looking at our records at {shop['shop_name']} and we saw how much you have supported us. Because you are one of our special regulars, we have kept a 'Thank You' surprise for your next visit. Just show this message to the manager when you come in so they can give you what we kept for you. We really appreciate your business."
                                
                                raw_phone = str(row['cust_phone']).strip().replace(" ", "").replace("+", "").replace("-", "")
                                if raw_phone.startswith("0"):
                                    c_phone = "234" + raw_phone[1:]
                                else:
                                    c_phone = raw_phone
                                
                                safe_msg = urllib.parse.quote(msg)
                                wa_link = f"https://wa.me/{c_phone}?text={safe_msg}"
                                
                                st.link_button(f"Reward {row['cust_name']}", wa_link, use_container_width=True)

                    with g_col2:
                        with st.container(border=True):
                            st.markdown("**Churn Risk (Absent > 21 Days)**")
                            twenty_one_days_ago = now - pd.Timedelta(days=21)
                            at_risk = customer_stats[customer_stats['last_visit'] < twenty_one_days_ago].sort_values('last_visit').head(5)

                            if not at_risk.empty:
                                for _, row in at_risk.iterrows():
                                    days_absent = (now - row['last_visit']).days
                                    st.write(f"{row['cust_name']} (Away {days_absent} days)")
                                    msg = f"Hello {row['cust_name']}, it has been a while since we saw you at {shop['shop_name']}. We truly miss having you around. To welcome you back, we have set aside a special gift for your next drop-off. It is only waiting for you for a short time, so try and stop by this week so it doesn't pass you by. Looking forward to seeing you again."
                                    
                                    raw_phone = str(row['cust_phone']).strip().replace(" ", "").replace("+", "").replace("-", "")
                                    if raw_phone.startswith("0"):
                                        c_phone = "234" + raw_phone[1:]
                                    else:
                                        c_phone = raw_phone
                                    
                                    safe_msg = urllib.parse.quote(msg)
                                    wa_link = f"https://wa.me/{c_phone}?text={safe_msg}"
                                    
                                    st.link_button(f"Win Back {row['cust_name']}", wa_link, use_container_width=True)
                            else:
                                st.write("All customers have visited recently.")
                else:
                    st.info("No business data available yet.")

            # --- SPRINT 7: SHOP COMMAND CENTER (PROFILE CLEANUP) ---
            with st.expander("⚙️ Shop Command Center", expanded=False):
                prof_tab, sec_tab = st.tabs(["Edit Profile", "Security Settings"])

                with prof_tab:
                    with st.form("edit_profile_form"):
                        st.markdown("**Update Shop Details**")
                        # Shop Code removed entirely from user view/edit
                        new_name = st.text_input("Shop Name", value=st.session_state.shop_info.get("shop_name", ""))
                        new_phone = st.text_input("Owner Phone", value=st.session_state.shop_info.get("owner_phone", ""))
                        
                        submit_profile = st.form_submit_button("Save Changes")
                        
                        if submit_profile:
                            try:
                                supabase.table("shops").update({
                                    "shop_name": new_name,
                                    "owner_phone": new_phone
                                }).eq("id", shop_id).execute()
                                
                                st.session_state.shop_info["shop_name"] = new_name
                                st.session_state.shop_info["owner_phone"] = new_phone
                                
                                st.success("Profile updated. If you changed your Shop Name, use the new one to log in next time.")
                            except Exception as e:
                                st.error(f"Network error, try again: {e}")

                # --- SPRINT 5: SECURITY TAB REDESIGN ---
                with sec_tab:
                    st.markdown("**Manage Access PINs & Settings**")
                    
                    st.markdown("**System Settings**")
                    st.session_state.trainer_wheels = st.toggle("Trainer Wheels (Show guides & hints for new staff)", value=st.session_state.trainer_wheels)
                    if st.session_state.trainer_wheels:
                        st.caption("Trainer Wheels active: Staff will see extra instructions on how to log orders.")
                    st.divider()

                    sec_col1, sec_col2 = st.columns(2)

                    with sec_col1:
                        st.markdown("**Change Owner Vault PIN**")
                        current_v_pin = st.text_input("Current Vault PIN", type="password")
                        new_owner_p = st.text_input("New Vault PIN", type="password", key="new_owner_pin")
                        
                        if st.button("Update Vault PIN"):
                            if current_v_pin != st.session_state.shop_info.get("owner_pin", "0000"):
                                st.error("Incorrect Current PIN.")
                            elif len(new_owner_p) < 4:
                                st.error("New PIN must be at least 4 digits.")
                            else:
                                supabase.table("shops").update({"owner_pin": new_owner_p}).eq("id", shop_id).execute()
                                st.session_state.shop_info["owner_pin"] = new_owner_p
                                st.success("Vault PIN secured.")

                    with sec_col2:
                        st.markdown("**Change Shop/Staff PIN**")
                        st.caption("Must include letters, numbers, and symbols (7+ chars).")
                        current_s_pin = st.text_input("Current Shop PIN", type="password")
                        new_shop_p = st.text_input("New Shop PIN", type="password", key="new_shop_pin")
                        
                        if st.button("Update Shop PIN"):
                            staff_check = supabase.table("staff").select("pin").eq("shop_id", shop_id).limit(1).execute()
                            actual_current = staff_check.data[0]['pin'] if staff_check.data else ""
                            
                            if current_s_pin != actual_current:
                                st.error("Incorrect Current Shop PIN.")
                            elif len(new_shop_p) < 7 or not re.search(r"[a-zA-Z]", new_shop_p) or not re.search(r"\d", new_shop_p) or not re.search(r"[\W_]", new_shop_p):
                                st.error("PIN is too weak. Make sure it has 7+ characters, letters, numbers, and a symbol.")
                            else:
                                supabase.table("staff").update({"pin": new_shop_p}).eq("shop_id", shop_id).execute()
                                st.success("Staff PIN secured.")

# APP ROUTER
if not st.session_state.auth:
    login_gate()

elif st.session_state.is_master:
    st.title("Washh Master Control")
    menu = st.sidebar.radio("Command", ["Network Health", "Onboarding", "Access Management"])

    # --- SPRINT 8: SUBSCRIPTION RADAR (Master Control untouched except for this tab) ---
    if menu == "Network Health":
        st.subheader("Global Operations & Subscriptions")
        res = supabase.table("shops").select("*").execute()
        
        if res.data:
            df_shops = pd.DataFrame(res.data)
            
            # Calculate days left
            df_shops['expiry_date'] = pd.to_datetime(df_shops['expiry_date']).dt.date
            today = date.today()
            df_shops['days_left'] = (df_shops['expiry_date'] - today).dt.days
            
            # Sort so the ones expiring soonest (or expired) are at the top
            df_shops = df_shops.sort_values('days_left')

            st.metric("Active Partners", len(df_shops[df_shops['is_active'] == True]))
            
            st.divider()
            st.markdown("### 📡 Subscription Radar")
            st.caption("Track who is expiring and nudge them to pay.")

            for _, s in df_shops.iterrows():
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 1, 1.5])
                    
                    status_emoji = "🟢" if s['is_active'] else "🔴"
                    c1.write(f"**{status_emoji} {s['shop_name']}**")
                    c1.caption(f"Phone: {s['owner_phone']}")
                    
                    d_left = s['days_left']
                    if d_left > 3:
                        c2.success(f"{d_left} Days Left")
                        msg = f"Boss! Hope the Washh system is keeping '{s['shop_name']}' running smoothly. Just a heads up, your subscription renews in {d_left} days! 🚀"
                    elif d_left > 0:
                        c2.warning(f"{d_left} Days Left")
                        msg = f"Boss! Your Washh system for '{s['shop_name']}' expires in {d_left} days. Let's get that ₦20k renewal sorted so your shop floor doesn't experience downtime! ⏰"
                    elif d_left == 0:
                        c2.error("Expires TODAY")
                        msg = f"Boss! Your Washh access for '{s['shop_name']}' expires TODAY. Send the ₦20k renewal now so the system doesn't lock your front desk out at midnight! 🚨"
                    else:
                        c2.error(f"Expired {-d_left} days ago")
                        msg = f"Boss! Your Washh system for '{s['shop_name']}' is currently locked. Let's get your renewal sorted so your staff can start logging orders again! 🔓"

                    # Naija-proof the admin out-bound message
                    raw_phone = str(s['owner_phone']).strip().replace(" ", "").replace("+", "").replace("-", "")
                    if raw_phone.startswith("0"): c_phone = "234" + raw_phone[1:]
                    else: c_phone = raw_phone
                    
                    safe_msg = urllib.parse.quote(msg)
                    wa_link = f"https://wa.me/{c_phone}?text={safe_msg}"
                    
                    c3.link_button("Send WhatsApp Nudge 📲", wa_link, use_container_width=True)

            st.divider()
            st.write("**Quick Actions: Status & Renewal Override**")
            with st.form("renewal_form", clear_on_submit=True):
                col1, col2, col3 = st.columns(3)
                
                shop_list = df_shops['shop_name'].tolist()
                t_name = col1.selectbox("Select Shop to Update", shop_list)
                t_status = col2.selectbox("Set Active", [True, False])
                t_expiry = col3.date_input("New Expiry Date")
                
                if st.form_submit_button("Update Partner"):
                    supabase.table("shops").update({"is_active": t_status, "expiry_date": str(t_expiry)}).eq("shop_name", t_name).execute()
                    st.success(f"Shop '{t_name}' updated successfully!")
                    st.rerun()

    elif menu == "Onboarding":
        st.subheader("New Partner Onboarding")
        st.info("Note: Partners can now self-onboard from the login page. This tab is for manual overrides.")
        with st.form("new_shop", clear_on_submit=True):
            s_name = st.text_input("Business Name")
            s_code = st.text_input("Unique Shop Code")
            s_expiry = st.date_input("Expiry Date")
            if st.form_submit_button("Deploy"):
                if s_name and s_code:
                    supabase.table("shops").insert({
                        "shop_name": s_name, "shop_code": s_code,
                        "is_active": True, "expiry_date": str(s_expiry), "owner_pin": "0000"
                    }).execute()
                    st.success(f"Deployed {s_name}.")
                    st.rerun()
                else:
                    st.error("Missing Info.")

    elif menu == "Access Management":
        st.subheader("Staff PIN Setup")
        shops_res = supabase.table("shops").select("id, shop_name").execute()
        if shops_res.data:
            s_list = {s['shop_name']: s['id'] for s in shops_res.data}
            target = st.selectbox("Select Shop", list(s_list.keys()))
            with st.form("new_pin", clear_on_submit=True):
                s_staff = st.text_input("Staff Name (e.g. Front Desk)")
                p = st.text_input("New PIN", type="password")
                if st.form_submit_button("Save PIN"):
                    if len(p) >= 4 and s_staff:
                        supabase.table("staff").insert({
                            "shop_id": s_list[target],
                            "staff_name": s_staff,
                            "pin": p
                        }).execute()
                        st.success(f"Access granted for {s_staff}.")
                        st.rerun()
                    else:
                        st.error("Staff Name and a 4-digit PIN are required.")

    if st.button("Logout of Master"):
        st.session_state.clear()
        st.rerun()

else:
    shop_workspace()
