# Narrator Hook System — Naomi Kessler

A fixed list of even 20-30 full hooks still repeats every 20-30 episodes —
across 100 videos that's noticeable, and noticeable is the thing we're
trying to avoid. So this isn't a list to pick from. It's three independent
phrase banks plus a set of skeletons for how to arrange them. Combining
them gives thousands of distinct openings, not dozens — and because the
pieces recombine differently each time, no fixed phrase is doing enough of
the work on its own for a pattern to emerge.

The episode's actual hook (the surprising fact, the image, the
contradiction — Nebuchadnezzar's madness, Cornelius's prayer, Moses's
murder) always still comes first or is interwoven. Everything below is the
self-identification beat that gets folded into that hook, not a preamble
bolted in front of it.

---

## The three slots

Not every skeleton uses all three. Real people don't recite a fixed set of
beats every time they talk — sometimes you just say your name and move on;
sometimes you explain the channel; sometimes you skip straight to the
topic. Treat "which slots appear" as its own variable, not just "which
phrase fills the slot."

### Slot A — Self-identification ("I'm Naomi")

1. I'm Naomi.
2. My name's Naomi.
3. I'm Naomi Kessler.
4. I'm Naomi —
5. This is Naomi.
6. I go by Naomi here.
7. You're watching Naomi dig through history again.
8. Naomi here.
9. It's Naomi.
10. I'm Naomi, by the way.
11. Naomi Kessler —
12. I'm Naomi, and yes, I know that name comes up in this history too.

### Slot B — Channel identity (what this channel does)

1. On this channel, we go looking for who people actually were, not just the stories about them.
2. This is where we dig past the version of history everyone already agrees on.
3. I spend my time finding the real people underneath the stories you think you already know.
4. This channel exists for exactly one thing: the people history either got wrong or skipped entirely.
5. Here, we don't do the polished version. We do the real one.
6. If you're new — this is where unpopular facts about famous names, and completely unknown names, get the same treatment.
7. I do history the way it actually happened, not the way it gets simplified.
8. This is the place for names you know and names you've never once heard, told with the same respect.
9. Every episode here is one person, taken seriously.
10. I've built this whole channel around one question: who were these people, actually?
11. This channel doesn't care whether you've heard of someone. It cares whether the record has something worth hearing.
12. I don't do the highlight reel. I do the person.

### Slot C — Topic pivot (naming the character)

1. Today: [Character].
2. Today, we're looking at [Character].
3. This time it's [Character].
4. That question, today, has a name: [Character].
5. [Character] is who we're doing today.
6. Today's name is [Character].
7. We're spending this one on [Character].
8. [Character]. That's today's subject.
9. This episode belongs to [Character].
10. Today it's [Character]'s turn.
11. Which brings us to [Character].
12. So — [Character].

---

## Skeletons (which slots, in what order)

Each skeleton names the slots it uses, in sequence. "—" means that skeleton
skips the slot entirely. Mix skeletons across episodes the same way you'd
mix phrase choices — don't let two consecutive episodes share a skeleton.

| # | Order | Notes |
|---|-------|-------|
| 1 | A → C, folded into one sentence | No channel-identity beat at all. Shortest, plainest — good for quieter/obscure figures. |
| 2 | B → A → C | Channel identity first, name second, then pivot. |
| 3 | A → B → C | Classic order, but B and C should still vary in length/wording. |
| 4 | A only, C folded into A's sentence, no B | Minimal. "I'm Naomi, and this is [Character]." |
| 5 | Question → A → C | Open on a question, then identify, then answer with the name. |
| 6 | C → A → B | Name the subject before self-identifying — inverts the usual order. |
| 7 | A → C, B dropped | Momentum-first, no pause for channel description. |
| 8 | Confession/aside → A → B(short) | "I'll be honest, this one surprised me. I'm Naomi... " |
| 9 | B(long) → pause → A(short) → C(short) | Channel identity gets the most room; self-ID and pivot are clipped. |
| 10 | Stakes statement → A → C | State what's at risk in how you think about something, then identify, then name. |
| 11 | A → aside about the channel's returning-viewer/new-viewer split → C | "If you've been here before... if you haven't..." — use sparingly, it's a strong marker, shouldn't appear often. |
| 12 | C first (bare name, no article) → A → B(short) | "[Character]. I'm Naomi — this is where..." |

## Combinatorics

12 skeletons × up to 12 phrasings per slot used ≈ thousands of distinct
surface realizations, before even accounting for the episode-specific hook
sentence that precedes all of this. That's the actual point: nobody
rewatching this channel start-to-finish should be able to predict the next
episode's opening shape from the last five.

## Rotation rules

- Never repeat the exact (skeleton, Slot A phrase, Slot B phrase, Slot C
  phrase) combination across the 100-episode run.
- Never reuse the same Slot A phrase two episodes in a row.
- Skeletons 11 and 12 (the strongest/most stylized) should each show up
  only a handful of times across the full run — they're seasoning, not
  structure.
- Match skeleton weight to the episode's content mode: shorter/plainer
  skeletons (1, 4, 7) suit obscure figures where the hook needs room;
  fuller skeletons (2, 3, 9) suit well-known figures where establishing
  "this is the unpopular version" needs a beat.
- **Only use real Chatterbox Turbo tokens — verify against the model, don't
  guess.** `[breath]` is not a trained token (confirmed against
  `added_tokens.json` on the model's Hugging Face repo) and got read aloud
  as literal text during the voice audition. The real, complete set of 19
  trained tokens is: `[advertisement]`, `[angry]`, `[chuckle]`,
  `[clear throat]`, `[cough]`, `[crying]`, `[dramatic]`, `[fear]`, `[gasp]`,
  `[groan]`, `[happy]`, `[laugh]`, `[narration]`, `[sarcastic]`, `[shush]`,
  `[sigh]`, `[sniff]`, `[surprised]`, `[whispering]`. Of these, only
  `[sigh]` has actually been confirmed working by ear so far (Nebuchadnezzar
  episode). The others — especially `[narration]`, `[dramatic]`, and
  `[whispering]`, which read as directly relevant to this channel's
  register — are real per the model source but not yet audition-tested by
  us; don't treat them as confirmed until they've actually been heard.
  For anything not on this list, get pacing and breath room from
  punctuation, sentence length, and line breaks instead. Overall
  tone/register still goes through `deliveryDirection` (a separate field
  passed to the TTS capability, not inline script text) — see
  `NarrationGenerationInput` in `src/voice/narration-generator.ts`.

## Applied so far

- **Episode 01 — Nebuchadnezzar** (`01-nebuchadnezzar.md`): skeleton #2 (B→A→C), channel-identity first.

All three openings read as distinct without ever touching the same
skeleton twice — that's the standard the other 97 need to hold to.
