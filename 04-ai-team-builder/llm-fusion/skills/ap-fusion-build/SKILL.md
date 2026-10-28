---
name: ap-fusion-build
description: "Have several different models plan the same build separately, merge the strongest plan blind, then build and audit it. Use for \"run a fusion build on this\" or \"have several models plan this first\"."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Original starter method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Fusion Build

Use when several strong plans should compete before you commit to building one.

## 1. One build brief

The goal, what done looks like, constraints (stack, files in scope, what must not change), and how it will be checked. Show it to the owner.

## 2. Sealed plans

Give the same brief to 3 seats from different model families, each in a fresh session, each asked for a plan only: steps, files touched, risks, tests. No seat sees another's plan. Paid calls need approval.

## 3. Merge blind

Relabel the plans A, B, C. Compare them step by step. Build one merged plan that keeps the strongest choice at each point and notes where it came from. Flag any step where all three disagree: that is a question for the owner.

## 4. Build

One builder executes the merged plan in a separate working copy or branch. Changes to live systems, installs, publishing and spending stay behind their own approvals.

## 5. Audit

A different seat from the builder checks the result against the brief and the tests. Report: what was built, what was verified (and how), what is assumed, and the audit's findings.
