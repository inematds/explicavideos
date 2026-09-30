# Explicavideos

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

Reproducible process for explainer videos with Nei’s avatar and voice, illustrations, chapters, and captions. Derived from the completed Astra Básico and OSWork Quick productions.

[User Guide](https://inematds.github.io/explicavideos/guia/en/) · [OSWork Source](https://inematds.github.io/oswork/)

## Actual Workflow

Source → scenes with coverage → blocks of up to 4.400 characters → HeyGen Studio via the subscription → download → Groq transcription with word-level timestamps → HyperFrames composition → validation → rendering → concatenation → GitHub Release and player → bot v3.

The OSWork adapter covers all 48 topics, every explanatory field, eight labs, and reviews in 122 scenes. First production: Portuguese. The engine supports PT/ES/EN; other languages require reviewed scene files and are not translated automatically.

## Operation

Requires Python 3 with requests and beautifulsoup4, Node, FFmpeg, authenticated gh, user systemd, Xvfb, and the authenticated HeyGen profile. The browser adapter uses the Playwright installed in inemaccbot. This version is executable in the INEMA environment; adjust paths for another machine. This is not a public service.

```bash
python3 explica.py --config examples/oswork.json prepare
python3 explica.py --config examples/oswork.json preview
python3 engine/check_layouts.py
python3 explica.py --config examples/oswork.json start
python3 explica.py --config examples/oswork.json status
journalctl --user -u explica-oswork-completo-submit -n 20 --no-pager
```

`prepare` does not overwrite productions that have already started. `start` launches five persistent services; it does not stop services that are already active. Do not restart a `needs_review` submission: first check whether an ID exists in HeyGen. The production in progress is already prepared; use `status`, not `prepare`.

## Format v2: explainer animation (2.0.0)

> 2.2.3: Local Whisper — skipped segments (gaps > 3 s between words) are retranscribed automatically, with up to 3 attempts; the alignment check (v1 and v2) counts a spoken number in digits ("83%") as a match against the spelled-out script. LOOP-R PT: 10 failed blocks scoring between 0,79 and 0,88 passed with scores of 0,97–0,99.
>
> 2.2.2: services (`start`) run inside `explica.slice` (`~/.config/systemd/user/explica.slice`: MemoryMax=40G, no swap). If the render batch runs out of memory, the kernel kills a render, not the session terminals (incident on 2026-09-27 04:01).
>
> 2.2.1: `"transcriber": "whisper-local"` in the config switches Groq for local Whisper large-v3 (one process at a time, lock in /tmp; `whisper_prompt` for proper names), and `"balanced_blocks": true` balances the blocks so the last block is not too short (< 60 s). Without these keys, behavior remains unchanged. First use: LOOP-R (`examples/loop-r-*.json`).
>
> 2.1.1: v2 in PT/EN/ES (fixed labels and `lang` per language; `setup_output` accepts v1 in any language) and the authorship rule "no empty frame for more than 3 s".
>
> 2.0.1: the previous shot stays on screen until the next one shows content (labels do not count), and the scene’s large title waits for the first content — measured empty-stage time fell from 26% to 17% in OSWork v6.2 M1; what remains are frames with little content, to be addressed in the visual script.

In v2, the visuals explain what is being said at the moment it is spoken. Each scene gets a visual script (`<output>/visual-v2/pt-bNN.json`), with shots using 21 animated primitives in `engine/v2/runtime/v2.js`. All timings are **spoken cues**, resolved using the actual transcript. Captions use the script’s spelling, and the avatar and audio from the v1 production are reused, with no new generation in HeyGen. Rules and catalog: [engine/v2/AUTHORING.md](engine/v2/AUTHORING.md). Approved example: `visual-v2/pt-b01.json` from OSWork.

```bash
export EXPLICAVIDEOS_CONFIG=examples/oswork-v2.json
python3 engine/v2/setup_output.py            # new output directory; v1 is untouched
python3 engine/v2/build_block.py 1 --strict   # cues → timings, 0 warnings, gaps > 10 s flagged
engine/v2/run_lane.sh 1 2 3                   # HyperFrames check + render verified at 25 fps per block
python3 engine/assemble_languages.py && python3 engine/publish_finished.py
```

The v1 engine (`explica.py`, `engine/*.py`) remains unchanged and available. The previous version of the OSWork video is in release `video-v1.0.0`.

## Configuration for Other Videos

Copy examples/oswork.json and change id, title, source_repo, output, github_repo, and release_tag. For content that is not OSWork, provide `scene_files` with paths by language, for example `{"pt":"/caminho/lesson-pt.json"}`. Each scene contains title, chapter, speech, labels, source, kind, and takeaway; svg is optional. The script must be reviewed before `start`.

Media and state are stored in `~/projetos/output/<id>/`. The repository contains the engine, configurations, documentation, and visual assets; it does not contain credentials or MP4s.

## Quality and Recovery

- Source frozen as JSON, coverage by topic, and SHA-256 for each block.
- Never automatically repeat a submission with an ambiguous result.
- Avatar: TEMPLATE-AVATAR16 template, Nei, INEMATIME voice, Avatar III.
- Actual transcription; word match above 90% for rendering/publication.
- Composition 1920×1080, 25 fps; captions without overlap.
- HyperFrames check, actual duration, audio presence, and FFmpeg decoding.
- MP4 and SRT in Release; player with chapters and VTT in the course itself.
- Final notice in bot v3 only after publication and portal receipt.

`verification/production.json` records failures by block. Fix the cause and remove only that block’s state to resume it, preserving its HeyGen ID. Services have a 12-hour window; monitor with status and journalctl. There is no blind retry of generation.

## Costs

Avatar generation uses the HeyGen subscription session in the browser. The HeyGen API is used only for queries; Groq charges for transcription according to the account. HyperFrames renders locally. The engine does not call an LLM to coordinate each step. A subscription does not mean unlimited usage; this project records duration and IDs, but does not calculate provider bills.

## HeyGen: how the engine generates, checks and downloads (options)

**Current model — the default, in production. Unchanged.** Generation runs through a Playwright script in the HeyGen **studio** (`engine/heygen-studio.mjs`: clone `TEMPLATE-AVATAR16`, set title and speech, "Generate" → modal → "Submit"), billed to the subscription through the logged-in browser profile on display `:99`. Checking the queue (`submit.py`), following progress (`monitor.py`, every 60 s) and downloading the MP4 use **read-only** calls to `GET /v3/videos/<id>` on the HeyGen **API**.

**Option under study — studio end to end (NOT implemented yet).** The same `| estudio` route used by [promoavatar3](https://github.com/inematds/promoavatar3), carried all the way: check status and download through the studio too, matching the exact title, with no API key. Gains: no API at all; it sees the real state (Draft, queued, processing, done, failed). Costs: depends on the profile session and on HeyGen's layout; each check opens a browser (seconds, every 5–10 min); submit and checks share display `:99`, one at a time.

**Why — the 2026-09-29 case.** Three OSWork v6.2 blocks sat as `pending` in the API for 4 days. In the studio all three were **Draft**: the modal's final click did not register, the script saved the ID anyway, and the API reports a draft as `pending`. Nothing was generated or billed.

**Minimal guard for both models (pending):** after "Submit", confirm in Projects that the title left **Draft**; otherwise mark `needs_review`. Unblocking a draft means generating video: only with explicit authorization. Never resubmit without looking at the studio first.

## References and Licenses

Pipeline adapted from astrabasico and oswork-quick. Local layout fonts: Montserrat and DejaVu; animation: GSAP. Educational content and diagrams belong to the source course. Preserve asset licenses when redistributing.

## Verification

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q engine
```


## OSWork Delivery

[Watch the complete video](https://inematds.github.io/oswork/videos/). Publication receipt in docs/video-publication.json.
