---
name: geo-client-workflow
description: 'Gate skill execution, log tokens per-project.'
version: 1.0.0
---

# GEO/SEO Client Workflow

## When to Use
Every time a user requests work on a client project (audit, redesign, content, reporting). This skill ensures consistent execution method confirmation, token logging, and project file updates.

## Execution Gate: Ask Before Running a Skill
**Rule:** When a user requests a task that has a defined skill (e.g., technical-health, metadata-onpage-seo, web-performance-audit), do NOT assume execution method. Load the skill via skill_view(), summarize it to the user, and ask:

> "I found the [skill-name] skill for this task. Should I run it myself with direct tools, or delegate to a subagent using the skill?"

Wait for explicit direction before proceeding. Reason: the user may want to delegate for speed (parallel work) or review the skill first. Silent execution wastes time and violates the user's workflow preference.

## Token Logging: Before/After Cost Comparison
**Rule:** For every client project, create a `docs/cost-log.md` file showing BEFORE (baseline) and AFTER (actual) costs with DIFFERENCE calculated.

**Procedure:**
1. **Before work starts:** Create cost log with baseline (all zeros):
   ```markdown
   ## 📊 COST SUMMARY
   | Metric | Before | After | Difference |
   |--------|--------|-------|------------|
   | **Session Duration** | 0m | TBD | TBD |
   | **Total Tokens** | 0 | TBD | TBD |
   | **Est. Cost** | $0.00 | **TBD** | **TBD** |
   ```

2. **After work completes:** Update with actual metrics from `hermes insights`:
   ```markdown
   | Metric | Before | After | Difference |
   |--------|--------|-------|------------|
   | **Session Duration** | 0m | 6h 23m | +6h 23m |
   | **Total Tokens** | 0 | 587,497 | +587,497 |
   | **Input Tokens** | 0 | 412,345 | +412,345 |
   | **Output Tokens** | 0 | 175,152 | +175,152 |
   | **Tool Calls** | 0 | 126 | +126 |
   | **Messages** | 0 | 315 | +315 |
   | **Est. Cost** | $0.00 | **$0.52** | **+$0.52** |
   ```

3. **Cost calculation by model:**
   - Extract actual model used from `hermes insights`
   - Use provider-specific pricing (Nous Portal rates for Kimi: $0.60/M input, $2.50/M output)
   - Calculate: `(input_tokens / 1M × input_price) + (output_tokens / 1M × output_price)`
   - Show breakdown: Input $X.XX + Output $Y.YY = Total $Z.ZZ

4. **Cost by agent/task:** When using multi-agent delegation, estimate per-agent costs based on duration and typical token rates:
   ```markdown
   | Agent | Duration | Tokens | Est. Cost | % of Total |
   |-------|----------|--------|-----------|------------|
   | Technical Health | 303s | 98,456 | $0.11 | 27% |
   | Metadata/SEO | 237s | 67,234 | $0.08 | 19% |
   ```

**Why Before/After:** Shows client exactly what was spent on their project, enables ROI calculation, and builds cost awareness for future engagements.

**Cost Estimation Rule:** Never guess token-to-dollar conversion. Use `hermes insights --days 1` to get actual session data. When Hermes data is incomplete, use the actual model pricing from the provider (Nous Portal shows Kimi rates: K2-Thinking $0.60/M input, $2.50/M output). Mark rough estimates as '~' when authoritative data is unavailable.

## Project File Updates
**Rule:** After work on a client project completes, update the client's project log file (stored in `hermes-projects/`) with:
1. Summary of what was done
2. Status/current blockers
3. Next steps
4. Token usage (see Logging rule above)

**Project Folder Structure:** Organize all client projects consistently:
```
hermes-projects/CLIENT-NAME/
├── README.md           # Project hub: overview, status, quick links
├── audits/             # Raw audit data, checklists, findings
├── reports/            # Client-facing PDF/HTML reports
├── assets/             # Screenshots, diagrams, exports
└── docs/
    └── project-log.md  # Full project history and decisions
```

Move existing root-level `.md` files into `docs/project-log.md` and create README.md as the project hub. This structure scales across dozens of clients and makes handoffs predictable.

Reason: Maintains a durable record of client work history, decision points, and progress across sessions. Standardized structure enables quick navigation and prevents file sprawl.

## Multi-Agent Audit Orchestration
**Rule:** For comprehensive audits requiring multiple specialized agents (Technical Health, Metadata/SEO, GEO AI, Backlinks, Analytics), use delegate_task to run agents in parallel:

```python
delegate_task(tasks=[
    {"goal": "Run Technical Health audit", "context": "..."},
    {"goal": "Run Metadata/On-Page SEO audit", "context": "..."},
    {"goal": "Run GEO AI Visibility audit", "context": "..."},
    {"goal": "Run Backlink Authority audit", "context": "..."},
    {"goal": "Run Analytics Tracking audit", "context": "..."}
])
```

**Consolidation Pattern:** After all agents complete:
1. Collect findings from each agent's output
2. Create master scorecard showing scores per agent
3. Merge action plans into single prioritized list
4. Generate one comprehensive report (not 5 separate reports)
5. Update project log with cross-agent findings

**Reference:** See `technical-audit-reporting` skill for consolidated report format with executive scorecard.

Reason: Parallel execution reduces total audit time from ~60 min to ~15 min. Consolidated output prevents client confusion from multiple separate reports.
