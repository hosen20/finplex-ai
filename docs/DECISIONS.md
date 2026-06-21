# Decisions

This document records important project decisions and the reason behind each one.

## 1. Local-First Product

Decision: Finplex AI runs as a complete local product using Docker infrastructure and locally started services.

Reason: local-first development is reproducible, affordable, easier to debug, and suitable for review by cloning the repository.

## 2. No Public Sign-Up

Decision: Finplex AI does not allow public tenant sign-up.

Reason: the product handles invoices, payment records, customer history, and AI-generated payment follow-up drafts. Tenant onboarding should be controlled by a platform admin.

## 3. Streamlit For Platform Admin

Decision: Platform administration lives in a Streamlit app.

Reason: Streamlit is fast for internal operational tools and keeps platform-level tenant management separate from the tenant-facing React workspace.

## 4. React For Tenant Users

Decision: Tenant users use the React workspace.

Reason: tenant users need a polished product interface for invoice upload, customer intelligence, review queue, approvals, and decision history.

## 5. FastAPI As The Product Gateway

Decision: both Streamlit and React call FastAPI instead of editing the database directly.

Reason: API-level RBAC, validation, audit logging, and tenant isolation stay consistent across all clients.

## 6. Kafka For Invoice Processing

Decision: invoice processing is asynchronous through Kafka.

Reason: OCR, retrieval, risk scoring, LLM drafting, and guardrails can be slow. The upload request should return quickly while processing continues in workers.

## 7. Human Approval Required

Decision: AI drafts are never final actions until a human approves them.

Reason: payment follow-up is sensitive. The AI should assist reviewers, not replace accountability.

## 8. Provider-Agnostic AI

Decision: OCR, LLM, and retrieval logic are isolated behind model-server services.

Reason: the project can switch providers or use local/free options without rewriting the API and frontend.

## 9. Tenant ID Everywhere

Decision: every tenant-owned object carries tenant scope.

Reason: tenant isolation is the most important SaaS security boundary.

## 10. Public And Synthetic Data Only

Decision: local data should be public, synthetic, or privacy-safe.

Reason: the repository must be safe to show on a hiring portal and must not include private financial records.
