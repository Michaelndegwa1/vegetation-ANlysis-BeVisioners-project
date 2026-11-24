# Memory and Token Management with Claude Code: A General Guide

> A practical guide for any team member using Claude Code, on any kind of project. It explains how Claude Code remembers things between sessions, how to keep each session's context small and focused, and how that affects quality and cost. It covers several starting points: a brand-new project, an existing codebase, joining a team, and small one-off tasks.

Checked against the Claude Code docs in November 2026. Commands change between versions, so run `/help` if something here does not match what you see.

---

## The Core Idea

**Claude Code only knows two things at any moment: what is in its memory files, and what is in the current conversation.**

- Everything it learns in a session (file contents, decisions, your corrections) lives in the conversation. When the session ends, or is cleared, that knowledge is gone unless it was written to a memory file.
- Everything in the conversation is re-sent to the model on every turn. A long, cluttered session costs more on every message and gives less focused answers.

So there are two skills to learn:

1. **Memory:** write down the small set of facts every future session needs, and nothing else.
2. **Context hygiene:** keep each session focused on one task, and stop old material piling up.

Done well, a new session starts with the right knowledge in seconds, and each turn stays cheap and accurate.

---

## Part 1: Understanding Context and Tokens

### 1.1 What the Context Window Contains

The context window is everything the model can see in a session. It fills up with:

| Source | Example | Grows during the session? |
|---|---|---|
| System instructions | Claude Code's built-in instructions | No |
| Memory files | CLAUDE.md files, the auto memory index | No (loaded at the start) |
| Tool definitions | Built-in tools, MCP servers you have connected | No |
| Your messages | Questions, pasted logs, pasted errors | Yes |
| Claude's replies | Explanations, plans, code | Yes |
| Tool results | Files read, search results, command output | Yes, and usually the biggest part |

The last row is the one to watch. Reading one large file or printing a long log can use more space than an hour of conversation.

### 1.2 Tokens in Practice

- A token is roughly 4 characters of English text or code. 1,000 lines of typical code is in the region of 10,000 tokens.
- Every turn re-sends the whole conversation. Claude Code uses **prompt caching** so the unchanged part is much cheaper, but it still counts toward the context limit.
- When the context gets close to full, Claude Code **auto-compacts**: it replaces older conversation with a summary. Summaries lose detail, so it is better to stay well below the limit.

### 1.3 Why Smaller Context Gives Better Answers

A focused context is not only cheaper. When the context holds three unrelated tasks, two abandoned approaches and a 2,000-line log, the model has more irrelevant material to weigh, and earlier mistakes can resurface. One task per session, with only the relevant files read, consistently gives better results.

### 1.4 Seeing What Is Going On

| Command | What it shows |
|---|---|
| `/context` | How full the context is, broken down by memory, tools, conversation, with suggestions |
| `/usage` (also `/cost`) | Tokens used, cost or plan usage, and how much came from the cache |
| `/statusline` | Sets up a permanent status line, for example showing context use or cost |

**Habit:** glance at `/context` when a session has been running a while, or when answers start to drift.

---

## Part 2: How Claude Code Remembers Things

There are two kinds of memory: **instructions you write** (CLAUDE.md files) and **notes Claude writes** (auto memory). Both load automatically at the start of a session.

### 2.1 CLAUDE.md Files

| Level | Location | Who sees it | Put here |
|---|---|---|---|
| Organisation | Managed policy file set by IT, for example `/Library/Application Support/ClaudeCode/CLAUDE.md` (macOS), `/etc/claude-code/CLAUDE.md` (Linux) | Everyone on that machine | Company rules: security, compliance, approved tools |
| Personal | `~/.claude/CLAUDE.md` | Only you, in every project | Your preferences: language, tone, commit style, tools you like |
| Project | `./CLAUDE.md` or `./.claude/CLAUDE.md`, committed to git | The whole team | How to build and test, conventions, architecture, "never do X" rules |
| Project, personal | `./CLAUDE.local.md`, gitignored | Only you, this project | Your local URLs, test accounts, personal shortcuts |
| Subfolder | `CLAUDE.md` inside a folder, such as `backend/CLAUDE.md` | The team | Rules for one area. Loaded only when Claude works on files there |

Related features:

- **`/init`** reads the codebase and writes a starting project CLAUDE.md. Always review it: it tends to be long and to describe things Claude could find by itself.
- **`/memory`** opens the memory files for editing and turns auto memory on or off.
- **Imports:** a line `@docs/api.md` in a CLAUDE.md pulls that file in. Imports can be nested a few levels deep. Use imports to point to documentation that already exists instead of copying it.
- **AGENTS.md:** if a repo has an `AGENTS.md` (a format shared with other AI tools) and no CLAUDE.md, Claude Code can read it instead. This is configurable in `/config`.

### 2.2 Auto Memory

- Claude Code keeps its own notes per project in `~/.claude/projects/<project>/memory/`.
- `MEMORY.md` is the **index**: it loads at the start of every session. Individual topic files are listed in it and read when relevant.
- It is on by default. Turn it off with `/memory` or the `autoMemoryEnabled` setting.
- It is stored **on your machine only**, not in the repo. Your teammates do not get your auto memory.
- You can manage it in plain language: "remember that the staging database is read-only", "forget the note about the old deploy script", "what do you have in memory about testing?".

### 2.3 Which Memory to Use

| The fact is... | Put it in |
|---|---|
| Needed by the whole team, true for the project | Project `CLAUDE.md` (commit it) |
| About how *you* like to work, in any project | `~/.claude/CLAUDE.md` |
| About you, for this project only (local paths, accounts) | `CLAUDE.local.md` |
| Something Claude learned along the way: progress, a decision, a correction you gave | Auto memory |
| Long reference material (API docs, specs) | A normal doc in the repo, linked with `@` from CLAUDE.md |
| A secret (token, password, key) | **Nowhere in memory.** Use environment variables or a secrets manager |

---

## Part 3: Starting Points

Not every project starts the same way. Here is how to set up memory for the common cases.

### 3.1 Starting a Brand-New Project

There is no code yet, so there is nothing for `/init` to read. Memory starts with your decisions.

**Step 1: write a short project CLAUDE.md before the first line of code.**

```markdown
# Recipe Planner

A web app for planning weekly meals. Next.js 15, TypeScript, PostgreSQL via Prisma.

## Commands
- Dev server: `pnpm dev`
- Tests: `pnpm test` (Vitest). Run the related test file after every change.
- Lint: `pnpm lint`

## Conventions
- Use pnpm, never npm or yarn.
- Server code goes in `src/server/`, UI in `src/app/`.
- All database access goes through `src/server/db.ts`.

## Rules
- Ask before adding a new dependency.
- Never commit; I commit myself.
```

**Step 2: as decisions are made, add them as one-line rules**, with the reason if it is not obvious ("Dates are stored in UTC; the UI converts to local time").

**Step 3: once there is real code, run `/init`** and merge anything useful into your CLAUDE.md, rather than replacing it.

### 3.2 Working on an Existing Codebase You Own

**Step 1: run `/init`**, then edit the result down. Keep build and test commands, conventions and non-obvious rules. Remove long descriptions of folders and files: Claude can see those itself.

**Step 2: let the first session be a map, not a change.**

> "Read the project and summarise: tech stack, how the code is organised, how to run and test it, and anything unusual. Don't change anything. Then suggest what belongs in CLAUDE.md."

For a large codebase, ask for a subagent to do the reading so the main session stays small:

> "Use a subagent to explore the repo and report back the architecture and the 10 most important files, in under 300 words."

**Step 3: write the results down.** Short facts go in CLAUDE.md. A longer architecture write-up goes in a doc (for example `docs/architecture.md`), imported or referenced from CLAUDE.md.

### 3.3 Joining a Team Project

- Read the project CLAUDE.md first. It is what every teammate's Claude sees.
- Put your personal set-up (local ports, test logins, your preferred workflow) in `CLAUDE.local.md` or `~/.claude/CLAUDE.md`, **not** in the shared file.
- If you find something missing or wrong in the shared CLAUDE.md, change it through a normal pull request, like code.
- Expect your auto memory to be empty at first. It fills up as you work.

### 3.4 Several Related Repositories

When the work spans several repos (for example a mobile app, a backend and a website):

- Open Claude Code in a parent folder that contains them, or use `/add-dir` to give a session access to another folder.
- Give each repo its own CLAUDE.md about that repo.
- Put cross-repo facts (how the app calls the backend, shared data formats) in the CLAUDE.md of the folder you usually start from.

### 3.5 Small, One-Off Tasks

Writing a script, analysing a CSV, drafting an email, answering a question:

- No setup needed. Your personal `~/.claude/CLAUDE.md` still applies.
- Do it in a fresh session, or `/clear` before, so it does not inherit unrelated history.
- If you will do the same kind of task again, ask Claude to remember the useful bits ("remember that our sales exports use semicolons as separators").

### 3.6 Non-Code Work

Claude Code is also used for documents, research and data. The same rules apply:

- Put the conventions in memory: house style, report format, who the audience is.
- Keep source material in files and point to them, rather than pasting large texts into the chat.
- Use a separate session per document or piece of research.

---

## Part 4: Writing Good Memory

Everything in CLAUDE.md files and the auto memory index is loaded into **every** session, and is part of every turn. It should be short, accurate and useful.

### 4.1 What to Store

| Store | Do not store |
|---|---|
| Commands that cannot be guessed: build, test, run, deploy | File and folder lists (Claude can look) |
| Rules that are easy to break | Code patterns already visible in the code |
| Decisions and their reasons | Git history, who changed what |
| Where key things are, when it is not obvious | Long copied documentation (link to it) |
| Corrections you have had to give more than once | Temporary details of today's task |
| Facts confirmed from source that were hard to find | Secrets, credentials, customer data |
| Current status and next steps of longer work | Debugging steps once the fix is in the code |

**Test for each line:** "Would a capable new teammate get this wrong without being told?" If not, leave it out.

### 4.2 How to Write It

**Short, direct rules work best.**

| Weak | Strong |
|---|---|
| "We generally prefer to use pnpm in this project because of workspace support." | "Use pnpm, never npm." |
| "Be careful with dates." | "Store dates in UTC. Convert to local time only in the UI." |
| "Tests are important." | "After any change, run the related test: `pnpm test <file>`." |
| "Don't break the API." | "Never rename fields in `api/schema.ts`; mobile apps depend on them." |

**Give the reason when the rule looks odd.** Claude follows a rule better, and applies it sensibly to new cases, when it knows why:

```markdown
- Never call the payments API from tests, even in staging. Staging charges a real test card and is rate limited.
```

**Group related rules under headings** (Commands, Conventions, Rules, Architecture) so they are easy to find and update.

### 4.3 A Simple Auto Memory Layout

For longer projects, a small set of topic files works well, each with one purpose:

| File | Holds |
|---|---|
| `MEMORY.md` | The index: one line per memory file, nothing else |
| `progress.md` | What was done, what is in progress, what comes next |
| `feedback_*.md` | How you want Claude to work ("ask before committing", "no emojis in docs") |
| `project_*.md` | Facts about the project that are not in the code: decisions, constraints, deadlines |
| `reference_*.md` | Where to find things outside the repo: dashboards, tickets, documents |

You do not need to create these by hand. Ask: "save this as a feedback memory" or "update progress with what we did today".

### 4.4 The Progress Note

For any work that spans several sessions, the most valuable memory is a short progress note that answers three questions:

1. What was just finished?
2. What is in progress, and in what state?
3. What comes next, in order?

At the end of a session: *"Update the progress memory with what we did and what is next."*
At the start of the next: *"Check progress and continue."*

A good progress note means the next session starts working within seconds instead of spending its first several turns re-discovering where things stand.

### 4.5 Keeping Memory Healthy

- **Update when facts change, not later.** Out-of-date memory is worse than none: Claude follows it confidently.
- **Delete what is no longer true.** "Remove the memory about the old login flow."
- **Review every few weeks.** Open `/memory`, skim, prune.
- **Watch the size.** If CLAUDE.md is growing past a page or two, move detail into separate docs and link them.
- **Treat it as text anyone could read.** No secrets, no personal data about customers.

---

## Part 5: Managing Context During a Session

### 5.1 One Task per Session

The single most effective habit. When you move to an unrelated task, start fresh with **`/clear`**. Memory files still load, so nothing important is lost, and the old task's files and logs stop costing tokens.

| Same session | New session (`/clear`) |
|---|---|
| A follow-up fix to the feature you just built | A different feature |
| "Now add a test for that" | "Unrelated: why is the CI failing?" |
| Refining a document you are writing | Starting a different document |

### 5.2 Compacting

- **`/compact`** replaces the conversation so far with a summary, to free space while keeping the thread.
- You can steer what the summary keeps: `/compact keep the decisions about the database schema and the list of failing tests`.
- A `# Compact instructions` section in CLAUDE.md sets what should always survive compaction for that project.
- **Auto-compact** runs by itself near the limit. It works, but it can fire at an awkward moment and always loses some detail. `/autocompact` lets you change when it triggers.

**Good times to compact:** after a long investigation, once you know the answer and are about to implement. **Bad time:** in the middle of a tricky debugging step where details matter.

### 5.3 Going Back Instead of Piling On

- **`/rewind`** returns to an earlier point in the conversation (and the code checkpoints) when an approach did not work. This is better than adding corrections on top of a wrong path, which leaves the wrong path in the context.
- **`/resume`** (or starting with `claude --continue`) brings back an earlier session when you do want its history.

### 5.4 Plan Before Changing

**Plan mode** (Shift+Tab, or `/plan`) lets Claude investigate and propose a plan without editing anything. For anything bigger than a small fix, agreeing a plan first avoids long back-and-forth after a wrong start, which is one of the biggest sources of wasted tokens.

### 5.5 Subagents Keep the Main Session Small

A subagent is a separate Claude instance with its own context. It does the heavy reading and sends back only a summary.

**Use one when the task means:**
- Searching or reading across many files ("where is X handled?").
- Reading long logs or large outputs.
- Independent research or review.
- Several independent tasks that can run in parallel.

**Example:**

> "Use a subagent to read all the files under `src/billing/` and report back how invoices are generated, in under 200 words. Don't paste code, just file names and a short explanation."

The main session receives 200 words instead of thousands of lines.

**Brief subagents fully.** They do not see your conversation. Include what the project is, the exact task, file paths, what is already known, and the format and length of the answer you want.

### 5.6 Ask for Less

Most context waste comes from reading more than needed.

| Wasteful | Efficient |
|---|---|
| "Find the login code" | "Look at `src/auth/login.ts`, the `refresh` function" |
| Pasting a 3,000-line log | "The error is in `logs/app.log` around 14:05; show only the error lines" |
| "Read the whole spec" | "Read section 4 of `docs/spec.md`" |
| "Run the full test suite and show me the output" | "Run the tests and show only the failures" |
| Pasting a whole document to ask about one paragraph | Pasting just that paragraph |

---

## Part 6: Models, Effort and Cost

### 6.1 Match the Model to the Task

**`/model`** switches models during a session.

| Task | Good fit |
|---|---|
| Quick questions, simple edits, renaming, formatting | A smaller, faster model |
| Everyday coding and writing | A mid-size model |
| Hard debugging, architecture, careful reviews | The strongest model |

### 6.2 Effort and Speed

- **`/effort`** sets how much reasoning Claude does, from `low` to `max`. Lower is faster and cheaper for routine work; raise it for tricky problems.
- **`/fast`** turns fast mode on or off for quicker output on supported models.

### 6.3 Caching

Claude Code caches the unchanged start of the conversation, so repeated turns are cheaper. The cache resets when the conversation is compacted or the instructions change, which is another reason to compact at natural breaks rather than constantly. `/usage` shows how much is coming from the cache.

### 6.4 Tools, MCP Servers and Skills

- **MCP servers** (connections to Jira, Slack, databases, browsers) add their tool names and instructions to every session. Full tool details load only when used, but unused servers still add some overhead. Turn off the ones a project does not need with `/mcp`.
- **Skills** load only when used, so installing them costs little.
- **Large outputs from tools** (a database query returning thousands of rows, a browser page dump) are the same as large files: ask for filtered results.

---

## Part 7: Worked Examples

### Example A: A Multi-Day Feature

**Day 1**
1. `/plan`: "Plan adding CSV export to the reports page. Read only what you need."
2. Agree the plan, then implement.
3. End: "Update the progress memory: what is done, what is left."

**Day 2**
1. New session: "Check progress and continue the CSV export."
2. Claude reads the progress note and the few files involved, and carries on.
3. Midway, an unrelated bug report arrives: finish or note the current step, `/clear`, handle the bug, then `/resume` or start fresh with "check progress and continue".

### Example B: Debugging with Large Logs

1. "Use a subagent to read `logs/server.log` from 09:00 to 10:00 and report the errors, their counts and the first stack trace of each, in under 150 words."
2. Work on the main session with that short summary.
3. Once the cause is found: `/compact keep the root cause and the files involved`, then fix.

### Example C: Correcting Claude Once, Not Every Time

Claude keeps using npm in a pnpm project. Instead of correcting it every session:

> "We use pnpm here, never npm. Add that to the project CLAUDE.md so the whole team's sessions know."

Personal preference rather than a team rule? Say "remember this for me" and it goes into your own memory instead.

### Example D: A Quick One-Off

"Convert `data.csv` to JSON grouped by country" in a fresh session. No memory work needed. If it is a recurring task, ask Claude to remember the format details for next time.

---

## Part 8: Checklists

### Setting Up a Project
- [ ] Project CLAUDE.md exists with commands, conventions and key rules
- [ ] It is short (a page or two), with longer material in linked docs
- [ ] Personal settings are in `CLAUDE.local.md` or `~/.claude/CLAUDE.md`, not the shared file
- [ ] No secrets in any memory file
- [ ] Unused MCP servers turned off for the project

### Starting a Session
- [ ] One clear task for this session
- [ ] For ongoing work: "check progress and continue"
- [ ] Point to exact files or sections, not "the whole thing"
- [ ] Bigger change? Start in plan mode

### During a Session
- [ ] `/clear` when switching to something unrelated
- [ ] Large searches, logs and reviews go to a subagent
- [ ] Ask for filtered output, not everything
- [ ] Check `/context` if the session is long or answers drift
- [ ] `/compact` with a focus note at natural breaks
- [ ] `/rewind` instead of stacking corrections on a wrong path
- [ ] Corrected Claude on a rule? Ask it to remember the rule

### Ending a Session
- [ ] Progress memory updated for multi-session work
- [ ] New facts or decisions saved to the right place
- [ ] Out-of-date memory removed

### Every Few Weeks
- [ ] Review CLAUDE.md files and auto memory, remove what is no longer true
- [ ] Check `/usage` to see where tokens are going

---

## Quick Command Reference

| Command | What it does |
|---|---|
| `/init` | Create a starting project CLAUDE.md from the codebase |
| `/memory` | Edit memory files, turn auto memory on or off |
| `/context` | Show what is using the context window |
| `/clear` | Start a fresh conversation (memory still loads) |
| `/compact [focus]` | Summarise the conversation to free space |
| `/autocompact` | Change when automatic compaction triggers |
| `/rewind` | Go back to an earlier point in the conversation |
| `/resume` | Continue an earlier session (`claude --continue` from the terminal) |
| `/plan` or Shift+Tab | Plan mode: investigate before editing |
| `/model` | Switch model |
| `/effort` | Set reasoning effort |
| `/fast` | Toggle fast mode |
| `/usage` (`/cost`) | Token use, cost and cache stats |
| `/mcp` | Manage MCP servers |
| `/add-dir` | Give the session access to another folder |
| `/statusline` | Show context use or cost permanently |
| `/help` | List all commands in your version |

---

## Lessons That Apply Everywhere

1. **Memory is for what cannot be found.** If Claude can read it from the code, do not store it. Store decisions, rules and hard-won facts.
2. **Short memory beats long memory.** Every line loads into every session. A one-page CLAUDE.md that is always right beats a ten-page one that is half out of date.
3. **Out-of-date memory is worse than none.** Update or delete the moment something changes.
4. **One task per session.** `/clear` is free and is the biggest single saving.
5. **The biggest token costs are tool outputs, not conversation.** Be precise about what to read, and send large reads to subagents.
6. **Plan first for anything non-trivial.** A wrong start costs far more than a short plan.
7. **Correct once, then make it a rule.** If you correct the same thing twice, it belongs in memory.
8. **A progress note makes the next session instant.** It costs a few lines and removes all re-orientation.
9. **Team knowledge goes in the repo; personal knowledge stays personal.** Shared CLAUDE.md for the team, local files and auto memory for you.
10. **Never put secrets in memory.** It is plain text, and the project file is shared.

---

*Created: November 2026*
