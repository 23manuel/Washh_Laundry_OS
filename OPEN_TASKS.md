# OPEN_TASKS.md

# Washh Current Sprint

Sprint Goal:
Prepare Washh for pilot laundries and eliminate trust-destroying issues.

---

# P0 - Must Fix Before Pilot Launch

## Critical Bug Fixes

* [ ] Fix delivery_target → delivery_date mismatch
* [ ] Fix total_price → total mismatch
* [ ] Verify all order-related column names

---

## Security

* [ ] Implement bcrypt password hashing
* [ ] Create migration-safe password upgrade path
* [ ] Stop storing new passwords as plaintext
* [ ] Verify login works with hashed passwords
* [ ] Replace default PIN 0000
* [ ] Generate secure random PINs
* [ ] Remove default PIN hints

---

## Tenant Isolation

* [ ] Audit every Supabase query
* [ ] Verify business_id filtering everywhere
* [ ] Verify laundries cannot access other laundries' data
* [ ] Verify owner-only areas are protected

This is considered one of the highest-value validation tasks.

---

## Reliability

* [ ] Implement database write error handling
* [ ] Add success/failure feedback for critical operations
* [ ] Verify order creation cannot silently fail
* [ ] Verify order updates cannot silently fail
* [ ] Verify debt-clearing workflow behaves correctly

---

## Authentication

* [ ] Review master admin access
* [ ] Move master credentials to secrets/environment variables
* [ ] Rotate master credentials
* [ ] Verify admin access works as intended

---

# P1 - Before First Paying Customers

## Staff Accountability

* [ ] Track logged-in staff identity
* [ ] Associate actions with staff users
* [ ] Improve authorization boundaries

---

## Audit Logging

* [ ] Record critical actions
* [ ] Track order status changes
* [ ] Track password changes
* [ ] Track PIN changes
* [ ] Track administrative actions

---

## Operational Improvements

* [ ] Improve onboarding experience
* [ ] Improve owner settings experience
* [ ] Improve navigation structure
* [ ] Verify Owner Vault accessibility

---

# P2 - Technical Debt

## Refactoring

* [ ] Split app.py into modules
* [ ] Separate UI from business logic
* [ ] Centralize Supabase access
* [ ] Remove duplicated phone formatting
* [ ] Remove duplicated validation logic

---

## Documentation

* [ ] Create architecture diagrams
* [ ] Document authentication flow
* [ ] Document database schema
* [ ] Document deployment process

---

# Future Considerations (Not Current Priorities)

These are intentionally deferred.

* Render optimization
* Redis
* FastAPI
* React frontend
* Microservices
* Advanced scaling
* Performance optimization for large datasets

Do not prioritize these until revenue and retention have been validated.

---

# Acceptance Test Plan

Before pilot launch, manually verify:

## Authentication

* [ ] Business signup
* [ ] Staff login
* [ ] Password change
* [ ] PIN change

## Operations

* [ ] Create order
* [ ] Move order through every status
* [ ] Mark order delivered
* [ ] Clear customer debt

## Financial Controls

* [ ] Vault access works
* [ ] Incorrect PIN denied
* [ ] Correct PIN accepted

## Administration

* [ ] Business onboarding
* [ ] Staff creation
* [ ] Subscription updates

## Data Protection

* [ ] Laundry A cannot see Laundry B data
* [ ] Staff permissions enforced
* [ ] Passwords stored hashed

---

# Current Mission

Do not redesign Washh.

Do not rebuild Washh.

Do not optimize for scale.

Build enough reliability, security, and trust for real laundries to use the platform daily for 30 consecutive days.
