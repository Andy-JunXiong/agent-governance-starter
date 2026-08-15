# Documentation archive-index planning

`agentgov plan documentation-archive` is a development-preview, read-only
planner for a logical development-log index. It inventories eligible dated
records, renders the exact candidate content for
`docs/development-log/INDEX.md`, and reports whether that candidate would be a
create, update, or no-op. It is read-only by default; an explicit interactive
apply path can maintain only that index file.

## Run the planner

Provide the repository and an explicit inclusive date:

```powershell
agentgov plan documentation-archive . --through 2026-08-14
agentgov plan documentation-archive . --through 2026-08-14 --format json
```

The planner never consults the host clock. `--through` must be a real calendar
date in strict `YYYY-MM-DD` form, so the same repository snapshot and input
produce the same eligibility decision.

## Eligibility and ordering

The planner examines direct Markdown children of `docs/development-log/` only.
An eligible filename is either `YYYY-MM-DD.md` or
`YYYY-MM-DD-lowercase-descriptor.md`, and its date must be on or before the
explicit through-date. `INDEX.md`, later-dated records, non-Markdown files, and
non-dated Markdown are not index entries.

Entries are ordered newest date first and then by repository-relative path.
That second key keeps multiple records from the same day stable. Every entry
contains the original path, the first level-one heading, and the SHA-256 of the
unchanged source bytes. A missing or repeated level-one heading produces a
deterministic warning; a missing heading uses a filename-derived title.

The human-facing candidate keeps each record compact: date, title, and stable
relative link only. Source SHA-256 values remain available in the JSON
`entries` and terminal diagnostics as machine-verifiable integrity evidence;
they do not dominate the proposed Markdown index.

“Archive” means logical inclusion in the index candidate only. Eligible logs
remain at their stable paths. The planner never moves, renames, deletes, or
rewrites a historical record.

## Output contract

Text output shows the state, eligible entries, exact target action and digests,
the complete candidate between `CONTENT-BEGIN` and `CONTENT-END`, and all
findings. JSON output implements the strict
`agentgov.documentation-archive-plan` 1.0 contract defined by
`schemas/documentation-archive-plan.schema.json`. The presentation refinement
does not change that schema: entry hashes and candidate-content digests remain
in their existing fields.

The overall states are:

- `pass`: at least one eligible record and no deterministic warning or failure;
- `warn`: a candidate exists, but a deterministic title warning needs review;
- `fail`: an invalid dated filename, unsafe path, or missing log directory
  prevents an exact candidate;
- `not_applicable`: no record is eligible through the supplied date.

Deterministic findings are labeled `pass`, `warn`, `fail`, or
`not_applicable`. Whether the proposed index is useful is explicitly
`advisory`; it is not presented as an objective pass or failure.

The command returns exit code `1` only for a deterministic `fail` plan. A
valid `pass`, `warn`, or `not_applicable` plan returns `0`. Invalid command
input or an operational read error returns `2` on stderr.

## Apply the exact candidate

After reviewing the terminal preview, rerun it with the explicit apply flag:

```powershell
agentgov plan documentation-archive . --through 2026-08-15 --apply
```

For a create or update, the command prints the complete plan, requires a real
interactive terminal, and accepts only the exact confirmation `APPLY INDEX`.
Non-interactive input or any other response cancels without writing. JSON
format cannot be combined with `--apply`. A no-op reports the unchanged index
without prompting because it performs no write.

After confirmation, AgentGov regenerates the complete plan and compares the
explicit through-date, ordered paths, titles, every source SHA-256, findings,
candidate content, action, and target before/after digests. Any difference is
a stale plan and fails before the index changes. An absent target uses
exclusive creation. An existing regular index is written to a flushed
same-directory temporary file, revalidated again, and replaced atomically;
temporary files are removed after success or failure.

This rejects stale AgentGov previews and narrows the concurrent-change window.
It cannot transactionally control an arbitrary external process that writes
during the final replacement boundary.

## Authority and stop boundary

Without `--apply`, the planner performs no repository write. The JSON plan is
still read-only evidence and its authority boundary remains entirely false.
The confirmed apply path writes only `docs/development-log/INDEX.md`; it never
opens a dated log for write and never moves, renames, deletes, or rewrites a
historical record. Confirmation grants no scheduling, Git, publication,
release, or deployment authority. It also grants no first-closeout reminder or
external action. Automatic refresh remains a separate, undecided product
requirement.
