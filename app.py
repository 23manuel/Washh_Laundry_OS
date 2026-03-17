# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import re
from supabase import create_client, Client
from datetime import datetime, date

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

# LOGIN GATE
def login_gate():
    st.title("Washh: Access Portal")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            shop_code = st.text_input("Shop Code", key="gate_shop_code").strip()
            pin = st.text_input("Staff PIN", type="password", key="gate_staff_pin")

            if st.button("Enter Workspace", use_container_width=True):
                # Master Backdoor
                if shop_code == st.secrets["auth"]["master_code"] and pin == st.secrets["auth"]["master_pin"]:
                    st.session_state.auth = True
                    st.session_state.is_master = True
                    st.rerun()

                # Tenant Verification
                res = supabase.table("shops").select("*").eq("shop_code", shop_code).execute()
                if res.data:
                    shop = res.data[0]
                    expiry = datetime.strptime(shop["expiry_date"], "%Y-%m-%d").date()

                    if not shop.get("is_active", True) or date.today() > expiry:
                        st.error("Account Suspended. Contact Administration.")
                    else:
                        staff = supabase.table("staff").select("*").eq("shop_id", shop["id"]).eq("pin", pin).execute()
                        if staff.data:
                            st.session_state.auth = True
                            st.session_state.shop_info = shop
                            st.rerun()
                        else:
                            st.error("Invalid Staff PIN.")
                else:
                    st.error("Shop Code not found.")

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
                                c_phone = str(r['cust_phone']).replace(" ", "").replace("+", "")
                                bal_ready = r['total_price'] - r['amount_paid']
                                
                                # Only mention balance if they actually owe money
                                bal_text = f" Your balance is N{bal_ready:,.0f}." if bal_ready > 0 else ""
                                
                                msg = f"Hello {r['cust_name']}, your clothes are ready and looking sharp at {shop['shop_name']}!{bal_text} You can pick them up anytime or let us know if you prefer delivery."
                                
                                st.link_button("WhatsApp Nudge", f"https://wa.me/{c_phone}?text={msg.replace(' ', '%20')}", use_container_width=True)

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
            
            # --- EXPANDER 1: BUSINESS COMMAND CENTER (Open by default) ---
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
                                c_phone = str(row['cust_phone']).replace(" ", "").replace("+", "")
                                st.link_button(f"Reward {row['cust_name']}", f"https://wa.me/{c_phone}?text={msg.replace(' ', '%20')}", use_container_width=True)

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
                                    c_phone = str(row['cust_phone']).replace(" ", "").replace("+", "")
                                    st.link_button(f"Win Back {row['cust_name']}", f"https://wa.me/{c_phone}?text={msg.replace(' ', '%20')}", use_container_width=True)
                            else:
                                st.write("All customers have visited recently.")
                else:
                    st.info("No business data available yet.")

            # --- EXPANDER 2: SHOP COMMAND CENTER (Closed by default) ---
            with st.expander("⚙️ Shop Command Center", expanded=False):
                prof_tab, sec_tab = st.tabs(["Edit Profile", "Security Settings"])

                with prof_tab:
                    with st.form("edit_profile_form"):
                        st.markdown("**Update Shop Details**")
                        new_name = st.text_input("Shop Name", value=st.session_state.shop_info.get("shop_name", ""))
                        new_phone = st.text_input("Owner Phone", value=st.session_state.shop_info.get("owner_phone", ""))
                        new_code = st.text_input("Shop Code (e.g., SIMON01)", value=st.session_state.shop_info.get("shop_code", ""))
                        
                        submit_profile = st.form_submit_button("Save Changes")
                        
                        if submit_profile:
                            if not re.match(r"^[A-Z]+[0-9]+$", new_code):
                                st.error("Boss, Shop Code must be CAPITAL LETTERS followed by numbers (e.g., WASHH01). No spaces.")
                            else:
                                try:
                                    supabase.table("shops").update({
                                        "shop_name": new_name,
                                        "owner_phone": new_phone,
                                        "shop_code": new_code
                                    }).eq("id", shop_id).execute()
                                    
                                    st.session_state.shop_info["shop_name"] = new_name
                                    st.session_state.shop_info["owner_phone"] = new_phone
                                    st.session_state.shop_info["shop_code"] = new_code
                                    
                                    st.success("Profile updated successfully. Your shop is locked in.")
                                except Exception as e:
                                    st.error(f"Network error, try again: {e}")

                with sec_tab:
                    st.markdown("**Manage Access PINs**")
                    sec_col1, sec_col2 = st.columns(2)

                    with sec_col1:
                        st.markdown("**Owner Vault PIN**")
                        new_owner_p = st.text_input("New Vault PIN", type="password", key="new_owner_pin")
                        if st.button("Update Vault PIN"):
                            if len(new_owner_p) >= 4:
                                supabase.table("shops").update({"owner_pin": new_owner_p}).eq("id", shop_id).execute()
                                st.session_state.shop_info["owner_pin"] = new_owner_p
                                st.success("Vault PIN secured.")
                            else:
                                st.error("PIN must be at least 4 digits.")

                    with sec_col2:
                        st.markdown("**Shop/Staff PIN**")
                        new_shop_p = st.text_input("New Shop PIN", type="password", key="new_shop_pin")
                        if st.button("Update Shop PIN"):
                            if len(new_shop_p) >= 4:
                                supabase.table("staff").update({"pin": new_shop_p}).eq("shop_id", shop_id).execute()
                                st.success("Staff PIN secured.")
                            else:
                                st.error("PIN must be at least 4 digits.")

# APP ROUTER
if not st.session_state.auth:
    login_gate()

elif st.session_state.is_master:
    st.title("Washh Master Control")
    menu = st.sidebar.radio("Command", ["Network Health", "Onboarding", "Access Management"])

    if menu == "Network Health":
        st.subheader("Global Operations")
        res = supabase.table("shops").select("*").execute()
        if res.data:
            df_shops = pd.DataFrame(res.data)
            st.metric("Active Partners", len(df_shops[df_shops['is_active'] == True]))
            st.dataframe(df_shops[['shop_name', 'shop_code', 'is_active', 'expiry_date']], use_container_width=True, hide_index=True)

            st.divider()
            st.write("**Quick Actions: Status & Renewal**")
            with st.form("renewal_form", clear_on_submit=True):
                col1, col2, col3 = st.columns(3)
                t_code = col1.text_input("Shop Code")
                t_status = col2.selectbox("Set Active", [True, False])
                t_expiry = col3.date_input("New Expiry Date")
                if st.form_submit_button("Update Partner"):
                    if t_code:
                        supabase.table("shops").update({"is_active": t_status, "expiry_date": str(t_expiry)}).eq("shop_code", t_code).execute()
                        st.success(f"Shop {t_code} updated!")
                        st.rerun()
                    else:
                        st.error("Enter Shop Code.")

    elif menu == "Onboarding":
        st.subheader("New Partner Onboarding")
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
