# Mileth College Contest Hall

A website for showcasing, judging, and archiving creative works submitted to the
**Mileth College Contest Hall** — the in‑game contest board from the MMO *Dark Ages*,
where players (“aislings”) submit art, writing, lore, and philosophy to be recognized
by the College and awarded nobility.

This project takes the College’s existing contest board and turns it into a proper,
living website: a place where every submission is displayed, its progress is tracked
from “just submitted” all the way to “nobility awarded,” and new works can be entered.

---

## Why it exists

The College already keeps a contest board online, but it’s a single hand‑maintained
page. This project does three things that page can’t:

1. **Archives every work** so nothing gets lost, with links to both the original and a
   preserved copy.
2. **Shows where each submission is in the judging process** at a glance.
3. **Provides a real submission and review pipeline**, so entrants, reviewers, and the
   College’s administrators (the “Chancellors”) each have a proper way to do their part.

Everything currently on the old board — all 66 archived works — is already loaded in.

---

## The journey of a submission

Every entry moves through the same four steps. The website shows exactly which step a
work is on, using a colored progress bar.

| Step | Name | What it means |
|------|------|----------------|
| 1 | **Submission** | The work has been entered into the College. |
| 2 | **Review** | A Chancellor has opened it for judging. Nobles read it and recommend a level of recognition (or none). |
| 3 | **Loures Confirmation** | The recommendation has been sent to the Library of Loures for final approval. |
| 4 | **Nobility Awarded** | The work is officially recognized and the aisling is awarded nobility. |

When a work is reviewed, it’s given a **recommendation** — a recognition level. From
lowest to highest, these are: **Village → Clave → Kingdom → Aisling**. A work can also
receive **No Award**.

---

## What you can do

Depending on who you are, the site offers different things:

- **Anyone (a visitor)** can browse the board, filter works by subject (Art, Literature,
  Lore, Philosophy, and more), and follow links to read each piece.
- **Entrants** can submit a new work through a simple form. It enters the board at
  Step 1 and waits for a Chancellor to open it for review.
- **Nobles (verified reviewers)** can sign in and leave a recommendation and comments on
  a submission — this is the judging that drives a work toward recognition.
- **Chancellors (the College’s administrators)** manage everything behind the scenes:
  accepting submissions, moving them through the steps, recording the final outcome, and
  managing who’s allowed to review.

---

## A note on trust and privacy

Reviewing is limited to verified nobles, and signing in is handled securely — your
session is protected and your login is never stored anywhere a malicious webpage could
reach it. The public can read the board freely; only the right people can judge or
administer it.

---

## Under the hood (for the curious)

You don’t need to know any of this to use the site, but in short:

- The **public website** people browse is the part that gets published online.
- A separate **engine** stores all the works, handles submissions and reviews, and gives
  the Chancellors an admin dashboard to manage it all.

If you’re a developer looking to run or deploy it, the technical setup, commands, and
deployment notes live in [`CLAUDE.md`](./CLAUDE.md).

---

*This is a fan project celebrating the creativity of the Dark Ages community. It is not
affiliated with the game’s creators.*
