# Washh Copilot Context

## Project Overview

Washh is a Business Operating System (BOS) designed for high-volume laundry businesses.

The platform digitizes laundry operations including customer management, order tracking, production workflow, inventory visibility, operational reporting and business analytics.

Washh is not a consumer laundry marketplace.

The system is designed primarily for laundry operators and internal staff.

---

## Current Technology

Frontend:

* Streamlit

Backend:

* Python

Database:

* TBD

Deployment:

* Migrating from Streamlit deployment toward Render deployment.

---

## Core Principles

1. Do not invent business rules.

2. Ask before introducing new workflows.

3. Preserve existing functionality unless explicitly instructed.

4. Minimize breaking changes.

5. Refactor incrementally.

6. Prioritize maintainability over clever code.

---

## Business Workflow

Customer
→ Laundry Received
→ Processing
→ Quality Check
→ Ready
→ Delivered

Status transitions should follow business logic and not be reordered without approval.

----

## UI Principles

* Clean operations dashboard.
* Mobile-friendly.
* Fast loading.
* Minimal clicks.
* Suitable for laundry staff with limited technical experience.

---

## Coding Rules

* Explain architectural changes before implementing them.
* Prefer modular functions.
* Avoid large monolithic functions.
* Preserve backward compatibility where possible.
* Do not create placeholder code unless requested.

---

## Current Priorities

1. Improve user experience.
2. Improve deployment architecture.
3. Improve operational visibility.
4. Prepare system for future scale.
