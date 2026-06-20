Security Audit: app.py

CRITICAL Issues

1. Plain Text Password Storage (Lines 161, 589)

Location: Lines 161, 589

Issue: Passwords stored directly in Supabase without hashing

Evidence:

# Line 161 - Signup
supabase.table("staff").insert({
    "password": new_password,  # Plain text
}).execute()

# Line 589 - Master control onboarding
supabase.table("staff").insert({
    "password": p,  # Plain text
}).execute()

Impact: Full compromise of all staff credentials if Supabase is breached

2. Hard-Coded Default PIN (Lines 152, 567)

Location: Lines 152, 567

Issue: All new businesses created with identical default PIN "0000"

Evidence:

"owner_pin": "0000"  # Line 152
"owner_pin": "0000"  # Line 567

Impact: Any new shop is immediately accessible to attackers who know the default PIN

Compounded by: Line 278 explicitly hints at this default PIN to users

3. Plain Text PIN Comparison (Lines 281, 444)

Location: Lines 281, 444

Issue: PINs compared directly in memory without hashing

Evidence:

# Line 281 - Vault unlock
if v_pin == current_pin:

# Line 444 - PIN change verification
if current_v_pin != st.session_state.shop_info.get("owner_pin", "0000"):

Impact: PIN values exposed in session state and memory

4. Master Backdoor in Client Code (Lines 59, 61)

Location: Lines 59-62

Issue: Master access credentials stored in plaintext in app code and checked client-side

Evidence:

if business_input_name == st.secrets["auth"]["master_code"] and password == st.secrets["auth"]["master_pin"]:
    st.session_state.auth = True
    st.session_state.is_master = True

Impact:

Master credentials visible to anyone with access to code/binary

No server-side validation

Single credential pair grants unlimited access to all businesses

Attacker can immediately access master control panel to disable all shops or modify all data

5. Plain Text Password in Database Query (Line 90)

Location: Line 90

Issue: Password transmitted and queried as plain text

Evidence:

staff = supabase.table("staff").select("*").eq("business_id", laundry["id"]).eq("password", password).execute()

Impact: Password exposed in query logs, network traffic, database logs

HIGH Issues

6. No SQL Injection Protection on Business Name (Lines 65, 128, 544)

Location: Lines 65, 128, 544

Issue: Unsanitized business names used in Supabase queries with ilike and eq

Evidence:

# Line 65 - Login
res = supabase.table("laundries").select("*").ilike("business_name", business_input_name).execute()

# Line 128 - Signup duplicate check
name_check = supabase.table("laundries").select("business_name").ilike("business_name", new_business_name).execute()

# Line 544 - Master update
supabase.table("laundries").update({"is_active": t_status, "expiry_date": str(t_expiry)}).eq("business_name", t_name).execute()

Impact: Potential for query manipulation if Supabase's query builder is vulnerable

7. Session State Authorization Bypass (Lines 33-37, 60-61, 92-93, 168-169)

Location: Lines 33-37, 60-61, 92-93, 168-169

Issue: All authorization stored entirely in client-side Streamlit session state

Evidence:

if "auth" not in st.session_state: st.session_state.auth = False
if "is_master" not in st.session_state: st.session_state.is_master = False

st.session_state.auth = True  # Line 60, 92, 168
st.session_state.is_master = True  # Line 61

Impact:

Attacker can modify browser storage to change st.session_state.auth = True

Can escalate to master by changing st.session_state.is_master = True

No server-side session validation after login

No session tokens or signed cookies

8. No Authorization Check on Business Operations (Lines 195, 216, 226)

Location: Lines 195, 216, 226, 292

Issue: Only checks business_id from session state, which is controlled by client

Evidence:

# Line 195 - Order lookup
existing = supabase.table("orders").select("cust_name, location").eq("business_id", business_id).execute()

# Line 216 - Order insert (uses business_id from session)
supabase.table("orders").insert({
    "business_id": business_id,
    ...
}).execute()

# Line 292 - Vault access
res = supabase.table("orders").select("*").eq("business_id", business_id).execute()

Impact:

If attacker modifies st.session_state.shop_info["id"] to another business's ID, they access that business's data

Horizontal privilege escalation: access any business's orders and financial data

No server-side verification that user owns the business_id they're querying

9. Master Control Accessible Without Proper Role Verification (Lines 475-600)

Location: Lines 475-600

Issue: Master control panel only checks client-side is_master flag

Evidence:

elif st.session_state.is_master:
    st.title("Washh Master Control")
    menu = st.sidebar.radio("Command", ["Network Health", "Onboarding", "Access Management"])

Impact:

Attacker who sets st.session_state.is_master = True gains access to:

All business data (Line 482)

Ability to create new businesses (Line 559)

Ability to create staff accounts for any business (Line 586)

Ability to disable any business (Line 544)

10. No Rate Limiting on Login Attempts (Lines 57-98)

Location: Lines 57-98

Issue: No protection against brute force attacks on business names or passwords

Evidence:

if st.button("Enter Workspace", use_container_width=True):
    # No rate limiting, no attempt counter
    res = supabase.table("laundries").select("*").ilike("business_name", business_input_name).execute()

Impact:

Attacker can brute force business names (max 4-character codes are weak)

Attacker can brute force staff passwords

Streamlit reruns on every click with no throttling

11. Supabase Client Uses Service Role Key (Lines 26-28)

Location: Lines 26-28

Issue: Supabase client initialized with full service role key accessible from st.secrets

Evidence:

@st.cache_resource
def init_connection() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]  # Likely the service key
    return create_client(url, key)

Impact:

If key is the service role key (not anon key), all RLS policies are bypassed

Full database access from frontend

No row-level security enforced

12. Vault Unlock Stored in Session State (Lines 276-282, 289)

Location: Lines 276-282, 289

Issue: Vault unlock status stored in client-side session state with no timeout

Evidence:

if not st.session_state.vault_unlocked:
    # ... PIN check ...
    st.session_state.vault_unlocked = True  # Line 282
    st.rerun()
else:
    # Full access to financial data

Impact:

Once vault is unlocked, it remains unlocked for the entire session

No re-authentication for sensitive operations

No timeout or activity log

MEDIUM Issues

13. Weak Master Code Generation (Lines 138-139)

Location: Lines 138-139

Issue: Business codes generated with weak entropy (only 4 characters, ASCII uppercase + digits)

Evidence:

random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
auto_code = f"WASHH-{random_str}"

Impact:

Only 36^4 = 1.67 million possible codes

Business code visible in signup message (Line 139)

Weak for any security-critical use

14. Plain Text Credentials in Session State (Lines 93, 169)

Location: Lines 93, 169

Issue: Entire laundry business record (including owner_pin and all data) stored in session state

Evidence:

st.session_state.shop_info = laundry  # Line 93, 169
# Contains: business_name, owner_pin, owner_phone, is_active, etc.

Impact:

All business data persisted in browser memory/state

Can be accessed by browser extensions or malicious JavaScript

Owner PIN visible in shop_info dict

15. No Input Validation on Phone Numbers (Lines 110, 203)

Location: Lines 110, 203, and throughout

Issue: Phone numbers accepted without validation

Evidence:

new_phone = st.text_input("Phone Number", placeholder="080...").strip()
# No validation, no format checking

Impact:

Invalid data in database

SQL injection risk if values used in queries

User enumeration (can check all phone numbers via signup)

16. No CSRF Protection (Lines 57, 117, 212, 410, 443, 459, 543, 584)

Location: Throughout form submissions

Issue: Streamlit forms have no CSRF tokens

Evidence:

if st.button("Enter Workspace", use_container_width=True):
    # No CSRF token validation

if st.form_submit_button("Create profile", use_container_width=True):
    # No CSRF token validation

Impact:

Cross-site request forgery possible if user authenticated to site in another tab

Malicious site can trigger account creation, orders, etc.

17. No Audit Logging of Sensitive Operations (Lines 78, 216, 269, 337, 414, 449, 468, 544, 586)

Location: Throughout database writes

Issue: No logging of who performed what action and when

Evidence:

supabase.table("laundries").update({"is_active": False}).eq("id", laundry["id"]).execute()
# No audit trail

Impact:

Cannot detect unauthorized access

Cannot trace who disabled a business or modified orders

Regulatory compliance issues

18. Plaintext Display of Financial Data (Lines 317-319, 334-335)

Location: Lines 317-319, 334-335

Issue: Sensitive financial data displayed without encryption in Streamlit UI

Evidence:

c1.metric("Expected Value", f"N {filtered_df['total'].sum():,.0f}")
c2.metric("Revenue Collected", f"N {filtered_df['amount_paid'].sum():,.0f}")
c3.metric("Outstanding Debt", f"N {filtered_df['balance'].sum():,.0f}")

dc2.write(f"Owes: **N{r['balance']:,.0f}**")

Impact:

Accessible via browser cache, history, and network tools

No encryption or masking of sensitive amounts

19. User Enumeration via Signup (Lines 128, 133)

Location: Lines 128, 133

Issue: Explicit error messages reveal whether business names and phone numbers are registered

Evidence:

st.error(f"The name '{new_business_name}' is already taken. Try adding your location...")
st.error("This phone number is already registered to another business.")

Impact:

Attacker can enumerate all business names and phone numbers

Can map business names to phone numbers

20. No HTTPS Enforcement Visible (No TLS pinning)

Location: Lines 26-28, 85, 263, 529

Issue: Supabase communications may not enforce HTTPS; no certificate pinning

Evidence:

url = st.secrets["supabase"]["url"]  # Could be HTTP
wa_link = f"https://wa.me/{c_phone}?text={safe_msg}"  # Only WhatsApp is HTTPS

Impact:

Supabase credentials could be intercepted if URL is HTTP

Man-in-the-middle attacks possible

21. Exception Messages Expose Sensitive Details (Line 424)

Location: Line 424

Issue: Exception details displayed to user

Evidence:

except Exception as e:
    st.error(f"Network error, try again: {e}")

Impact:

Database error messages may leak schema, column names, or other sensitive info

LOW Issues

22. Hardcoded Admin WhatsApp Number (Line 40)

Location: Line 40

Issue: Admin phone number hardcoded in application

Evidence:

ADMIN_WA_NUMBER = "2348058535372"

Impact:

Phone number exposed in code

Could be changed via code injection

23. Weak PIN Requirements (Lines 446-447)

Location: Lines 446-447

Issue: Vault PIN only requires 4 digits (10,000 possible values)

Evidence:

elif len(new_owner_p) < 4:
    st.error("New PIN must be at least 4 digits.")

Impact:

Easy to brute force with 10,000 possible values

No rate limiting on attempts (Issue #10)

24. Time-Based Expiry Without Server Validation (Lines 69, 71, 489-490)

Location: Lines 69, 71, 489-490

Issue: Subscription expiry checked client-side only

Evidence:

expiry = datetime.strptime(laundry["expiry_date"], "%Y-%m-%d").date()
is_expired = date.today() > expiry

Impact:

Client could modify expiry_date in shop_info to extend access

No server-side expiry enforcement

25. Unsanitized URL Construction (Lines 262-263, 529)

Location: Lines 262-263, 529

Issue: User data embedded in WhatsApp URLs without full sanitization

Evidence:

safe_msg = urllib.parse.quote(msg)
wa_link = f"https://wa.me/{c_phone}?text={safe_msg}"

Impact:

If message contains attacker-controlled data, could craft malicious WhatsApp links

Low risk as customer data is trusted, but violates defense-in-depth

Summary Table

Severity

Count

Issues

CRITICAL

5

Plain text passwords, default PIN, PIN comparison, master backdoor, password in queries

HIGH

7

SQL injection risk, session auth bypass, no authorization checks, master control exposure, no rate limiting, service key exposure, vault session storage

MEDIUM

8

Weak code generation, credentials in session, no input validation, no CSRF, no audit logging, plaintext financial data, user enumeration, no HTTPS enforcement, exception details

LOW

3

Hardcoded phone number, weak PIN requirements, client-side expiry checks, unsanitized URLs


Data Integrity Audit: app.py

CRITICAL Issues

1. Orphaned Staff Records After Business Signup Failure (Lines 144-164)

Location: Lines 144-164

Issue: Business creation and staff creation are two separate, unrelated Supabase calls with no transaction

Evidence:

# Line 144-153: Insert business
new_laundry = supabase.table("laundries").insert({
    "business_name": new_business_name,
    ...
}).execute()

shop_record = new_laundry.data[0]

# Line 158-164: Insert staff (separate, unprotected call)
supabase.table("staff").insert({
    "business_id": shop_record["id"],
    ...
}).execute()

Impact:

If staff insertion fails but business creation succeeds, orphaned business exists with no staff account

User believes signup failed but business is created in database

If business insertion fails but Streamlit caches the response, staff insert could reference non-existent shop_record["id"] (IndexError)

No rollback mechanism

2. No Error Checking on execute() Responses (Throughout)

Location: Lines 78, 90, 144, 158, 216, 269, 292, 337, 414, 449, 468, 544, 559, 586

Issue: All Supabase operations assume success with no validation of response

Evidence:

new_laundry = supabase.table("laundries").insert({...}).execute()
shop_record = new_laundry.data[0]  # Crashes if data is empty

supabase.table("orders").insert({...}).execute()  # Success assumed
st.success("Order logged.")  # Claimed success without validation

supabase.table("orders").update({...}).execute()  # No check if update affected rows

Impact:

If insert/update fails, code proceeds as if successful

new_laundry.data[0] will raise IndexError if insert failed

User sees success message even if data wasn't written

Silent data loss or corruption

3. Duplicate Business Name Signup Race Condition (Lines 127-155)

Location: Lines 127-155

Issue: Check-then-act pattern with no atomic constraint

Evidence:

# Line 128: Check for duplicate
name_check = supabase.table("laundries").select("business_name").ilike("business_name", new_business_name).execute()
if name_check.data:
    st.error("The name is taken.")
else:
    # Line 144: Insert (race window here)
    new_laundry = supabase.table("laundries").insert({
        "business_name": new_business_name,
        ...
    }).execute()

Impact:

Two users can simultaneously pass the duplicate check and both insert the same business name

Duplicate business names in database

Violates assumed unique constraint on business_name

Login will grab res.data[0] (line 68), returning arbitrary duplicate

4. Duplicate Phone Number Signup Race Condition (Lines 132-155)

Location: Lines 132-155

Issue: Same check-then-act pattern for phone numbers

Evidence:

# Line 133: Check for duplicate
phone_check = supabase.table("laundries").select("owner_phone").eq("owner_phone", new_phone).execute()
if phone_check.data:
    st.error("Phone already registered.")
else:
    # Line 144: Insert (race window here)
    new_laundry = supabase.table("laundries").insert({...}).execute()

Impact:

Same as business name race condition

Multiple businesses with same phone number

Violates assumed unique constraint

5. Order Amount Fields Can Become Inconsistent (Lines 207-220, 337)

Location: Lines 207-220, 337

Issue: total and amount_paid are separate fields with no constraint that amount_paid <= total

Evidence:

# Line 207-208: User can enter arbitrary amounts
total = col2.number_input("Total Bill", min_value=0)
paid = col2.number_input("Amount Paid", min_value=0)

# Line 337: Direct update without validation
supabase.table("orders").update({"amount_paid": r['total']}).eq("id", r["id"]).execute()

Impact:

User could enter paid > total (e.g., total=1000, paid=5000)

Negative balance displayed (line 245: bal = r['total'] - r['amount_paid'])

Financial reports show incorrect debt (line 300: balance = total - amount_paid)

"Clear Debt" button sets amount_paid = r['total'] without checking current state (race condition)

6. Lost Staff Password Update When Multiple Staff Exist (Lines 460-469)

Location: Lines 460-469

Issue: Password update uses .limit(1) but updates all staff for the business

Evidence:

# Line 460: Fetch only first staff record
staff_check = supabase.table("staff").select("password").eq("business_id", business_id).limit(1).execute()
actual_current = staff_check.data[0]['password'] if staff_check.data else ""

# Line 468: But update affects ALL staff
supabase.table("staff").update({"password": new_shop_p}).eq("business_id", business_id).execute()

Impact:

If business has multiple staff, actual_current is only 1 staff's password

Verification happens against wrong staff member

.update().eq("business_id", business_id) updates ALL staff passwords, not just the current user

All staff passwords get overwritten to match one staff member's change

Other staff accounts broken or changed without their consent

7. Session State Not Synced With Database After Updates (Lines 419-420, 450)

Location: Lines 419-420, 450

Issue: Session state updated locally but may diverge from actual database state

Evidence:

# Line 414-417: Database updated
supabase.table("laundries").update({
    "business_name": new_name,
    "owner_phone": new_phone
}).eq("id", business_id).execute()

# Line 419-420: Session state updated (could fail)
st.session_state.shop_info["business_name"] = new_name
st.session_state.shop_info["owner_phone"] = new_phone

Impact:

If database update succeeds but session state assignment fails, user sees old data locally

If exception occurs (line 424), session state isn't updated but database is

Other sessions/devices will see new data, current user sees old data

Login name changed in database but user doesn't know

HIGH Issues

8. Status Transitions Not Validated (Lines 230-270)

Location: Lines 230-270

Issue: Status field can be set to ANY value; no enum validation

Evidence:

stages = ["Received", "Sorting", "Processing", "Quality Check", "Ready"]
# ... line 268 ...
next_s = stages[i+1] if i < len(stages)-1 else "Delivered"
supabase.table("orders").update({"status": next_s}).eq("id", r["id"]).execute()

Impact:

If stages list is modified or corrupted, invalid statuses written

No constraint prevents setting status to invalid values

UI expects specific statuses but database may contain garbage

Filtering on status (line 226: .neq("status", "Delivered")) could miss orders in invalid states

Operations view (line 236: df[df["status"] == stage]) silently skips orders with misspelled statuses

9. Column Name Inconsistencies Cause Silent Data Loss (Lines 241, 349)

Location: Lines 241, 349

Issue: Code references column names that don't exist in the data

Evidence:

# Line 241: Tries to access 'delivery_target' (column is 'delivery_date')
st.caption(f"{r['items_count']} pcs | Due: {r['delivery_target']}")

# Line 349: Tries to sum 'total_price' (column is 'total')
customer_stats = dfv.groupby(['cust_name', 'cust_phone']).agg(
    total_spent=('total_price', 'sum'),  # ← This column doesn't exist
    ...
).reset_index()

Impact:

Line 241 throws KeyError runtime (breaks Operations view)

Line 349 silently creates NaN values for total_spent (Loyalty Board shows $0 for all customers)

Financial analysis completely wrong (line 358: top spenders all show N 0.00)

Business owner makes decisions based on zero financial data

10. Clear Debt Button Race Condition (Lines 336-339)

Location: Lines 336-339

Issue: Button reads balance from DataFrame but database could change between read and write

Evidence:

# Line 337: Reads r['total'] from loaded DataFrame (stale)
if dc3.button("Clear Debt", key=f"clear_debt_{r['id']}"):
    supabase.table("orders").update({"amount_paid": r['total']}).eq("id", r["id"]).execute()

Impact:

If order's total changes after DataFrame is loaded, incorrect amount is set

User thinks they're clearing exact debt but database has different amount

If same order updated by another user, Clear Debt overwrites their change

Two staff members both hitting "Clear Debt" on same order: first clears it correctly, second overwrites it with stale amount

11. Metadata Fields Missing From New Staff/Business (Lines 163, 591)

Location: Lines 163, 591

Issue: created_at set as string, but timestamp handling is inconsistent

Evidence:

# Line 163: String timestamp
"created_at": str(datetime.now())

# Line 303-305: Code assumes created_at might not exist or needs conversion
if 'created_at' in dfv.columns:
    dfv['created_at'] = pd.to_datetime(dfv['created_at'])
else:
    dfv['created_at'] = pd.Timestamp.now()

Impact:

Timestamp format inconsistent with Supabase standards (should be ISO 8601)

Pandas conversion may fail on malformed timestamps

Expiry date filtering uses date.today() (Python date) vs pd.Timestamp (pandas)

Timezone handling broken (line 310: attempts to access .dt.tz which may not exist)

12. Business Name Change Breaks Login Without User Knowledge (Lines 414-420)

Location: Lines 414-420

Issue: Business name is the login identifier, but change happens silently

Evidence:

supabase.table("laundries").update({
    "business_name": new_name,
    ...
}).eq("id", business_id).execute()

st.success("Profile updated. If you changed your Business Name, use the new one to log in next time.")

Impact:

User changes business name, logs out, tries to log in with OLD name → fails

No confirmation dialog

User may not remember the new name they just set

If business name changed to conflict with another business (race condition), login logic grabs wrong business

13. Missing Data Validation When Rendering Orders (Lines 245-248)

Location: Lines 245-248

Issue: DataFrame values assumed to exist and be numeric, no null checks

Evidence:

bal = r['total'] - r['amount_paid']  # What if these are NULL or missing?
st.write(f"Balance: N{bal}")

if r['notes']: st.info(r['notes'])  # What if r['notes'] is None?

Impact:

If total or amount_paid is NULL, subtraction returns NaN

Displayed as "Balance: N nan"

If notes is empty string vs None, condition behaves inconsistently

Financial display unreliable

14. Multiple Staff Can Exist for One Business With No Coordination (Lines 158-164, 460-469)

Location: Lines 158-164, 460-469

Issue: No constraint that staff is unique or linked correctly

Evidence:

# Signup creates 1 staff
supabase.table("staff").insert({
    "business_id": shop_record["id"],
    "staff_name": manager_name,
    ...
}).execute()

# Master can create more staff
supabase.table("staff").insert({
    "business_id": s_list[target],
    "staff_name": s_staff,
    ...
}).execute()

# But password change updates ALL staff (line 468)
supabase.table("staff").update({"password": new_shop_p}).eq("business_id", business_id).execute()

Impact:

Multiple staff accounts for same business undefined behavior

No concept of "current user" in the system

Any staff edit changes all staff credentials

Staff can't have individual accounts or audit trails

15. Vault PIN Not Refreshed From Database (Lines 275-281)

Location: Lines 275-281

Issue: PIN read once at session init, not re-fetched when checking unlock

Evidence:

# Line 174: shop_info loaded at session start
laundry = st.session_state.shop_info

# Line 275: Used later without refresh
current_pin = laundry.get("owner_pin", "0000")

if st.button("Unlock"):
    if v_pin == current_pin:  # Uses stale PIN

Impact:

If PIN changed in another session/browser, this session still uses old PIN

User who changed PIN can't unlock vault in another tab

Stale credentials accepted as valid

16. Staff Password Verification References Wrong Table (Lines 90-96)

Location: Lines 90-96

Issue: Staff lookup checks password directly in database query

Evidence:

staff = supabase.table("staff").select("*").eq("business_id", laundry["id"]).eq("password", password).execute()
if staff.data:
    st.session_state.auth = True

Impact:

If multiple staff exist for business, query returns first match (undefined order)

No concept of which staff member is logging in

Audit trail impossible

Staff can't have session-specific data

MEDIUM Issues

17. DataFrame Grouped By Multiple Columns Without Unique Constraint (Lines 348-351)

Location: Lines 348-351

Issue: Grouping by cust_name, cust_phone but no guarantee combination is unique

Evidence:

customer_stats = dfv.groupby(['cust_name', 'cust_phone']).agg(
    total_spent=('total_price', 'sum'),
    last_visit=('created_at', 'max')
).reset_index()

Impact:

If two different customers have same name or phone, they're merged into one row

"John Smith" with phone "08012345678" from two customers → combined statistics

Loyalty board shows inflated spending for duplicates

Churn risk analysis incorrect

18. Orders Can Have Negative Item Counts (Line 205)

Location: Line 205

Issue: Only validates min_value=1 on client side, no database constraint

Evidence:

items = col1.number_input("Total Items", min_value=1)

Impact:

If user bypasses Streamlit UI, could insert negative items_count

Reports show nonsensical item counts

Inventory tracking broken

19. Expiry Date Can Be Set to Past (Line 555)

Location: Line 555

Issue: Onboarding accepts any date, no validation

Evidence:

s_expiry = st.date_input("Expiry Date")  # No min/max validation
supabase.table("laundries").insert({
    "expiry_date": str(s_expiry),
}).execute()

Impact:

Admin could accidentally set expiry to past date

Business immediately locked out on login (line 71-80)

No way to detect if it's a mistake vs intentional

20. Phone Number Format Inconsistency (Lines 110, 251-255, 524-526)

Location: Throughout

Issue: Phone numbers stored and manipulated in different formats

Evidence:

new_phone = st.text_input("Phone Number", placeholder="080...").strip()  # Raw input

# Later, formatted differently
raw_phone = str(r['cust_phone']).strip().replace(" ", "").replace("+", "").replace("-", "")
if raw_phone.startswith("0"):
    c_phone = "234" + raw_phone[1:]

Impact:

Phone "08012345678" and "2348012345678" treated as different customers

Same customer lookup might fail if format differs

Duplicate customer records created

21. ilike() Query Can Match Partial Names (Line 65)

Location: Line 65, 128

Issue: Using ilike() for case-insensitive match, but could return multiple partial matches

Evidence:

res = supabase.table("laundries").select("*").ilike("business_name", business_input_name).execute()
if res.data:
    laundry = res.data[0]  # Grabs first match blindly

Impact:

User types "Washh" but database has "Washh Lekki", "Washh Ikoyi", "Washh Surulere"

Returns first match arbitrarily

User logs into wrong business

With duplicate names (from race condition), returns undefined business

22. No Constraint on Unique Columns in Signup (Lines 128, 133)

Location: Lines 128-155

Issue: Checks for duplicates in app code, not enforcing database unique constraint

Evidence:

name_check = supabase.table("laundries").select("business_name").ilike("business_name", new_business_name).execute()
# ... then later ...
phone_check = supabase.table("laundries").select("owner_phone").eq("owner_phone", new_phone).execute()

Impact:

If database constraint not configured, duplicates possible despite checks

Master control (line 559) can bypass checks and insert duplicates

Race conditions allow duplicates anyway

23. Missing Not-Null Constraints in Order Creation (Line 213-214)

Location: Line 213-214

Issue: Only validates name and phone, but other fields could be NULL

Evidence:

if not name or not phone_val:
    st.error("Missing credentials.")
else:
    # But location, notes, etc could be NULL
    supabase.table("orders").insert({
        "location": loc,  # Could be empty string
        "notes": notes,   # Could be empty
        ...
    }).execute()

Impact:

Orders with missing delivery locations

Notes accidentally NULL instead of empty string

Operations view breaks when trying to display (line 247: Loc: {r['location']})

24. Delivered Orders Never Deleted, Memory/Performance Impact (Line 226)

Location: Line 226

Issue: Filters out delivered orders from operations view but they accumulate in database

Evidence:

res = supabase.table("orders").select("*").eq("business_id", business_id).neq("status", "Delivered").execute()

Impact:

All orders ever created remain in database

Financial reports (line 292) fetch ALL orders: supabase.table("orders").select("*").eq("business_id", business_id).execute()

As business grows, this query gets slower

No archive or cleanup mechanism

25. Timezone Handling Broken for Revenue Reports (Lines 310-313)

Location: Lines 310-313

Issue: Mixing naive datetimes with timezone-aware ones

Evidence:

now = pd.Timestamp.now(tz=dfv['created_at'].dt.tz if hasattr(dfv['created_at'].dt, 'tz') else None)
today_start = now.normalize()
week_start = today_start - pd.Timedelta(days=today_start.weekday())

Impact:

If some orders have timezone info and others don't, comparisons fail

"Today" cutoff could include/exclude yesterday's orders depending on timezone

Week boundaries misaligned if timezone switches during DST

Multi-region businesses show incorrect revenue by date

26. Master Control Updates Based on Stale UI Data (Line 544)

Location: Line 544

Issue: Business name selected from UI-rendered list but database could have duplicates

Evidence:

shop_list = df_shops['business_name'].tolist()
t_name = col1.selectbox("Select Business to Update", shop_list)

supabase.table("laundries").update({"is_active": t_status, "expiry_date": str(t_expiry)}).eq("business_name", t_name).execute()

Impact:

If duplicate business names exist (from race condition), .eq("business_name", t_name) updates ALL matching businesses

Intended single business update affects multiple businesses

Wrong business can be locked/enabled

LOW Issues

27. No Soft Deletes or Audit Trail (Throughout)

Location: All database writes

Issue: No deleted_at field or change log

Impact:

Deleted orders impossible to recover

No compliance trail for financial records

28. trail_start_date Typo in Column (Lines 149, 564)

Location: Lines 149, 564

Issue: Column named trail_start_date (should be trial_start_date)

Evidence:

"trail_start_date": trial_start,

Impact:

Typo persisted in database schema

Code references trial_start but column is trail_start_date

Confusing naming (trail vs trial)

29. Numeric Fields Stored as Strings (Lines 140, 141)

Location: Lines 140, 141

Issue: Dates converted to strings before insertion

Evidence:

trial_start = str(date.today())
trial_expiry = str(date.today() + timedelta(days=30))

Impact:

Date comparisons require string parsing

Database can't validate date constraints

Sorting by date in UI requires conversion

30. Email-Like Data Missing (Phone is Only Contact)

Location: Throughout

Issue: No email field for notifications, only WhatsApp

Impact:

No recovery mechanism if phone lost

Communication channel vulnerable

Summary Table

Severity

Count

Key Issues

CRITICAL

7

Orphaned records, no error checking, race conditions (2), amount validation, staff password cascading, session desync

HIGH

8

Status not validated, column name mismatches, Clear Debt race, timestamp inconsistency, business name breaks login, missing nullability checks, multiple staff coordination, stale vault PIN

MEDIUM

10

Grouping without unique constraint, negative items, past expiry dates, phone format inconsistency, partial name matching, missing constraints, missing not-nulls, performance degradation, timezone issues, master updates affect duplicates

LOW

3

No soft deletes, typo in column name, numeric fields as strings, missing email contact


Architectural Analysis: app.py

1. Current Architecture Diagram

┌─────────────────────────────────────────────────────────────────────┐
│                    SINGLE FILE: app.py (604 lines)                  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  PRESENTATION LAYER (Streamlit UI - Tightly Coupled)         │  │
│  │                                                              │  │
│  │  ├─ Login Gate (lines 43-98)                               │  │
│  │  │  ├─ Master backdoor logic                               │  │
│  │  │  └─ Subscription expiry check                           │  │
│  │  │                                                          │  │
│  │  ├─ Signup/Onboarding (lines 101-170)                      │  │
│  │  │  ├─ Form rendering                                      │  │
│  │  │  ├─ Input validation                                    │  │
│  │  │  ├─ Business creation logic                             │  │
│  │  │  └─ Staff creation logic                                │  │
│  │  │                                                          │  │
│  │  ├─ Shop Workspace (lines 173-469)                         │  │
│  │  │  ├─ Log Orders (lines 184-222)                          │  │
│  │  │  │  ├─ Form rendering                                   │  │
│  │  │  │  └─ Customer lookup                                  │  │
│  │  │  │                                                      │  │
│  │  │  ├─ Operations (lines 224-272)                          │  │
│  │  │  │  ├─ Kanban-style rendering                           │  │
│  │  │  │  ├─ Status transitions                               │  │
│  │  │  │  └─ WhatsApp messaging                               │  │
│  │  │  │                                                      │  │
│  │  │  ├─ Owner Vault (lines 274-469)                         │  │
│  │  │  │  ├─ PIN unlock logic (lines 274-290)                 │  │
│  │  │  │  ├─ Financial Dashboard (lines 295-397)              │  │
│  │  │  │  │  ├─ Revenue metrics (lines 307-324)               │  │
│  │  │  │  │  ├─ Debt ledger (lines 328-341)                  │  │
│  │  │  │  │  └─ Customer analytics (lines 345-395)            │  │
│  │  │  │  └─ Security Settings (lines 399-469)                │  │
│  │  │  │     ├─ Profile edits (lines 403-424)                 │  │
│  │  │  │     └─ PIN/Password changes (lines 426-469)          │  │
│  │  │                                                          │  │
│  │  └─ Master Control (lines 475-600)                         │  │
│  │     ├─ Network Health (lines 480-546)                      │  │
│  │     ├─ Manual Onboarding (lines 548-572)                   │  │
│  │     └─ Access Management (lines 574-596)                   │  │
│  │                                                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              ↓↓↓                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  BUSINESS LOGIC (Scattered in UI Functions)                 │  │
│  │                                                              │  │
│  │  ├─ Authentication & Authorization                          │  │
│  │  │  ├─ Master backdoor check (lines 59)                    │  │
│  │  │  ├─ Subscription validation (lines 71-72)               │  │
│  │  │  ├─ Staff password verification (lines 90)              │  │
│  │  │  └─ Vault PIN validation (lines 281)                    │  │
│  │  │                                                          │  │
│  │  ├─ Data Validation                                         │  │
│  │  │  ├─ Password strength (lines 124-125, 465)              │  │
│  │  │  ├─ Required fields (lines 120, 213)                    │  │
│  │  │  ├─ Duplicate checks (lines 128, 133)                   │  │
│  │  │  └─ Expiry calculations (lines 69, 489-490)             │  │
│  │  │                                                          │  │
│  │  ├─ Domain Logic (Order Management)                         │  │
│  │  │  ├─ Status transitions (lines 230-270)                  │  │
│  │  │  ├─ Order state machine                                 │  │
│  │  │  └─ Balance calculations (lines 245, 257-258, 300)      │  │
│  │  │                                                          │  │
│  │  ├─ Analytics & Reporting                                   │  │
│  │  │  ├─ Revenue calculations (lines 315-324)                │  │
│  │  │  ├─ Customer segmentation (lines 348-351)               │  │
│  │  │  ├─ Churn analysis (lines 375-395)                      │  │
│  │  │  └─ Time-based filtering (lines 321-323)                │  │
│  │  │                                                          │  │
│  │  └─ Notification Logic                                      │  │
│  │     ├─ WhatsApp message formatting (lines 260, 359, 382)   │  │
│  │     ├─ Phone normalization (lines 251-255, 361-365, etc.)  │  │
│  │     └─ Expiry nudge messages (lines 512-521)               │  │
│  │                                                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              ↓↓↓                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  DATA ACCESS LAYER (Raw Supabase Calls - No Abstraction)    │  │
│  │                                                              │  │
│  │  Direct .table().select/insert/update calls scattered:      │  │
│  │  ├─ laundries table (lines 65, 78, 128, 133, 414, 449,    │  │
│  │  │                   544, 559, 576)                         │  │
│  │  ├─ staff table (lines 90, 158, 460, 468, 586)             │  │
│  │  └─ orders table (lines 195, 216, 226, 269, 292, 337)      │  │
│  │                                                              │  │
│  │  NO LAYER ISOLATION:                                        │  │
│  │  • 30+ direct Supabase calls in UI functions                │  │
│  │  • No repository pattern                                    │  │
│  │  • No abstraction of database shape                         │  │
│  │  • SQL queries mixed into UI rendering logic                │  │
│  │                                                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              ↓↓↓                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  EXTERNAL DEPENDENCIES                                      │  │
│  │                                                              │  │
│  │  ├─ Supabase Client (lines 8, 25-30)                       │  │
│  │  │  └─ Connected via st.secrets (lines 26-27)              │  │
│  │  │                                                          │  │
│  │  ├─ Streamlit Session State (lines 32-37)                  │  │
│  │  │  └─ Auth state, shop_info, vault_unlocked, etc.         │  │
│  │  │                                                          │  │
│  │  ├─ Pandas DataFrames (lines 3, 229, 285, 297, etc.)       │  │
│  │  │  └─ In-memory aggregations, filtering                   │  │
│  │  │                                                          │  │
│  │  └─ Standard Library (re, urllib, random, datetime)         │  │
│  │                                                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

2. Functional Domains Identified

Domain 1: Authentication & Authorization (Cross-cutting)

Responsibility: Verify identity and grant access

Current locations: Lines 59, 71-78, 90-96, 275-282, 444, 463-464

Issues:

Tightly coupled to login UI (lines 43-98)

Master backdoor in plain code (line 59)

Session state used for authorization (lines 33-37, 60-61)

No abstraction: master check, subscription check, password check all inline

Domain 2: Business Onboarding & Lifecycle (Business Core)

Responsibility: Create businesses, manage subscriptions, expiry

Current locations: Lines 137-170 (signup), 544-546 (renewal), 69-78 (expiry checks)

Issues:

Signup logic embedded in form submission (lines 119-170)

No separate onboarding workflow

Subscription expiry checked in login (lines 71-78) instead of dedicated service

Expiry auto-lock scattered (line 77-78)

Domain 3: Staff & User Management (Identity)

Responsibility: Create staff, manage credentials, roles

Current locations: Lines 158-164 (creation), 460-469 (password change), 90 (login)

Issues:

Staff creation assumes success (no error handling)

Password change affects entire business (line 468) not individual

No concept of "current user" or staff identity

No role-based access control

Domain 4: Order Management (Core Business)

Responsibility: Create orders, track status, manage lifecycle

Current locations: Lines 184-222 (creation), 224-272 (operations), 267-270 (status changes)

Issues:

Order creation mixed with form rendering (lines 200-222)

Status transitions hardcoded in UI (lines 230, 268)

No order state machine or validation

Status values undefined (no enum)

Domain 5: Financial Management & Analytics (Analytics)

Responsibility: Revenue tracking, debt ledger, customer insights

Current locations: Lines 295-397 (financial dashboard), 348-351 (customer stats)

Issues:

Complex aggregations in UI (lines 315-324)

DataFrames do all filtering/grouping (lines 297-324)

Revenue calculations duplicated (lines 245, 257, 300)

Timezone handling broken (lines 310-313)

Domain 6: Customer Management (Customer)

Responsibility: Lookup customers, track history, segment for marketing

Current locations: Lines 195-198 (lookup), 348-351 (segmentation), 375-395 (churn)

Issues:

Customer lookup is ad-hoc (lines 195)

No customer entity/repository

Phone normalization duplicated 5 times (lines 251-255, 361-365, etc.)

Grouping by name+phone without uniqueness constraint (line 348)

Domain 7: Notifications (Communication)

Responsibility: Format and send WhatsApp messages

Current locations: Lines 260-265, 359-370, 382-393, 512-531

Issues:

Message templates hardcoded in UI

Phone formatting logic repeated (5x)

No notification queue or retry logic

WhatsApp links generated inline

Domain 8: Vault & Security (Authorization)

Responsibility: PIN-based access control to sensitive data

Current locations: Lines 274-290 (unlock), 275-281 (PIN check), 439-451 (PIN change)

Issues:

PIN stored in session state

No timeout or re-authentication

Vault unlock is client-side flag (line 282)

PIN comparison is plaintext (line 281)

Domain 9: System Administration (Master Control)

Responsibility: Manage all businesses, subscriptions, staff

Current locations: Lines 475-600

Sub-domains:

Network Health: Lines 480-546 (subscription monitoring)

Onboarding: Lines 548-572 (manual business creation)

Access Management: Lines 574-596 (staff creation)

Issues:

Three different admin functions with different validation rules

No centralized admin service layer

Business name selected from UI list but query updates by name (race condition)

3. Coupling Analysis

UI-to-Business Logic Coupling (SEVERE)

Function

UI Components

Business Logic

Database Calls

Coupling Level

login_gate()

lines 44-98

lines 59, 65, 69-78, 83-90

lines 65, 78, 90

EXTREME

signup (in login_gate)

lines 108-170

lines 124-155

lines 128, 133, 144, 158

EXTREME

shop_workspace() operations

lines 234-270

lines 230-270

lines 226, 269

SEVERE

vault financial dashboard

lines 295-397

lines 297-324, 348-351

lines 292

SEVERE

clear_debt_button

lines 336

lines 300, 337

lines 337

EXTREME

master_network_health

lines 501-531

lines 488-530

lines 482, 544

SEVERE

Cross-Domain Coupling

Order Management ←→ Financial Analytics (balance calc used in 3 places)
                ↓
        Lines 245, 257, 300 all compute: total - amount_paid

Customer Management ←→ Notifications (phone normalization)
                    ↓
        Lines 251-255, 361-365, 384-388, 524-526 all duplicate

Authentication ←→ Session State ←→ Authorization
        ↓
        Lines 33-37 define state, line 60-61 set it, 
        lines 92-93 use it, but no refresh from DB

4. Responsibility Violations (SOLID)

Single Responsibility Principle Violations

Function

Responsibilities

Lines

login_gate()

1. Form rendering 2. Auth logic 3. Subscription check 4. Data lookup 5. Expiry lock

43-98

shop_workspace()

1. Menu routing 2. Order CRUD 3. Status transitions 4. Financial reporting 5. Settings UI 6. Vault access

173-469

Signup block

1. Form rendering 2. Password validation 3. Duplicate checking 4. Business creation 5. Staff creation 6. Auto-login

101-170

Financial dashboard

1. Data fetch 2. Aggregation 3. Timezone handling 4. Filtering 5. UI rendering 6. Action handlers

295-397

5. Recommended Module Structure

Phase 1: Foundation (Lowest Risk)

Extract reusable utilities with no dependencies:

washh_laundry_os/
├── config.py
│   ├── Constants (ADMIN_WA_NUMBER, PIN_LENGTH, etc.)
│   └── Configuration (load from st.secrets)
│
├── core/
│   └── validators.py
│       ├── validate_password(password) → bool
│       ├── validate_phone(phone) → str (normalized)
│       ├── validate_order_amounts(total, paid) → bool
│       └── validate_pin(pin) → bool
│
├── models/
│   ├── __init__.py (TypedDicts for data structures)
│   ├── business.py
│   │   ├── LaundryDTO (business_name, owner_phone, expiry_date, etc.)
│   │   └── SubscriptionStatus (enum: trial, active, expired)
│   ├── order.py
│   │   ├── OrderDTO (cust_name, total, amount_paid, status, etc.)
│   │   └── OrderStatus (enum: Received, Sorting, Processing, etc.)
│   ├── customer.py
│   │   └── CustomerDTO (name, phone, total_spent, last_visit)
│   └── staff.py
│       └── StaffDTO (name, role, created_at)
│
└── app.py (refactored, still imports above)

Risk: VERY LOW - No existing functionality changes, only adding new files

Phase 2: Data Access Layer

Extract database queries into repositories:

washh_laundry_os/
├── repositories/
│   ├── __init__.py
│   ├── base.py
│   │   ├── class BaseRepository:
│   │   │   ├── __init__(supabase_client)
│   │   │   └── _handle_response(response)
│   │   └── (error handling, retry logic)
│   │
│   ├── business_repository.py
│   │   ├── class BusinessRepository(BaseRepository):
│   │   │   ├── find_by_name(name) → LaundryDTO | None
│   │   │   ├── create(data: LaundryDTO) → LaundryDTO
│   │   │   ├── update(id, fields) → bool
│   │   │   ├── check_duplicate_name(name) → bool
│   │   │   ├── check_duplicate_phone(phone) → bool
│   │   │   └── find_expired() → List[LaundryDTO]
│   │
│   ├── order_repository.py
│   │   ├── class OrderRepository(BaseRepository):
│   │   │   ├── create(data: OrderDTO) → OrderDTO
│   │   │   ├── find_by_id(id) → OrderDTO | None
│   │   │   ├── find_by_business(business_id) → List[OrderDTO]
│   │   │   ├── find_active_by_business(business_id) → List[OrderDTO]
│   │   │   ├── update_status(id, new_status) → bool
│   │   │   ├── find_customer_history(business_id, phone) → List[OrderDTO]
│   │   │   └── find_all_for_analytics(business_id) → List[OrderDTO]
│   │
│   ├── staff_repository.py
│   │   ├── class StaffRepository(BaseRepository):
│   │   │   ├── create(data: StaffDTO) → StaffDTO
│   │   │   ├── find_by_business(business_id) → List[StaffDTO]
│   │   │   ├── verify_password(business_id, password) → StaffDTO | None
│   │   │   ├── update_password(business_id, new_password) → bool
│   │   │   └── get_first_by_business(business_id) → StaffDTO | None
│   │
│   └── customer_repository.py
│       ├── class CustomerRepository(BaseRepository):
│       │   ├── find_by_business_and_phone(business_id, phone) → CustomerDTO | None
│       │   ├── get_all_for_business(business_id) → List[CustomerDTO]
│       │   └── get_loyal_customers(business_id, top_n=5) → List[CustomerDTO]
│
└── app.py (refactored to use repositories)

Migration path: Replace all supabase.table().select()... with repo.find_by_x() calls

Risk: LOW - Repositories are thin wrappers, same API calls but abstracted

Phase 3: Business Logic Services

Extract domain logic into service classes:

washh_laundry_os/
├── services/
│   ├── __init__.py
│   │
│   ├── auth_service.py
│   │   ├── class AuthService:
│   │   │   ├── verify_business_login(name, password) → LaundryDTO | AuthError
│   │   │   ├── check_master_access(name, password) → bool
│   │   │   ├── check_subscription_valid(laundry: LaundryDTO) → bool
│   │   │   └── lock_expired_business(laundry_id) → None
│   │   └── class AuthError(Exception)
│   │
│   ├── onboarding_service.py
│   │   ├── class OnboardingService:
│   │   │   ├── validate_signup_request(data) → ValidationResult
│   │   │   ├── create_business_and_staff(data) → (LaundryDTO, StaffDTO) | OnboardingError
│   │   │   └── generate_business_code() → str
│   │
│   ├── order_service.py
│   │   ├── class OrderService:
│   │   │   ├── create_order(business_id, order_data) → OrderDTO
│   │   │   ├── get_active_orders(business_id) → List[OrderDTO]
│   │   │   ├── transition_order_status(order_id, new_status) → bool
│   │   │   ├── calculate_balance(total, paid) → float
│   │   │   └── validate_status_transition(current, new) → bool
│   │   └── class OrderStatusMachine:
│   │       ├── valid_statuses = {...}
│   │       ├── transitions = {current: [allowed_next]}
│   │       └── is_valid_transition(current, new) → bool
│   │
│   ├── financial_service.py
│   │   ├── class FinancialService:
│   │   │   ├── get_revenue_metrics(business_id, period) → RevenueMetrics
│   │   │   ├── get_debt_ledger(business_id) → List[Debt]
│   │   │   ├── clear_debt(order_id) → bool
│   │   │   ├── get_customer_stats(business_id) → List[CustomerStats]
│   │   │   └── get_churn_risk(business_id, threshold_days=21) → List[CustomerStats]
│   │   └── class RevenueMetrics(TypedDict): expected, collected, outstanding
│   │
│   ├── customer_service.py
│   │   ├── class CustomerService:
│   │   │   ├── find_or_create_from_order(business_id, phone) → CustomerDTO
│   │   │   ├── get_customer_history(business_id, phone) → List[OrderDTO]
│   │   │   └── segment_customers(business_id) → {loyal: [...], at_risk: [...]}
│   │
│   ├── notification_service.py
│   │   ├── class NotificationService:
│   │   │   ├── format_ready_notification(order, business) → str
│   │   │   ├── format_loyalty_notification(customer, business) → str
│   │   │   ├── format_churn_notification(customer) → str
│   │   │   ├── format_expiry_notification(business, days_left) → str
│   │   │   ├── normalize_phone(phone) → str (single source of truth)
│   │   │   └── generate_whatsapp_link(phone, message) → str
│   │
│   ├── vault_service.py
│   │   ├── class VaultService:
│   │   │   ├── verify_pin(business_id, pin_from_input) → bool
│   │   │   └── update_pin(business_id, current_pin, new_pin) → bool
│   │
│   └── subscription_service.py
│       ├── class SubscriptionService:
│       │   ├── check_expiry(laundry: LaundryDTO) → bool
│       │   ├── get_days_remaining(expiry_date) → int
│       │   ├── renew_subscription(business_id, new_expiry) → bool
│       │   └── get_expiring_soon(threshold_days=3) → List[LaundryDTO]
│
└── app.py (refactored to use services)

Migration path: Replace inline logic with service.method() calls

Risk: MEDIUM - Services have new behavior, but tested independently first

Phase 4: UI Components

Extract Streamlit UI into composable components:

washh_laundry_os/
├── ui/
│   ├── __init__.py
│   │
│   ├── components/
│   │   ├── __init__.py
│   │   ├── forms.py
│   │   │   ├── render_login_form() → (name, password) | None
│   │   │   ├── render_signup_form() → SignupData | None
│   │   │   ├── render_order_form(prefill) → OrderData | None
│   │   │   └── render_vault_pin_form() → str | None
│   │   │
│   │   ├── orders.py
│   │   │   ├── render_order_card(order) → None
│   │   │   ├── render_kanban_board(orders) → None
│   │   │   └── render_order_details(order) → None
│   │   │
│   │   ├── financial.py
│   │   │   ├── render_revenue_metrics(metrics) → None
│   │   │   ├── render_debt_ledger(debts) → None
│   │   │   └── render_customer_analytics(stats) → None
│   │   │
│   │   └── notifications.py
│   │       ├── render_whatsapp_button(phone, msg) → None
│   │       └── render_status_indicator(status) → None
│   │
│   └── pages/
│       ├── __init__.py
│       ├── login_page.py
│       │   └── show_login() → bool (True if logged in)
│       ├── shop_page.py
│       │   ├── show_orders_tab() → None
│       │   ├── show_operations_tab() → None
│       │   └── show_vault_tab() → None
│       ├── admin_page.py
│       │   ├── show_network_health() → None
│       │   ├── show_onboarding() → None
│       │   └── show_access_management() → None
│       │
│       └── utils.py
│           ├── show_success(msg) → None
│           ├── show_error(msg) → None
│           └── show_warning(msg) → None
│
└── app.py (simplified orchestrator)

Migration path: Extract UI blocks into component functions, call from main

Risk: MEDIUM-HIGH - UI changes visible to users, requires careful testing

Phase 5: Dependency Injection & Configuration

Add service container to manage dependencies:

washh_laundry_os/
├── container.py
│   ├── class ServiceContainer:
│   │   ├── __init__(supabase_client, config)
│   │   ├── get_auth_service() → AuthService
│   │   ├── get_order_service() → OrderService
│   │   ├── get_business_repository() → BusinessRepository
│   │   └── ... (all other services/repos)
│   │
│   └── get_container() → ServiceContainer (singleton)
│
└── app.py
    ├── container = get_container()
    ├── auth_service = container.get_auth_service()
    └── ... (uses services instead of direct calls)

Risk: LOW - Purely refactoring, no behavior changes

6. Refactor Sequence (Lowest Risk First)

PHASE 0: Foundation (Week 1)

Effort: 2-4 hours | Risk: VERY LOW | Value: High setup for later phases

Create config.py (30 min)

Move ADMIN_WA_NUMBER → constant

Extract PIN/password rules (min length, etc.)

Create enums for OrderStatus, SubscriptionStatus

Create models/__init__.py (1 hour)

Define TypedDicts for LaundryDTO, OrderDTO, StaffDTO, CustomerDTO

No logic, just data structure definitions

Use typing.TypedDict (Python 3.8+)

Create core/validators.py (1 hour)

Extract validate_password() from lines 124-125, 465-466

Extract normalize_phone() from lines 251-255, 361-365, etc. (DRY violation!)

Extract validate_pin() from lines 446-447

Test independently with unit tests

Add unit tests (1-2 hours)

test_validators.py: password, phone, pin validation

Run before deploying any change

Refactoring in app.py:

# BEFORE
if len(new_password) < 7 or not re.search(r"[a-zA-Z]", new_password) or not re.search(r"\d", new_password):
    st.error("Password too weak...")

# AFTER
from core.validators import validate_password
if not validate_password(new_password):
    st.error("Password too weak...")

Git commits:

feat: add config, models, validators modules

test: add unit tests for validators

PHASE 1: Repository Layer (Week 2)

Effort: 4-6 hours | Risk: LOW | Value: Testable data access

Create repositories/base.py (1 hour)

BaseRepository.__init__(supabase_client)

_handle_response(response) - error checking

Common patterns (execute, error handling)

Create repositories/business_repository.py (1.5 hours)

Extract lines 65, 128, 133, 414, 482, 576 into methods

find_by_name(name) - replaces line 65

check_duplicate_name(name) - replaces line 128

check_duplicate_phone(phone) - replaces line 133

update(id, fields) - replaces lines 414, 449

Test with Supabase test account

Create repositories/order_repository.py (1.5 hours)

Extract lines 195, 216, 226, 269, 292, 337

find_customer_history() - replaces line 195

create() - replaces line 216

find_active() - replaces line 226

update_status() - replaces line 269

Create repositories/staff_repository.py (1 hour)

Extract lines 90, 158, 460, 468

verify_password() - replaces line 90

create() - replaces line 158

update_password() - replaces lines 468

Replace first query in app.py (30 min)

Change line 65: supabase.table("laundries").select("*").ilike(...)

To: business_repo.find_by_name(business_input_name)

Test login still works

Add integration tests (1-2 hours)

Mock Supabase responses

Test repo methods with test data

Refactoring in app.py:

# BEFORE (line 65)
res = supabase.table("laundries").select("*").ilike("business_name", business_input_name).execute()
if res.data:
    laundry = res.data[0]

# AFTER
from repositories.business_repository import BusinessRepository
repo = BusinessRepository(supabase)
laundry = repo.find_by_name(business_input_name)
if laundry:

Git commits:

refactor: extract business repository

refactor: extract order repository

refactor: extract staff repository

test: add integration tests for repositories

Deployment: Incremental - one repo at a time, test each

PHASE 2: Service Layer (Week 3-4)

Effort: 6-8 hours | Risk: MEDIUM | Value: Testable business logic

Create services/auth_service.py (2 hours)

Extract lines 59, 71-78, 90-96 into methods

verify_business_login(name, password) - returns LaundryDTO or raises AuthError

check_master_access(name, password) -> bool

check_subscription_valid(laundry) -> bool

lock_expired_business(id) -> None

Create services/order_service.py (2 hours)

Extract lines 230-270 into methods

create_order(business_id, data) -> OrderDTO

get_active_orders(business_id) -> List[OrderDTO]

transition_status(order_id, new_status) -> bool

calculate_balance(total, paid) -> float

Create OrderStatusMachine class (state validation)

Create services/financial_service.py (2 hours)

Extract lines 297-324, 348-351 into methods

get_revenue_metrics(business_id, period) -> RevenueMetrics

get_debt_ledger(business_id) -> List[Debt]

get_customer_stats(business_id) -> List[CustomerStats]

NOTE: still uses pandas for now, can improve later

Create services/notification_service.py (1.5 hours)

Extract lines 260-265, 359-370, 382-393, 512-531

format_ready_notification(order, business) -> str

format_loyalty_notification(customer, business) -> str

format_churn_notification(customer) -> str

normalize_phone(phone) -> str (single source of truth!)

generate_whatsapp_link(phone, msg) -> str

Replace queries with services (2 hours)

Change line 216-220 to order_service.create_order()

Change line 269 to order_service.transition_status()

Change lines 315-324 to financial_service.get_revenue_metrics()

Add unit tests (2-3 hours)

Mock repositories

Test business logic independently

Test state transitions

Test calculations

Refactoring in app.py:

# BEFORE (line 216-220)
supabase.table("orders").insert({
    "business_id": business_id,
    ...
}).execute()

# AFTER
order_service.create_order(business_id, order_data)

Git commits:

refactor: extract auth service

refactor: extract order service

refactor: extract financial service

refactor: extract notification service

test: add unit tests for services

Deployment: Services deployed gradually, tested with mock data first

PHASE 3: UI Components (Week 5)

Effort: 4-6 hours | Risk: MEDIUM-HIGH | Value: Reusable UI

Create ui/components/forms.py (1.5 hours)

Extract lines 49-98 → render_login_form()

Extract lines 108-117 → render_signup_form()

Extract lines 200-210 → render_order_form()

Return structured data, not just values

Keep Streamlit calls, just organize them

Create ui/components/orders.py (1 hour)

Extract lines 238-270 → render_order_card(order)

Extract lines 233-270 → render_kanban_board(orders)

Create ui/components/financial.py (1 hour)

Extract lines 315-319 → render_revenue_metrics(metrics)

Extract lines 331-339 → render_debt_ledger(debts)

Create ui/pages/login_page.py (1 hour)

Extract lines 43-98 → show_login()

Use forms and services

Return authentication result

Refactor main app.py (1.5 hours)

Replace form rendering with component calls

Keep routing logic, extract UI blocks

Main becomes orchestrator

Test UI changes (2 hours)

Manual testing of all pages

Ensure no visual regressions

Refactoring in app.py:

# BEFORE (lines 49-98 all inline)
with col2:
    with st.container(border=True):
        business_input_name = st.text_input("Business Name", ...)
        ...
        if st.button("Enter Workspace"):
            # 50 lines of logic

# AFTER
from ui.pages.login_page import show_login
if not st.session_state.auth:
    show_login()

Git commits:

refactor: extract login page component

refactor: extract order components

refactor: extract financial components

Deployment: Pages deployed one at a time, visual testing before each

PHASE 4: Dependency Injection (Week 6)

Effort: 2-3 hours | Risk: LOW | Value: Testability, easy mocking

Create container.py (1 hour)

ServiceContainer class

Initialize all repositories and services

Single get_container() entry point

Refactor app.py (1 hour)

container = get_container()

auth_service = container.get_auth_service()

order_service = container.get_order_service()

Remove direct Supabase calls

Add container tests (1 hour)

Verify all services initialized

Test with mock Supabase

Git commits:

refactor: add service container and DI

Deployment Schedule

Week 1: PHASE 0 (validators, config)
        ↓ Deploy to staging
        ↓ No feature changes, just extracted code

Week 2: PHASE 1 (repositories)
        ↓ Replace 1 query at a time
        ↓ Test login, then order creation, etc.
        ↓ Deploy incrementally

Week 3-4: PHASE 2 (services)
        ↓ Replace auth logic in login
        ↓ Replace order logic in operations
        ↓ Replace financial logic in vault
        ↓ Deploy feature by feature

Week 5: PHASE 3 (UI components)
        ↓ Extract forms (no logic change)
        ↓ Extract pages (no logic change)
        ↓ Deploy pages one at a time

Week 6: PHASE 4 (DI)
        ↓ Final cleanup, wire everything
        ↓ Deploy complete refactored version

Post-refactor optimizations:
        ↓ Add caching layer
        ↓ Optimize financial queries
        ↓ Add real-time updates

7. Risk Mitigation Strategies

Phase 0 (Very Low Risk)

Run validators against existing code patterns

Unit tests verify same behavior as inline code

No changes to app.py behavior

Phase 1 (Low Risk)

Repositories are thin wrappers, test with real Supabase test account

Deploy one repository at a time

Keep old inline queries commented, switch back if needed

Monitor error logs for failed queries

Phase 2 (Medium Risk)

Services tested with mocked repositories first

Run services against actual data in staging

A/B test: old vs. new logic side-by-side for 1 feature

Rollback plan: revert to Phase 1 if issues arise

Phase 3 (Medium-High Risk)

UI changes visible to users

Deploy to staging, have team test UI

Automated screenshot tests (if available)

Manual QA on all major flows

Feature flags to toggle old vs. new UI

Phase 4 (Low Risk)

DI is a refactoring of existing code

Unit tests verify everything wires correctly

No behavior changes

8. Code Debt Reduction Summary

Issue

Phase

Impact

Effort

Phone normalization duplicated 5x

2

Removes 50 lines

30 min

Balance calculation duplicated 3x

2

Standardizes calc

1 hour

Password validation duplicated 2x

0

Removes 10 lines

30 min

No error handling on inserts

1

Prevents data loss

2 hours

UI mixed with business logic

3

Enables testing

4 hours

No transaction support

Post-6

Prevents orphaned data

2 hours

No audit logging

Post-6

Adds compliance

3 hours

DataFrame logic in UI

2

Testable analytics

2 hours

Total estimated refactoring effort: 6 weeks, 1-2 hours per day average

Summary

Current state: Single 604-line monolithic file with UI, business logic, and data access tightly coupled.

Target state: Modular architecture with clear separation:

UI components (presentational)

Services (business logic)

Repositories (data access)

Models (domain entities)

Key wins:

✅ Business logic testable independently

✅ Phone normalization extracted (5x duplication removed)

✅ Error handling centralized

✅ Easy to add features without touching 10+ places

✅ Enables multi-user scenarios (current code assumes 1 staff/business)

Highest risk phase: Phase 3 (UI changes visible), but done last with foundation in place


Streamlit to Render Migration Evaluation

Executive Summary

Washh can be migrated to Render, but faces significant architectural challenges specific to its use of Streamlit's session state and multi-user concurrency model. Migration is feasible but requires careful planning around session management, not framework changes.

Timeline: 1-2 weeks for straightforward deployment | 2-4 weeks if session persistence needed

Recommendation: Migrate as-is first, then refactor session state if multi-instance issues arise

1. Deployment Blockers

BLOCKER 1: Session State Loss on Instance Restart (CRITICAL)

Impact: Users lose authentication and vault unlock status on any restart

Current behavior on Streamlit Cloud:

Session state persists for user's browser session

Each user gets isolated session storage

App can restart without affecting user state (user has browser copy)

What breaks on Render:

User logs in → st.session_state.auth = True (in memory)
  ↓
  Render instance restarts (during deployment, scaling, etc.)
  ↓
  Session state lost → st.session_state.auth = False
  ↓
  User sees login page despite being authenticated
  ↓
  User frustrated, lost work

Lines affected: 33-37 (session state init), 60-61, 92-93 (auth set), 181 (logout clears all)

Mitigation options (in order of preference):

Use persistent session storage (Recommended) - Store session in Redis or PostgreSQL

# INSTEAD OF:
st.session_state.auth = True
st.session_state.shop_info = laundry

# DO THIS:
session_id = st.query_params.get("sid", str(uuid4()))
store_session(session_id, {"auth": True, "shop_info": laundry})
st.query_params["sid"] = session_id

Effort: 3-4 hours

Risk: LOW (only affects session handling)

Use browser-side cookies with authentication tokens

# On login, issue JWT:
token = jwt.encode({"business_id": laundry["id"], "exp": ...}, secret)
st.session_state["token"] = token

# On every rerun, verify token is still valid
if not verify_token(st.session_state.get("token")):
    st.session_state.auth = False

Effort: 4-5 hours

Risk: MEDIUM (JWT management)

Live with session loss - Accept users re-login after restart

Effort: 0 hours

Risk: HIGH (bad user experience, data loss if editing)

BLOCKER 2: Multi-Instance Concurrency (HIGH IMPACT)

Impact: Multiple app instances can't share session state or coordinate updates

Scenario:

Instance 1: User A logs in
  → st.session_state.auth = True (only in Instance 1's memory)

Instance 2: Load balancer routes User A to Instance 2
  → st.session_state.auth = False (Instance 2 has no record of login)
  → User A sees login page again

Why it happens:

Streamlit stores session state in-memory only

Render can scale to multiple instances

Each instance is isolated

Lines affected: 33-37, 60-61, 92-93, 174-175

Mitigation options:

Disable auto-scaling (Simplest)

Set Render to use 1 instance (no load balancing)

Effort: 5 minutes (config change)

Limitation: No horizontal scaling

Use sticky sessions

Route same user always to same instance (by IP or cookie)

Render doesn't support sticky sessions natively

Effort: HIGH (reverse proxy setup)

Not recommended for Render

Store session state externally (Redis)

# After login, store in Redis:
redis.set(f"session:{session_id}", json.dumps(auth_state), ex=3600)

# On new request, fetch from Redis:
auth_state = redis.get(f"session:{session_id}")
st.session_state.update(auth_state)

Effort: 4-5 hours

Risk: LOW

Requires Redis addon (Render: $15/month)

BLOCKER 3: Secrets Management (MEDIUM)

Current setup (Streamlit Cloud):

Secrets stored in .streamlit/secrets.toml

Not committed to Git

Lines affected: 26-27 (Supabase), 59 (Master code)

What happens on Render:

If .streamlit/secrets.toml is in .gitignore, Render won't have access

Supabase credentials must be set as environment variables in Render dashboard

Migration steps:

# 1. Create .env.render (NOT committed)
SUPABASE_URL=your_url
SUPABASE_KEY=your_service_key
MASTER_CODE=your_master_code
MASTER_PIN=your_master_pin

# 2. Add to Render dashboard:
   Environment Variables → Copy from .env.render

# 3. Update app.py to read from environment:
   url = os.environ.get("SUPABASE_URL")
   key = os.environ.get("SUPABASE_KEY")

Effort: 30 minutes | Risk: LOW

BLOCKER 4: File System Impermanence (MEDIUM)

Impact: Any files written to disk are lost on restart

Current uses in app.py:

None found (good news!)

Potential issues if added:

Caching files to /tmp won't persist

User uploads won't be saved

CSV exports need explicit cleanup

Mitigation: Ensure all file operations are temporary or use S3-like storage

2. Streamlit-Specific Dependencies

Hard Dependencies on Streamlit (Cannot Remove)

Dependency

Location

Why It's Needed

Render Compatibility

st.session_state

Lines 33-37, 60-61, 92-93, 174, 407-408, etc.

Stores auth and UI state

PROBLEMATIC (in-memory only)

st.cache_resource

Lines 24-28

Caches Supabase client

✅ Works fine (process-scoped)

st.secrets

Lines 26-27, 59

Loads credentials

⚠️ Need os.environ instead

st.rerun()

Lines 62, 94, 170, 182, etc.

Triggers full page re-render

✅ Works fine

st.text_input()

Lines 54-55, 109-115, 202-204, etc.

Form inputs

✅ Works fine

st.button() / st.form_submit_button()

Lines 57, 117, 212, 267, 280, 443, 459, 584

Form submission

✅ Works fine

st.markdown() / st.write()

Throughout

Rendering

✅ Works fine

st.sidebar

Lines 177-178

Navigation

✅ Works fine

st.expander()

Lines 243, 295, 353, 372, 400

UI sections

✅ Works fine

Summary: Only st.session_state and st.secrets are problematic. Everything else works on Render.

3. Session State Dependencies (DETAILED ANALYSIS)

Session State Uses in Code

# Lines 33-37: INITIALIZATION
if "auth" not in st.session_state: st.session_state.auth = False
if "is_master" not in st.session_state: st.session_state.is_master = False
if "shop_info" not in st.session_state: st.session_state.shop_info = None
if "vault_unlocked" not in st.session_state: st.session_state.vault_unlocked = False
if "trainer_wheels" not in st.session_state: st.session_state.trainer_wheels = True

# Lines 60-61: AUTH SET (login master backdoor)
st.session_state.auth = True
st.session_state.is_master = True

# Lines 92-93: AUTH SET (normal login)
st.session_state.auth = True
st.session_state.shop_info = laundry

# Line 174: AUTH CHECK (read shop_info)
laundry = st.session_state.shop_info

# Lines 181: LOGOUT
st.session_state.clear()

# Lines 188, 407-408, 431, 444, 450: UI STATE READS
if st.session_state.trainer_wheels:
new_name = st.text_input(..., value=st.session_state.shop_info.get(...))
st.session_state.trainer_wheels = st.toggle(...)
st.session_state.vault_unlocked = True  # Line 282

# Lines 407-408, 419-420: SESSION STATE MODIFICATION (profile edit)
st.session_state.shop_info["business_name"] = new_name
st.session_state.shop_info["owner_phone"] = new_phone

Session State Dependency Map

app.py
├─ Login Authentication (lines 60-61, 92-93)
│  └─ Stores: auth, is_master, shop_info
│  └─ Used by: shop_workspace() (line 174), master control (line 475)
│  └─ CRITICAL: Determines which page is shown
│
├─ Vault Access (lines 282, 289)
│  └─ Stores: vault_unlocked
│  └─ Used by: Lines 276, 286 to gate financial data
│  └─ MEDIUM: Affects authorization to sensitive data
│
├─ Trainer Wheels (lines 188, 431, 433)
│  └─ Stores: trainer_wheels
│  └─ Used by: UI hints
│  └─ LOW: Just UX preference
│
└─ Profile Updates (lines 419-420, 450)
   └─ Stores: shop_info updates
   └─ Used by: Form prefills (lines 407-408)
   └─ MEDIUM: If not saved, user loses edits

Risk Analysis by Session Variable

Variable

Risk Level

Affected Functionality

Impact

auth

CRITICAL

Login gate

Users locked out after restart

is_master

CRITICAL

Master control access

Admin locked out

shop_info

CRITICAL

All operations, business context

App non-functional

vault_unlocked

HIGH

Financial data access

Users must re-unlock vault

trainer_wheels

LOW

Help text visibility

UX regression only

4. Environment Variable Requirements

Render Environment Variables Needed

# Supabase (from Render dashboard → Settings → Environment)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJxx...        # Service role key

# Authentication (master backdoor)
MASTER_CODE=your_secret_code
MASTER_PIN=your_secret_pin

# Optional: Session storage (if using Redis)
REDIS_URL=redis://user:pass@host:port

# Optional: App configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true

# Recommended: For better performance
STREAMLIT_CLIENT_TOOLBARMODE=minimal
STREAMLIT_LOGGER_LEVEL=warning

Code Changes for Environment Variables

Current (lines 26-27):

@st.cache_resource
def init_connection() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

Change to:

import os

@st.cache_resource
def init_connection() -> Client:
    url = os.environ.get("SUPABASE_URL") or st.secrets["supabase"]["url"]
    key = os.environ.get("SUPABASE_KEY") or st.secrets["supabase"]["key"]
    if not url or not key:
        raise ValueError("Supabase credentials not found in environment or secrets")
    return create_client(url, key)

For master code (line 59):

MASTER_CODE = os.environ.get("MASTER_CODE", st.secrets.get("auth", {}).get("master_code"))
MASTER_PIN = os.environ.get("MASTER_PIN", st.secrets.get("auth", {}).get("master_pin"))

if business_input_name == MASTER_CODE and password == MASTER_PIN:
    ...

Effort: 1 hour | Risk: LOW

5. Scaling Limitations

Render Infrastructure Constraints

Aspect

Streamlit Cloud

Render

Impact

Instances

1 (managed)

Configurable (1-N)

Multi-instance breaks session state

Auto-scaling

No

Yes

Session loss across instances

Memory

1 GB

512 MB - 8 GB

⚠️ DataFrames may exceed 512MB for large businesses

Storage

1 GB (ephemeral)

Configurable (ephemeral)

No persistent file storage

Cold start

~5s

~10-20s (depends on size)

Longer startup

Concurrency

Unlimited (managed)

Limited per instance

May need scaling

Database connections

Via Supabase

Via Supabase

Same as before

Scaling Scenario Analysis

Small deployment (1-10 businesses, <100 users):

1 Render instance sufficient

Memory: 512 MB - 1 GB (pandas operations)

Estimated cost: $7-10/month

Medium deployment (10-100 businesses, 100-1000 users):

Render auto-scaling needed

PROBLEM: Multi-instance requires session store (Redis)

Memory: 2-4 GB per instance

Estimated cost: $50-100/month + $15/month Redis

Large deployment (100+ businesses, 1000+ users):

Professional infrastructure needed

Render alone insufficient

Would need: Flask/FastAPI (not Streamlit)

This requires framework rewrite (not covered in this evaluation)

Performance Limiting Factors

Financial Dashboard Queries (Lines 292, 482)

Fetches ALL orders for a business

Pandas operations in-memory

Limitation: Becomes slow when business has 10,000+ orders

Mitigation: Pre-aggregate on Supabase, paginate results

Customer Analytics (Lines 348-351)

GroupBy on full DataFrame

Limitation: 100,000+ rows will be slow

Mitigation: Move groupby to SQL query

Session State Serialization

If externalized to Redis, serialization overhead

Limitation: Large shop_info objects slow down auth

Mitigation: Store only business_id in session, fetch rest on demand

6. Expected Benefits of Migration to Render

Operational Benefits

Benefit

How It Works

Impact

More control over environment

Linux container with custom Python

Can install system packages, tune runtime

Predictable pricing

Pay for instance + bandwidth, not users

Cost doesn't spike with user growth

Persistent processes

Can run background jobs

Future: subscription expiry cron job

Custom domain

Render provides free domain + custom domains

Professional branding

Better deployment

Git-triggered deploys, rollback support

Safer releases

Log access

Real-time logs in dashboard

Better debugging

Environment variables

Render UI for secrets management

No .gitignore needed

Auto-scaling

Add instances as load increases

Handle traffic spikes

Performance Benefits

Startup time: ~10-20s vs 5s (Streamlit Cloud optimized)

Memory: Configurable 512MB-8GB per instance

CPU: Shared CPU tier, upgrade to dedicated if needed

Bandwidth: Faster CDN (Cloudflare backed)

Development Benefits

Pull code from any Git branch

Deploy specific commit

Easy rollback if deployment fails

Full SSH access for debugging

7. Expected Limitations of Render

Hard Limitations (Can't Overcome Without Framework Change)

No sticky sessions

Each request could go to different instance

Solution: Externalize session state to Redis/PostgreSQL

Ephemeral storage

/tmp files lost on restart

Solution: Use S3 for file uploads (not currently needed)

No WebSocket persistence

If Streamlit tries to maintain WebSocket, it breaks across instances

Solution: Render <-> Render load balancer (Render handles this)

Slower cold starts than Streamlit Cloud

Streamlit Cloud optimized for instant startup

Render: 10-20 seconds typical

Acceptable for internal business app

Soft Limitations (Workarounds Exist)

Limitation

Workaround

Effort

Session state in-memory

Store in Redis

4-5 hours

Multi-instance session loss

Use single instance or Redis

5 min - 5 hours

Secrets in .streamlit/secrets.toml

Use environment variables

1 hour

Large DataFrames in memory

Pre-aggregate in Supabase

2-3 hours

Deployment secrets visible in build

Use Render secrets, not source code

1 hour

8. Migration Path & Checklist

Phase 1: Preparation (2-3 hours)

Create Render account

Set up empty Render service connected to GitHub

Create .env.render file (NOT committed) with all secrets

Create requirements.txt from current environment

Add render.yaml or configure Render dashboard

Render Configuration File (render.yaml):

services:
  - type: web
    name: washh
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run app.py
    envVars:
      - key: SUPABASE_URL
        scope: run
      - key: SUPABASE_KEY
        scope: run
      - key: MASTER_CODE
        scope: run
      - key: MASTER_PIN
        scope: run
      - key: STREAMLIT_SERVER_HEADLESS
        value: true
      - key: STREAMLIT_SERVER_PORT
        value: 8501
      - key: STREAMLIT_SERVER_ADDRESS
        value: 0.0.0.0

Phase 2: Deployment (30 minutes)

Copy code to GitHub repo

Create Render service from GitHub

Set environment variables in Render dashboard

Trigger deploy

Test login flow

Test order creation

Test vault access

Verify Supabase connectivity

Expected issues at this point:

✅ Login works

✅ Order creation works

⚠️ Session loss on instance restart (acceptable short-term)

⚠️ Multi-instance routing issues (if auto-scaling enabled)

Phase 3: Session State Hardening (2-3 hours, if needed)

If users report session loss after restart:

Add Redis layer:

Add Redis addon to Render ($15/month)

Store session state after each action

Read session state on page load

Alternative: JWT tokens

Issue JWT on login (includes business_id)

Store in session + browser cookie

Verify token on every page load

Alternative: Database sessions

Create sessions table in Supabase

Write session to DB after login

Read session from DB on load

Phase 4: Performance Tuning (4-6 hours, optional)

If response times slow down:

Enable Streamlit caching for Supabase queries

Move financial aggregations to Supabase

Paginate financial dashboard (don't load all orders at once)

Add Redis caching for expensive queries

9. Deployment Checklist

Before Migration

[ ] Backup Supabase database
[ ] Document all environment variables and their values
[ ] Create GitHub repository (if not exists)
[ ] Test app locally with environment variables
[ ] Create .env.render file locally (for reference)
[ ] Verify all secrets are in .gitignore

During Migration

[ ] Create Render account and project
[ ] Create render.yaml or configure via dashboard
[ ] Set all environment variables in Render
[ ] Deploy to Render
[ ] Test login with real Supabase credentials
[ ] Test order creation
[ ] Test vault unlock
[ ] Test master control panel
[ ] Verify no sensitive data in logs
[ ] Check response times (should be <5s)

Post-Migration

[ ] Monitor error logs for 24 hours
[ ] Have team members test on mobile
[ ] Test with multiple concurrent users
[ ] Monitor memory usage (should stay <80% of allocated)
[ ] Create deployment runbook for team
[ ] Document Render-specific configs
[ ] Plan session state improvements (if issues arise)

10. Cost Comparison

Current Cost (Streamlit Cloud)

Streamlit Community Cloud:  $0 (free tier)
Total:                      $0/month

Render Costs

Web Service (1 instance):
  - Starter tier:            $7/month (512MB RAM, shared CPU)
  - Standard tier:           $12/month (1GB RAM, shared CPU)
  - Pro tier:                $29+/month (dedicated CPU)

Redis (if session store needed):
  - Starter tier:            $15/month (256MB)
  - Standard tier:           $50+/month (1GB)

Custom domain:              Included with Render

Estimated minimum:
  - Without session store:   $7-12/month
  - With session store:      $22-27/month

Cost Justification

Current Problem

Render Cost

Benefit

Free tier might get suspended

$7/month

Guaranteed uptime

Limited by Streamlit's constraints

$12/month

Full control, custom features

Can't scale to multiple users

$15/month (Redis)

Multi-user support

Limited logging/debugging

Included

Better observability

Estimated break-even: 2-3 months of paying vs. running on Streamlit Cloud limitations

11. Risk Assessment

Migration Risks (Probability × Impact)

Risk

Probability

Impact

Mitigation

Session loss on restart

HIGH (100%)

MEDIUM (users re-login)

Redis + 4 hours

Multi-instance routing breaks auth

HIGH (if scaling)

HIGH (app broken)

Single instance or Redis

Environment variables exposed

LOW (good practices)

CRITICAL (data breach)

Use Render secrets UI

Supabase connection fails

LOW (same as before)

HIGH (app down)

Supabase status monitoring

Memory exhaustion on large query

MEDIUM (10k+ orders)

HIGH (app crash)

Pagination + tuning

Cold start delays

HIGH (10-20s)

LOW (acceptable)

None needed

Overall Migration Risk: MEDIUM → LOW (with session state mitigation)

12. Render-Specific Advantages vs. Alternatives

Platform

Cold Start

Scaling

Session State

Ease

Cost

Streamlit Cloud

5s ⭐

Limited

Built-in ⭐

Easiest ⭐

$0

Render

15s

Auto ⭐

Manual

Easy

$7-27/mo

Railway

15s

Auto

Manual

Easy

$5-20/mo

Fly.io

20s

Auto ⭐

Manual

Medium

$3-50/mo

AWS Fargate

20s

Auto

Manual

Hard

$20-100+/mo

DigitalOcean

Instant

Manual

Custom

Hard

$6-100/mo

Recommendation: Render is optimal choice for Streamlit on production — good balance of ease and cost.

Summary & Recommendation

Can Washh migrate to Render?

✅ YES, with minor architectural changes to session state handling

Should it migrate?

✅ YES if:

Current Streamlit Cloud deployment is unstable or hitting limits

Need guaranteed uptime

Planning to scale to multiple concurrent users

Want more control over deployment process

❌ NO if:

Current Streamlit Cloud works fine

Don't have $10-30/month budget

User base is <50 people

Key Blockers & Solutions

Blocker

Solution

Effort

Cost

Session loss

Add Redis

4-5 hours

$15/month

Multi-instance issues

Single instance OR Redis

5 min - 4 hrs

$0 - $15/month

Secrets management

Env vars

1 hour

$0

Large DataFrames

Query optimization

2-3 hours

$0

Recommended Approach

Week 1: Basic Migration

Deploy as-is to Render (2 hours setup + testing)

Accept temporary session loss on restart

Cost: $7-12/month

Week 2: Session Hardening (if needed)

Add Redis addon ($15/month)

Store session state externally (4-5 hours development)

Test multi-user scenarios

Cost: +$15/month, +4-5 hours

Week 3: Performance Tuning (optional)

Move analytics to Supabase queries

Add pagination to financial dashboard

Monitor and optimize

Cost: +2-3 hours development

Total Timeline: 1-2 weeks for functional deployment, 2-4 weeks for production-hardened deployment

Total Cost: $7-12/month (basic) or $22-27/month (hardened)