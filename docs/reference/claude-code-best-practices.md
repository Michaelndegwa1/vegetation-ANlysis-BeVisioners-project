# Building with Claude Code — General Best Practices

> A reusable methodology for any software project. Covers the full lifecycle from first exploration to active development, including how to use subagents, manage context, and structure documentation so every session starts rich and builds fast.

---

## The Fundamental Trade-off

**Cheap sessions vs. informed sessions are not the same thing.**

An uninformed session wastes tokens re-discovering facts that were already known. An informed session — one where Claude walks in with accurate docs and a clear memory — builds correctly on the first attempt.

Invest heavily in the planning phase. It pays back every build session after.

---

## Part 1 — Project Onboarding

### 1.1 Clone Everything Locally

Claude Code reads files from your filesystem. It cannot fetch from remote URLs or access repos it cannot see. Before your first session:

- Clone all repos into a consistent working directory
- Keep related repos as siblings: `work/project/android/`, `work/project/ios/`, `work/project/api/`
- Confirm Claude can read them: `! ls /path/to/project/`

### 1.2 Start with a Map, Not a Dive

Your first session should produce a map of the codebase — not implementation. Ask Claude to explore each repo and produce a notes file per repo.

**Good first prompt:**
> "Explore `/path/to/android/` and write `android-notes.md` covering: tech stack, folder structure, key classes and what they do, architecture pattern, and anything unusual."

**What to capture in notes files:**
- Language, framework, key dependencies and their versions
- Folder structure with purpose annotations
- The 5–10 most important files and what they own
- Architecture pattern (MVVM, BLoC, MVC, etc.)
- Data storage (SQLite, Core Data, SharedPreferences, etc.)
- Network layer (how HTTP calls are made)
- Known issues or tech debt
- Approximate size (file count, line count)

### 1.3 Use the Explore Subagent for Broad Scanning

When you need to find something across a large codebase without knowing exactly where it is, use the `Explore` subagent. It searches efficiently without pulling full file contents into the main context.

**When to use Explore:**
- "Where is the FCM handler defined?"
- "Which files reference `action=list`?"
- "Find all places where the bitmask is evaluated"

**How to invoke it:** Claude Code will use it automatically when searching, or you can hint: *"search the codebase for X"*.

**When NOT to use Explore:** For deep reading of a specific file you already know. Use `Read` directly instead — it's faster and more precise.

---

## Part 2 — Verification Before Documentation

### 2.1 Never Trust Assumptions — Verify From Source

The most expensive bugs are the ones planted during planning. A wrong field name, a backwards color assignment, or a misunderstood API semantic becomes many hours of debugging during implementation.

**Rule:** Any fact that is not confirmed from actual source code is an assumption. Assumptions must be verified before they enter a spec.

**Common things that are wrong in first-draft docs:**
- Exact API field names (`coords_lat` not `lat`, `notification_id` not `notification-id`)
- Bitmask bit positions and their semantic meaning
- Which features exist in the backend vs. which have UI in the app
- Whether data is stored locally or always fetched
- Which endpoints exist in one domain but not another
- What "acknowledge" actually does (mark as read? send hardware command?)

### 2.2 The Verification Session

After your initial notes files exist, do a dedicated verification session:

1. List every uncertain or assumed detail across all your draft docs
2. For each item, ask Claude to read the relevant source file and confirm
3. Correct every doc immediately when an error is found
4. Record all confirmed facts in a `project_technical_details.md` memory file

**Good verification prompt:**
> "Read `api/api.php` lines 340–380 and confirm: which bit position corresponds to SOS in the alert bitmask, and what are the exact field names sent in the FCM payload?"

### 2.3 Use Subagents for Parallel Verification

When you have multiple independent things to verify — different repos, different features — run them as parallel subagents rather than sequentially in the main session.

**Why:** Parallel subagents run simultaneously. Verifying 4 things in parallel takes the same wall-clock time as verifying 1.

**Pattern:**
```
Agent 1 (background): Verify FCM payload fields in api/api.php + servidor/api.php
Agent 2 (background): Verify marker color bitmask in android VesselData.java
Agent 3 (background): Verify buoy rendering logic in iOS Comunes.swift
```

All three run at the same time. Main session continues or waits for results.

**When to run in background vs. foreground:**
- **Foreground** (wait for result): when you need the answer before you can proceed
- **Background** (fire and continue): when the work is independent and you have other things to do

---

## Part 3 — The Documentation Stack

Build these documents in order. Each one depends on the previous.

### Layer 1 — Product Overview (`app-about.md`)

One document describing the product as a user and a developer would understand it. This is what Claude reads first in every build session to understand the domain.

**Contents:**
- What the app is and who uses it
- Every screen with a one-paragraph description
- Every API endpoint: when called, params, response, side effects
- Push notification payload structure (exact field names)
- Data stored locally vs. fetched from server
- Authentication flow
- Multi-domain / multi-tenant logic if applicable

### Layer 2 — Architecture Proposal (`flutter-proposal.md` or similar)

The "why" behind every major technical decision.

**Contents:**
- Package/library selections with rationale
- Architecture pattern (BLoC, Riverpod, Provider, etc.) and why
- Feature scope — what to port, what to improve, what to skip
- Domain divergence handling (e.g. ZunTrack vs ZuniSOS capabilities)
- Phased migration or build plan with clear phase boundaries
- Feature parity table: existing apps vs new app

### Layer 3 — Technical Specification (`flutter-technical-spec.md` or similar)

The "what to build, exactly" doc. This is Claude's primary reference during implementation. It must be precise enough that Claude can write code without guessing.

**Per-feature contents:**
- Data models: all fields, types, nullable/non-nullable, where they come from
- BLoC events (sealed class + concrete subclasses, all fields)
- BLoC states (all fields, copyWith, Equatable props)
- Repository method signatures and return types
- API call details: action, request params, response field names
- Edge cases: conditional behavior, domain-specific logic
- Code snippets for non-obvious parts

**Rule:** If Claude would have to guess something, the spec is incomplete. Add it.

### Layer 4 — Folder Structure (`folder-structure.md`)

Every folder name, file name, and class name — decided before the first `flutter create`.

**Contents:**
- Full `lib/` tree with every file listed and annotated
- Feature folder anatomy (what goes in bloc/, view/, screens/, widgets/, data/)
- Shared vs. feature-scoped models rule
- Router path strings
- File naming conventions and class naming conventions
- File templates for the most-used patterns (BLoC state, BLoC events, page/view split)

### Layer 5 — UI Reference (`ui-design-prompt.md`)

A precise, color-accurate description of every screen.

**Contents:**
- Color palette with hex values AND semantic meaning (not just "red" — "red = SOS emergency, highest priority")
- Typography scale
- Component style definitions (button radius, input style, card shadow, etc.)
- Screen-by-screen layout descriptions
- Domain divergence noted per screen (which screens differ between domains)
- Prompt templates for AI UI generators (Midjourney, Uizard, v0, Galileo)

### Layer 6 — i18n Plan (`ui-reuse-plan.md` / `i18n-strategy.md`)

**Contents:**
- Complete ARB key inventory — every user-visible string with placeholder specs
- Locale detection order
- Date/number formatting patterns
- Background notification string handling (no context available)
- Translation pipeline (manual, DeepL, Google Translate)
- CI completeness check to catch missing translations

---

## Part 4 — The Memory System

### 4.1 What Memory Is

Claude Code has a per-project memory directory. Files written there are automatically loaded at the start of every session in that project. This is how knowledge persists across conversations.

**Location:** `.claude/projects/<encoded-project-path>/memory/`

The `MEMORY.md` file in that directory is the index — it's always loaded. Individual memory files are referenced from the index.

### 4.2 What to Store in Memory

Store facts that are **not derivable from reading the current code**. If Claude can just `grep` for it or `Read` the file, don't store it — it'll be found fresh. Memory is for knowledge that requires interpretation.

| Store in memory | Do NOT store in memory |
|---|---|
| Verified API field names | File paths (grep finds them) |
| Bitmask semantics | Code patterns (they're in the code) |
| Domain capability differences | Git history |
| Which features have no UI yet | Architecture (it's in the spec) |
| Session progress + next steps | In-progress task details |
| User/team preferences | Debugging solutions (fix is in the code) |

### 4.3 Memory File Types

| File | Type | Contents |
|---|---|---|
| `project_<repo>.md` | project | Repo overview: tech stack, structure, key classes |
| `project_technical_details.md` | project | Source-verified low-level facts |
| `progress.md` | project | Current status + next steps — update every session |
| `feedback_<topic>.md` | feedback | How Claude should behave on this project |
| `user_<topic>.md` | user | About the developer: expertise, preferences |
| `reference_<topic>.md` | reference | Where to find external resources |

### 4.4 The `progress.md` Rule

Update `progress.md` at the end of every session. It should always answer:
- What was just completed
- What is currently in progress
- What comes next (in order)

This is the single most valuable memory file. A good progress note means the next session starts building in 30 seconds instead of spending 5 minutes re-orienting.

---

## Part 5 — Subagent Patterns

Subagents are separate Claude instances that run tasks independently. Use them to parallelize work, protect the main context from large outputs, and tackle tasks that are too broad for a single focused session.

### 5.1 When to Use Subagents

| Use case | Agent type | Mode |
|---|---|---|
| Searching/finding things in a codebase | Explore | Foreground |
| Deep research across multiple files | general-purpose | Foreground or background |
| Updating multiple independent files simultaneously | general-purpose | Background (parallel) |
| Reviewing code for correctness | code-reviewer | Foreground |
| Architecture planning | Plan | Foreground |
| Anything that would flood the main context with large outputs | general-purpose | Foreground |

### 5.2 The Parallel Background Pattern

When you have N independent update tasks, run them all as background agents simultaneously rather than one at a time.

**Example — updating 4 notes files in parallel:**
```
Session: "We've verified these new facts. Update all four notes files."

→ Agent A (background): Update android-notes.md with marker colors + FCM details
→ Agent B (background): Update ios-notes.md with buoy logic + settings defaults
→ Agent C (background): Update api-notes.md with endpoint details + ACK semantics
→ Agent D (background): Update servidor-notes.md with missing endpoint list

Main session: continues with other work or waits for notifications
```

All four complete in parallel. Total time = slowest single agent, not sum of all four.

### 5.3 Protecting the Main Context

The main session context is finite and expensive. Large outputs (full file contents, long search results, extensive code analysis) eat context fast and slow down every subsequent exchange.

**Rule:** If a task would return more than ~500 lines of output, delegate it to a subagent. The subagent absorbs the large output; only its summary returns to the main context.

**Examples of context-protecting subagent use:**
- "Explore this 5,000-line file and summarize the authentication flow"
- "Read all 4 repos and tell me every place `action=list` is called"
- "Review this entire feature implementation against the spec and list discrepancies"

### 5.4 Foreground vs Background Decision

```
Is the result needed before the next step?
  ├─ Yes → run foreground (wait for result)
  └─ No  → run background (continue working)
        └─ Are there multiple independent tasks?
              ├─ Yes → launch all as background simultaneously
              └─ No  → still background if you have other work
```

### 5.5 Writing Good Subagent Prompts

A subagent has no memory of your conversation. Brief it like a colleague who just walked in.

**Include in every subagent prompt:**
- What the project is (one sentence)
- What specific task to do
- Exact file paths to read or write
- What facts are already known (so it doesn't re-derive them)
- What format the output should take

**Bad prompt:** "Update the android notes with the new info"

**Good prompt:**
> "This is the Z-Alert Flutter rewrite project. We've verified from Android source (`VesselData.java`) that: SOS = bit 6 = RED marker, forbidden zone = bits 1/9/11 = PINK marker, buoys use `tipo == -1` for detection and `ic_circle_black_24dp` as icon. Update `/path/to/android-notes.md` to add a 'Marker Color Logic' section with this information. Read the file first so you don't overwrite existing content."

---

## Part 6 — Build Sessions

### 6.1 How to Scope a Session

Each session should have one clearly defined output. Vague sessions produce vague code.

| Too broad | Well scoped |
|---|---|
| "Build the alerts feature" | "Implement AlertsBloc and AlertRepository per Section 5.3 of the spec" |
| "Set up the project" | "Scaffold the folder structure from `folder-structure.md` and install all packages from `flutter-proposal.md` Section 3" |
| "Add notifications" | "Implement FcmService — register token on login, handle foreground messages, dispatch FcmAlertReceived to AlertsBloc" |

### 6.2 The Session Opening Pattern

Start every build session with a clear reference chain:

1. **What to build:** specific feature or task
2. **Where the spec is:** exact section of the technical spec
3. **What context matters:** which memory files or planning docs are relevant

**Example:**
> "Implement the Alert data model and AlertRepository. Follow Section 5.3 of `flutter-technical-spec.md`. Key facts are in `project_technical_details.md` — alerts are never stored locally, the 24h window, and the exact API response field names."

### 6.3 The Spec Is the Source of Truth

Once the technical spec is finalized, treat it as authoritative. During build sessions:

- If Claude writes code that conflicts with the spec → the spec wins, fix the code
- If the spec seems wrong → pause, verify from source, update the spec, then re-run
- Do NOT re-verify source code during build sessions — that's what the planning phase was for

**Exception:** If a genuine bug or inconsistency is discovered during building that wasn't caught in planning, stop, verify from source, update the spec and memory, then continue.

### 6.4 Token Efficiency Rules

| Rule | Why |
|---|---|
| Reference specific sections, not whole docs | "Section 5.3" loads less than "the whole spec" |
| One feature per session | Keeps context focused, reduces drift |
| Use subagents for large output tasks | Protects main context |
| Don't re-explain what memory already covers | Memory files load automatically |
| Update `progress.md` at session end | Next session starts immediately, no re-orientation |
| Prefer `Edit` over `Write` for existing files | Sends only the diff, not the full file |

---

## Part 7 — Session Hygiene

### At the Start of Every Session
- Check `progress.md` — confirms where you are and what comes next
- Confirm the relevant spec section is still current (no changes since last session)

### During a Session
- If a new verified technical fact is discovered → update the relevant memory file immediately, don't wait
- If a spec error is found → fix the spec before continuing to build
- Mark tasks done as you go — don't batch completions

### At the End of Every Session
- Update `progress.md`: what was done, what's in progress, what's next
- If any planning doc was corrected during the session, bump its version number and note the change in the footer
- If a new technical fact was confirmed → add it to `project_technical_details.md`

---

## Part 8 — The Document and Memory Map

```
project-root/
│
├── Codebase analysis (one per repo)
│   ├── android-notes.md
│   ├── ios-notes.md
│   ├── api-notes.md
│   └── servidor-notes.md  (or backend-notes.md, etc.)
│
├── Planning docs (build in this order)
│   ├── app-about.md                ← Layer 1: Product + API overview
│   ├── <tech>-proposal.md          ← Layer 2: Architecture decisions
│   ├── <tech>-technical-spec.md    ← Layer 3: Per-feature implementation spec
│   ├── folder-structure.md         ← Layer 4: Full file tree + naming rules
│   ├── ui-design-prompt.md         ← Layer 5: Screen descriptions + color system
│   └── ui-reuse-plan.md            ← Layer 6: Component reuse + ARB keys
│
├── Strategy docs (optional)
│   └── i18n-strategy.md            ← Translation pipeline
│
└── Workflow docs
    ├── claude-workflow.md           ← Project-specific workflow
    └── claude-code-best-practices.md ← This file

.claude/projects/<path>/memory/
├── MEMORY.md                        ← Index (always auto-loaded)
├── project_<repo>.md                ← One per repo
├── project_technical_details.md     ← Verified low-level facts
├── progress.md                      ← Current status + next steps
└── feedback_<topic>.md              ← How Claude should behave
```

---

## Part 9 — Quick Reference Checklists

### Starting a New Project
- [ ] All repos cloned locally
- [ ] Notes file per repo written
- [ ] Uncertain details verified from source
- [ ] `app-about.md` written
- [ ] Architecture proposal written and reviewed
- [ ] Technical spec written per feature
- [ ] Folder structure decided
- [ ] UI descriptions written with correct color semantics
- [ ] ARB keys inventoried
- [ ] Memory files created and indexed in `MEMORY.md`
- [ ] `progress.md` written with Phase 1 next steps

### Before Each Build Session
- [ ] Check `progress.md` — know what you're building
- [ ] Identify the spec section that covers today's task
- [ ] Confirm the spec hasn't drifted from reality

### After Each Build Session
- [ ] `progress.md` updated
- [ ] New technical facts added to `project_technical_details.md`
- [ ] Any corrected planning docs have updated version numbers

### When to Spawn a Subagent
- [ ] Task requires reading/searching across many files
- [ ] Multiple independent tasks can run in parallel
- [ ] Output would be large enough to crowd out main context
- [ ] Task is a review/audit (independent perspective is valuable)

---

## Lessons That Apply to Any Project

1. **Verify colors, enums, and field names from source — never assume.** These are the details most likely to be wrong and most expensive to fix later.

2. **"Supported by backend" ≠ "has a UI".** Always check both sides. Features the backend supports but the app doesn't expose are opportunities.

3. **Domain divergence is always more complex than it looks.** If your project has multiple environments, tenants, or user types — map every capability difference explicitly before building.

4. **Parallel background agents are underused.** When you have 4 files to update or 4 things to verify, don't do them one at a time. Fire all 4 and come back when they're done.

5. **The spec saves more tokens than it costs.** A well-written spec section costs ~2,000 tokens to produce. It saves 10,000+ tokens of back-and-forth during implementation because Claude never has to guess.

6. **Update memory when facts change, not at the end of the project.** Stale memory is worse than no memory — it confidently tells Claude wrong things.

7. **`progress.md` is the highest-value memory file.** It costs almost nothing to write and eliminates all re-orientation overhead at session start.

---

*Created: June 2026*
