# External facts check

External facts the build plan depends on, checked against official docs, licence files and package metadata on 2026-10-03. Status values: confirmed / differs (from the plan's assumption) / unverified (no official source found).

## 1. anthropics/claude-code-action@v1 inputs and triggers
- **Claim checked:** Inputs `claude_code_oauth_token`, `prompt` (can it be a slash command or skill such as `/annotate-batch`?), and `claude_args` with `--allowedTools`, `--max-turns`, `--model`. Does it run on schedule or workflow_dispatch without a PR or issue?
- **Finding:** All three inputs exist. `claude_code_oauth_token` is a subscription token from `claude setup-token` and works on Pro, Max, Team and Enterprise plans. `prompt` takes "plain text or a skill invocation". For a skill in the repo's `.claude/skills/`, run `actions/checkout` first, then pass `/skill-name` as the prompt. `claude_args` "accepts any Claude Code CLI argument", including `--max-turns`, `--model` and `--allowedTools`. When `prompt` is set, the action runs in **automation mode**: "on any GitHub event, including a cron schedule". The action README also lists `workflow_dispatch`. Caveats:
  - With a plain-text prompt, Claude has no shell or GitHub API access until tools are granted through `--allowedTools` or `settings` `permissions.allow`. A skill instead gets the tools in its `allowed-tools` frontmatter.
  - Bot actors are rejected unless they are listed in `allowed_bots`. This also covers scheduled runs whose cron was last edited by a bot.
  - Scheduled workflows run only from the default branch. In public repos, GitHub disables them after 60 days of inactivity.
  - When `github_token` is omitted, the action authenticates as the Claude GitHub App, not as `GITHUB_TOKEN`.
- **Source:** https://code.claude.com/docs/en/github-actions ; https://github.com/anthropics/claude-code-action/blob/main/docs/usage.md ; https://github.com/anthropics/claude-code-action/blob/main/docs/solutions.md
- **Checked:** 2026-10-03
- **Status:** confirmed

## 2. Claude Code subagents, permissions and hooks
- **Claim checked:** Can the `tools:` frontmatter scope paths, such as `Write(videos/**)`? Do subagents work in headless `-p` runs? Do settings.json path rules apply per subagent or to the whole session? Do PreToolUse hooks run for subagent tool calls?
- **Finding:**
  - `tools` takes **tool names only** ("comma-separated string such as `Read, Grep, Bash` or a YAML list"). A specifier still acts on the whole tool: "A `disallowedTools` entry with a specifier, such as `Bash(git push *)`, still removes the whole tool from the subagent". For finer control the docs point to `permissions.deny` in settings.
  - Path rules use gitignore syntax with anchors `//abs`, `~/`, `/` (relative to the settings source) and `./`. Only **`Read(...)` and `Edit(...)`** path rules are checked. A path rule on `Write(...)` "is accepted but never consulted" and triggers a startup warning, so use `Edit(videos/**)` instead.
  - Settings rules apply to the whole session. Subagent frontmatter can set `permissionMode` (inherited from the main session when unset) and `hooks`, but it has no per-subagent allow or deny path list.
  - Hooks: "a `PreToolUse` hook in `settings.json` also runs before every tool a subagent uses". Hooks in a subagent's frontmatter run only while that subagent is active. The permissions page says frontmatter hooks in a *project* subagent are "Not used" until the folder is trusted. This matters on CI, where trust may need to be set in `~/.claude.json`.
  - Headless: subagents work with `-p` and in the Agent SDK. The docs cover `--append-subagent-system-prompt` and `CLAUDE_AGENT_SDK_DISABLE_BUILTIN_AGENTS=1` for those modes. Fork mode is off by default with `-p`.
- **Source:** https://code.claude.com/docs/en/sub-agents ; https://code.claude.com/docs/en/permissions
- **Checked:** 2026-10-03
- **Status:** differs (no path scoping in `tools`; `Write(path)` rules are ignored)

## 3. Claude image input
- **Claim checked:** Recommended maximum dimensions or megapixels, auto-resize behaviour, and maximum images per request.
- **Finding:**
  - Limits by resolution tier:

    | Tier | Models | Max long edge | Max visual tokens |
    |---|---|---|---|
    | High-resolution | Claude 4.7 and later | 2576 px | 4784 |
    | Standard | All other models | 1568 px | 1568 |

  - Images above either limit are **downscaled automatically**, keeping the aspect ratio. Setting `"oversized_image": "error"` rejects them instead. Cost is ⌈w/28⌉×⌈h/28⌉ tokens. A 1920×1080 image is not resized on the high-res tier and costs 2691 tokens.
  - Hard limits: 8000×8000 px per image, and 10 MB base64 per image on the direct API.
  - Images per request: **600** on the API (**100** for models with a 200k context window), and 20 per message on claude.ai.
  - Requests with **more than 20 images** use a stricter per-image dimension limit. To stay safe, keep each side at **2000 px or less**.
  - The request size limit is 32 MB. For many images the docs recommend the Files API.
- **Source:** https://platform.claude.com/docs/en/build-with-claude/vision
- **Checked:** 2026-10-03
- **Status:** confirmed

## 4. GitHub Actions minutes, storage and runner specs (private repos)
- **Claim checked:** Included minutes and storage on Free and Pro plans, and the standard Linux runner specs for private repos.
- **Finding:**
  - Free: **2,000 min/month and 500 MB artifact storage**.
  - Pro: **3,000 min/month and 1 GB**.
  - Cache is **10 GB per repo** on every plan and is separate from artifact storage.
  - Linux 2-core overage costs $0.006/min.
  - `ubuntu-latest` in private repos has **2 vCPU, 8 GB RAM, 14 GB SSD**. Public repos get 4 vCPU and 16 GB.
- **Source:** https://docs.github.com/en/billing/concepts/product-billing/github-actions ; https://docs.github.com/en/actions/reference/runners/github-hosted-runners
- **Checked:** 2026-10-03
- **Status:** confirmed

## 5. GITHUB_TOKEN-created events
- **Claim checked:** Expected: events created with the default `GITHUB_TOKEN` do not trigger new workflow runs, except `workflow_dispatch` and `repository_dispatch`.
- **Finding:** "events triggered by the `GITHUB_TOKEN` will not create a new workflow run", with these exceptions:
  1. `workflow_dispatch` and `repository_dispatch` always create runs.
  2. **New:** `pull_request` `opened`, `synchronize` or `reopened` events from a PR created or updated with GITHUB_TOKEN create runs "in an **approval-required** state", which a person must approve.
  
  Other events (push, merge to main, closed) still create no runs. The Claude docs add that the action authenticates as the **Claude GitHub App** by default, and that the app's commits and PRs do trigger CI, unlike GITHUB_TOKEN.
- **Source:** https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow ; https://code.claude.com/docs/en/github-actions#ci-not-running-on-claudes-commits
- **Checked:** 2026-10-03
- **Status:** differs (adds an approval-required PR exception)

## 6. GitHub Packages / GHCR storage
- **Claim checked:** Storage limits for private packages on Free and Pro.
- **Finding:**
  - GitHub Packages: Free includes **500 MB storage and 1 GB transfer per month**. Pro includes **2 GB and 10 GB**.
  - Container registry: "Container image storage and bandwidth for the Container registry is **currently free**". GitHub will give at least one month's notice before this changes.
- **Source:** https://docs.github.com/en/billing/concepts/product-billing/github-packages
- **Checked:** 2026-10-03
- **Status:** confirmed

## 7. Cloudflare R2 free tier
- **Claim checked:** Free storage, Class A and Class B operations per month, and egress.
- **Finding:** **10 GB-month storage, 1 million Class A and 10 million Class B requests per month, and free egress.** The free tier applies to Standard storage only, not Infrequent Access.
- **Source:** https://developers.cloudflare.com/r2/pricing/
- **Checked:** 2026-10-03
- **Status:** confirmed

## 8. Licences: audio and vision dependencies
- **Claim checked:** Code and weight licences for laion_clap, msclap, faster-whisper, Whisper, demucs, RapidOCR and PySceneDetect.
- **Finding:**

  | Component | Code licence | Weights licence |
  |---|---|---|
  | laion_clap (LAION-AI/CLAP; PyPI laion-clap 1.1.7) | **CC0-1.0** (the PyPI classifier says Apache) | Checkpoints in HF `lukewys/laion_clap` are **CC0-1.0**; the HF Transformers ports (`laion/clap-htsat-unfused`, `laion/larger_clap_general`) are **Apache-2.0** |
  | microsoft msclap (CLAP; PyPI msclap 1.3.4) | **MIT** | HF `microsoft/msclap` is tagged **MS-PL** |
  | faster-whisper (PyPI 1.2.1) | **MIT** | n/a |
  | OpenAI Whisper | MIT | MIT: "Whisper's code and model weights are released under the MIT License" |
  | demucs (PyPI 4.1.0) | **MIT**; `adefossez/demucs` is "the officially maintained Demucs" | No separate licence for htdemucs weights was found; the README states only MIT |
  | rapidocr-onnxruntime | **Apache-2.0**; latest is 1.4.4, superseded by package `rapidocr` 3.9.2 (Apache-2.0) | — |
  | PySceneDetect (PyPI scenedetect 0.7.1) | **BSD-3-Clause** | n/a |

- **Source:** raw LICENSE/README files at github.com/{LAION-AI/CLAP, microsoft/CLAP, SYSTRAN/faster-whisper, openai/whisper, adefossez/demucs, RapidAI/RapidOCR, Breakthrough/PySceneDetect}; pypi.org JSON API; huggingface.co/api/models/{lukewys/laion_clap, microsoft/msclap, laion/clap-htsat-unfused}
- **Checked:** 2026-10-03
- **Status:** confirmed. The htdemucs weights licence is unverified beyond the repo-level MIT; the msclap weights (MS-PL) differ from the code (MIT).

## 9. GSAP and Remotion licences
- **Claim checked:** Is GSAP free, including plugins such as CustomEase? Is Remotion free for companies?
- **Finding:**
  - **GSAP**: npm `gsap` 3.15.0 uses the "Standard 'no charge' license", effective 2025-04-30 under Webflow. "All of GSAP including the plugins that were formerly 'members-only' like SplitText and MorphSVG can be used in commercial projects at no charge". The one restriction: no use in no-code visual animation builders that compete with Webflow.
  - **Remotion** (npm 4.0.532, "SEE LICENSE IN LICENSE.md") is source-available, not OSS. It is free for individuals, **for-profit organisations with up to 3 employees**, non-profits, and during evaluation. Everyone else needs a **Company License** from remotion.pro. Copying or modifying Remotion code to sell or relicense a derivative is not allowed.
  - Remotion 5.0 draft (PR #3750): **contractors count toward team size**, plus formal T&Cs.
- **Source:** https://gsap.com/standard-license ; https://github.com/remotion-dev/remotion/blob/main/LICENSE.md ; https://github.com/remotion-dev/remotion/pull/3750
- **Checked:** 2026-10-03
- **Status:** GSAP confirmed; Remotion differs (free only up to 3 employees)

## 10. ElevenLabs
- **Claim checked:** (a) the MCP server's tools, timestamps, API key and credits; (b) the REST with-timestamps endpoint; (c) v3 audio tags and timestamps; (d) API access in plans and whether overage can be disabled; (e) pronunciation dictionaries.
- **Finding:**
  - **(a) MCP server:** `elevenlabs/elevenlabs-mcp` was **archived on 2026-08-20** and is deprecated in favour of the hosted MCP at `https://api.elevenlabs.io/v1/mcp`, which uses OAuth with no API key.
    - The local server needed `ELEVENLABS_API_KEY`. Its tools included `text_to_speech`, `speech_to_text`, `text_to_sound_effects`, `search_voices`, `list_models`, `get_voice`, `voice_clone`, `isolate_audio`, `check_subscription`, `speech_to_speech`, `text_to_voice`, `compose_music`, `video_to_music`, agent and phone tools, and `play_audio`.
    - Its `text_to_speech` calls `client.text_to_speech.convert` (no timestamps) and returns only a file path or the audio. **No alignment data.**
    - The hosted MCP's TTS returns "a short-lived download link", with no timestamps mentioned.
    - Both servers bill credits: "ElevenLabs credits are needed to use these tools".
  - **(b) REST with-timestamps:** `POST /v1/text-to-speech/{voice_id}/with-timestamps` returns `audio_base64`, `alignment` and `normalized_alignment`, each with `characters`, `character_start_times_seconds` and `character_end_times_seconds`. Alignment is **character-level only**, so word timings must be derived. The request accepts `pronunciation_dictionary_locators` (max 3).
  - **(c) Models and audio tags:**
    - Current models include `eleven_v4` (10k character limit) and `eleven_v3` (5k).
    - v3 audio tags include `[laughs]`, `[sighs]`, `[whispers]` and others. v4 docs list `[short pause]`, `[long pause]`, `[laughs]` and `[chuckles]`.
    - "Eleven v4 and Eleven v3 do not support SSML break tags."
    - The with-timestamps docs list no model restriction, but no page explicitly confirms that timestamps work with v3 or v4.
  - **(d) Plans and billing:**
    - Subscriptions include API access, credits and API access tiers.
    - Pay As You Go is **opt-in** (add funds or enable Auto Top Up) and has an optional monthly spend cap. Without it, "usage pauses immediately … no postpaid billing".
    - Legacy usage-based billing has an on/off toggle and is no longer offered on new self-serve plans.
  - **(e) Pronunciation dictionaries:**
    - `POST /v1/pronunciation-dictionaries/add-from-rules` accepts alias and phoneme rules.
    - Per-model support from the best-practices page:

      | Model | Pronunciation dictionaries | Phoneme tags | Notes |
      |---|---|---|---|
      | **v4** | **Not supported** | **Not supported** | Use inline IPA `/…/` instead |
      | Multilingual v2 | Supported | Not supported | — |
      | Flash v2.5 | Supported | Supported | — |
      | v3 | Not stated | Not stated | — |

  - **(f) Live API check (2026-10-05, Robert's key):**
    - `with-timestamps` returns character alignment with **both `eleven_v3` and `eleven_multilingual_v2`**
      (premade voice Jessica, `cgSgspJ2msm6clMCkdW9`), which closes the open part of (c) for those two models.
    - The account is on the **free plan**: Voice Library voices (Hope, Zara, Maisie) return HTTP 402
      `paid_plan_required` ("Free users cannot use library voices via the API"). Premade voices work.
      After the upgrade to **Starter** the same voices work over the API (11 library voices generated).
      On Starter, library voices also work without being added to My Voices (5 generated directly, 2026-10-06).
      Starter includes 30k credits/month and a commercial licence (pricing page, 2026-10-06); the page gives
      1 credit per character for Multilingual v2 but no per-character rate for v4.
    - **Real spend** (`GET /v1/usage/character-stats`, readable with this key): ~11.1k credits for all voice
      auditions (multilingual v2 6.2k, v4 2.8k, v3 0.5k, 1.65k from other use) — well under 1 credit per
      character for the short library-voice reads.
  - **v4 cost (live, 2026-10-06):** the Acme v2 voice run (18 takes, 2,798 characters on `eleven_v4`)
    cost **306 credits**, about 0.11 per character; the response's credit header and
    `/v1/usage/character-stats` agree. Multilingual v2 bills about 1 per character.
  - **(g) Eleven Music:** `POST /v1/music` (`prompt` or `composition_plan`, `music_length_ms` 3,000-600,000,
    `model_id` `music_v1` | `music_v2` | `music_v2_5`, `force_instrumental`). "The Music API is available
    for paid subscribers"; "cleared for nearly all commercial uses, from film and television to podcasts and
    social media videos, and from advertisements to gaming" (per-plan terms: the Eleven Music model-specific
    terms, not read here). Live check on Starter: a 100 s instrumental bed on `music_v2_5` cost **1,250
    credits** (~12.5 per second) and measured exactly at the prompted 120 BPM (beat confidence 0.88),
    -15.4 LUFS, true peak -1.2 dBTP.
    `composition_plan` for `music_v2`/`music_v2_5` is `chunks` (`text` with `[Section]` and `{directions}`,
    `duration_ms` 3,000-120,000, `positive_styles`, optional `negative_styles`, `context_adherence`); durations
    are always enforced. `force_instrumental` is refused with a plan (HTTP 422, "can only be used with
    `prompt`"); a 7-chunk instrumental plan without lyrics came back with no vocals (whisper heard 0 words).
    - `with-timestamps` also returns alignment with **`eleven_v4`**. Audio tags (`[sighs]`, `[giggles]`,
      `[chuckles]`, `[laughs]`, `[whispers]`, emotion tags) appear in `alignment.characters` but are not
      spoken; a local whisper round trip found none read aloud in 4 tagged reads.
    - The key is scoped: `GET /v1/user/subscription` returns `missing_permissions` (`user_read`), so quota
      cannot be read with it.
- **Source:** https://github.com/elevenlabs/elevenlabs-mcp (README and `elevenlabs_mcp/server.py`) ; https://elevenlabs.io/docs/agents-platform/operate/hosted-mcp ; https://elevenlabs.io/docs/api-reference/text-to-speech/convert-with-timestamps ; https://elevenlabs.io/docs/overview/models ; https://elevenlabs.io/docs/best-practices/prompting/eleven-v3 ; https://elevenlabs.io/docs/overview/capabilities/text-to-speech/best-practices ; https://elevenlabs.io/docs/overview/administration/pay-as-you-go ; https://elevenlabs.io/docs/help-center/account/general/how-do-i-enable-usage-based-billing-for-my-account ; https://elevenlabs.io/docs/api-reference/pronunciation-dictionaries/create-from-rules ; https://elevenlabs.io/docs/api-reference/music/compose ; https://elevenlabs.io/docs/overview/capabilities/music ; https://elevenlabs.io/pricing
- **Checked:** 2026-10-03
- **Status:** (a) differs; (b) confirmed (character-level only); (c) timestamps confirmed live for v4, v3 and multilingual v2; (d) confirmed; (e) confirmed with model caveats
- **Addendum (2026-10-12, ADR 0030): sound effects.**
  - The request is `POST https://api.elevenlabs.io/v1/sound-generation` with the header `xi-api-key` and a JSON
    body:
    - `text` (required);
    - `duration_seconds` (0.5-30, optional; the model picks a length when it is omitted);
    - `prompt_influence` (0-1, default 0.3);
    - `loop` (bool);
    - `model_id` (only `eleven_text_to_sound_v2`).
  - Optional query: `output_format`.
  - It returns an MP3. Used by `create/footage/sfx.py: el_sound`, cached by prompt and length.
  - Source: elevenlabs.io/docs/api-reference/text-to-sound-effects/convert (checked 2026-10-12).

## 11. Platform loudness targets
- **Claim checked:** Do LinkedIn and YouTube publish an official loudness normalisation target (LUFS)?
- **Finding:**
  - **LinkedIn**: its official ad specs list only "AAC or MPEG4" audio and a sample rate "Less than 64KHz", with **no LUFS target**. The "-14 LUFS" figure appears only on third-party blogs.
  - **YouTube**: the official upload settings give AAC-LC or Opus, stereo or 5.1, 48 kHz, and 384 kbps stereo, with **no published LUFS target**. The widely cited "-14 LUFS" is community-derived from "Stats for nerds" content loudness and is not official.
  - Related official Google figures: Display & Video 360 uses -24 LKFS ±2 (IAB). Google Assistant recommends -16 LUFS.
- **Source:** https://www.linkedin.com/help/lms/answer/a424737 ; https://support.google.com/youtube/answer/1722171 ; https://support.google.com/displayvideo/answer/3129957 ; https://developers.google.com/assistant/tools/audio-loudness
- **Checked:** 2026-10-03
- **Status:** unverified (no official LUFS target from either platform)

## 12. GSAP and Remotion curve behaviour (verified by sampling the libraries)
- **Claim checked:** Do lens' first-principles curves draw what GSAP 3.14.2 and Remotion 4.0.532 draw?
- **Finding:**
  - All 32 sampled GSAP eases (power1-4, sine, expo, circ in/out/inOut, back and elastic with parameters)
    match to 5e-9. GSAP's `expo` is not the textbook 2^(10(t-1)): its "in" form is
    2^(10(t-1)) * t + t^6 * (1 - t), which starts at exactly 0.
  - Remotion's `spring()` matches the analytic mass-spring-damper to 5e-9 for zeta <= 1. For an
    **overdamped** config (zeta > 1) Remotion draws the **critically damped** curve at the same
    omega0 (also to 5e-9), not the overdamped one. An overdamped measured motion therefore cannot be
    reproduced exactly in Remotion; lens marks it `remotion_exact: false`.
- **Source:** `scripts/golden_curves.mjs` samples both packages into `tests/fixtures/golden-curves.json`;
  `tests/test_measure.py` checks lens against it. No library source is copied (ADR 0004); the GSAP
  expo formula was read from the published bundle to explain the mismatch.
- **Checked:** 2026-10-04
- **Status:** confirmed (sampled outputs)

## 13. Sentence embeddings for pattern clustering (S9)
- **Claim checked:** Can a small local sentence-transformer be used to cluster the annotators' `other`
  pattern names (no pay-per-use API)?
- **Finding:** `sentence-transformers/all-MiniLM-L6-v2` is licensed **apache-2.0** (model card and the
  Hub API `cardData.license`). Revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` is pinned in config.
  It loads with plain `transformers` (mean pooling over the last hidden state, then L2 normalisation, as
  the model card describes), so no new dependency is needed. It runs on CPU in about 30 s for ~200 texts.
- **Source:** https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2 (README front matter);
  https://huggingface.co/api/models/sentence-transformers/all-MiniLM-L6-v2
- **Checked:** 2026-10-05
- **Status:** confirmed

## 14. HyperFrames CLI (Phase 2 renderer)
- **Claim checked:** package, licence, composition contract, telemetry, and what renders need.
- **Finding:**
  - npm `hyperframes` 0.8.137 (HeyGen, `github.com/heygen-com/hyperframes`), **Apache-2.0**; Node >= 22 and FFmpeg.
  - A composition is HTML with a root `data-composition-id` + `data-width/height`; timed clips use
    `data-start`/`data-duration`; one **paused** GSAP timeline per composition, registered on
    `window.__timelines[<id>]`. Sub-compositions take variables (`data-composition-variables`).
  - **Telemetry is on by default** (anonymous usage); `hyperframes telemetry disable` turns it off. `create`
    runs it before every snapshot.
  - `snapshot --describe` sends frames to **Gemini** when `GEMINI_API_KEY` is set: `create` always passes
    `--describe false` (no pay-per-use APIs).
  - Asset paths must be **root-relative** (`assets/...`); `../` fails lint (`invalid_parent_traversal_in_asset_path`).
  - Local rendering needs Chrome Headless Shell (`hyperframes browser ensure`).
  - In this cloud sandbox the headless Chrome does not trust the egress proxy CA, so CDN scripts and Google
    Fonts fail (`ERR_CERT_AUTHORITY_INVALID`). `create` bundles GSAP and fonts locally, which also makes
    renders reproducible offline.
- **Source:** `npx hyperframes@0.8.137 --help`, `docs compositions|data-attributes|gsap`, `snapshot --help`,
  `doctor`; npm registry metadata.
- **Checked:** 2026-10-06
- **Status:** confirmed

## 15. HyperFrames quality tooling (check, skills, registry, capture)
- **Claim checked:** what HyperFrames ships for layout/motion QA and authoring guidance, and what calls paid services.
- **Finding:**
  - `hyperframes check [--at-transitions] [--samples N] [--json]` runs lint, runtime, layout (text overlap,
    occlusion, overflow, out-of-canvas), motion and WCAG contrast in one browser pass. `--at-transitions` also samples
    every tween boundary. Deliberate layering is declared per element with `data-layout-allow-overlap`,
    `data-layout-allow-occlusion`, `data-layout-allow-overflow` (reason as the value).
  - The npm tarball ships 3 skills; the repo (`skills/`) has 21, Apache-2.0: `product-launch-video`
    (motion doctrine: `power3` long-tail eases, no bounce, reveals timed to the voice in the back half, no idle
    breathing/drift, velocity-matched cuts), `hyperframes-animation` (about 50 named motion rules, 22 blueprints),
    `hyperframes-creative`, `faceless-explainer`, `pr-to-video` (`cut-catalog.md`: zoom-through, inverse
    zoom-through, cut-the-curve, waterfall; peak blur 10px for text, 18-20px for full-frame surfaces).
  - Registry: 410 blocks/components (`hyperframes catalog --query ... --json`, `hyperframes add <name>`),
    Apache-2.0; some blocks imitate third-party brands. The `hyperframes-launches` repo's media, fonts and brand
    marks are **not** Apache-2.0.
  - `hyperframes capture <url> --skip-vision` saves screenshots, HTML/CSS, tokens, fonts and SVGs of a site;
    without `--skip-vision` it captions images through Gemini/OpenRouter (pay-per-use). In this sandbox capture
    fails on the proxy CA (`ERR_CERT_AUTHORITY_INVALID`); run it locally.
  - Paused-timeline gotchas confirmed by lint/render: initial hides must be `gsap.set` outside the timeline;
    a `fromTo` that starts later needs `immediateRender: false` or its from-state shows at t=0.
- **Source:** `npx hyperframes@0.8.137 check --help`, `lint`; `github.com/heygen-com/hyperframes` at 0.8.137
  (`skills/**`, `registry/**`, LICENSE, `hyperframes-launches` NOTICE).
- **Checked:** 2026-10-06
- **Status:** confirmed

## 16. AI engine and source logos (SVG)
- **Claim checked:** where to get real ChatGPT/OpenAI, Gemini, Perplexity (and source) marks, and under what terms.
- **Finding:**
  - `@lobehub/icons-static-svg` 1.95.1, **MIT**: `openai`, `gemini-color`, `perplexity-color`, `claude-color`,
    `copilot-color`, `grok` and 700+ AI brands as 24x24 SVGs.
  - simple-icons 16.34.0, **CC0**, single colour: has `googlegemini`, `perplexity`, `anthropic`,
    `githubcopilot`, `reddit`, `youtube`, `facebook`; **OpenAI was removed**. Pin the version (jsDelivr
    `@latest` served a stale 15.x copy).
  - The licences cover the files; the marks stay trademarks. Showing an engine's logo to name the engine a
    product tracks is nominative use; follow each brand's guidelines (no recolour, stretch or crop;
    `openai.com/brand`). Logos are fetched at build time into `data/`, not committed (CLAUDE.md media rule).
- **Source:** npm registry metadata and tarball (`npm view`/`npm pack @lobehub/icons-static-svg`),
  `github.com/lobehub/lobe-icons`, `github.com/simple-icons/simple-icons` (DISCLAIMER), `openai.com/brand`.
- **Checked:** 2026-10-06
- **Status:** confirmed

## 17. Vertical safe zones and specs (TikTok, Reels, Shorts)
- **Claim checked:** where platform UI covers a 1080x1920 frame; upload specs. Full detail:
  `docs/research/sources/vertical-safe-zones-and-specs.md`.
- **Finding:**
  - No platform publishes an organic safe zone in text. TikTok's ad templates (720x1280 / 540x960 PNGs) scaled
    to 1080x1920 give top 240, bottom 660, sides 120 ("may be cropped based on device type"), action rail
    x 780–960 from y 840 down. The product-anchor template gives top 252, rail x ≥ 840 from y 360, and a bottom of
    812–1014 px for 1–4 caption lines.
  - Meta Reels ads: keep "14% of the top, 35% of the bottom, and 6% on each side" clear (bottom 40% with disclaimers).
  - YouTube vertical ads overlay (1080x1920): safe x 48–888, y 288–1248.
  - House intersection: core x 120–780, y 288–1248.
  - No platform publishes a loudness target. TikTok creators can post 3-minute videos (some 5 or 10); Shorts up
    to 3 min (uploads from 2024-10-15), max 1080p; YouTube encoding H.264 High, AAC-LC/Opus 48 kHz, 8 Mbps at 1080p30.
  - TikTok best practices: hook in the first 6 s, proposition in the first 3 s, "5-10 words per second" of text.
- **Source:** ads.tiktok.com/help/article/video-ads-specifications (updated June 2026) + its safe-zone zips;
  ads.tiktok.com/help/article/creative-best-practices; facebook.com/business/ads-guide/update/video/instagram-reels;
  facebook.com/business/help/980593475366490; support.google.com/google-ads/answer/13547298 (overlay PNG);
  support.google.com/youtube/answer/15424877, /10059070, /1722171; developers.tiktok.com content-posting-api-media-transfer-guide.
- **Checked:** 2026-10-09
- **Status:** confirmed for the measurements; the live UI varies by device and app version (all three platforms say so).
  The organic TikTok/Instagram help pages are client-rendered and could not be read.

## 18. TikTok policy points for business videos
- **Finding:**
  - The AI label is required for realistic AI people or scenes and for AI audio that imitates a real person's voice.
    It is not required for animated or artistic styles or for generic TTS that is not a recognisable person's voice.
    So a clone of Robert's voice needs the label.
  - Commercial Music Library sounds are licensed for TikTok only.
  - Own-brand promotion uses "Disclose commercial content" → "Your brand".
- **Source:** TikTok Community Guidelines (released 2026-08-25, effective 2026-09-24); TikTok Commercial Music
  Library terms; TikTok Branded Content Policy (effective 2026-08-31). Detail: `docs/research/sources/short-form-editing-craft.md` §5, §9.
- **Checked:** 2026-10-09
- **Status:** confirmed (verbatim from TikTok's pages)

## 19. Presenter-footage tools (licences)
- **Finding:**
  - Permissive licences: WhisperX 3.8.6 BSD-2 (alignment models for en and ro Apache-2.0); Silero VAD 6.2.3 MIT;
    OpenCV YuNet MIT; MediaPipe 1.1.0 Apache-2.0 (model cards unchecked); OpenTimelineIO 0.18.1 Apache-2.0;
    auto-editor Unlicense; DeepFilterNet MIT/Apache-2.0.
  - CrisperWhisper weights are **non-commercial** (Nyra Health NC licence; v1 cc-by-nc-4.0).
  - GPL-3.0: whisper-timestamped, praat-parselmouth, pedalboard, RobustVideoMatting.
  - HyperFrames 0.8.143: the render pre-extracts video frames with FFmpeg at source resolution; HDR inputs switch
    the output to HDR10 unless `--sdr`; `skills/talking-head-recut` (overlay/pip/split/stack) and
    `skills/embedded-captions` exist.
  - Homebrew `ffmpeg` 9.0.2 lacks zimg/libplacebo; `ffmpeg-full` has them.
- **Source:** PyPI/Hugging Face/npm/Homebrew metadata and LICENSE files; `github.com/heygen-com/hyperframes` at
  46f6cb3. Detail: `docs/research/sources/presenter-footage-pipeline.md`.
- **Checked:** 2026-10-09
- **Status:** confirmed, except the MediaPipe model-card licences and the torchaudio wav2vec2 weight licence (unverified)
- **Addendum (2026-10-09):** YuNet's model files are in Git LFS. `raw.githubusercontent.com` returns 403 for them;
  `media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2026may.onnx`
  serves them (sha256 `ebafce4e…22f0f0`, pinned in config). The zoo README says the 2026may model has dynamic input
  dims for OpenCV 5's ONNX Runtime engine; the 2023mar model is fixed-shape. Licence: MIT (`models/face_detection_yunet/LICENSE`).
  OpenCV 5.0.0 `cv2.FaceDetectorYN` runs it at about 10 ms per 720p frame on CPU.
- **Addendum (2026-10-12, ADR 0030):** the OpenCV zoo's BlazePose landmark model
  `models/pose_estimation_mediapipe/pose_estimation_mediapipe_2023mar.onnx` (Git LFS; served by
  `media.githubusercontent.com`, sha256 `9d89c599…67ed2f3f`, pinned in config `create.footage.pose`). Licence:
  Apache-2.0 (`models/pose_estimation_mediapipe/LICENSE`). Input: a 256 x 256 RGB crop in 0..1; outputs 39 x 5
  landmarks (x, y in crop pixels, z, visibility and presence as logits; the first 33 are BlazePose's keypoints)
  and a confidence. OpenCV 5.0.0 `cv2.dnn` runs it on CPU. Checked on a 4K still of take 1: every joint on the body.

## 20. Brand capture, token format, font licences
- **Finding:**
  - DTCG Format and Resolver modules reached stable 2025.10 (Final Community Group Reports, 2025-10-28). They are
    not a W3C Standard.
  - Dembrandt MIT; Style Dictionary Apache-2.0 (2025.10 support in progress).
  - Adobe Fonts terms (2024-06-18) forbid self-hosting and copying font files, so they cannot be used in our bundle.
  - acme.example uses Geist / Geist Mono (OFL 1.1).
- **Source:** designtokens.org / w3.org/community/design-tokens; github.com/dembrandt; adobe.com Fonts additional
  terms; acme.example CSS. Detail: `docs/research/sources/brands-and-formats-audit.md`.
- **Checked:** 2026-10-09
- **Status:** confirmed

## 21. ElevenLabs speech-to-text (Scribe)
- **Claim checked:** the endpoint, request fields and response shape that F2 (`create transcribe`) relies on.
- **Finding:**
  - `POST https://api.elevenlabs.io/v1/speech-to-text`, multipart, header `xi-api-key`.
  - **Request:**
    - `model_id` (`scribe_v2`), exactly one of `file` or `source_url`;
    - `language_code` (ISO 639-1/3, null = auto-detect);
    - `tag_audio_events`;
    - `timestamps_granularity` `word | character`;
    - `diarize`;
    - `keyterms`: at most 1000, each under 50 characters and 5 words, no `<>{}[]\`, +20% surcharge.
  - **Response:** `language_code`, `language_probability`, `text`, and `words[]` with `text`, `type`
    (`word | spacing | audio_event`), `start`, `end` (nullable), `speaker_id`, `logprob`.
  - **Verbatim by default:** `no_verbatim=true` (scribe_v2 only) removes "filler words, false starts and non-speech
    sounds".
  - **Limits:** file under 5 GB; at least 100 ms of audio.
  - **Measured 2026-10-09 on a 21 s clip:** "Um," and "to--" came back as words, "Acme" was spelled as the
    keyterm, and a sine tone was tagged "[beep]". About 2 s.
- **Source:** https://elevenlabs.io/docs/api-reference/speech-to-text/convert
- **Checked:** 2026-10-09
- **Status:** confirmed (docs and one live call)

## 22. Reading TikTok from the cloud (studies/tiktok)
- **Claim checked:** whether a cloud container can list and download public TikToks for the TikTok study.
- **Finding:**
  - `www.tiktok.com/@handle/video/<id>` pages return a "Site Maintenance" page to headless Chromium from the
    cloud. yt-dlp (2026.x) fails on them with "Unexpected response from webpage request".
  - These work from the cloud:
    - Discover pages (`/discover/<phrase>`) and the creator embed (`/embed/@handle`) render in headless Chromium
      and link the videos (about 20-25 per discover page; a creator's recent videos in the embed).
    - The embed player (`/embed/v2/<id>`) carries the item JSON in `#__FRONTITY_CONNECT_STATE__`: caption,
      createTime, plays, likes, comments, shares, duration, author, music.
    - The item JSON's `video.urls` downloads with the browser context's cookies as an H.264/AAC MP4 (576x1024
      or 720x1280). Do not take the page's first `<video>`: it is a generic TikTok promo clip.
    - Some copies have a ~4 s TikTok end slate appended; the JSON's `duration` (whole seconds) is the video's
      own length.
  - `www.tiktok.com/oembed?url=` answers plain curl with title and author only.
- **Source:** tested in this container (study/web/tiktok.cjs); developers.tiktok.com/doc/embed-videos (embed
  player).
- **Checked:** 2026-10-13
- **Status:** works today; TikTok changes its web app often, so a failed fetch should be retried and reported.
  The 576x1024 copy is for measuring only and is never committed or republished.

## 23. SFX library for the motion route (c8_grade, c12_mix)
- **Claim checked:** where the motion route's sound effects come from and whether they may be used in our videos.
- **Finding:**
  - The pinned `hyperframes@0.8.137` npm package bundles 19 SFX in
    `package/dist/skills/media-use/audio/assets/sfx/` (chime, click, click-soft, error, glitch-1..3,
    impact-bass-1/2, key-press, notification, ping, pop, riser, sparkle, typing, whoosh, whoosh-cinematic,
    whoosh-short). Its CREDITS.md says they are from Pixabay under the Pixabay Content License.
  - Pixabay Content License summary: free use, no attribution required, modification allowed; content may not
    be sold or distributed on a standalone basis (with no creative effort applied), used in immoral, illegal
    or misleading ways, or as part of a trademark. Mixed into a finished video is not standalone.
  - `create grade` downloads the package tarball once (data/create/_cache/, never committed) and copies the
    files into the render bundle; the files are never committed or shipped on their own.
- **Source:** https://registry.npmjs.org/hyperframes/-/hyperframes-0.8.137.tgz (CREDITS.md);
  https://pixabay.com/service/license-summary/
- **Checked:** 2026-10-17
- **Status:** fine for finished videos; only the full Pixabay Content License is binding.

## 24. Claude Code: what costs context (ADR 0035)
- **Claim checked:** which repo settings keep text out of every request, and the harness behaviour the video
  flow relies on (background renders, resuming an agent).
- **Finding:**
  - Skill frontmatter `disable-model-invocation: true`: "This removes the skill from Claude's context entirely";
    the skill still runs as `/<name>` (code.claude.com/docs/en/skills). Our agents read their SKILL.md by path,
    which the flag does not touch. `user-invocable: false` keeps the description in context.
  - Permissions: "A bare tool name like `Bash` removes the tool from Claude's context entirely"; a scoped rule
    only blocks matching calls (code.claude.com/docs/en/permissions). The docs do not say a server-level
    `mcp__<server>` deny removes connector tools from context; `deniedMcpServers` blocks connectors by name
    (code.claude.com/docs/en/mcp).
  - Agent frontmatter (code.claude.com/docs/en/sub-agents): `effort` takes low, medium, high, xhigh or max (the
    levels available depend on the model); `omitClaudeMd: true` leaves CLAUDE.md out of the agent's context
    (Claude Code 2.1.271 or later; the cloud image has 2.1.309). We set it on self-contained builder and
    reviewer agents, whose agent file and skill carry their rules; annotators keep CLAUDE.md.
  - Measured 2026-10-23 with two probe sessions that only replied "ok": the first request of a fresh session on
    this repo is 90,501 tokens; with `permissions.deny` on the tools a video never uses (claude-code-remote's
    session and trigger tools, Workflow, onboarding, loop and review tools, and the Claude Docs, ClickUp, Figma,
    Gmail, Calendar, Sheets, Planable, Semrush, SEOmonitor and Spotify connectors) it is 68,860 (-24%). Changing
    `.claude/settings.json` mid-session also removes or restores those tools live. The first ~48k of the prompt
    is shared across sessions and read from cache.
  - Harness (tool descriptions in Claude Code on the web, 2026-10-23; observed in this repo's sessions): a Bash
    command with `run_in_background` wakes the session when it exits, so renders need no polling; `SendMessage`
    to an agent's id continues it with its context; a custom agent starts at 6-9k tokens of context, a
    general-purpose one at ~59k, the main session at ~83k (result events of five video sessions, ADR 0035).
- **Source:** code.claude.com/docs/en/skills, /permissions, /mcp (via the claude-code-guide agent); session
  result events 2026-10-17.
- **Checked:** 2026-10-23
- **Status:** relied on by process-take, build-panel and the agent-only skills; recheck if Claude Code changes
  how skills or agents load.

## 25. DaVinci Resolve 21.1.2 scripting and DJI Mimo takes (skill resolve-fix-take)
- **Claim checked:** how a raw take from Robert's iPhone + DJI Osmo Mobile (DJI Mimo app) is encoded, and what the
  Resolve scripting API (DaVinci Resolve MCP, Resolve Studio 21.1.2) can do to grade and level it.
- **Finding (measured on walmart-agents, 2026-10-29):**
  - DJI Mimo "Log" files carry `com.apple.quicktime.filterBaked=1`, `filterID=AppleLog-Rec709`,
    `colorSpace=rec709`, `productModel=OM508`: the Apple Log → Rec.709 conversion is baked into the pixels
    (blacks reach 10-bit 44-73; skin R/G ~1.4). Resolve still tags the clip "Apple Log" on import.
  - Resolve 21.1.2 offers an "Apple Log 2" input colour space (gamma reads "Apple Log"); `SetClipProperty`
    cannot change "Input Gamma" on that clip (every value returns False), project input settings do not override it.
  - Under colour management a nested timeline used as a clip is colour-converted again (double transform).
  - The API has no node or CST insertion: `SetCDL` and `Graph.SetLUT` on node 1 are the grading tools;
    `Project.RefreshLUTList()` makes a newly written `.cube` usable.
  - Audio: `TimelineItem.AddEffect("audio", "Audio FX/Fairlight FX/Limiter")` works but its parameters cannot be
    set; the Dialogue Leveler is settable through `SetProperty` (`AudioDialogueLeveler*`); `AnalyzeAudioLevels`
    and the render place a clip's Limiter differently relative to clip volume, so levels are tuned on renders.
  - `SetRenderSettings` `ExportVideo` persists from a previous audio-only job.
  - Apple Log 2 uses the Apple Log curve with the wider Apple Wide Gamut (third-party guides:
    gamut.io/apple-log-vs-apple-log-2-in-davinci-resolve-why-color-space-matters/,
    gamut.io/apple-log-2-color-grading-workflow-the-3-step-method/); not needed for baked DJI takes.
- **Source:** the take's ffprobe tags and pixel measurements; Resolve's scripting stubs (MCP
  `get_scripting_api`, 21.1.2) and calls run against Resolve Studio 21.1.2 on Robert's Mac.

## Implications for the plan
- **Per-subagent path-restricted Write will not work as written.**
  - `tools:` takes tool names only, and `Write(path)` permission rules are silently ignored.
  - Instead, use `Edit(videos/**)` rules, which apply to the whole session, or a PreToolUse hook that checks `file_path` (in settings.json, or in subagent frontmatter, which requires a trusted folder on CI).
- **Chaining workflows on bot-created PRs:**
  - PRs or pushes made with GITHUB_TOKEN either do not trigger workflows or wait for manual approval (new `pull_request` exception).
  - PRs made by the Claude GitHub App (the action's default auth) or by a PAT or app token do trigger workflows.
  - claude-code-action rejects bot actors unless they are listed in `allowed_bots`.
  - `workflow_dispatch` or `repository_dispatch` is the reliable way to chain.
- **ElevenLabs via MCP does not provide timestamps.** The local MCP is archived, and neither MCP's TTS tool returns alignment data. Use the REST `/with-timestamps` endpoint, which gives character-level alignment that must be aggregated into words. The MCP also needs an API key or OAuth and spends the same credits.
- **ElevenLabs model choice affects pronunciation control.** v4 does not support pronunciation dictionaries or phoneme tags, and neither v3 nor v4 supports SSML `<break>`. Use `[short pause]`/`[long pause]` tags or punctuation, and test with-timestamps against the chosen model.
- **LinkedIn -16 to -14 LUFS is not an official target.** Neither LinkedIn nor YouTube publishes a LUFS figure. Treat -14 LUFS integrated with a true peak of about -1 dBTP as a convention and label it that way in the plan.
- **GHCR images with model weights:** container registry storage and bandwidth are currently free (with one month's notice before any change). Each weight's licence must allow redistribution. CC0, MIT, Apache-2.0 and MS-PL all allow it, but MS-PL requires shipping the licence text, and the htdemucs weights licence is unconfirmed beyond the repo's MIT. Note the 14 GB runner disk when pulling large images.
- **Remotion is not freely usable by companies above 3 employees,** and Remotion 5.0 will count contractors. Using the npm package for golden tests is still "use". The free licence covers only individuals, small companies and evaluation, so either confirm eligibility or buy a Company License. Reimplementing the spring math from first principles is lower risk than copying code.
- **Use the `rapidocr` package (3.x) instead of the frozen `rapidocr-onnxruntime` (1.4.4).** Both are Apache-2.0.
- **Size the Actions budget for a private repo on Free:** 2,000 min/month on a 2 vCPU, 8 GB, 14 GB disk runner, with 500 MB artifact storage and 10 GB cache. Prefer R2 (10 GB free, free egress) for rendered media.
- **Claude image input:** keep frames to 2000 px or less per side when sending more than 20 images per request. The high-res models auto-downscale above a 2576 px long edge or 4784 tokens.
