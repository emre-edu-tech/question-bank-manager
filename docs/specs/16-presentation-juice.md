# Step 16 — Presentation Juice: Sounds, Confetti & Level-Up Moment

**Context:** builds on `15-topic-mastery-profile.md`. Almost entirely frontend work in `app/static/js/quiz.js` (plus one new JS file and small template changes), with a **small API addition** to `/answer` for level-up detection. Keep the project's "no dependencies" ethos: **no CDN scripts, no audio files** — the fair environment may be offline.

**Goal:** make the existing per-question flow *feel* like a game — sound feedback, confetti on wins, a dramatic full-screen level-up celebration, and a visible countdown tied to the speed bonus (step 11).

## Tasks

1. **New file `app/static/js/juice.js`** — a small self-contained module (IIFE, vanilla JS), loaded by the quiz page template *before* `quiz.js`. It exposes three things on a namespace object (e.g. `window.QBJuice`): `play(name)`, `burst()`, `celebrate()`.

2. **Sound manager (WebAudio, no files)**

   - Lazily create an `AudioContext` on first user interaction (browser autoplay policy — the first choice click qualifies).
   - Synthesized cues, all very short:
     - `correct` — quick ascending two-note blip
     - `wrong` — low short buzz
     - `levelup` — short ascending arpeggio
     - `gameover` — short descending two-note
   - **Mute toggle:** a small 🔊/🔇 button in the quiz header (add to the quiz page template). State persisted in `localStorage` key `"qb-sound-muted"` (`"1"`/`"0"`); default is sound ON. Button toggles and re-renders its icon.

3. **Confetti (vanilla canvas, no library)**

   - A full-screen `<canvas>` appended by JS: `position:fixed inset-0 pointer-events-none z-50`.
   - `burst()` spawns ~60 small colored rectangles/atoms from the top-center area falling with gravity for ~1.5 s, then removes itself. Keep it under ~60 lines.
   - Respect `prefers-reduced-motion`: skip the animation entirely when matched.

4. **Level-up detection — small backend change** (extend `POST /quizzes/<slug>/answer` in `app/public/routes.py`)

   - ⚠️ `student.total_xp` is credited only at `/finish` (idempotency guard), so mid-quiz leveling must use **effective XP**:

     ```python
     effective_xp_before = student.total_xp + attempt.xp_earned - xp_awarded
     effective_xp_after  = student.total_xp + attempt.xp_earned
     old_level = calculate_level(effective_xp_before)
     new_level = calculate_level(effective_xp_after)
     ```

   - Add to the response:

     ```python
     "level_number": new_level[0],
     "level_name": new_level[1],
     "level_up": new_level[0] > old_level[0],
     ```

5. **Level-up moment** (extend `quiz.js`)

   - On `data.level_up === true`: show a full-screen overlay (fixed, semi-transparent dark background, centered card): `"🎉 Seviye N: <level_name>!"` with a short congratulation line. Big burst of confetti + `levelup` sound.
   - Auto-dismiss after ~2.5 s, or immediately on click. While visible, the quiz stays usable (overlay is click-through-safe: clicking it dismisses it).
   - All overlay Tailwind classes must appear as literals in `quiz.js`'s comment block for the Tailwind scanner.
   - ⚠️ Per `AGENTS.md`: run `npm run build:css` and include the rebuilt `app/static/dist/output.css`.

6. **Wire sounds & confetti into the existing flow** (extend `quiz.js`)

   - Correct answer → `play('correct')` + small `burst()`.
   - Wrong answer → `play('wrong')`.
   - Game over → `play('gameover')` (skip the correct/wrong cue in that same tick if both would fire).
   - Level-up → handled by its own moment above (don't stack a second confetti).
   - All sound/burst calls must be no-ops if `window.QBJuice` failed to load — wrap calls in a helper that checks existence, so a missing `juice.js` never breaks answering.

7. **Countdown bar (visual only, feeds the existing speed bonus)**

   - Speed bonus boundaries are ≤10 s (full +5) and ≤20 s (+2). Add a thin bar (`h-1.5 rounded bg-blue-500`) at the top of each question card, hidden by default.
   - Because all questions render on one page, bars run **sequentially**: the first question's bar starts on page load; each subsequent card's bar starts when the previous question is answered. Implementation: JS sets an initial width of 100% then transitions to 0% with `transition: width Xs linear` where X = 20 s, started via a reflow + class toggle.
   - Purely cosmetic: the actual timing sent to `/answer` remains the existing `Date.now()` measurement — do not derive timing from the bar.
   - When the bar visually empties, the student knows the full-bonus window is gone; no penalty is displayed (there is none below 20 s).
   - Skip the animation under `prefers-reduced-motion`.

8. **Update `docs/specs/00-overview.md`**: note step 16 in the build order; the only API change is the three added fields on `/answer`.

## Acceptance criteria

- Correct answers play a sound and burst confetti; wrong answers play the buzz; muted state survives a page reload.
- No external requests: page works fully offline (check DevTools Network — no CDN, no audio file fetches).
- Crossing a level threshold mid-quiz (e.g. a student at 45 XP answering +10/+5) triggers exactly one full-screen level-up celebration with sound and confetti; the celebration never blocks or breaks the following question.
- `level_up` is `false` on ordinary answers, and repeated `/answer` calls never double-celebrate the same level.
- The countdown bar animates per question in sequence and does not affect reported `time_taken_seconds` or awarded XP.
- Answering still works with `juice.js` removed from the page (no JS errors from missing helpers).
- `npm run build:css` was run; the committed `output.css` includes the new classes.
