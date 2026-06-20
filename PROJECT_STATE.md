# PROJECT_STATE.md

# Washh Project State

Last Updated: June 2026

---

# Project Overview

Washh is a laundry business operating system designed to digitize and automate operational workflows for laundry businesses.

The project currently uses:

* Streamlit
* Supabase
* A single primary application file (`app.py`)

The immediate objective is to prepare the product for pilot usage by real laundry businesses while operating under a zero-dollar infrastructure budget.

Current focus is operational reliability, user experience, and pilot validation.

---

# Current Business Context

Known facts:

* Real businesses have expressed interest in using Washh.
* Potential customers have reached out through TikTok.
* The platform includes a 30-day free trial model.
* The intention is to validate usage and willingness to pay before committing to paid infrastructure or major platform spending.

Current operating principle:

1. Launch pilots.
2. Validate real usage.
3. Validate retention.
4. Validate payment conversion.
5. Upgrade infrastructure only when justified by customer demand and revenue.

---

# Current Technology Stack

## Application Layer

* Streamlit

## Database Layer

* Supabase

## Authentication

* Custom authentication implemented inside `app.py`

## Deployment

Current deployment:

* Streamlit deployment

Target direction under evaluation:

* Render deployment

Reason:

* Improve user experience
* Improve interface quality
* Improve visual presentation
* Improve overall customer-facing product experience

No framework migration decision has been formally documented.

---

# Repository Structure

Confirmed repository files:

* .devcontainer
* .gitignore
* COPILOT_CONTEXT.md
* LICENSE
* README.md
* app.py
* requirements.txt

---

# Current Architecture

Current architecture is largely contained within `app.py`.

Observed responsibilities include:

* Authentication
* Business onboarding
* Staff management
* Order management
* Operational workflow management
* Subscription management
* Master administration
* Customer analytics
* Vault functionality

No modular architecture currently exists based on available information.

---

# Confirmed User Roles

## Master Admin

Observed capabilities:

* Network Health
* Subscription monitoring
* Business onboarding
* Staff account creation
* Access management

Observed master menu:

* Network Health
* Onboarding
* Access Management

---

## Laundry Business

Observed capabilities include:

* Login
* Order management
* Workflow tracking
* Customer management
* Financial tracking
* Vault access

---

## Staff

Observed capabilities:

* Login
* Operational usage

Full permission boundaries have not yet been verified.

---

# Confirmed Database Tables

The following tables are referenced in available code.

## laundries

Observed fields:

* id
* business_name
* business_code
* owner_phone
* subscription_status
* trail_start_date
* is_active
* expiry_date
* owner_pin

Purpose:

* Tenant management
* Subscription management
* Business identity

---

## staff

Observed fields:

* business_id
* staff_name
* password
* role
* created_at

Purpose:

* Authentication
* Staff access management

---

## orders

Observed fields:

* id
* business_id
* cust_name
* cust_phone
* location
* items_count
* total
* amount_paid
* delivery_date
* notes
* status
* created_at

Purpose:

* Order lifecycle management
* Payment tracking
* Customer history

---

# Confirmed Order Lifecycle

Current operational workflow:

Received
↓
Sorting
↓
Processing
↓
Quality Check
↓
Ready

Associated functions observed in audits and discussions:

* Customer tracking
* Payment tracking
* Outstanding balance tracking
* Operational visibility

Future enhancements have been discussed but are not yet implemented.

---

# Subscription Model

Observed behavior:

* Businesses can be onboarded.
* Trial periods are supported.
* Expiry dates are tracked.
* Businesses can be activated or deactivated.
* Subscription status is monitored from Master Control.

Master Control includes:

* Subscription Radar
* WhatsApp renewal nudges
* Manual renewal override

---

# Audit Findings

## Architecture Findings

Observed findings:

* Large monolithic app.py
* Business logic and UI logic mixed together
* Duplicate helper logic present
* Limited separation of concerns

Status:

Recognized technical debt.

---

## Code Quality Findings

Observed findings:

Unreachable route:

* Potential Owner Vault route accessibility issue identified by Copilot audit.

Duplicate logic:

* Phone formatting repeated multiple times.
* Password validation repeated multiple times.

Column inconsistencies identified:

* delivery_target vs delivery_date
* total_price vs total

Status:

Column inconsistencies are considered operational issues because they may affect functionality.

---

## Security Findings

Observed findings:

* Plaintext password storage
* Default owner PIN value of 0000
* Master access mechanism requires review

Status:

These findings have been classified as high priority for pilot readiness.

---

## Reliability Findings

Observed findings:

* Database write operations generally assume success.
* Limited write-failure handling.
* User feedback during failures is inconsistent.

Status:

Reliability improvements are planned before pilot onboarding.

---

# Accepted Project Constraints

These constraints are currently accepted unless explicitly changed.

## Financial Constraints

* Infrastructure budget = $0
* Paid services should be avoided where practical

---

## Product Constraints

* Existing application should continue evolving rather than being rewritten
* Pilot validation is prioritized over architectural redesign
* Improvements should focus on reliability and usability first

---

## Deployment Direction

Current intention:

* Improve user-facing experience
* Explore Render deployment
* Improve visual presentation and usability

Not yet verified:

* Exact deployment architecture
* Exact UI technology changes
* Exact migration strategy

These remain open decisions.

---

# Current Priorities

## P0

Highest priority work before pilot launch:

* Fix column inconsistencies
* Improve password security
* Remove default PIN usage
* Improve database write handling
* Review tenant isolation and data separation

---

## P1

After P0 stabilization:

* Improve staff accountability
* Improve auditability
* Improve operational controls

---

## P2

Future technical debt reduction:

* Modularization
* Code organization
* Architecture cleanup

---

# Decision Framework

When evaluating recommendations:

Priority order is:

1. Reliability
2. Operational trust
3. User experience
4. Security
5. Architecture improvements
6. Scaling concerns

The project is currently optimizing for successful pilot adoption rather than large-scale infrastructure readiness.
