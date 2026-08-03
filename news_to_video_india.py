#!/usr/bin/env python3
"""
================================================================================
 INDIA TRENDING NEWS & GLOBAL GEOPOLITICS -> HINDI SHORT-FORM VIDEO GENERATOR
 (forked from the English/US news_to_video_final.py v4 pipeline - same engine,
 different market/language/topic. See CHANGELOG below for the exact diff.)
================================================================================

PIPELINE (DAILY BATCH MODEL) - unchanged from the US pipeline:
  1. Gather candidates: yesterday's leftover queue (queued_news_india.txt) +
     fresh whitelisted, non-duplicate headlines from Google News RSS (India/
     Hindi edition: general trending feed + world/geopolitics feeds).
  2. ONE NVIDIA LLM call ranks all candidates by viral potential.
  3. Take the top DAILY_STORY_TARGET (3) stories. For each: fact-check + write
     a Hindi script with a duration-enforcement retry loop (30-40s).
  4. edge-tts -> natural Hindi voiceover (with word-level timestamps).
  5. Pexels -> 1080x1920 (9:16) stock footage, cut every 2-3s, dynamic PIL
     captions rendered in a Devanagari-capable font.
  6. Upload to YouTube as `private` with `publishAt` set to the next available
     one of 3 fixed India peak-time slots (IST) - it goes public automatically
     at that time, no manual step needed.
  7. Deliver the same video + copy-paste metadata to Telegram as a review copy.
  8. Any candidates not selected today are written back to queued_news_india.txt
     so no good story is wasted - re-ranked alongside fresh news tomorrow.

--------------------------------------------------------------------------------
CHANGELOG vs the US/English news_to_video_final.py this was forked from
--------------------------------------------------------------------------------
  [CHANGED] Market/language/topic: US tech news (English) -> India trending
            news + global geopolitics (Hindi). TTS: en-US-AndrewNeural ->
            hi-IN-MadhurNeural (hi-IN-SwaraNeural documented as the
            alternative). The `script_en` JSON key/field NAME is kept as-is
            everywhere in the code (deliberate minimal-diff choice) but now
            HOLDS Hindi/Devanagari text - don't let the name confuse you.
  [ADD]   Devanagari font support RE-ADDED to find_caption_font() (the
          English v4 fork this was forked from had deliberately dropped it -
          see its own changelog - since English captions don't need it, but
          Hindi captions do, or they render as blank/tofu boxes). Tries
          fontconfig (`fc-match :lang=hi`) first since exact install paths
          vary by distro, then known Noto/Lohit Devanagari paths, then a
          download fallback, then logs an actionable warning if all three
          fail. main.yml installs `fonts-noto-core` via apt so this should
          resolve on the first candidate path in CI.
  [CHANGED] SOURCE_WHITELIST -> Times of India, India Today, News18, NDTV,
            Hindustan Times, Indian Express, The Hindu, WION, ANI (India) +
            Reuters, AP, BBC, Al Jazeera (international wire, for objective
            framing specifically on the geopolitics stories).
  [CHANGED] NEWS_RSS_FEEDS -> India/Hindi Google News edition (hl=hi-IN&
            gl=IN&ceid=IN:hi): general top-stories feed + WORLD topic feed +
            two targeted geopolitics/foreign-policy search feeds. UNVERIFIED
            live (no network access available while writing this fork) - if
            the first run logs "Found 0 fresh whitelisted candidate(s)",
            this is the first thing to check, exactly like the TECHNOLOGY-
            feed bug the US pipeline hit before (see its [FIX] entry below).
  [CHANGED] SCRIPT_PROMPT_TEMPLATE + SCORING_PROMPT_TEMPLATE rewritten for a
            Hindi scriptwriter/news-analyst persona. Same hook / fast body /
            analysis-beat / CTA structure, but the analysis beat is steered
            toward "what this means for India" specifically, and the fact-
            check role doubles as a monetization-compliance gate: a story
            that's primarily an active war/attack/mass-casualty event gets
            marked not-credible rather than risk YouTube's Sensitive Events
            ad-suitability policy on something an LLM can't responsibly
            fact-check from a short RSS summary alone. The prompt also
            explicitly forbids presenting the AI narration as a named real
            anchor/expert (YouTube's "inauthentic content" policy singles
            out synthetic personas posed as experts).
  [CHANGED] YOUTUBE_CATEGORY_ID: "28" (Science & Technology) -> "25" (News &
            Politics). Added defaultLanguage/defaultAudioLanguage: "hi" to
            the upload snippet.
  [CHANGED] YOUTUBE_TIME_ZONE -> Asia/Kolkata; SLOT_WINDOWS -> 3 IST windows
            (morning/lunch/evening) positioned ahead of India's ~7-11PM IST
            Shorts engagement peak - not literally the same clock times as
            the US EST slots, same mechanism (jittered window, not fixed
            HH:MM) applied to a different market.
  [CHANGED] Every credential env var (NVIDIA_API_KEY, PEXELS_API_KEY,
            TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, YOUTUBE_CLIENT_ID/SECRET/
            REFRESH_TOKEN) now reads from an _INDIA-suffixed env var name -
            fully separate GitHub Secrets from the US pipeline, zero
            collision risk running both workflows out of the same repo.
            Python-side variable names unchanged (purely local to this file,
            no need to touch every call site).
  [CHANGED] PROCESSED_NEWS_FILE / QUEUED_NEWS_FILE / PENDING_YOUTUBE_UPLOADS_FILE
            all suffixed _india.txt - these get committed back to the shared
            git repo by the workflow, so without distinct names this
            pipeline's dedup/queue/retry state would silently collide with
            the US pipeline's on every commit.
  [KEPT]  Everything else byte-for-byte: video assembly, Ken Burns, color
          grade, karaoke captions, watermark/intro sting/music (all still
          optional/graceful), fuzzy dedup, LLM call budget+pacing, mark-
          processed-after-render ordering, config validation, and the
          openai + moviepy==1.0.3 dependency fix.

--------------------------------------------------------------------------------
CHANGELOG round 2 - regional expansion, 6-video schedule, AI-image fallback,
retry-queue fix, decision log
--------------------------------------------------------------------------------
  [ADD]   State/regional coverage: 5 new RSS feeds (West Bengal/Kolkata, Mumbai/
          Maharashtra, Delhi/NCR, Punjab, Kerala - one feed PER region rather
          than one combined OR-query, so a quiet day for one state doesn't
          drown out another), ABP Live added to SOURCE_WHITELIST (strong
          regional bureau coverage), SCRIPT_PROMPT_TEMPLATE's analysis-beat
          now branches between "what this means for India" (geopolitics) and
          "why this matters locally" (state/regional stories) rather than
          forcing every story into the national-impact frame.
  [ADD]   AI-generated visual fallback (generate_ai_background_image +
          _image_to_clip_file): Pexels is tried first; if a story nets fewer
          than MIN_BACKGROUND_CLIPS (3), Pollinations.ai (free, key-less, no
          new secret) tops up the gap with generated images, wrapped as
          silent .mp4s so they flow through the exact same crop/Ken-Burns/
          color-grade pipeline as real footage. Prompt is constrained to
          symbolic/generic imagery with no real identifiable people, to stay
          clear of deepfake/misrepresentation risk on news content. UNVERIFIED
          live (no network access while writing this) - if it never produces
          an image, that's the first thing to check.
  [CHANGED] DAILY_STORY_TARGET 3 -> 6; SLOT_WINDOWS -> 6 narrow (~14min)
          windows centered on ~7:40AM/9:00AM/11:11AM/1:11PM/6:00PM/7:30PM IST
          instead of 3 wide windows - MAX_CANDIDATES_TO_SCORE and
          MAX_DAILY_ATTEMPTS raised to match (25, 12). main.yml's cron moved
          earlier (5:00AM IST) and timeout raised (120->180min) since
          rendering 6 videos takes meaningfully longer than 3 - if runs start
          approaching the timeout, the per-frame Ken Burns/color-grade PIL
          pass is the likely hotspot to profile first.
  [FIX]   retry_pending_youtube_uploads() used to just drop a pending upload
          once its local mp4 didn't survive to the next day's fresh GitHub
          Actions runner - which, combined with any YouTube upload failure,
          made the entire retry queue silently do nothing. process_single_story
          now sends to Telegram BEFORE attempting the YouTube upload (not
          after) specifically so a telegram_file_id is available to store in
          the pending-queue entry; the retry pass now re-downloads the video
          from Telegram via that file_id when the local copy is gone, instead
          of just dropping the entry.
  [ADD]   log_decision() + decisions_log_india.jsonl: one JSON line per story
          (skipped/failed/produced + why), committed alongside the other
          state files - a persistent, greppable record that outlives GitHub
          Actions' ~90-day run-log retention.
  [DEFERRED after round 2, RESOLVED in round 3] The "cancel by video ID"
          helper script mentioned above is now built - see cancel_upload.py
          + india_geo_cancel.yml.

--------------------------------------------------------------------------------
CHANGELOG round 3 - full India states/UTs coverage, parallel+fair RSS
scanning, cancel-upload kill-switch
--------------------------------------------------------------------------------
  [CHANGED] NEWS_RSS_FEEDS: the 5 hand-picked state feeds replaced with
          INDIA_STATES_AND_UTS - all 28 states + 8 union territories, one
          feed per region, generated programmatically (name list -> URL) so
          adding/removing coverage later is a one-line change, not hunting
          through dozens of literal URL strings. Feed count: 4 national -> 40
          total.
  [FIX]   scan_fresh_candidates() rewritten for the 40-feed scale - it had
          two real problems at the old 4-9 feed count that would have gotten
          much worse at 40: (1) feeds were fetched one at a time with no
          explicit timeout, so one slow/hung feed would delay or stall every
          feed after it - now fetched in parallel via ThreadPoolExecutor,
          each with its own REQUEST_TIMEOUT; (2) candidates were merged by
          walking NEWS_RSS_FEEDS in its fixed list order until max_count was
          hit, which let the first few (usually highest-volume, national)
          feeds fill the cap before a smaller state's feed was ever reached
          - now merged round-robin across feeds in a freshly SHUFFLED order
          each run, so which feeds get first pick varies day to day instead
          of a handful of feeds permanently crowding out the rest.
          MAX_CANDIDATES_TO_SCORE raised 25 -> 35 to match.
  [ADD]   cancel_upload.py + india_geo_cancel.yml: a standalone kill-switch -
          given a YouTube video ID, sets it back to private so a scheduled
          publishAt won't fire. Imports get_youtube_service() from THIS file
          rather than duplicating the OAuth logic, so it can never drift out
          of sync with however this script authenticates. Triggered manually
          from the Actions tab (workflow_dispatch), no local setup needed -
          this is the practical answer to "what if a bad story gets through"
          without building a full interactive approve/reject system into the
          cron pipeline itself.
  [STILL DEFERRED, same reasoning as round 2] Merging this and the US script
          into one config-driven multi-channel file - better done once the
          config surface (still moving every round so far) stabilizes. A
          YouTube-Analytics feedback loop into future ranking - needs real
          performance data to be worth building.

--------------------------------------------------------------------------------
CHANGELOG round 4 - time-synced, India-contextualized visuals (post first
live run, which succeeded: 6/6 videos rendered and published)
--------------------------------------------------------------------------------
  [ADD]   ScriptBeat + ScriptPackage.shot_list: SCRIPT_PROMPT_TEMPLATE now
          asks for an ordered shot list (4-7 beats), each with a script
          excerpt, a SPECIFIC India-contextualized visual description
          (Durga Puja mentioned -> Durga idol/pandal imagery, "police" ->
          Indian police specifically, a named state/city -> that place's
          own culture/landmarks - not generic/Western stock), and a
          prefer_ai_generation flag for concepts real stock footage won't
          have (deities, festivals, local tradition).
  [ADD]   build_synced_background_video() + fetch_beat_footage() +
          _allocate_beat_durations(): footage is now sourced and assembled
          PER BEAT, in shot_list order, instead of from one flat keyword
          pool for the whole story - durations are allocated proportional
          to each beat's phrase length (robust; deliberately not matched
          against word-timestamps character-for-character, which would be
          fragile against any LLM punctuation/spacing drift). Beats flagged
          prefer_ai_generation skip straight to AI generation; others try
          Pexels first with an India-biased query ("India " prefixed onto
          the visual) before falling back to AI generation. Reuses
          build_background_video()'s existing per-segment pipeline (crop,
          Ken Burns, color grade) unchanged, just called once per beat
          instead of once per story, then crossfaded together - the tested
          segment-level code isn't touched, only how footage gets sourced
          and ordered around it.
  [KEPT, defense-in-depth] generate_script_package() parses shot_list
          defensively - a missing/malformed entry is dropped, never raises.
          build_synced_background_video() falls back to the original flat
          fetch_background_clips()+build_background_video() path (using
          visual_keywords) if shot_list is empty or every beat's footage
          sourcing fails - a newer, less-tested code path degrades to the
          one already proven live, rather than failing the story.
  [CLARIFIED, not a code change] Two things raised after the first live run
          that are policy/strategy facts, not bugs: (1) containsSyntheticMedia
          stays True regardless of voice quality - trying to make the
          narration undetectable as AI is the opposite of what protects
          monetization (undisclosed synthetic content is what YouTube's
          "inauthentic content" policy actively terminates channels for;
          disclosed synthetic content is fully monetizable). (2) Guideline
          compliance alone doesn't unlock monetization - YPP still requires
          hitting actual thresholds (1,000 subscribers + 10M Shorts views in
          90 days, or 500 subs + 3M Shorts views for the earlier fan-funding
          tier) on top of staying policy-compliant.

--------------------------------------------------------------------------------
CHANGELOG round 5 - Hinglish text everywhere except the TTS input, stronger
dual (Shorts feed + search) SEO framing
--------------------------------------------------------------------------------
  [CHANGED] title/description/hashtags/tags now generated in Hinglish (Hindi
          words, Roman/English letters, natural casual spelling - "mere pas
          khuchvi nehi hay..." style) instead of Devanagari. script_en is
          DELIBERATELY UNCHANGED (still Devanagari) - it feeds
          synthesize_voice_with_timing() directly, and edge-tts's hi-IN
          voice needs Devanagari to pronounce Hindi correctly; Roman-script
          input would be read back with English pronunciation rules.
  [ADD]   script_romanized: a new LLM output field, same content as
          script_en word-for-word in the same order, transliterated to
          Hinglish - explicitly instructed to match script_en's word count
          exactly, since that's what makes the next point possible.
  [ADD]   build_romanized_word_timings(): captions now display the Hinglish
          script_romanized instead of Devanagari script_en, while keeping
          the CORRECT per-word timing from the actual synthesized audio -
          maps script_romanized's words onto the Devanagari word-timing
          list by index (word N's Roman spelling gets word N's real
          start/end time). Falls back to the original Devanagari captions
          if the word counts don't match (a real possibility with any LLM
          output) rather than producing misaligned or truncated captions.
  [CHANGED] title/description/hashtags/tags prompt instructions strengthened
          for dual discovery: optimized to match what people actually type
          into YouTube search on a phone keyboard (very often Roman letters
          even for Hindi-intent searches) as well as for Shorts-feed
          virality - the Hinglish choice above and this SEO goal reinforce
          each other rather than being separate asks.

--------------------------------------------------------------------------------
CHANGELOG round 6 - CONFIRMED LIVE BUG FIX (caption boxes), foreign-country
footage nuance, voice pacing, after real published videos were reviewed
--------------------------------------------------------------------------------
  [FIX, confirmed live] find_caption_font()'s font download URL and apt-path
          guesses were both unreliable in practice - real published videos
          showed blank/tofu boxes instead of Hindi captions. Replaced the
          download URL with one directly fetched and confirmed (not
          assumed from a search result) to be a real ~138KB static TTF -
          github.com/openmaptiles/fonts - and added a post-download sanity
          check (actually load it with PIL.ImageFont before trusting it,
          since a 200 OK response can still be an HTML error page body, not
          a font). Static (non-variable) weight also sidesteps a separate
          risk: PIL's ImageFont has had mixed support for variable-font
          weight-axis selection, and Noto's own current default
          distribution is a variable font.
  [CHANGED] shot_list's visual field: beats genuinely ABOUT a specific named
          foreign country (a global geopolitics story) now describe THAT
          country's own context instead of being forced into Indian
          imagery; every other beat still defaults to India. Removed
          fetch_beat_footage()'s blanket "prepend India to every Pexels
          query" logic, which would have contradicted a beat the LLM
          correctly wrote as foreign-context (e.g. "Madrid Spain city
          street") - the geographic context now lives entirely in the
          LLM's own `visual` text per the updated prompt instruction.
  [CHANGED] TTS_RATE eased from +8% to +2% (closer to natural conversational
          pace); TTS_VOICE now reads from an optional env var for A/B
          testing hi-IN-MadhurNeural vs hi-IN-SwaraNeural without editing
          code. NOTE: actual voice-cloning/generative quality on par with
          paid tools (ElevenLabs, Veo 3, etc.) is NOT achievable within a
          $0 TTS engine - this is a real ceiling of the free-tier approach,
          not a bug to fix in code.
  [NOTE, not a code change] "Automatically detect and adapt to future
          YouTube policy changes with zero human check-in" isn't something
          any code can do - there's no machine-readable policy-change feed
          designed for this, and correctly interpreting policy nuance needs
          human judgment even for platforms with dedicated trust & safety
          teams. Realistic version: periodic manual check-ins (ask me to
          search current guidelines every so often) rather than a fully
          autonomous self-updating system.

--------------------------------------------------------------------------------
CHANGELOG round 7 - Hinglish detection safety net, 1.3x rate, after the file
in active use was confirmed byte-identical to round 6 (so remaining Hinglish
reports needed a real code fix, not just "redeploy the latest version")
--------------------------------------------------------------------------------
  [ADD]   contains_devanagari() + romanize_metadata_if_needed(): the
          Hinglish instruction for title/description/hashtags/tags can get
          diluted in a schema this dense (shot list + script +
          script_romanized + SEO metadata, each with detailed rules) - the
          model doesn't always follow every instruction with equal weight.
          This detects leftover Devanagari via a Unicode range check after
          generation and, if the per-story LLM call budget allows, runs ONE
          small focused follow-up call asking specifically to Hinglish-ify
          just the offending fields - cheaper and more likely to succeed
          than re-running the whole complex generation. Ships the original
          text if the cleanup call also fails or budget is exhausted,
          rather than losing the story.
  [CHANGED] TTS_RATE -> +30% (1.3x), requested explicitly. Flagged honestly
          in the constant's own comment: this is faster than the +8% that
          was already reported as sounding rushed/AI-ish, so it may make
          that specific complaint worse, not better - these are two
          different, somewhat competing asks (faster pacing vs. more
          natural-sounding), not a contradiction in the code.

--------------------------------------------------------------------------------
CHANGELOG round 8 - broadcast-style top banner (BREAKING NEWS badge +
dynamic topic ticker + channel tagline), scoped after a reference mockup
--------------------------------------------------------------------------------
  [ADD]   build_breaking_news_banner() + _fit_font() + _draw_text_centered():
          a persistent top-of-frame graphic on every video - red "BREAKING
          NEWS" badge + blue accent block, a full-width ticker bar showing
          THIS video's own topic (pkg.title, auto-shrinks to fit), and a
          fixed channel tagline bar underneath (CHANNEL_TAGLINE, env-
          overridable). Unlike everything else added this session, this was
          rendered STANDALONE and actually viewed as a PNG before being
          wired into the pipeline, specifically because a layout mistake
          here would be a lot more visible/embarrassing than a backend bug -
          worth the extra verification step this one time.
  [CHANGED] build_watermark_clip()'s vertical position now offsets below the
          new banner instead of the top-right corner it used before - the
          two would otherwise physically overlap on screen.
  [DECLINED, explained to the user rather than silently skipped] A
          photorealistic human AI news-anchor avatar (from the same
          reference mockup) was NOT built: (1) budget - that quality of
          avatar generation (HeyGen/Synthesia-tier) isn't available free;
          (2) more importantly, it directly conflicts with a rule already
          in SCRIPT_PROMPT_TEMPLATE - "never present the AI narration as a
          named real anchor" - a photorealistic fake anchor delivering
          "Breaking News" is a heavier version of exactly what that rule
          exists to prevent, not a lighter one.
  [DEFERRED] The reference mockup's multi-panel picture-in-picture mosaic
          (several clips composited simultaneously in a grid, each with its
          own label) was scoped OUT of this round on purpose - meaningfully
          more complex than a single persistent overlay (per-panel timing,
          borders, label sync), better attempted as its own focused pass
          once the banner is confirmed looking right on a real render.

--------------------------------------------------------------------------------
CHANGELOG round 9 - ACTUAL ROOT CAUSE of the box-rendering bug found and
fixed (it was never really about Devanagari), banner centered
--------------------------------------------------------------------------------
  [FIX, root cause] Boxes were appearing on BOTH the Hinglish captions AND
          the pure-English banner text ("BREAKING NEWS") - a real screenshot
          showed this after round 8. That combination was the tell: a
          missing-Devanagari-glyph problem could explain boxes on Hindi
          text, but not on plain English text too. Actual cause:
          find_caption_font() was still the SAME function used from when
          captions WERE Devanagari (rounds 1/6/7 fetched a font specifically
          for Devanagari coverage), and it kept being reused everywhere even
          after captions/title/banner switched to Hinglish (Roman script)
          in round 5 - the fetched font (openmaptiles/fonts'
          NotoSansDevanagari, a script-specific subset built for multi-font
          map-rendering pipelines) may carry no Latin glyphs at all. Any
          character missing from a font renders as a box - true of Hindi
          letters in a Latin-only font, equally true of English letters in a
          Devanagari-only font. Same failure mode, opposite direction from
          the bug fixed two rounds ago.
  [CHANGED] find_caption_font(need_devanagari: bool = False) - now defaults
          to a plain bold LATIN font already on the runner (DejaVu Sans
          Bold/Liberation Sans Bold - no download, nothing to get wrong),
          since that's what captions/banner/thumbnail need almost all the
          time post-Hinglish-switch. Devanagari coverage (the openmaptiles
          fetch) is now only requested for the rare per-story fallback case
          where build_romanized_word_timings() couldn't map that story's
          captions to Hinglish. build_romanized_word_timings() now returns
          (words, used_romanization) specifically so process_single_story
          can pick the right font for THIS story's actual outcome instead of
          assuming. Banner and thumbnail get their own guaranteed-Latin
          find_caption_font() call regardless of any single story's caption
          fallback status, since their text (title, tagline, "BREAKING
          NEWS") is always Roman either way.
  [CHANGED] Banner's "BREAKING NEWS" badge is now full-width and centered -
          was a 62%-width red block + blue filler on the right, which read
          as off-center/lopsided rather than centered. Re-rendered and
          viewed before shipping, same as round 8's original banner.

--------------------------------------------------------------------------------
CHANGELOG round 10 - optional Sarvam AI voice (more natural Hindi/Hinglish
TTS), tried first when configured, always falls back to edge-tts
--------------------------------------------------------------------------------
  [ADD]   synthesize_voice_with_timing_sarvam() + synthesize_voice_with_timing_smart():
          Sarvam's Bulbul v3 is purpose-built for Indian languages/accents
          (natural Hinglish code-switching, prosody, emotion) - a real step
          up from edge-tts specifically for this channel's needs, per the
          user's own research. Only gap: Sarvam's TTS response is audio
          only, no word-boundary timestamps the way edge-tts provides (which
          the whole caption-sync system depends on). Bridged by
          synthesizing via Sarvam TTS, then immediately running that SAME
          audio back through Sarvam's OWN speech-to-text (Saaras v3, which
          DOES return word-level timestamps) to recover per-word timing -
          alignment should be reliable since it's clean single-voice audio
          with no background noise, not real-world messy speech.
  [ADD]   SARVAM_API_KEY_INDIA (optional GitHub Secret, empty by default)
          and SARVAM_VOICE (env-overridable, default "roopa"). Presence of
          the key is the on/off switch - nothing changes for anyone who
          hasn't signed up for it. sarvam-ai added to both workflows' pip
          install line unconditionally (harmless if unused).
  [DEFENSIVE] synthesize_voice_with_timing_smart() tries Sarvam first only
          when the key is set, catches ANY exception from it (bad response
          shape, decode failure, self-transcription word-count sanity check
          failing), and falls back to edge-tts automatically - a Sarvam-side
          problem degrades to the proven voice instead of breaking the
          story. edge-tts remains the always-available, no-signup default.
  [HONEST COST NOTE] Sarvam is NOT unlimited-free like edge-tts - generous
          free credits on signup (roughly hundreds of thousands of
          characters, likely months of runway at 6 videos/day), then a
          small per-character cost after that. A real, small, ongoing cost
          if the free credits run out, not zero-budget-forever - flagged
          honestly rather than oversold, since that's a real departure from
          this whole project's zero-budget baseline.
  [UNVERIFIED LIVE] The exact Sarvam TTS/STT request/response shapes above
          are from current API docs and SDK examples, not a live test run
          (no network access while writing this) - same honesty standard as
          every other new external integration this session. Test with a
          real SARVAM_API_KEY_INDIA set and check the logs for "Sarvam TTS
          failed" warnings on the first run to confirm it's actually being
          used rather than silently falling back every time.

--------------------------------------------------------------------------------
CHANGELOG round 11 - Latin font install (real fix, not another guess this
time), voice +30%, music down further, tighter word-to-footage sync, new
slot times
--------------------------------------------------------------------------------
  [FIX] The round-9 Latin-font fix assumed DejaVu Sans Bold/Liberation Sans
          Bold/FreeSans Bold would already be present on the GitHub Actions
          runner, the same kind of pre-installed-font assumption that was
          already wrong once before (fonts-noto-core, round 6). Rather than
          keep guessing at what's already on the image, both workflow
          YAMLs' apt-get line now installs fonts-dejavu-core EXPLICITLY -
          deterministic (the step fails loudly if it can't install, instead
          of silently falling through to a missing font at render time)
          rather than assumed. If boxes are STILL happening after this on a
          verified-fresh run, that's a real, different bug worth a fresh
          screenshot - the find_caption_font()/build_romanized_word_timings()
          logic itself was traced end-to-end this round and is internally
          consistent (Latin words always paired with a Latin font call,
          Devanagari words always paired with a Devanagari font call, no
          path that can mismatch the two).
  [CHANGED] VOICE_VOLUME_BOOST = 1.3 (+30%, requested) applied via
          .volumex() on the final voice track - changes loudness only, not
          pitch/speed/timing, so it doesn't touch caption sync the way a
          naive whole-video speed change would. MUSIC_VOLUME lowered
          0.12 -> 0.07 (requested - quieter, further under the now-louder
          voice).
  [CHANGED] shot_list beat count raised from "4 to 7" to "7 to 12" (shorter
          beats, more of them) for tighter matching between what's being
          said and what's on screen. HONEST LIMIT: true word-by-word visual
          switching (a new clip on literally every spoken word) isn't
          implemented and isn't really practical - at ~90 words/video
          that's a fresh Pexels/AI-image fetch every ~0.35s, both far too
          slow to render and, more fundamentally, not how real video
          editing looks (cuts that fast read as chaotic, not synced). This
          is the practical version of the same request: several times more
          cut points than before, each still genuinely content-matched.
  [CHANGED] SLOT_WINDOWS updated to the newly requested times: ~7:30AM,
          ~9:00AM, ~11:11AM, ~1:40PM, 6:00-6:30PM (used as given, wider than
          the usual ~14min windows since an explicit range was specified),
          ~8:00PM IST.

--------------------------------------------------------------------------------
CHANGELOG round 12 - CRITICAL FIX: wrong PyPI package name was blocking
every single run at the dependency-install step (confirmed via a real
Actions failure log)
--------------------------------------------------------------------------------
  [FIX] round 10 added "sarvam-ai" (with a hyphen) to both workflows' pip
          install line - that PyPI package does not exist ("ERROR: Could
          not find a version that satisfies the requirement sarvam-ai" -
          confirmed from an actual failed run's log, not assumed). The
          code's own import statement was already correct
          (`from sarvamai import SarvamAI`, no hyphen, matching the real
          package). This was a pure pip-install-line typo, but a total one -
          it failed the "Install Python dependencies" step directly, before
          the pipeline script ever ran, so every run since round 10 failed
          immediately regardless of any other change. Fixed to `sarvamai`
          (no hyphen) here and in india_geo.yml.

--------------------------------------------------------------------------------
ENVIRONMENT SETUP
--------------------------------------------------------------------------------
!apt-get update && apt-get install -y ffmpeg fonts-noto-core fonts-dejavu-core
!pip install -q feedparser openai edge-tts "moviepy==1.0.3" pillow numpy requests sarvamai \
    google-api-python-client google-auth-oauthlib google-auth-httplib2

--------------------------------------------------------------------------------
YOUTUBE OAUTH SETUP (one-time, required before the first upload - use the NEW
India channel's Google account, NOT the US channel's)
--------------------------------------------------------------------------------
RECOMMENDED for CI (GitHub Actions) - OAuth Playground, no local script run:
1. In Google Cloud Console, create an OAuth Client ID of type "Web application"
   for a project with the YouTube Data API v3 enabled. Add
   `https://developers.google.com/oauthplayground` as an Authorized redirect URI.
   Note the Client ID and Client Secret.
2. Go to https://developers.google.com/oauthplayground, click the gear icon
   (top right) and check "Use your own OAuth credentials" - paste your Client
   ID and Client Secret there.
3. In the left panel, find "YouTube Data API v3" and select the
   `https://www.googleapis.com/auth/youtube.upload` scope. Click "Authorize
   APIs", sign in with the INDIA channel's Google account, allow access.
4. Click "Exchange authorization code for tokens" - copy the Refresh Token.
5. Set these GitHub Secrets: NVIDIA_API_KEY_INDIA, PEXELS_API_KEY_INDIA,
   TELEGRAM_BOT_TOKEN_INDIA, TELEGRAM_CHAT_ID_INDIA, YOUTUBE_CLIENT_ID_INDIA,
   YOUTUBE_CLIENT_SECRET_INDIA, YOUTUBE_REFRESH_TOKEN_INDIA.

ALTERNATIVE for local use - browser consent flow:
1. Create an OAuth Client ID of type "Desktop app" instead, download it as
   `client_secrets_india.json` next to this script.
2. Run this script ONCE on a machine with a browser (it opens a consent
   screen via `run_local_server`), which creates `youtube_token_india.json`.
   Copy that token file alongside the script wherever you run it afterward -
   it auto-refreshes. (Not used if the seven env vars above are set.)

RUN:
    python news_to_video_india.py

Only the CONFIGURATION block below needs editing.
================================================================================
"""

import os
import re
import sys
import json
import base64
import time
import html
import random
import difflib
import asyncio
import logging
import tempfile
import textwrap
import traceback
import subprocess
import concurrent.futures
from urllib.parse import quote as _urlquote
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple, Set

import requests
import feedparser
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Compatibility shim: Pillow >= 10 removed the legacy Image.ANTIALIAS alias
# (replaced by Image.Resampling.LANCZOS), but moviepy 1.0.x's built-in
# clip.resize() effect still references Image.ANTIALIAS internally on its
# pure-PIL fallback path (used whenever OpenCV isn't installed - which is
# our case, we don't install cv2). Without this shim, crop_and_resize_9x16()
# crashes on every single background segment with "module 'PIL.Image' has
# no attribute 'ANTIALIAS'", which cascades into build_background_video()
# raising "Failed to build any usable video segments" and a 0-video batch.
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

import edge_tts
from openai import OpenAI

from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    CompositeVideoClip,
    CompositeAudioClip,
    ImageClip,
    concatenate_videoclips,
    concatenate_audioclips,
    vfx,
)

try:
    from zoneinfo import ZoneInfo
except ImportError:  # Python < 3.9
    from backports.zoneinfo import ZoneInfo  # pip install backports.zoneinfo

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request as GoogleAuthRequest
from googleapiclient.discovery import build as build_google_service
from googleapiclient.http import MediaFileUpload

# ==============================================================================
# 1. CONFIGURATION  --  REPLACE THESE VALUES
# ==============================================================================
# Every value below can be overridden by an environment variable of the same
# name (falls back to the hardcoded placeholder if the env var isn't set).
# This lets the exact same file run unmodified locally/Colab (edit the
# strings directly) or in CI such as GitHub Actions (set repo secrets as env
# vars - nothing in this file needs to change or be patched at deploy time).
NVIDIA_API_KEY       = os.environ.get("NVIDIA_API_KEY_INDIA", "YOUR_NVIDIA_API_KEY")
# Optional: purpose-built Indian-language TTS (Sarvam Bulbul v3) as a more
# natural-sounding alternative to edge-tts, tried first when set - see
# synthesize_voice_with_timing_smart(). Empty by default, so this changes
# nothing for anyone who hasn't explicitly signed up and set it.
SARVAM_API_KEY       = os.environ.get("SARVAM_API_KEY_INDIA", "")
PEXELS_API_KEY        = os.environ.get("PEXELS_API_KEY_INDIA", "YOUR_PEXELS_API_KEY")
TELEGRAM_BOT_TOKEN    = os.environ.get("TELEGRAM_BOT_TOKEN_INDIA", "YOUR_TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID      = os.environ.get("TELEGRAM_CHAT_ID_INDIA", "YOUR_TELEGRAM_CHAT_ID")

YOUTUBE_CLIENT_SECRETS_FILE = os.environ.get("YOUTUBE_CLIENT_SECRETS_FILE", "client_secrets_india.json")
YOUTUBE_TOKEN_FILE          = os.environ.get("YOUTUBE_TOKEN_FILE", "youtube_token_india.json")

# Preferred auth method for CI (GitHub Actions): a refresh token obtained
# once via Google's OAuth Playground (https://developers.google.com/oauthplayground)
# - no local browser flow or token file needed at all. If all three of these
# are set, get_youtube_service() uses them directly and skips the file-based
# flow below entirely.
YOUTUBE_CLIENT_ID           = os.environ.get("YOUTUBE_CLIENT_ID_INDIA", "")
YOUTUBE_CLIENT_SECRET       = os.environ.get("YOUTUBE_CLIENT_SECRET_INDIA", "")
YOUTUBE_REFRESH_TOKEN       = os.environ.get("YOUTUBE_REFRESH_TOKEN_INDIA", "")

# In CI (e.g. GitHub Actions cron), set this to 0 via the AUTO_LOOP_INTERVAL_HOURS
# env var - the scheduler triggers a fresh run, so the script should do ONE
# batch and exit, not sleep in a loop (which would just get killed at the
# job timeout and waste runner minutes for nothing).
AUTO_LOOP_INTERVAL_HOURS = int(os.environ.get("AUTO_LOOP_INTERVAL_HOURS", "24"))
# Suffixed _india vs the US pipeline's processed_news.txt/queued_news.txt/
# pending_youtube_uploads.txt - these get committed back to the shared git
# repo, so distinct names are required to avoid the two pipelines' dedup/
# queue/retry state silently colliding on every commit.
PROCESSED_NEWS_FILE      = "processed_news_india.txt"
QUEUED_NEWS_FILE         = "queued_news_india.txt"
PENDING_YOUTUBE_UPLOADS_FILE = "pending_youtube_uploads_india.txt"   # stories rendered OK but whose YouTube upload failed
DECISION_LOG_FILE            = "decisions_log_india.jsonl"   # structured, persistent record of what happened to each story and why - outlives GitHub Actions' ~90-day run-log retention

# ------------------------------------------------------------------------------
# Tuning knobs (safe to leave as-is)
# ------------------------------------------------------------------------------
# India/Hindi Google News edition (hl=hi-IN&gl=IN&ceid=IN:hi). UNVERIFIED live -
# no network access while forking this file. If scan_fresh_candidates() logs
# "Found 0 fresh whitelisted candidate(s)", check these feeds first (this is
# exactly the failure mode the US pipeline hit once with the wrong feed URL).
def _state_feed_url(query: str) -> str:
    return f"https://news.google.com/rss/search?q={_urlquote(query)}&hl=hi-IN&gl=IN&ceid=IN:hi"


# All 28 states + 8 union territories - every region gets its own feed rather
# than one combined OR-query, so a quiet day for a small state doesn't get
# drowned out by a busy day in a big one (see the round-robin merge in
# scan_fresh_candidates). A couple of major cities are OR'd into their
# state's query since that's how they're more often named in headlines.
# Defined as names, not hand-typed URLs, so adding/removing coverage later is
# a one-line change here instead of hunting through 36 literal URL strings.
INDIA_STATES_AND_UTS = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
    "Karnataka OR Bengaluru", "Kerala", "Madhya Pradesh",
    "Maharashtra OR Mumbai", "Manipur", "Meghalaya", "Mizoram", "Nagaland",
    "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu OR Chennai",
    "Telangana OR Hyderabad", "Tripura", "Uttar Pradesh", "Uttarakhand",
    "West Bengal OR Kolkata",
    "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu", "Delhi OR NCR",
    "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
]

NEWS_RSS_FEEDS = [
    # General India top-stories / trending feed
    "https://news.google.com/rss?hl=hi-IN&gl=IN&ceid=IN:hi",
    # World / geopolitics topic feed
    "https://news.google.com/rss/headlines/section/topic/WORLD?hl=hi-IN&gl=IN&ceid=IN:hi",
    # Targeted search: geopolitics / diplomacy / India foreign policy
    "https://news.google.com/rss/search?q=geopolitics%20OR%20diplomacy%20OR%20%22foreign%20policy%22%20India&hl=hi-IN&gl=IN&ceid=IN:hi",
    # Targeted search: India's strategic neighborhood - diplomatic/trade/border
    # framing, not raw conflict footage (kept deliberately narrow, see
    # SCRIPT_PROMPT_TEMPLATE's fact-check/compliance gate below)
    "https://news.google.com/rss/search?q=India%20Pakistan%20OR%20India%20China%20OR%20border%20OR%20%22trade%20deal%22&hl=hi-IN&gl=IN&ceid=IN:hi",
] + [_state_feed_url(name) for name in INDIA_STATES_AND_UTS]
# Kept for backward compatibility (e.g. NEWS_RSS_URL env override still works and
# is folded into the feed list below) - prefer editing NEWS_RSS_FEEDS directly.
NEWS_RSS_URL = os.environ.get("NEWS_RSS_URL", "")
if NEWS_RSS_URL and NEWS_RSS_URL not in NEWS_RSS_FEEDS:
    NEWS_RSS_FEEDS.insert(0, NEWS_RSS_URL)
NVIDIA_MODEL                 = os.environ.get("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct")
NVIDIA_BASE_URL               = "https://integrate.api.nvidia.com/v1"  # fixed NVIDIA NIM endpoint, not a secret
TTS_VOICE                   = os.environ.get("TTS_VOICE", "hi-IN-MadhurNeural")    # or "hi-IN-SwaraNeural" (female) - override via env var to A/B test without editing code
SARVAM_VOICE                 = os.environ.get("SARVAM_VOICE", "roopa")    # bulbul:v3 Hindi speaker - see the full speaker list in synthesize_voice_with_timing_sarvam's docstring
TTS_RATE                    = "+30%"    # 1.3x - requested explicitly. NOTE: this is now FASTER than the +8% that was already flagged as sounding rushed/AI-ish - if it sounds worse, not better, this is why; ease back toward +10-15% if so
VIDEO_WIDTH                 = 1080
VIDEO_HEIGHT                 = 1920
CLIP_SEGMENT_MIN_SEC        = 2.0
CLIP_SEGMENT_MAX_SEC        = 3.0
PEXELS_RESULTS_PER_QUERY    = 5
MAX_BACKGROUND_CLIPS        = 10
WORDS_PER_CAPTION_CHUNK     = 4
OUTPUT_DIR                  = os.path.join(os.getcwd(), "output")
TEMP_DIR                    = tempfile.mkdtemp(prefix="n2v_")
MAX_LLM_RETRIES          = 3        # malformed-JSON / API-error retries, per single generate_script_package() call
MAX_DURATION_RETRIES        = 3        # outer duration-enforcement rewrite attempts, per story
MAX_LLM_CALLS_PER_CYCLE  = 6        # hard cap on NVIDIA LLM calls for ONE story's script generation
LLM_MIN_INTERVAL_SEC     = 4.5      # min seconds between consecutive NVIDIA LLM calls (free-tier RPM safety margin)
MAX_FEED_ENTRIES_SCANNED    = 40       # how many RSS entries to scan when building the candidate pool
REQUEST_TIMEOUT             = 60
TARGET_MIN_SEC               = 30.0
TARGET_MAX_SEC               = 40.0
FUZZY_DEDUP_THRESHOLD         = 0.82
FUZZY_DEDUP_MAX_COMPARE       = 500
DEBUG_RSS_STRUCTURE           = True

DAILY_STORY_TARGET          = 6        # videos produced per daily batch (was 3 - doubled for the 6-slot schedule)
MAX_CANDIDATES_TO_SCORE     = 35       # cap on candidates sent to the single ranking NVIDIA LLM call (raised again - 40 feeds now, up from 4)
MAX_DAILY_ATTEMPTS          = 12       # safety cap on total stories attempted in one batch (incl. fact-check skips) - kept at 2x DAILY_STORY_TARGET, same ratio as before

YOUTUBE_TIME_ZONE            = "Asia/Kolkata"     # IST, no DST (zoneinfo handles it either way)
# Each slot is a (start_hour, start_minute, end_hour, end_minute) window in local
# time; compute_slot_datetime() picks a random minute inside the window each time,
# so scheduled times vary day to day instead of always landing on the dot - kept
# deliberately NARROW (10-15 min) around each requested time rather than collapsed
# to one fixed HH:MM, so the schedule still isn't perfectly robotic day to day.
SLOT_WINDOWS = [
    (7, 23, 7, 37),     # Slot 1: ~7:30 AM
    (8, 53, 9, 7),      # Slot 2: ~9:00 AM
    (11, 4, 11, 18),    # Slot 3: ~11:11 AM
    (13, 33, 13, 47),   # Slot 4: ~1:40 PM
    (18, 0, 18, 30),    # Slot 5: 6:00-6:30 PM (given as an explicit range, so used as-is rather than narrowed)
    (19, 53, 20, 7),    # Slot 6: ~8:00 PM
]
SLOT_MIN_LEAD_MINUTES        = 20      # don't schedule inside a window that ends within this many minutes (rolls to next day)
YOUTUBE_CATEGORY_ID          = "25"    # News & Politics

# ------------------------------------------------------------------------------
# Polish: background music, transitions, and channel branding (all optional -
# every one of these degrades gracefully to "skip it" if the asset is missing,
# so the pipeline never breaks because a music folder or logo isn't set up yet)
# ------------------------------------------------------------------------------
MUSIC_DIR                    = os.environ.get("MUSIC_DIR", "music")   # put your own royalty-free .mp3/.wav tracks here
VOICE_VOLUME_BOOST            = 1.3     # +30% - requested; volumex changes loudness only, not pitch/duration/timing (unlike a naive speed-change), so caption sync is unaffected
MUSIC_VOLUME                 = 0.07    # was 0.12 - lowered further per request; now noticeably further under the (now louder) voice
CROSSFADE_DURATION           = 0.35    # seconds of crossfade between background clips
ENABLE_KEN_BURNS             = True    # subtle continuous zoom-in per background segment
KEN_BURNS_ZOOM_AMOUNT        = 0.06    # max zoom over a segment's duration (0.06 = 6%)
COLOR_GRADE_SATURATION       = 1.08    # >1.0 = more saturated; consistent "look" across videos
COLOR_GRADE_CONTRAST         = 0       # moviepy vfx.lum_contrast contrast parameter - see WARNING below
LOGO_PATH                    = os.environ.get("LOGO_PATH", os.path.join("assets", "logo.png"))  # transparent PNG, put your own here
WATERMARK_WIDTH_RATIO        = 0.16    # logo width as a fraction of video width
WATERMARK_OPACITY            = 0.55
INTRO_STING_DURATION         = 0.8     # seconds; added ON TOP of the 30-40s main content
MAX_YOUTUBE_UPLOAD_RETRIES   = 5       # cap on daily retry attempts for a failed upload before it's dropped from the pending queue

# Authoritative source whitelist: domain -> list of name fragments as they may
# appear in the RSS <source> tag or in the "Headline - Source Name" suffix.
SOURCE_WHITELIST: Dict[str, List[str]] = {
    # India - general / trending news
    "timesofindia.indiatimes.com": ["times of india", "toi"],
    "indiatoday.in": ["india today"],
    "news18.com": ["news18"],
    "ndtv.com": ["ndtv"],
    "hindustantimes.com": ["hindustan times"],
    "indianexpress.com": ["indian express"],
    "thehindu.com": ["the hindu"],
    # India - geopolitics / strategic affairs focus
    "wionews.com": ["wion"],
    "aninews.in": ["ani", "asian news international"],
    # International wire / geopolitics (objective, non-graphic framing)
    "reuters.com": ["reuters"],
    "apnews.com": ["associated press", "ap news"],
    "bbc.com": ["bbc"],
    "aljazeera.com": ["al jazeera"],
    # Strong regional/state bureau coverage across India specifically
    "abplive.com": ["abp live", "abp"],
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("news2video")

_rss_debug_dumped = False
_last_llm_call_ts = 0.0


# ==============================================================================
# 2. DATA MODELS
# ==============================================================================
@dataclass
class NewsItem:
    title: str
    summary: str
    link: str
    source_name: str


@dataclass
class ScriptBeat:
    phrase: str                       # excerpt of script_en (Hindi) this beat roughly covers
    visual: str                       # SIMPLE ENGLISH, India-contextualized visual description
    prefer_ai_generation: bool = False  # True for concepts real stock footage won't have (deities, festivals, specific local culture)


@dataclass
class ScriptPackage:
    script_en: str
    script_romanized: str
    title: str
    description: str
    hashtags: List[str]
    tags: List[str]
    thumbnail_idea: str
    visual_keywords: List[str] = field(default_factory=list)
    shot_list: List[ScriptBeat] = field(default_factory=list)
    is_credible: bool = True
    credibility_note: str = ""


@dataclass
class WordTiming:
    text: str
    start: float
    end: float


@dataclass
class CaptionChunk:
    text: str
    start: float
    end: float


class CredibilitySkipError(Exception):
    def __init__(self, note: str):
        super().__init__(note)
        self.note = note


class LLMCallBudget:
    def __init__(self, max_calls: int):
        self.max_calls = max_calls
        self.used = 0

    def consume(self) -> bool:
        if self.used >= self.max_calls:
            return False
        self.used += 1
        return True

    def remaining(self) -> int:
        return max(0, self.max_calls - self.used)


# ==============================================================================
# 3. CONFIG VALIDATION
# ==============================================================================
def validate_config() -> None:
    placeholders = {
        "NVIDIA_API_KEY": NVIDIA_API_KEY,
        "PEXELS_API_KEY": PEXELS_API_KEY,
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
    }
    missing = [k for k, v in placeholders.items() if not v or v.startswith("YOUR_")]
    if missing:
        raise ValueError(
            "Config error - replace these at the top of the script before running: "
            + ", ".join(missing)
        )
    if not (YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET and YOUTUBE_REFRESH_TOKEN) and not os.path.exists(YOUTUBE_CLIENT_SECRETS_FILE):
        log.warning(
            "  No YouTube credentials found (neither YOUTUBE_CLIENT_ID/SECRET/REFRESH_TOKEN env vars "
            f"nor a '{YOUTUBE_CLIENT_SECRETS_FILE}' file) - YouTube uploads will be skipped "
            "(video still renders and goes to Telegram). See the OAuth setup notes at the top of this file."
        )


# ==============================================================================
# 4. NEWS: WHITELIST FILTER, DEDUP, CANDIDATE SCAN, QUEUE PERSISTENCE
# ==============================================================================
def _strip_html(raw: str) -> str:
    text = re.sub(r"<[^>]+>", " ", raw or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _normalize_headline(title: str) -> str:
    t = title.lower().strip()
    t = re.sub(r"[^\w\s]", "", t)
    t = re.sub(r"\s+", " ", t)
    return t


def load_processed_headlines(path: str = PROCESSED_NEWS_FILE) -> List[str]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [_normalize_headline(line) for line in f if line.strip()]


def mark_headline_processed(title: str, path: str = PROCESSED_NEWS_FILE) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(title.strip() + "\n")


def log_decision(event: str, title: str, detail: str = "") -> None:
    """Structured, persistent record of what happened to each story and why -
    committed to git alongside the other state files (see the workflow's
    persist-state step), so it survives past GitHub Actions' ~90-day run-log
    retention and is greppable/JSON-parseable instead of buried in free-text
    logs. Never allowed to break the pipeline - a logging failure is not a
    reason to fail a story that otherwise succeeded."""
    try:
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "title": title[:120],
            "detail": detail[:200],
        }
        with open(DECISION_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        log.warning(f"  Could not write decision log entry: {e}")


def is_duplicate_headline(title: str, processed_normalized: List[str]) -> bool:
    norm = _normalize_headline(title)
    if norm in processed_normalized:
        return True
    window = processed_normalized[-FUZZY_DEDUP_MAX_COMPARE:]
    for prev in window:
        if difflib.SequenceMatcher(None, norm, prev).ratio() >= FUZZY_DEDUP_THRESHOLD:
            return True
    return False


def load_queue(path: str = QUEUED_NEWS_FILE) -> List[NewsItem]:
    if not os.path.exists(path):
        return []
    items: List[NewsItem] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                items.append(NewsItem(
                    title=d["title"], summary=d.get("summary", ""),
                    link=d.get("link", ""), source_name=d.get("source_name", ""),
                ))
            except Exception as e:
                log.warning(f"  Skipping malformed queue line: {e}")
    return items


def save_queue(items: List[NewsItem], path: str = QUEUED_NEWS_FILE) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps({
                "title": it.title, "summary": it.summary,
                "link": it.link, "source_name": it.source_name,
            }, ensure_ascii=False) + "\n")


def _debug_dump_entry(entry) -> None:
    global _rss_debug_dumped
    if _rss_debug_dumped:
        return
    _rss_debug_dumped = True
    try:
        src = getattr(entry, "source", None)
        log.info("  [DEBUG] Sample RSS entry structure (first scanned item this process):")
        log.info(f"    title        = {getattr(entry, 'title', None)!r}")
        log.info(f"    link         = {str(getattr(entry, 'link', None))[:90]!r}")
        if src is not None:
            log.info(f"    source.title = {getattr(src, 'title', None)!r}")
            log.info(f"    source.href  = {getattr(src, 'href', None)!r}")
        else:
            log.info("    source       = <not present on this entry - title-suffix fallback will be used>")
        log.info("    (Set DEBUG_RSS_STRUCTURE = False once verified, to reduce log noise.)")
    except Exception as e:
        log.warning(f"  [DEBUG] entry dump failed (non-fatal): {e}")


def _extract_source_name(entry) -> str:
    src = getattr(entry, "source", None)
    if src is not None:
        title = getattr(src, "title", None)
        if not title and isinstance(src, dict):
            title = src.get("title")
        if title:
            return str(title).strip()
    raw_title = getattr(entry, "title", "") or ""
    if " - " in raw_title:
        return raw_title.rsplit(" - ", 1)[-1].strip()
    return ""


def _is_whitelisted_source(source_name: str, link: str) -> bool:
    """Primary signal is source_name; the link-domain check is a harmless
    secondary signal only (Google News RSS `link` values are normally
    redirect blobs, not the publisher's real domain). Verify with
    DEBUG_RSS_STRUCTURE=True on first run."""
    name_lower = (source_name or "").lower()
    link_lower = (link or "").lower()
    for domain, fragments in SOURCE_WHITELIST.items():
        if domain in link_lower:
            return True
        for frag in fragments:
            if frag in name_lower:
                return True
    return False


def _fetch_one_feed(feed_url: str):
    """Fetches+parses a single RSS feed with an explicit timeout via requests
    - feedparser's own URL-fetching path doesn't reliably respect
    REQUEST_TIMEOUT, which matters a lot now that NEWS_RSS_FEEDS has 40
    entries: one slow/hung feed must not be able to stall the whole batch."""
    try:
        resp = requests.get(feed_url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return feed_url, feedparser.parse(resp.content)
    except Exception as e:
        log.warning(f"  Failed to fetch/parse feed '{feed_url}': {e}")
        return feed_url, None


def scan_fresh_candidates(
    processed_normalized: List[str],
    exclude_items: List[NewsItem],
    max_count: int = MAX_CANDIDATES_TO_SCORE,
) -> List[NewsItem]:
    """Scans EVERY feed in NEWS_RSS_FEEDS (national trending/geopolitics +
    one feed per covered state/UT - 40 feeds total) for fresh, whitelisted
    headlines not already in the processed log or in the current
    queue/exclude list.

    Two things changed once the feed list grew from 4 to 40:
    1. Fetches now run in parallel (ThreadPoolExecutor) instead of one at a
       time - sequential fetching of 40 feeds would mean one slow feed
       delays every feed after it. Each fetch still has its own
       REQUEST_TIMEOUT ceiling.
    2. The merge is a round-robin across feeds, in a freshly SHUFFLED order
       each run, instead of walking NEWS_RSS_FEEDS in its fixed list order.
       The old fixed-order walk would let the first few (highest-volume,
       usually national) feeds fill max_count before ever reaching a
       smaller state's feed - shuffling means which feeds get first pick
       varies day to day, so coverage evens out across runs instead of a
       handful of feeds permanently crowding out the rest.
    """
    log.info(f"Scanning {len(NEWS_RSS_FEEDS)} Google News RSS feed(s) for fresh, whitelisted candidate headlines ...")
    exclude_norm = [_normalize_headline(it.title) for it in exclude_items]

    fetched: Dict[str, object] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(16, len(NEWS_RSS_FEEDS))) as pool:
        for feed_url, feed in pool.map(_fetch_one_feed, NEWS_RSS_FEEDS):
            if feed is not None:
                if feed.entries:
                    fetched[feed_url] = feed.entries[:MAX_FEED_ENTRIES_SCANNED]
                else:
                    log.warning(f"  Feed returned no entries: {feed_url}")

    feed_order = list(fetched.keys())
    random.shuffle(feed_order)

    results: List[NewsItem] = []
    seen_norm_titles: List[str] = []
    max_len = max((len(v) for v in fetched.values()), default=0)

    for i in range(max_len):
        if len(results) >= max_count:
            break
        for feed_url in feed_order:
            if len(results) >= max_count:
                break
            entries = fetched[feed_url]
            if i >= len(entries):
                continue
            entry = entries[i]

            if DEBUG_RSS_STRUCTURE:
                _debug_dump_entry(entry)

            title = _strip_html(getattr(entry, "title", "")).strip()
            if not title or len(title) < 5:
                continue
            if (is_duplicate_headline(title, processed_normalized)
                    or is_duplicate_headline(title, exclude_norm)
                    or is_duplicate_headline(title, seen_norm_titles)):
                continue

            source_name = _extract_source_name(entry)
            link = getattr(entry, "link", "")
            if not _is_whitelisted_source(source_name, link):
                continue

            summary = _strip_html(getattr(entry, "summary", "")).strip()
            if not summary or summary == title:
                summary = title

            results.append(NewsItem(title=title, summary=summary, link=link, source_name=source_name))
            seen_norm_titles.append(_normalize_headline(title))

    log.info(f"  Found {len(results)} fresh whitelisted candidate(s) across all feeds.")
    return results


# ==============================================================================
# 5. NVIDIA LLM: CANDIDATE RANKING (1 call) + FACT-CHECK/SCRIPT (per story)
# ==============================================================================
SCORING_PROMPT_TEMPLATE = """You are a viral news content strategist for a short-form
Hindi-language YouTube Shorts channel covering trending/viral India news (national AND
state/regional - e.g. West Bengal/Kolkata, Mumbai/Maharashtra, Delhi, Punjab, Kerala) and
global geopolitics, for a general Indian audience.

Rank the following candidate news stories by viral potential for a short-form video
(curiosity, surprise, relevance/shareability for an Indian audience). Prefer a clear,
objective news hook over speculation or one-sided political framing.

STORIES:
{numbered_list}

Respond ONLY with a valid JSON array, one object per story, in this exact form:
[{{"index": 0, "virality_score": 7, "reason": "one short phrase"}}, ...]
Include every index from 0 to {max_index} exactly once. virality_score is an integer 1-10.
"""

SCRIPT_PROMPT_TEMPLATE = """You are an expert Hindi-language scriptwriter and news analyst
for an Indian YouTube Shorts / Instagram Reels channel covering trending viral news -
national AND state/regional (e.g. West Bengal/Kolkata, Mumbai/Maharashtra, Delhi, Punjab,
Kerala, and other states as they trend) - plus global geopolitics, for a general Indian
audience.

ROLE 1 - FACT-CHECKER & COMPLIANCE GATE: Judge whether this headline/context is a
credible, verifiable news story (as opposed to an unverified rumor, propaganda, or
baseless clickbait). Also set is_credible to false if the story is primarily about an
active war, terrorist attack, mass-casualty event, or other acute crisis where objective,
non-graphic, non-exploitative coverage isn't realistically possible from a short RSS
summary alone - skip it rather than risk sensationalizing it. This channel needs to stay
monetization-safe, so when in doubt about a sensitive/violent event, mark it not credible.

ROLE 2 - SCRIPTWRITER: If credible, write a 30-40 second vertical video script package
that is attractive, curiosity-driven, and SEO-friendly - optimized to stop the scroll and
rank in search - while staying factual.

NEWS HEADLINE: {title}
NEWS SOURCE: {source_name}
NEWS CONTEXT: {summary}
{feedback_block}
Respond ONLY with a single valid JSON object (no markdown fences, no commentary) with
EXACTLY these keys:

{{
  "is_credible": true or false,
  "credibility_note": "One short sentence in English explaining the credibility judgement.",
  "script_en": "The full spoken voiceover script, in natural, conversational, spoken HINDI
      (Devanagari script - NOT Hinglish/Latin transliteration here, even though several
      other fields below ARE Hinglish. This exact field feeds text-to-speech directly -
      the hi-IN voice needs Devanagari to pronounce Hindi correctly; Roman-script input
      would be read back with English pronunciation rules and sound wrong). STRICTLY 80
      to 100 Hindi words so spoken audio lands between 30 and 40 seconds. Structure
      internally as: (0-3s) a scroll-stopping, curiosity-driven HOOK; (3-25s) fast-paced
      storytelling that keeps SUSPENSE and curiosity high - withhold the key detail/twist
      a beat longer than feels natural, written so the visual background could reasonably
      cut to something new every 2-3 seconds; (25-35s) a distinct ANALYSIS beat in your own
      words - for a geopolitics/national story, explain what this means for India (bharat
      ke liye iska kya matlab hai); for a state/regional story, explain why it actually
      matters or what happens next for the people affected - either way this must read as
      genuine original commentary, not a repeated fact from the hook, and must not be
      one-sided political propaganda for or against any party, state, country, or group;
      (last 3-5s) a punchy call-to-action in Hindi telling viewers to like the video and
      subscribe. If the topic involves conflict or tragedy, stay factual and measured - no
      glorifying, mocking, or graphic language. Do NOT include stage directions,
      timestamps, or brackets - only words to be spoken aloud. If is_credible is false,
      still fill this with an empty string.",
  "script_romanized": "The EXACT SAME content as script_en, word for word, in the SAME
      ORDER, but spelled in Hinglish - Hindi words written in plain ENGLISH/ROMAN letters
      the way people actually type on WhatsApp/Instagram, NOT Devanagari, NOT a formal
      academic transliteration scheme with special marks. Match this natural, casual
      spelling style exactly - e.g. 'mere pas khuchvi nehi hay sab kuch khatam ho geya',
      'tum aj khubsurat lakhreheo', 'mere ko jorose vukh lagra hay'. CRITICAL: this must
      have the EXACT SAME NUMBER OF WORDS as script_en, one Roman word per Devanagari word
      in the same reading order - this drives the on-screen caption timing, so a mismatched
      word count breaks the captions for this video. If is_credible is false, still fill
      this with an empty string.",
  "title": "A highly attractive, curiosity-driven, clickbait-style video title in
      HINGLISH (Hindi words in Roman/English letters, same natural casual spelling style
      as script_romanized - NOT Devanagari) with 1-3 emojis - optimized to stop the scroll
      AND to match what someone would actually type into YouTube search for this story
      (people typing on a phone keyboard searching Hindi news very often type in Roman
      letters, not Devanagari - this directly helps search discovery, not just Shorts-feed
      virality). Still accurate to the story.",
  "description": "An attractive, SEO-optimized description (2-4 sentences) for YT
      Shorts, in HINGLISH (Roman letters, same style as above), written to rank in
      YouTube search for this story's topic and named entities (people, places, event).",
  "hashtags": ["10 to 15 high-ranking, SEO-friendly hashtags as strings, each starting
      with #, in Hinglish/Roman letters plus a few plain English ones for reach, covering
      the specific topic/place/people in this story as well as general ones, e.g.
      #Shorts, #IndiaNews, #Trending, #Bharat, plus story-specific ones (a state name, an
      event name, etc. in Roman letters)"],
  "tags": ["10 to 15 plain SEO keyword phrases (no #) for the YouTube tags box - Hinglish
      (Roman letters) plus English, matching real search queries someone would actually
      type for this exact story - specific names/places/events, not just generic terms"],
  "thumbnail_idea": "One concise sentence (in English, for your own production reference)
      describing a scroll-stopping, clickbait-style thumbnail visual concept.",
  "visual_keywords": ["4 to 6 SIMPLE ENGLISH keywords/phrases describing generic stock
      footage OR a generic AI-generated image that would visually match this story (e.g.
      'city skyline aerial', 'flags waving', 'government building exterior', 'world map
      globe', 'diplomatic handshake silhouette'). Generic and symbolic, NEVER a proper
      noun or a specific real person's name/likeness - this also feeds an AI-image
      fallback when stock footage search comes up empty, and generating a specific real
      person's face/likeness is exactly the kind of thing to avoid. Always in English
      regardless of script language."],
  "shot_list": [{{"phrase": "a short excerpt of script_en (Hindi) that this beat
      covers, roughly in reading order", "visual": "SIMPLE ENGLISH description of the
      SPECIFIC visual for exactly this moment - be SPECIFIC and CONTEXTUALIZED to the
      actual place in this beat, not generic: if this beat is genuinely ABOUT a specific
      NAMED FOREIGN COUNTRY/region (a global geopolitics story - e.g. this beat is about
      Spain, or China, or the US), describe THAT country's own recognizable context (e.g.
      'Madrid Spain city street', 'Beijing China skyline') - do not force Indian imagery
      onto a story that isn't about India. For every other beat (which is most of them,
      since this channel is India-first), default to INDIA: if the phrase mentions
      police, say 'Indian police officer in uniform' not just 'police'; if it names a
      festival or deity (Durga Puja, Ganesh Chaturthi, etc.), say the actual deity/
      festival imagery (e.g. 'Durga idol Hindu festival pandal'); if it names a specific
      Indian state or city, describe THAT place's recognizable culture, landmark, or map
      outline (e.g. 'Kerala backwaters houseboat', 'Punjab wheat fields Golden Temple',
      'West Bengal Howrah bridge Kolkata'); otherwise a generic but still India-set visual
      ('Indian government building exterior', 'Indian city street traffic') - never a
      specific real named person's face/likeness", "prefer_ai_generation": true if this is
      a specific cultural/religious/regional concept real stock footage is unlikely to
      have (a deity, a festival, a specific local landmark or tradition), false if it's a
      generic scene stock footage realistically has (traffic, a building, a crowd, a
      flag)}}] - 7 to 12 beats (more, shorter beats than before - tighter matching between
      what's being said and what's on screen) covering script_en roughly start to end in
      order. This drives WHICH footage shows WHEN; visual_keywords above is only used as a
      whole-story fallback if a usable shot_list can't be produced."
}}

Rules:
- script_en must be natural spoken Hindi in Devanagari script, energetic but credible
  news-analysis tone, no unexplained jargon.
- Never present the AI/automated narration as a named real anchor or "expert" - it should
  read as channel commentary, not impersonation.
- Output must be valid JSON only.
"""


def _extract_json_block(raw_text: str) -> str:
    text = raw_text.strip()
    text = re.sub(r"^```(json)?", "", text.strip(), flags=re.IGNORECASE).strip()
    text = re.sub(r"```$", "", text.strip()).strip()
    match = re.search(r"[\[{][\s\S]*[\]}]", text)
    if not match:
        raise ValueError("No JSON object/array found in NVIDIA LLM response.")
    return match.group(0)


def _llm_pace() -> None:
    global _last_llm_call_ts
    elapsed = time.time() - _last_llm_call_ts
    if elapsed < LLM_MIN_INTERVAL_SEC:
        time.sleep(LLM_MIN_INTERVAL_SEC - elapsed)
    _last_llm_call_ts = time.time()


def _build_nvidia_client() -> OpenAI:
    """NVIDIA NIM exposes an OpenAI-compatible endpoint, so the official
    `openai` SDK works unmodified - only base_url + api_key differ from
    talking to OpenAI directly."""
    return OpenAI(base_url=NVIDIA_BASE_URL, api_key=NVIDIA_API_KEY)


def score_candidate_stories(candidates: List[NewsItem]) -> List[Tuple[NewsItem, int]]:
    """Single NVIDIA LLM call that ranks all candidates by viral potential.
    Falls back to feed order (earlier = higher) if scoring fails for any
    reason, so an NVIDIA LLM hiccup never blocks the whole daily batch."""
    if not candidates:
        return []

    numbered = "\n".join(f"{i}. {c.title} — {c.summary[:160]}" for i, c in enumerate(candidates))
    prompt = SCORING_PROMPT_TEMPLATE.format(numbered_list=numbered, max_index=len(candidates) - 1)

    client = _build_nvidia_client()

    scores: Dict[int, int] = {}
    try:
        _llm_pace()
        resp = client.chat.completions.create(
            model=NVIDIA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
        )
        raw_text = resp.choices[0].message.content
        data = json.loads(_extract_json_block(raw_text))
        for item in data:
            idx = int(item["index"])
            scores[idx] = int(item.get("virality_score", 5))
    except Exception as e:
        log.warning(f"  Story scoring failed ({e}); falling back to feed order.")
        scores = {i: (len(candidates) - i) for i in range(len(candidates))}

    scored = [(c, scores.get(i, 0)) for i, c in enumerate(candidates)]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    log.info("  Ranked candidates: " + ", ".join(f"[{s}] {c.title[:40]}" for c, s in scored[:5]) + " ...")
    return scored


def generate_script_package(
    news: NewsItem,
    feedback: Optional[str] = None,
    budget: Optional[LLMCallBudget] = None,
) -> ScriptPackage:
    client = _build_nvidia_client()

    feedback_block = f"\nDURATION FEEDBACK FROM PREVIOUS ATTEMPT: {feedback}\n" if feedback else ""
    prompt = SCRIPT_PROMPT_TEMPLATE.format(
        title=news.title, source_name=news.source_name or "unknown",
        summary=news.summary, feedback_block=feedback_block,
    )

    required_keys = {
        "is_credible", "credibility_note", "script_en", "title", "description",
        "hashtags", "tags", "thumbnail_idea", "visual_keywords",
    }

    last_error: Optional[Exception] = None
    for attempt in range(1, MAX_LLM_RETRIES + 1):
        if budget is not None and not budget.consume():
            raise RuntimeError(f"NVIDIA LLM call budget exhausted ({budget.max_calls} calls) for this story.")
        try:
            _llm_pace()
            response = client.chat.completions.create(
                model=NVIDIA_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9,
                top_p=0.95,
            )
            json_str = _extract_json_block(response.choices[0].message.content)
            data = json.loads(json_str)

            missing = required_keys - set(data.keys())
            if missing:
                raise ValueError(f"NVIDIA LLM JSON missing keys: {missing}")
            if not isinstance(data["hashtags"], list) or not isinstance(data["tags"], list):
                raise ValueError("hashtags/tags must be arrays.")

            is_credible = bool(data["is_credible"])
            script_en = str(data["script_en"]).strip()
            if is_credible and len(script_en) < 20:
                raise ValueError("script_en too short for a credible story - likely a bad generation.")

            shot_list: List[ScriptBeat] = []
            try:
                for entry in data.get("shot_list", []):
                    phrase = str(entry.get("phrase", "")).strip()
                    visual = str(entry.get("visual", "")).strip()
                    if phrase and visual:
                        shot_list.append(ScriptBeat(
                            phrase=phrase, visual=visual,
                            prefer_ai_generation=bool(entry.get("prefer_ai_generation", False)),
                        ))
            except Exception as e:
                log.warning(f"  shot_list malformed, ignoring it for this story ({e}) - falling back to visual_keywords.")
                shot_list = []

            return ScriptPackage(
                script_en=script_en,
                script_romanized=str(data.get("script_romanized", "")).strip(),
                title=str(data["title"]).strip(),
                description=str(data["description"]).strip(),
                hashtags=[str(h).strip() for h in data["hashtags"] if str(h).strip()],
                tags=[str(t).strip() for t in data["tags"] if str(t).strip()],
                thumbnail_idea=str(data["thumbnail_idea"]).strip(),
                visual_keywords=[str(v).strip() for v in data.get("visual_keywords", []) if str(v).strip()],
                shot_list=shot_list,
                is_credible=is_credible,
                credibility_note=str(data.get("credibility_note", "")).strip(),
            )
        except Exception as e:  # noqa: BLE001
            last_error = e
            log.warning(f"  NVIDIA LLM attempt {attempt}/{MAX_LLM_RETRIES} failed: {e}")

    raise RuntimeError(f"NVIDIA LLM script generation failed after retries: {last_error}")


_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")


def contains_devanagari(text: str) -> bool:
    return bool(_DEVANAGARI_RE.search(text))


def romanize_metadata_if_needed(pkg: ScriptPackage, budget: "LLMCallBudget") -> ScriptPackage:
    """Safety net for when the main generation call doesn't fully follow the
    Hinglish instruction for title/description/hashtags/tags - the schema
    asks for a lot in one call (shot list, script, script_romanized, SEO
    metadata, all with their own detailed rules), and a long, dense prompt
    can dilute how strongly any single instruction is followed. Rather than
    re-running the whole complex generation (risking the same slip again),
    this detects leftover Devanagari via a Unicode range check and makes ONE
    small, focused follow-up call asking specifically to Hinglish-ify just
    the offending fields. Never raises and never worsens the package - a
    failed cleanup pass ships the original text rather than losing the
    story or crashing the batch."""
    fields = {
        "title": pkg.title,
        "description": pkg.description,
        "hashtags": pkg.hashtags,
        "tags": pkg.tags,
    }
    offending = {
        k: v for k, v in fields.items()
        if contains_devanagari(v if isinstance(v, str) else " ".join(v))
    }
    if not offending:
        return pkg

    log.warning(f"  Devanagari leaked into {list(offending.keys())} despite the Hinglish "
                f"instruction - attempting a focused cleanup pass.")
    if not budget.consume():
        log.warning("  LLM call budget exhausted - shipping as-is (Devanagari may show for this story).")
        return pkg

    try:
        _llm_pace()
        cleanup_prompt = (
            "Convert ONLY the values below to Hinglish - Hindi words spelled in casual "
            "Roman/English letters the way people type on WhatsApp (e.g. 'mere pas "
            "khuchvi nehi hay'), NOT Devanagari, NOT a formal transliteration scheme. "
            "Keep the same meaning and length; keep hashtags/tags as JSON arrays of the "
            "same length. Respond ONLY with a JSON object using these exact keys:\n\n"
            + json.dumps(offending, ensure_ascii=False)
        )
        resp = _build_nvidia_client().chat.completions.create(
            model=NVIDIA_MODEL,
            messages=[{"role": "user", "content": cleanup_prompt}],
            temperature=0.3,
        )
        fixed = json.loads(_extract_json_block(resp.choices[0].message.content))

        if "title" in fixed and isinstance(fixed["title"], str) and not contains_devanagari(fixed["title"]):
            pkg.title = fixed["title"].strip()
        if "description" in fixed and isinstance(fixed["description"], str) and not contains_devanagari(fixed["description"]):
            pkg.description = fixed["description"].strip()
        if "hashtags" in fixed and isinstance(fixed["hashtags"], list):
            cleaned = [str(h).strip() for h in fixed["hashtags"] if str(h).strip()]
            if cleaned and not contains_devanagari(" ".join(cleaned)):
                pkg.hashtags = cleaned
        if "tags" in fixed and isinstance(fixed["tags"], list):
            cleaned = [str(t).strip() for t in fixed["tags"] if str(t).strip()]
            if cleaned and not contains_devanagari(" ".join(cleaned)):
                pkg.tags = cleaned
        log.info("  -> Hinglish cleanup pass applied.")
    except Exception as e:
        log.warning(f"  Hinglish cleanup pass failed ({e}) - shipping original text for this story.")

    return pkg


def generate_with_duration_enforcement(
    news: NewsItem,
    budget: Optional[LLMCallBudget] = None,
) -> Tuple[ScriptPackage, str, List[WordTiming], float]:
    log.info(f"  Fact-check + script generation for: {news.title[:70]}")
    feedback: Optional[str] = None
    best: Optional[Tuple[float, ScriptPackage, str, List[WordTiming], float]] = None

    for attempt in range(1, MAX_DURATION_RETRIES + 1):
        if budget is not None and budget.remaining() <= 0:
            log.warning("  NVIDIA LLM call budget exhausted before duration target reached; stopping retries.")
            break
        try:
            pkg = generate_script_package(news, feedback=feedback, budget=budget)
        except RuntimeError as e:
            log.warning(f"  {e}")
            break

        if not pkg.is_credible:
            raise CredibilitySkipError(pkg.credibility_note or "Flagged as unverified by fact-check step.")

        tmp_voice_path = os.path.join(TEMP_DIR, f"voice_attempt_{attempt}_{random.randint(1000,9999)}.mp3")
        words = synthesize_voice_with_timing_smart(pkg.script_en, TTS_VOICE, tmp_voice_path)

        probe = AudioFileClip(tmp_voice_path)
        duration = probe.duration
        probe.close()

        diff = abs(duration - (TARGET_MIN_SEC + TARGET_MAX_SEC) / 2)
        if best is None or diff < best[0]:
            best = (diff, pkg, tmp_voice_path, words, duration)

        if TARGET_MIN_SEC <= duration <= TARGET_MAX_SEC:
            log.info(f"  -> Duration OK on attempt {attempt}: {duration:.1f}s")
            return pkg, tmp_voice_path, words, duration

        log.warning(f"  Attempt {attempt}/{MAX_DURATION_RETRIES}: duration {duration:.1f}s out of [30,40]s range, retrying ...")
        feedback = (
            f"The previous script produced {duration:.1f} seconds of speech, which is "
            f"{'too short' if duration < TARGET_MIN_SEC else 'too long'}. Rewrite the script to "
            f"strictly use 80 to 100 words so spoken duration lands between 30 and 40 seconds."
        )

    if best is None:
        raise RuntimeError("Could not generate a usable script within the NVIDIA LLM call budget.")

    _, pkg, voice_path, words, duration = best
    log.warning(f"  Duration enforcement did not converge; proceeding with closest attempt ({duration:.1f}s).")
    return pkg, voice_path, words, duration


# ==============================================================================
# 6. VOICEOVER SYNTHESIS + CAPTION CHUNKING
# ==============================================================================
def synthesize_voice_with_timing(text: str, voice: str, out_mp3_path: str) -> List[WordTiming]:
    async def _run() -> List[WordTiming]:
        communicate = edge_tts.Communicate(text, voice, rate=TTS_RATE)
        words: List[WordTiming] = []
        with open(out_mp3_path, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    start = chunk["offset"] / 1e7
                    dur = chunk["duration"] / 1e7
                    words.append(WordTiming(text=chunk["text"], start=start, end=start + dur))
        return words

    words = asyncio.run(_run())
    if not os.path.exists(out_mp3_path) or os.path.getsize(out_mp3_path) == 0:
        raise RuntimeError("edge-tts produced no audio output. Check network/voice name.")
    if not words:
        log.warning("  No word-boundary timestamps returned; captions will be coarse.")
    return words


def synthesize_voice_with_timing_sarvam(text: str, out_mp3_path: str) -> List[WordTiming]:
    """More natural-sounding Hindi voice than edge-tts (Sarvam's Bulbul v3 is
    purpose-built for Indian languages/accents, handles Hinglish code-mixing
    natively) - but unlike edge-tts, Sarvam's TTS response is JUST audio, no
    word-boundary timestamps alongside it. Sarvam separately offers STT
    (Saaras v3) WITH word-level timestamps, so this synthesizes the audio
    first, then immediately transcribes that same freshly-synthesized audio
    back through Sarvam's own STT to recover per-word timing - alignment
    should be very reliable since it's clean single-voice audio with no
    background noise, not messy real-world speech.

    UNVERIFIED END-TO-END (no network access while writing this) - API
    shapes below are from Sarvam's current docs/SDK examples, not a live
    test run. Raises on ANY failure (bad response shape, decode error, STT
    mismatch) rather than guessing - synthesize_voice_with_timing_smart()
    catches that and falls back to edge-tts, so a Sarvam-side problem
    degrades to the proven path instead of breaking the story."""
    from sarvamai import SarvamAI  # optional dependency - only imported if SARVAM_API_KEY is actually set

    client = SarvamAI(api_subscription_key=SARVAM_API_KEY)

    tts_resp = client.text_to_speech.convert(
        text=text,
        target_language_code="hi-IN",
        speaker=SARVAM_VOICE,
        model="bulbul:v3",
        pace=1.0,
    )
    audios = getattr(tts_resp, "audios", None) or tts_resp.get("audios")
    if not audios:
        raise RuntimeError("Sarvam TTS response had no audio data.")
    audio_bytes = base64.b64decode(audios[0])
    with open(out_mp3_path, "wb") as f:
        f.write(audio_bytes)
    if os.path.getsize(out_mp3_path) == 0:
        raise RuntimeError("Sarvam TTS decoded to an empty audio file.")

    stt_resp = client.speech_to_text.transcribe(
        file_path=out_mp3_path, language="hi-IN", model="saaras:v3", with_timestamps=True,
    )
    stt_words = getattr(stt_resp, "words", None)
    if not stt_words:
        raise RuntimeError("Sarvam STT self-transcription returned no word timestamps.")

    words = [WordTiming(text=w.text, start=float(w.start), end=float(getattr(w, "end", w.start))) for w in stt_words]
    if len(words) < len(text.split()) * 0.5:
        # STT badly under-recognized its own freshly synthesized audio - a
        # red flag something's off (wrong language tag, corrupt decode,
        # API hiccup) rather than a normal, trustworthy result.
        raise RuntimeError(f"Sarvam self-transcription only recovered {len(words)} words for a "
                            f"{len(text.split())}-word script - discarding as unreliable.")
    return words


def synthesize_voice_with_timing_smart(text: str, voice: str, out_mp3_path: str) -> List[WordTiming]:
    """Tries Sarvam (more natural Hindi/Hinglish voice) first if
    SARVAM_API_KEY is set, falls back to edge-tts (always available, no
    signup, proven in production) on ANY failure - a Sarvam-side issue
    (quota, network, API change, unreliable self-transcription) degrades to
    the known-working voice instead of failing the story."""
    if SARVAM_API_KEY:
        try:
            return synthesize_voice_with_timing_sarvam(text, out_mp3_path)
        except Exception as e:
            log.warning(f"  Sarvam TTS failed ({e}) - falling back to edge-tts for this story.")
    return synthesize_voice_with_timing(text, voice, out_mp3_path)


# ==============================================================================
# 7. PEXELS FOOTAGE SEARCH & DOWNLOAD
# ==============================================================================
def search_pexels_clips(query: str, per_page: int = PEXELS_RESULTS_PER_QUERY) -> List[str]:
    url = "https://api.pexels.com/videos/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": query, "orientation": "portrait", "per_page": per_page}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        videos = resp.json().get("videos", [])
    except Exception as e:
        log.warning(f"  Pexels search failed for '{query}': {e}")
        return []

    if not videos:
        params.pop("orientation", None)
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            videos = resp.json().get("videos", [])
        except Exception as e:
            log.warning(f"  Pexels fallback search failed for '{query}': {e}")
            return []

    links = []
    for v in videos:
        files = [f for f in v.get("video_files", []) if f.get("width") and f.get("height")]
        if not files:
            continue
        files.sort(key=lambda f: abs((f["width"] or 0) - VIDEO_WIDTH))
        best = files[0]
        if best.get("link"):
            links.append(best["link"])
    return links


def download_file(url: str, dest_path: str) -> Optional[str]:
    try:
        with requests.get(url, stream=True, timeout=REQUEST_TIMEOUT) as r:
            r.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 20):
                    if chunk:
                        f.write(chunk)
        return dest_path
    except Exception as e:
        log.warning(f"  Download failed for {url}: {e}")
        return None


def generate_ai_background_image(prompt: str, dest_png_path: str) -> Optional[str]:
    """Fallback visual source for when Pexels has no good stock footage for a
    query - common for abstract geopolitics/diplomacy concepts (there's no
    real stock footage of e.g. "India's Indo-Pacific strategy"). Uses
    Pollinations.ai's free, key-less image endpoint - no signup, no API key,
    no new GitHub Secret to manage. Anonymous access is rate-limited to
    roughly 1 request/15s, which is exactly why this is a FALLBACK: Pexels is
    tried first, this only fires for the shortfall (see fetch_background_clips).

    UNVERIFIED live (no network access available while writing this fork) -
    if this silently never produces images, check the request against
    https://pollinations.ai's current docs before assuming the calling logic
    is at fault - the shape of the fallback (try, log, return None, keep
    going) is what matters, not necessarily every query-param name below."""
    try:
        safe_prompt = (
            f"{prompt}, cinematic news broadcast background, symbolic and generic, "
            f"no real identifiable people, no text, no watermark"
        )[:250]
        encoded = requests.utils.quote(safe_prompt)
        url = (
            f"https://image.pollinations.ai/prompt/{encoded}"
            f"?width={VIDEO_WIDTH}&height={VIDEO_HEIGHT}&nologo=true&model=flux"
            f"&seed={random.randint(1, 999999)}"
        )
        resp = requests.get(url, timeout=max(REQUEST_TIMEOUT, 90))
        resp.raise_for_status()
        with open(dest_png_path, "wb") as f:
            f.write(resp.content)
        with Image.open(dest_png_path) as im:
            im.verify()  # raises if the response wasn't actually a decodable image
        return dest_png_path
    except Exception as e:
        log.warning(f"  AI image fallback failed for '{prompt[:60]}...': {e}")
        return None


def _image_to_clip_file(image_path: str, dest_mp4_path: str, duration: float) -> Optional[str]:
    """Wraps a still image as a short silent .mp4 so it flows through the
    EXACT SAME downstream pipeline (build_background_video -> VideoFileClip(
    path) -> crop/Ken-Burns/color-grade) as a real Pexels clip, with zero
    changes needed anywhere else in the video assembly code."""
    try:
        img_clip = ImageClip(image_path).set_duration(duration).set_fps(24)
        img_clip.write_videofile(
            dest_mp4_path, codec="libx264", audio=False, fps=24,
            preset="ultrafast", verbose=False, logger=None,
        )
        img_clip.close()
        return dest_mp4_path
    except Exception as e:
        log.warning(f"  Could not convert AI image to a clip file: {e}")
        return None


MIN_BACKGROUND_CLIPS = 3   # below this, top up with AI-generated images rather than
                            # letting build_background_video() loop 1-2 clips repetitively


def fetch_background_clips(visual_keywords: List[str], fallback_query: str) -> List[str]:
    log.info("  Searching & downloading Pexels stock footage ...")
    queries = list(visual_keywords) if visual_keywords else []
    if fallback_query:
        queries.append(fallback_query)
    if not queries:
        queries = ["technology abstract", "data center servers"]

    seen_urls = set()
    local_paths: List[str] = []
    for q in queries:
        if len(local_paths) >= MAX_BACKGROUND_CLIPS:
            break
        for link in search_pexels_clips(q):
            if link in seen_urls:
                continue
            seen_urls.add(link)
            dest = os.path.join(TEMP_DIR, f"clip_{len(local_paths)}_{random.randint(1000,9999)}.mp4")
            path = download_file(link, dest)
            if path:
                local_paths.append(path)
            if len(local_paths) >= MAX_BACKGROUND_CLIPS:
                break

    # Pexels came up short - top up with AI-generated images instead of relying
    # entirely on build_background_video()'s clip-looping to stretch 1-2 clips
    # across the full 30-40s, which looks visibly repetitive on screen.
    if len(local_paths) < MIN_BACKGROUND_CLIPS:
        log.warning(
            f"  Only {len(local_paths)} Pexels clip(s) found for this story - "
            f"topping up to {MIN_BACKGROUND_CLIPS} with AI-generated images."
        )
        needed = MIN_BACKGROUND_CLIPS - len(local_paths)
        ai_prompts = queries or ["news analysis abstract background"]
        avg_seg_duration = (CLIP_SEGMENT_MIN_SEC + CLIP_SEGMENT_MAX_SEC) / 2
        for i in range(needed):
            prompt = ai_prompts[i % len(ai_prompts)]
            img_path = generate_ai_background_image(
                prompt, os.path.join(TEMP_DIR, f"ai_img_{len(local_paths)}_{random.randint(1000,9999)}.png")
            )
            if img_path:
                mp4_path = os.path.join(TEMP_DIR, f"ai_clip_{len(local_paths)}_{random.randint(1000,9999)}.mp4")
                clip_path = _image_to_clip_file(img_path, mp4_path, avg_seg_duration)
                if clip_path:
                    local_paths.append(clip_path)
            if i < needed - 1:
                time.sleep(15)  # Pollinations anonymous rate limit: ~1 request/15s

    if not local_paths:
        raise RuntimeError(
            "No background clips could be downloaded from Pexels OR generated via the "
            "AI image fallback. Check PEXELS_API_KEY, network connectivity, and "
            "https://pollinations.ai's current status."
        )
    return local_paths


# ==============================================================================
# 8. VIDEO ASSEMBLY (crop/resize/concat, center-weighted bounding)
# ==============================================================================
def crop_and_resize_9x16(clip: VideoFileClip) -> VideoFileClip:
    target_ratio = VIDEO_WIDTH / VIDEO_HEIGHT
    w, h = clip.size
    if w <= 0 or h <= 0:
        raise ValueError("Invalid clip dimensions.")
    current_ratio = w / h

    if current_ratio > target_ratio:
        new_w = int(h * target_ratio)
        x1 = max(0, (w - new_w) // 2)
        clip = clip.crop(x1=x1, y1=0, x2=x1 + new_w, y2=h)
    else:
        new_h = int(w / target_ratio)
        trimmed = h - new_h
        upward_bias = int(trimmed * 0.15)
        y1 = max(0, (trimmed // 2) - upward_bias)
        y1 = min(y1, h - new_h)
        clip = clip.crop(x1=0, y1=y1, x2=w, y2=y1 + new_h)

    return clip.resize((VIDEO_WIDTH, VIDEO_HEIGHT))


def _apply_ken_burns(clip: VideoFileClip, zoom_amount: float = KEN_BURNS_ZOOM_AMOUNT) -> VideoFileClip:
    """Slow continuous zoom-in over the clip's duration, output size fixed at
    the clip's own W x H (crops the zoomed frame back each frame) - a cheap
    way to avoid dead-static stock-footage frames without real motion
    tracking. Implemented via .fl() (per-frame PIL resize+crop) rather than
    moviepy's vfx.resize, because vfx.resize with a time-varying factor
    changes frame size over time, which CompositeVideoClip can't composite
    against a fixed canvas."""
    w, h = clip.size
    duration = max(clip.duration, 0.01)

    def make_frame(get_frame, t):
        frame = get_frame(t)
        progress = min(1.0, t / duration)
        scale = 1.0 + zoom_amount * progress
        new_w, new_h = max(w, int(w * scale)), max(h, int(h * scale))
        img = Image.fromarray(frame).resize((new_w, new_h), Image.LANCZOS)
        x1 = (new_w - w) // 2
        y1 = (new_h - h) // 2
        img = img.crop((x1, y1, x1 + w, y1 + h))
        return np.array(img)

    return clip.fl(make_frame)


def apply_color_grade(clip: VideoFileClip) -> VideoFileClip:
    """Consistent, subtle color treatment applied to every video for a
    recognizable channel 'look' - a lightweight, zero-cost stand-in for a
    proper color-graded LUT. Never fatal: falls back to the ungraded clip on
    any error, since a missing 'look' is cosmetic, not a broken video.

    WARNING on COLOR_GRADE_CONTRAST: moviepy's vfx.lum_contrast formula is
    `pixel + contrast * (pixel - 127)`, NOT a 0-100 percentage. A value as
    "small-looking" as 6 pushes nearly every pixel to pure 0 or 255 per
    channel - a blown-out, posterized, often reddish-looking result (this
    shipped as a real bug in an earlier version of this file - default is
    now 0/disabled). If you want extra contrast, try something in the
    0.02-0.1 range and actually look at a rendered frame before trusting it."""
    try:
        graded = clip.fx(vfx.colorx, COLOR_GRADE_SATURATION)
        if COLOR_GRADE_CONTRAST:
            graded = graded.fx(vfx.lum_contrast, contrast=COLOR_GRADE_CONTRAST)
        return graded
    except Exception as e:
        log.warning(f"  Color grading skipped: {e}")
        return clip


def build_background_video(clip_paths: List[str], target_duration: float) -> VideoFileClip:
    log.info("  Assembling 1080x1920 background video ...")
    if target_duration <= 0:
        raise ValueError("target_duration must be positive.")

    segments = []
    total = 0.0
    idx = 0
    safety_counter = 0
    max_iterations = 500

    while total < target_duration and safety_counter < max_iterations:
        safety_counter += 1
        path = clip_paths[idx % len(clip_paths)]
        idx += 1
        try:
            raw_clip = VideoFileClip(path)
        except Exception as e:
            log.warning(f"  Skipping unreadable clip {path}: {e}")
            continue

        if raw_clip.duration is None or raw_clip.duration < 0.5:
            raw_clip.close()
            continue

        seg_len = random.uniform(CLIP_SEGMENT_MIN_SEC, CLIP_SEGMENT_MAX_SEC)
        seg_len = min(seg_len, target_duration - total, raw_clip.duration)
        if seg_len <= 0.15:
            raw_clip.close()
            continue

        max_start = max(0.0, raw_clip.duration - seg_len)
        start = random.uniform(0, max_start) if max_start > 0 else 0.0

        try:
            sub = raw_clip.subclip(start, start + seg_len)
            sub = crop_and_resize_9x16(sub)
            sub = sub.without_audio()
            if ENABLE_KEN_BURNS:
                sub = _apply_ken_burns(sub)
        except Exception as e:
            log.warning(f"  Failed to process segment from {path}: {e}")
            raw_clip.close()
            continue

        segments.append(sub)
        total += sub.duration

    if not segments:
        raise RuntimeError("Failed to build any usable video segments from downloaded clips.")

    if len(segments) > 1 and CROSSFADE_DURATION > 0:
        faded = [segments[0]] + [c.crossfadein(CROSSFADE_DURATION) for c in segments[1:]]
        bg = concatenate_videoclips(faded, padding=-CROSSFADE_DURATION, method="compose")
    else:
        bg = concatenate_videoclips(segments, method="compose")

    if bg.duration < target_duration:
        loops_needed = int(target_duration // bg.duration) + 1
        bg = concatenate_videoclips([bg] * loops_needed, method="compose")
    bg = bg.subclip(0, target_duration)
    bg = apply_color_grade(bg)

    log.info(f"  -> Background video assembled: {bg.duration:.1f}s across {len(segments)} segments")
    return bg


MIN_BEAT_DURATION = 2.0   # shortest a single shot_list beat's background segment can be - lowered from 2.5 to fit more, shorter beats (7-12 now vs 4-7 before) in the same 30-40s video


def _allocate_beat_durations(shot_list: List[ScriptBeat], total_duration: float) -> List[float]:
    """Splits total_duration across beats proportional to each beat's quoted
    phrase length - a simple, robust proxy for how much of the spoken audio
    that beat covers. Deliberately NOT matched against word-level timestamps
    character-for-character: an LLM-quoted phrase won't always reproduce
    script_en's exact punctuation/spacing, and proportional-by-length gives
    "roughly the right footage roughly when that part is being said" (what
    was actually asked for) without that fragility."""
    weights = [max(len(b.phrase), 1) for b in shot_list]
    total_weight = sum(weights)
    durations = [total_duration * w / total_weight for w in weights]
    durations = [max(d, MIN_BEAT_DURATION) for d in durations]
    scale = total_duration / sum(durations)
    return [d * scale for d in durations]


def fetch_beat_footage(beat: ScriptBeat) -> List[str]:
    """Sources footage for ONE shot_list beat. Concepts flagged
    prefer_ai_generation (a specific deity, festival, or local tradition -
    things Pexels' generic global stock library realistically won't have)
    go straight to AI generation rather than wasting a call on a search
    that's unlikely to match well. Everything else tries Pexels first with
    an India-biased query, topping up with AI generation if that comes up
    empty - reuses the same generate_ai_background_image() /
    _image_to_clip_file() building blocks as the story-level fallback in
    fetch_background_clips(), just scoped to a single beat."""
    paths: List[str] = []

    if not beat.prefer_ai_generation:
        # No longer force-prepends "India" here - the prompt now instructs the
        # LLM to already write the correct geographic context into `visual`
        # itself (a specific foreign country when the beat is genuinely about
        # one, India by default otherwise). Prepending India unconditionally
        # would contradict a beat the LLM correctly wrote as e.g. "Madrid
        # Spain city street".
        for link in search_pexels_clips(beat.visual)[:2]:
            dest = os.path.join(TEMP_DIR, f"beat_{random.randint(1000,9999)}.mp4")
            path = download_file(link, dest)
            if path:
                paths.append(path)

    if not paths:
        img_path = generate_ai_background_image(
            beat.visual,
            os.path.join(TEMP_DIR, f"beat_ai_{random.randint(1000,9999)}.png"),
        )
        if img_path:
            avg_seg = (CLIP_SEGMENT_MIN_SEC + CLIP_SEGMENT_MAX_SEC) / 2
            clip_path = _image_to_clip_file(
                img_path, os.path.join(TEMP_DIR, f"beat_ai_clip_{random.randint(1000,9999)}.mp4"), avg_seg
            )
            if clip_path:
                paths.append(clip_path)

    return paths


def build_synced_background_video(shot_list: List[ScriptBeat], target_duration: float, fallback_query: str) -> VideoFileClip:
    """Builds the background beat-by-beat, in shot_list order, instead of
    from one flat clip pool - so the footage on screen actually matches
    whatever the script is saying at roughly that moment (e.g. "police"
    gets Indian police footage right then, not just somewhere in the
    general rotation).

    Falls back to the original flat fetch_background_clips() +
    build_background_video() behavior if the LLM didn't return a usable
    shot_list (empty, or every beat fails) - a newer, less-tested code path
    should degrade to the proven one, not fail the whole story."""
    if not shot_list:
        log.info("  No shot_list from the LLM - using flat keyword-based footage instead.")
        clip_paths = fetch_background_clips([], fallback_query)
        return build_background_video(clip_paths, target_duration)

    durations = _allocate_beat_durations(shot_list, target_duration)
    beat_clips = []
    for beat, dur in zip(shot_list, durations):
        try:
            paths = fetch_beat_footage(beat)
            if not paths:
                log.warning(f"  No footage (Pexels or AI) for beat '{beat.visual[:40]}' - using generic fallback for this beat.")
                paths = fetch_background_clips([], fallback_query)
            beat_clips.append(build_background_video(paths, dur))
        except Exception as e:
            log.warning(f"  Beat '{beat.visual[:40]}' failed ({e}) - filling with generic fallback footage instead.")
            paths = fetch_background_clips([], fallback_query)
            beat_clips.append(build_background_video(paths, dur))

    if not beat_clips:
        log.warning("  Every shot_list beat failed - falling back to flat keyword-based footage for the whole story.")
        clip_paths = fetch_background_clips([], fallback_query)
        return build_background_video(clip_paths, target_duration)

    if len(beat_clips) > 1 and CROSSFADE_DURATION > 0:
        faded = [beat_clips[0]] + [c.crossfadein(CROSSFADE_DURATION) for c in beat_clips[1:]]
        bg = concatenate_videoclips(faded, padding=-CROSSFADE_DURATION, method="compose")
    else:
        bg = concatenate_videoclips(beat_clips, method="compose")

    bg = bg.subclip(0, min(bg.duration, target_duration))
    return bg


# ==============================================================================
# 9. DYNAMIC PIL CAPTIONS (English - no Devanagari/ImageMagick dependency)
# ==============================================================================
def find_caption_font(need_devanagari: bool = False) -> Optional[str]:
    """Returns a font path for on-screen text.

    ACTUAL ROOT CAUSE of boxes appearing on Hinglish captions AND the
    banner: this function used to always fetch a Devanagari-specific font
    and that was the ONLY font used everywhere, from back when captions
    were Devanagari. Once captions/title/banner switched to Hinglish
    (Roman script), that same Devanagari font kept being used for Roman
    text - and a font fetched specifically for Devanagari coverage
    (openmaptiles/fonts' NotoSansDevanagari, a script-specific subset meant
    to be paired with a separate Latin font in multi-font pipelines) may
    carry NO Latin glyphs at all. Every character shows as .notdef (a box)
    when a font has no glyph for it - that's true of "अ" in a Latin font
    just as much as "A" in a Devanagari-only font. Same bug, opposite
    direction from the one fixed two rounds ago.

    Fix: default to a plain bold LATIN font already present on the runner -
    no download, no network dependency, nothing to get wrong - since that's
    what captions/title/banner/thumbnail need almost all the time now.
    Devanagari coverage is only fetched when need_devanagari=True is passed
    explicitly - the rare case where build_romanized_word_timings() couldn't
    map a story's captions to Hinglish and they're falling back to
    Devanagari display for that one story."""
    if not need_devanagari:
        latin_candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        ]
        for path in latin_candidates:
            if os.path.exists(path):
                log.info(f"  Using caption font (Latin): {path}")
                return path
        try:
            result = subprocess.run(
                ["fc-match", "-f", "%{file}", ":lang=en"],
                capture_output=True, text=True, timeout=10,
            )
            candidate = result.stdout.strip()
            if candidate and os.path.exists(candidate):
                log.info(f"  Using caption font (Latin, via fontconfig): {candidate}")
                return candidate
        except Exception as e:
            log.warning(f"  No standard Latin font found and fc-match unavailable ({e}) - text may render as boxes.")
        return None

    try:
        result = subprocess.run(
            ["fc-match", "-f", "%{file}", ":lang=hi"],
            capture_output=True, text=True, timeout=10,
        )
        candidate = result.stdout.strip()
        if candidate and os.path.exists(candidate):
            log.info(f"  Using caption font (Devanagari): {candidate}")
            return candidate
    except Exception as e:
        log.info(f"  fc-match unavailable ({e}); trying known font paths.")

    candidates = [
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
        "/usr/share/fonts/truetype/lohit-devanagari/Lohit-Devanagari.ttf",
        os.path.join(TEMP_DIR, "NotoSansDevanagari-Bold.ttf"),
    ]
    for path in candidates:
        if os.path.exists(path):
            log.info(f"  Using caption font (Devanagari): {path}")
            return path

    # Verified download fallback (directly fetched and confirmed to exist,
    # not guessed) - two URLs tried in order in case one weight has an issue.
    download_urls = [
        "https://github.com/openmaptiles/fonts/raw/refs/heads/master/noto-sans/NotoSansDevanagari-Bold.ttf",
        "https://github.com/openmaptiles/fonts/raw/refs/heads/master/noto-sans/NotoSansDevanagari-Regular.ttf",
    ]
    for url in download_urls:
        dest = os.path.join(TEMP_DIR, os.path.basename(url))
        try:
            r = requests.get(url, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            with open(dest, "wb") as f:
                f.write(r.content)
            ImageFont.truetype(dest, 40)  # sanity-check it's actually a loadable font, not an HTML error page
            log.info(f"  -> Downloaded and verified {os.path.basename(url)} for Devanagari fallback captions.")
            return dest
        except Exception as e:
            log.warning(f"  Font download/validation failed for {url}: {e}")

    log.warning(
        "  Could not obtain a Devanagari-capable font from fontconfig, known paths, or "
        "download. Hindi captions will render as blank boxes with PIL's default font. "
        "ACTION: run `fc-list | grep -i devanagari` on the runner, or confirm "
        "'fonts-noto-core' actually provides Devanagari coverage on this Ubuntu version."
    )
    return None


def _measure_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, stroke_width: int = 4) -> Tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _layout_caption_words(
    words: List[str],
    font: ImageFont.FreeTypeFont,
    content_width: int,
    draw: ImageDraw.ImageDraw,
    stroke_width: int = 4,
) -> Tuple[List[List[dict]], int]:
    """Word-wraps a line of words to content_width using actual pixel widths
    (not character counts, which are unreliable for variable-width fonts).
    Returns (lines, space_width) where each line is a list of
    {'word', 'w', 'h'} dicts in reading order."""
    space_w, _ = _measure_text(draw, " ", font, stroke_width)
    lines: List[List[dict]] = []
    current: List[dict] = []
    current_w = 0
    for word in words:
        ww, wh = _measure_text(draw, word, font, stroke_width)
        extra = space_w if current else 0
        if current and current_w + extra + ww > content_width:
            lines.append(current)
            current, current_w, extra = [], 0, 0
        current.append({"word": word, "w": ww, "h": wh})
        current_w += extra + ww
    if current:
        lines.append(current)
    return lines, space_w


def render_caption_line_highlighted(
    line_words: List[str],
    highlight_idx: Optional[int],
    font_path: Optional[str],
    width: int = VIDEO_WIDTH,
    font_size: int = 66,
) -> np.ndarray:
    """Renders one caption line with every word in white except
    highlight_idx (drawn in accent yellow) - the 'karaoke' look. Called once
    per WORD with the same line_words/layout, only highlight_idx changes, so
    the caption bar never jitters between words - only the color does."""
    try:
        font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    probe = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    d = ImageDraw.Draw(probe)
    bar_margin = 24
    content_width = width - 2 * bar_margin - 60

    lines, space_w = _layout_caption_words(line_words, font, content_width, d)
    line_heights = [max((wd["h"] for wd in line), default=font_size) for line in lines]
    padding_y, line_spacing = 24, 14
    block_height = sum(line_heights) + line_spacing * (len(lines) - 1) + padding_y * 2

    img = Image.new("RGBA", (width, block_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(
        [bar_margin, 0, width - bar_margin, block_height], radius=20, fill=(0, 0, 0, 140),
    )

    global_idx = 0
    y = padding_y
    for line, lh in zip(lines, line_heights):
        line_w = sum(wd["w"] for wd in line) + space_w * (len(line) - 1)
        x = (width - line_w) // 2
        for wd in line:
            is_current = (highlight_idx is not None and global_idx == highlight_idx)
            color = (255, 220, 0, 255) if is_current else (255, 255, 255, 255)
            draw.text(
                (x, y), wd["word"], font=font,
                fill=color, stroke_width=4, stroke_fill=(0, 0, 0, 255),
            )
            x += wd["w"] + space_w
            global_idx += 1
        y += lh + line_spacing

    return np.array(img)


def _build_caption_chunks_fallback(audio_duration: float, full_script: str) -> List[CaptionChunk]:
    """Used only when edge-tts returned no word-boundary timestamps (rare) -
    evenly spaces static (non-karaoke) chunks across the audio so captions
    still exist, just without word-level highlighting."""
    pieces = full_script.split()
    chunk_size = max(1, WORDS_PER_CAPTION_CHUNK)
    n_chunks = max(1, len(pieces) // chunk_size + (1 if len(pieces) % chunk_size else 0))
    seg_len = audio_duration / n_chunks
    chunks = []
    for i in range(n_chunks):
        text = " ".join(pieces[i * chunk_size:(i + 1) * chunk_size])
        if text:
            chunks.append(CaptionChunk(text=text, start=i * seg_len, end=(i + 1) * seg_len))
    return chunks


def _compute_word_display_ends(words: List[WordTiming], audio_duration: float) -> List[float]:
    """Extends each word's display end time to the next word's start (so a
    caption never blanks out during a natural TTS pause), and the final
    word's end to the full audio duration. Computed across the WHOLE word
    sequence, independent of how words are later grouped into lines - a
    pause that falls on a line boundary still gets bridged correctly."""
    ends: List[float] = []
    for i, w in enumerate(words):
        if i + 1 < len(words):
            ends.append(max(w.end, words[i + 1].start))
        else:
            ends.append(max(w.end, audio_duration))
    return ends


def build_romanized_word_timings(devanagari_words: List[WordTiming], script_romanized: str) -> Tuple[List[WordTiming], bool]:
    """Captions display in Hinglish (Hindi words, Roman letters) even though
    the TTS input/audio stays Devanagari - edge-tts's hi-IN voice needs
    Devanagari to pronounce Hindi correctly; feeding it Roman-script text
    would read it back with English pronunciation and sound wrong. So the
    spoken audio and word-timing still come from script_en as before, and
    this maps the LLM's separately-generated script_romanized onto that SAME
    timing, word-for-word by index.

    Reliable exactly as long as script_romanized has the same word count as
    script_en, which the prompt explicitly instructs. Falls back to the
    original Devanagari words (rather than misaligned or truncated captions)
    if that count doesn't line up - a word-count mismatch is a real
    possibility with any LLM output and shouldn't break the video.

    Returns (words, used_romanization) - the caller needs that second value
    to pick the right FONT: Latin for the (normal) romanized case, Devanagari
    for the (rare) fallback case. Using the wrong one is exactly what caused
    the box-caption bug - see find_caption_font()'s docstring."""
    if not script_romanized or not devanagari_words:
        return devanagari_words, False

    roman_tokens = script_romanized.split()
    if len(roman_tokens) != len(devanagari_words):
        log.warning(
            f"  script_romanized word count ({len(roman_tokens)}) doesn't match "
            f"the spoken script ({len(devanagari_words)}) - captions will show "
            f"the Devanagari script for this story instead."
        )
        return devanagari_words, False

    return [
        WordTiming(text=roman_word, start=dw.start, end=dw.end)
        for roman_word, dw in zip(roman_tokens, devanagari_words)
    ], True


def build_caption_clips(
    words: List[WordTiming],
    audio_duration: float,
    full_script: str,
    font_path: Optional[str],
) -> List[ImageClip]:
    """Karaoke-style captions: groups words into short on-screen lines
    (WORDS_PER_CAPTION_CHUNK words each) and renders ONE ImageClip per WORD
    within that line - same line text/layout throughout the line's time
    span, only the currently-spoken word recolored - instead of one static
    block of text per line."""
    log.info("  Rendering karaoke-style word-highlighted captions ...")
    clips: List[ImageClip] = []

    if not words:
        for chunk in _build_caption_chunks_fallback(audio_duration, full_script):
            try:
                arr = render_caption_line_highlighted(chunk.text.split(), None, font_path)
            except Exception as e:
                log.warning(f"  Failed to render fallback caption '{chunk.text[:20]}...': {e}")
                continue
            duration = max(0.15, chunk.end - chunk.start)
            clips.append(
                ImageClip(arr).set_start(chunk.start).set_duration(duration)
                .set_position(("center", int(VIDEO_HEIGHT * 0.72)))
            )
        return clips

    display_ends = _compute_word_display_ends(words, audio_duration)

    for i in range(0, len(words), WORDS_PER_CAPTION_CHUNK):
        group = words[i:i + WORDS_PER_CAPTION_CHUNK]
        group_ends = display_ends[i:i + WORDS_PER_CAPTION_CHUNK]
        line_words = [w.text for w in group]
        for local_idx, (w, w_end) in enumerate(zip(group, group_ends)):
            duration = max(0.08, w_end - w.start)
            try:
                arr = render_caption_line_highlighted(line_words, local_idx, font_path)
            except Exception as e:
                log.warning(f"  Failed to render caption word '{w.text}': {e}")
                continue
            clips.append(
                ImageClip(arr).set_start(w.start).set_duration(duration)
                .set_position(("center", int(VIDEO_HEIGHT * 0.72)))
            )
    return clips


def _ensure_shorts_hashtag(pkg: ScriptPackage) -> None:
    """YouTube routes a video into the Shorts shelf using duration (<=60s,
    already satisfied here) and vertical aspect ratio (already 1080x1920) as
    the main signals, but including '#Shorts' in the title/description is a
    well-documented extra nudge. Belt-and-suspenders in case the NVIDIA LLM forgot it."""
    if not any(h.strip().lower() == "#shorts" for h in pkg.hashtags):
        pkg.hashtags.insert(0, "#Shorts")


CHANNEL_TAGLINE = os.environ.get("CHANNEL_TAGLINE", "DESH KII KHABAR AAGE HAI AAGE RAKHTI HAI")
BANNER_HEIGHT_RATIO = 0.17   # fraction of VIDEO_HEIGHT the whole banner complex occupies


def _fit_font(draw: ImageDraw.ImageDraw, text: str, font_path: Optional[str], max_width: int, max_size: int, min_size: int = 14) -> ImageFont.FreeTypeFont:
    """Shrinks font size until `text` fits max_width, so a long title/tagline
    doesn't overflow the fixed-width banner bar it's drawn on."""
    size = max_size
    while size > min_size:
        f = ImageFont.truetype(font_path, size) if font_path else ImageFont.load_default()
        bbox = draw.textbbox((0, 0), text, font=f)
        if bbox[2] - bbox[0] <= max_width:
            return f
        size -= 2
    return ImageFont.truetype(font_path, min_size) if font_path else ImageFont.load_default()


def _draw_text_centered(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, center_y: int, box_width: int, fill, x_offset: int = 0) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = x_offset + (box_width - tw) // 2 - bbox[0]
    y = center_y - th // 2 - bbox[1]
    draw.text((x, y), text, font=font, fill=fill)


def build_breaking_news_banner(topic_text: str, font_path: Optional[str], duration: float) -> ImageClip:
    """Persistent broadcast-style top banner: a 'BREAKING NEWS' badge, a
    dynamic ticker line carrying THIS video's topic, and the channel's fixed
    tagline underneath - composited once and held for the whole video, the
    way a real news channel's on-screen furniture works. Held constant in
    position/size/color across every video for a consistent channel look;
    only the ticker line's text changes per story. Layout was rendered
    standalone and visually checked before being wired in here, rather than
    shipped unseen."""
    w = VIDEO_WIDTH
    h = int(VIDEO_HEIGHT * BANNER_HEIGHT_RATIO)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    badge_h = int(h * 0.32)
    ticker_h = int(h * 0.40)
    tagline_h = h - badge_h - ticker_h

    # Full-width, centered badge (was a 62%-width red block + blue filler,
    # which read as off-center/lopsided rather than centered).
    draw.rectangle([0, 0, w, badge_h], fill=(178, 24, 24, 255))
    f_badge = _fit_font(draw, "BREAKING NEWS", font_path, int(w * 0.9), int(badge_h * 0.62))
    _draw_text_centered(draw, "BREAKING NEWS", f_badge, badge_h // 2, w, (255, 255, 255, 255))

    draw.rectangle([0, badge_h, w, badge_h + ticker_h], fill=(150, 18, 18, 255))
    ticker_display = topic_text.upper()[:70]
    f_ticker = _fit_font(draw, ticker_display, font_path, int(w * 0.94), int(ticker_h * 0.55))
    _draw_text_centered(draw, ticker_display, f_ticker, badge_h + ticker_h // 2, w, (255, 255, 255, 255))

    draw.rectangle([0, badge_h + ticker_h, w, h], fill=(242, 242, 242, 255))
    f_tag = _fit_font(draw, CHANNEL_TAGLINE, font_path, int(w * 0.94), int(tagline_h * 0.55))
    _draw_text_centered(draw, CHANNEL_TAGLINE, f_tag, badge_h + ticker_h + tagline_h // 2, w, (25, 25, 25, 255))

    return ImageClip(np.array(img)).set_duration(duration).set_position((0, 0))


def build_watermark_clip(duration: float) -> Optional[ImageClip]:
    """Small semi-transparent logo in the top-right corner for the whole
    main-content duration. Skips gracefully (returns None) if LOGO_PATH
    doesn't exist - branding is a nice-to-have, never a hard requirement."""
    if not os.path.exists(LOGO_PATH):
        return None
    try:
        logo_img = Image.open(LOGO_PATH).convert("RGBA")
        target_w = int(VIDEO_WIDTH * WATERMARK_WIDTH_RATIO)
        ratio = target_w / logo_img.width
        target_h = max(1, int(logo_img.height * ratio))
        logo_img = logo_img.resize((target_w, target_h), Image.LANCZOS)

        alpha = logo_img.split()[3].point(lambda p: int(p * WATERMARK_OPACITY))
        logo_img.putalpha(alpha)

        margin = 32
        # Offset below the top banner (build_breaking_news_banner) so the two
        # don't overlap - the banner now occupies the top BANNER_HEIGHT_RATIO
        # of the frame on every video.
        top_offset = int(VIDEO_HEIGHT * BANNER_HEIGHT_RATIO) + margin
        return (
            ImageClip(np.array(logo_img))
            .set_duration(duration)
            .set_position((VIDEO_WIDTH - target_w - margin, top_offset))
        )
    except Exception as e:
        log.warning(f"  Watermark generation skipped: {e}")
        return None


def build_intro_sting() -> Optional[ImageClip]:
    """A short branded opening: the logo fading in/out on a black background.
    Adds INTRO_STING_DURATION seconds ON TOP of the 30-40s main content -
    total stays comfortably under YouTube's Shorts duration limit. Skips
    gracefully if LOGO_PATH doesn't exist."""
    if not os.path.exists(LOGO_PATH):
        return None
    try:
        logo_img = Image.open(LOGO_PATH).convert("RGBA")
        target_w = int(VIDEO_WIDTH * 0.45)
        ratio = target_w / logo_img.width
        target_h = max(1, int(logo_img.height * ratio))
        logo_img = logo_img.resize((target_w, target_h), Image.LANCZOS)

        black_bg = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 255))
        x = (VIDEO_WIDTH - target_w) // 2
        y = (VIDEO_HEIGHT - target_h) // 2
        black_bg.paste(logo_img, (x, y), logo_img)

        return (
            ImageClip(np.array(black_bg))
            .set_duration(INTRO_STING_DURATION)
            .fadein(0.25)
            .fadeout(0.2)
        )
    except Exception as e:
        log.warning(f"  Intro sting generation skipped: {e}")
        return None


def pick_background_music(duration: float) -> Optional[AudioFileClip]:
    """Picks a random track from MUSIC_DIR, loops it to cover `duration`, and
    lowers its volume to MUSIC_VOLUME so it sits under the voice, not over
    it. Returns None (no music) if MUSIC_DIR doesn't exist or is empty -
    this is expected until you drop your own royalty-free tracks in there."""
    if not os.path.isdir(MUSIC_DIR):
        return None
    candidates = [f for f in os.listdir(MUSIC_DIR) if f.lower().endswith((".mp3", ".wav", ".m4a", ".ogg"))]
    if not candidates:
        return None

    chosen = os.path.join(MUSIC_DIR, random.choice(candidates))
    try:
        music = AudioFileClip(chosen)
    except Exception as e:
        log.warning(f"  Could not load background music '{chosen}': {e}")
        return None

    try:
        if music.duration < duration:
            loops_needed = int(duration // music.duration) + 1
            music = concatenate_audioclips([music] * loops_needed)
        music = music.subclip(0, duration).volumex(MUSIC_VOLUME)
        return music
    except Exception as e:
        log.warning(f"  Background music processing failed, continuing without music: {e}")
        return None


def generate_thumbnail(video_path: str, pkg: ScriptPackage, font_path: Optional[str]) -> Optional[str]:
    """Zero-cost thumbnail: grabs a frame a little into the video (skipping
    the very first frame, which is often mid-transition) and overlays a
    short, bold headline using the same PIL text pipeline as the captions -
    no paid image-generation API needed. Output is the native 1080x1920
    vertical frame, since YouTube's own Shorts thumbnail guidance recommends
    9:16 (not the classic 16:9 long-form thumbnail size).

    HONEST CAVEAT: YouTube's Shorts swipe feed usually IGNORES a custom
    thumbnail and auto-picks its own frame regardless of what's uploaded here
    - this is a platform limitation, not a bug in this script. The custom
    thumbnail still shows in search results, the channel's video grid, and
    "Watch Later"/playlists, so it's not wasted, just not guaranteed to
    appear in the Shorts feed itself."""
    try:
        clip = VideoFileClip(video_path)
        grab_time = min(1.2, max(0.1, clip.duration * 0.06))
        frame = clip.get_frame(grab_time)
        clip.close()
    except Exception as e:
        log.warning(f"  Thumbnail frame extraction failed: {e}")
        return None

    try:
        img = Image.fromarray(frame).convert("RGB")
        draw = ImageDraw.Draw(img, "RGBA")
        w, h = img.size

        headline_plain = re.sub(r"[\U0001F300-\U0001FAFF\U00002600-\U000027BF]", "", pkg.title).strip()
        wrapped = textwrap.fill(headline_plain[:70] or "Breaking Tech News", width=16)
        lines = wrapped.split("\n")

        try:
            font = ImageFont.truetype(font_path, 84) if font_path else ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()

        line_heights = []
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font, stroke_width=6)
            line_heights.append(bbox[3] - bbox[1])
        line_spacing = 16
        block_height = sum(line_heights) + line_spacing * (len(lines) - 1) + 80

        draw.rectangle([0, h - block_height, w, h], fill=(0, 0, 0, 165))

        y = h - block_height + 40
        for line, lh in zip(lines, line_heights):
            bbox = draw.textbbox((0, 0), line, font=font, stroke_width=6)
            lw = bbox[2] - bbox[0]
            x = (w - lw) // 2
            draw.text(
                (x, y), line, font=font,
                fill=(255, 220, 0, 255), stroke_width=6, stroke_fill=(0, 0, 0, 255),
            )
            y += lh + line_spacing

        thumb_path = os.path.join(TEMP_DIR, f"thumb_{random.randint(1000,9999)}.jpg")
        img.save(thumb_path, "JPEG", quality=90)
        return thumb_path
    except Exception as e:
        log.warning(f"  Thumbnail rendering failed: {e}")
        return None


def set_youtube_thumbnail(video_id: str, thumbnail_path: str) -> bool:
    try:
        youtube = get_youtube_service()
        youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(thumbnail_path)).execute()
        log.info(f"  -> Custom thumbnail set for {video_id}")
        return True
    except Exception as e:
        log.warning(f"  Setting custom thumbnail failed (video still uploaded fine): {e}")
        return False


# ==============================================================================
# 10. FINAL VIDEO ASSEMBLY
# ==============================================================================
def assemble_final_video(
    bg_clip: VideoFileClip,
    caption_clips: List[ImageClip],
    audio_path: str,
    out_path: str,
    banner_topic: Optional[str] = None,
    font_path: Optional[str] = None,
) -> str:
    log.info("  Rendering final 1080p vertical video (this can take a while) ...")
    audio = AudioFileClip(audio_path).volumex(VOICE_VOLUME_BOOST)
    duration = audio.duration

    music = pick_background_music(duration)
    final_audio = CompositeAudioClip([audio, music]) if music is not None else audio

    bg_clip = bg_clip.set_duration(duration)
    watermark = build_watermark_clip(duration)
    banner = build_breaking_news_banner(banner_topic, font_path, duration) if banner_topic else None
    layers = (
        [bg_clip, *caption_clips]
        + ([watermark] if watermark is not None else [])
        + ([banner] if banner is not None else [])
    )

    main_content = CompositeVideoClip(layers, size=(VIDEO_WIDTH, VIDEO_HEIGHT)).set_duration(duration)
    main_content = main_content.set_audio(final_audio)

    intro = build_intro_sting()
    final = concatenate_videoclips([intro, main_content], method="compose") if intro is not None else main_content

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    final.write_videofile(
        out_path, fps=30, codec="libx264", audio_codec="aac",
        preset="medium", bitrate="6000k", threads=4, logger=None,
    )

    audio.close()
    if music is not None:
        music.close()
    final.close()
    log.info(f"  -> Final video saved: {out_path} ({final.duration:.1f}s total)")
    return out_path


# ==============================================================================
# 11. YOUTUBE: OAUTH, SCHEDULED UPLOAD, TIME-SLOT COMPUTATION
# ==============================================================================
YOUTUBE_UPLOAD_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_youtube_service():
    # Preferred path for CI: build credentials directly from a refresh token
    # obtained via OAuth Playground - no local browser flow, no token file.
    if YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET and YOUTUBE_REFRESH_TOKEN:
        creds = Credentials(
            token=None,
            refresh_token=YOUTUBE_REFRESH_TOKEN,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=YOUTUBE_CLIENT_ID,
            client_secret=YOUTUBE_CLIENT_SECRET,
            scopes=YOUTUBE_UPLOAD_SCOPES,
        )
        creds.refresh(GoogleAuthRequest())  # exchanges the refresh token for a fresh access token
        return build_google_service("youtube", "v3", credentials=creds)

    # Fallback path for local/Colab use: file-based token, refreshed or
    # created via a one-time browser consent flow.
    creds = None
    if os.path.exists(YOUTUBE_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(YOUTUBE_TOKEN_FILE, YOUTUBE_UPLOAD_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(GoogleAuthRequest())
        else:
            if not os.path.exists(YOUTUBE_CLIENT_SECRETS_FILE):
                raise RuntimeError(
                    f"No YouTube credentials available: set YOUTUBE_CLIENT_ID + "
                    f"YOUTUBE_CLIENT_SECRET + YOUTUBE_REFRESH_TOKEN (CI), or provide "
                    f"'{YOUTUBE_CLIENT_SECRETS_FILE}' for a local browser-based flow. "
                    f"See the OAuth setup notes at the top of this file."
                )
            flow = InstalledAppFlow.from_client_secrets_file(YOUTUBE_CLIENT_SECRETS_FILE, YOUTUBE_UPLOAD_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(YOUTUBE_TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return build_google_service("youtube", "v3", credentials=creds)


def _random_minute_in_window(start_h: int, start_m: int, end_h: int, end_m: int) -> Tuple[int, int]:
    start_total = start_h * 60 + start_m
    end_total = end_h * 60 + end_m
    span = max(1, end_total - start_total)
    target_total = start_total + random.randint(0, span - 1)
    return divmod(target_total, 60)


def compute_slot_datetime(slot_index: int) -> str:
    """Returns an RFC3339 UTC timestamp ('...Z') for a random minute inside
    the next available occurrence of the given slot window (0, 1, or 2),
    rolling to tomorrow if today's window is already within
    SLOT_MIN_LEAD_MINUTES of ending or fully in the past. Randomizing within
    the window (rather than a fixed HH:MM) avoids every video publishing at
    an identical, obviously-automated timestamp day after day."""
    tz = ZoneInfo(YOUTUBE_TIME_ZONE)
    now_local = datetime.now(tz)
    start_h, start_m, end_h, end_m = SLOT_WINDOWS[slot_index % len(SLOT_WINDOWS)]

    hour, minute = _random_minute_in_window(start_h, start_m, end_h, end_m)
    candidate = now_local.replace(hour=hour, minute=minute, second=0, microsecond=0)

    window_end_today = now_local.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
    if candidate <= now_local + timedelta(minutes=SLOT_MIN_LEAD_MINUTES) or window_end_today <= now_local + timedelta(minutes=SLOT_MIN_LEAD_MINUTES):
        hour, minute = _random_minute_in_window(start_h, start_m, end_h, end_m)
        candidate = (now_local + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)

    candidate_utc = candidate.astimezone(timezone.utc)
    return candidate_utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def _truncate_youtube_tags(tags: List[str], limit_chars: int = 460) -> List[str]:
    out, total = [], 0
    for t in tags:
        add_len = len(t) + 1
        if total + add_len > limit_chars:
            break
        out.append(t)
        total += add_len
    return out


def upload_video_to_youtube(video_path: str, pkg: ScriptPackage, publish_at_utc: str) -> Optional[str]:
    """Uploads as privacyStatus=private with publishAt set, so YouTube flips
    it to public automatically at that timestamp - no manual step needed.
    Returns the video ID, or None if the upload was skipped/failed (caller
    treats this as non-fatal; the video still exists locally + on Telegram)."""
    try:
        youtube = get_youtube_service()
    except Exception as e:
        log.warning(f"  YouTube auth unavailable, skipping upload: {e}")
        return None

    body = {
        "snippet": {
            "title": pkg.title[:100],
            "description": (pkg.description + "\n\n" + " ".join(pkg.hashtags))[:4900],
            "tags": _truncate_youtube_tags(pkg.tags),
            "categoryId": YOUTUBE_CATEGORY_ID,
            "defaultLanguage": "hi",
            "defaultAudioLanguage": "hi",
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": publish_at_utc,
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": True,  # honest disclosure: TTS voice + AI-written script
        },
    }
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")

    try:
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        response = None
        while response is None:
            status, response = request.next_chunk()
        video_id = response.get("id")
        log.info(f"  -> Uploaded to YouTube, scheduled {publish_at_utc}: https://studio.youtube.com/video/{video_id}/edit")
        return video_id
    except Exception as e:
        log.warning(f"  YouTube upload request failed: {e}")
        return None


# ------------------------------------------------------------------------------
# YouTube-only retry queue: a story whose VIDEO rendered fine but whose
# YouTube upload failed (bad/expired OAuth, quota, transient API error) is
# never re-rendered from scratch - only the upload itself is retried, using
# the locally-saved mp4 (OUTPUT_DIR is never cleaned up between cycles).
# ------------------------------------------------------------------------------
def load_pending_youtube_uploads(path: str = PENDING_YOUTUBE_UPLOADS_FILE) -> List[dict]:
    if not os.path.exists(path):
        return []
    items: List[dict] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except Exception as e:
                log.warning(f"  Skipping malformed pending-upload line: {e}")
    return items


def save_pending_youtube_uploads(items: List[dict], path: str = PENDING_YOUTUBE_UPLOADS_FILE) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")


def extract_telegram_file_id(telegram_response: dict) -> Optional[str]:
    """Digs the video file_id out of a sendVideo response - lets the retry
    queue re-fetch the video FROM Telegram if the local mp4 doesn't survive
    to the next scheduled run (see retry_pending_youtube_uploads)."""
    try:
        return telegram_response.get("result", {}).get("video", {}).get("file_id")
    except (AttributeError, TypeError):
        return None


def download_telegram_file(file_id: str, dest_path: str) -> Optional[str]:
    """Re-downloads a video the bot itself already sent, keyed by file_id -
    Telegram keeps files the bot uploaded available for repeat access. This
    is what lets the YouTube retry queue survive GitHub Actions' ephemeral
    runners: the local mp4 is gone by the next day, but the Telegram copy
    isn't. UNVERIFIED live (no network access while writing this fork) - if
    this never recovers a file, getFile's response shape is the first thing
    to check against Telegram's current Bot API docs."""
    try:
        info_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile"
        resp = requests.get(info_url, params={"file_id": file_id}, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        file_path = resp.json().get("result", {}).get("file_path")
        if not file_path:
            log.warning("  Telegram getFile returned no file_path.")
            return None
        download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
        return download_file(download_url, dest_path)
    except Exception as e:
        log.warning(f"  Could not re-download video from Telegram (file_id={str(file_id)[:20]}...): {e}")
        return None


def queue_pending_youtube_upload(video_path: str, pkg: ScriptPackage, slot_index: int, telegram_file_id: Optional[str] = None) -> None:
    pending = load_pending_youtube_uploads()
    pending.append({
        "video_path": video_path,
        "telegram_file_id": telegram_file_id,
        "title": pkg.title,
        "description": pkg.description,
        "hashtags": pkg.hashtags,
        "tags": pkg.tags,
        "slot_index": slot_index,
        "retry_count": 0,
        "queued_at": datetime.now(timezone.utc).isoformat(),
    })
    save_pending_youtube_uploads(pending)
    log.info(f"  Queued for YouTube-only retry later: {pkg.title[:50]}")


def retry_pending_youtube_uploads() -> None:
    """Called at the start of every daily batch, before touching new
    candidates, so a fixed OAuth token or transient API outage gets
    yesterday's failed uploads out the door before spending any NVIDIA LLM/Pexels
    budget on fresh stories.

    GitHub Actions gives every run a fresh VM, so a locally-saved mp4 from a
    prior run never survives to today - retry_pending_youtube_uploads() used
    to just drop the entry when os.path.exists(video_path) was False, which
    made the retry queue silently useless in exactly the deployment it's
    meant for. It now falls back to re-fetching the video from Telegram via
    the stored telegram_file_id (see process_single_story - Telegram delivery
    happens before the YouTube attempt specifically so this file_id exists
    even when the YouTube upload fails). Entries with no recoverable video,
    or that have exhausted MAX_YOUTUBE_UPLOAD_RETRIES, are dropped (logged,
    not silently)."""
    pending = load_pending_youtube_uploads()
    if not pending:
        return

    log.info(f"Retrying {len(pending)} pending YouTube upload(s) from previous cycles ...")
    still_pending: List[dict] = []
    for entry in pending:
        video_path = entry.get("video_path", "")
        title = entry.get("title", "")[:60]

        if not os.path.exists(video_path):
            telegram_file_id = entry.get("telegram_file_id")
            recovered_path = None
            if telegram_file_id:
                log.info(f"  Local file gone (expected on a fresh runner) - re-fetching from Telegram: {title}")
                recovered_path = download_telegram_file(
                    telegram_file_id, os.path.join(TEMP_DIR, f"retry_{random.randint(1000,9999)}.mp4")
                )
            if not recovered_path:
                log.warning(f"  Dropping pending upload - no local file and Telegram re-fetch failed/unavailable: {title}")
                continue
            video_path = recovered_path
        if entry.get("retry_count", 0) >= MAX_YOUTUBE_UPLOAD_RETRIES:
            log.warning(f"  Dropping pending upload after {entry.get('retry_count', 0)} failed retries: {title}")
            continue

        pkg_stub = ScriptPackage(
            script_en="", script_romanized="", title=entry.get("title", ""), description=entry.get("description", ""),
            hashtags=entry.get("hashtags", []), tags=entry.get("tags", []),
            thumbnail_idea="", visual_keywords=[],
        )
        publish_at = compute_slot_datetime(entry.get("slot_index", 0))

        video_id = None
        try:
            video_id = upload_video_to_youtube(video_path, pkg_stub, publish_at)
        except Exception as e:
            log.warning(f"  Retry upload raised an unexpected error: {e}")

        if video_id:
            log.info(f"  -> Pending upload succeeded on retry: {title}")
            thumb_path = generate_thumbnail(video_path, pkg_stub, find_caption_font())
            if thumb_path:
                set_youtube_thumbnail(video_id, thumb_path)
            log_decision("youtube_retry_succeeded", title)
        else:
            entry["video_path"] = video_path  # persist the recovered path in case this run retries it again below
            entry["retry_count"] = entry.get("retry_count", 0) + 1
            still_pending.append(entry)

    save_pending_youtube_uploads(still_pending)
    if still_pending:
        log.info(f"  {len(still_pending)} upload(s) still pending after this retry pass.")


# ==============================================================================
# 12. TELEGRAM DELIVERY
# ==============================================================================
def send_video_to_telegram(video_path: str, caption: Optional[str] = None) -> dict:
    log.info("  Uploading video to Telegram ...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"

    file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
    if file_size_mb > 49:
        log.warning(f"  Video is {file_size_mb:.1f}MB - close to/over Telegram's 50MB Bot API upload limit.")

    with open(video_path, "rb") as f:
        files = {"video": (os.path.basename(video_path), f, "video/mp4")}
        data = {"chat_id": TELEGRAM_CHAT_ID, "supports_streaming": True}
        if caption:
            data["caption"] = caption[:1024]
        resp = requests.post(url, data=data, files=files, timeout=600)
    if not resp.ok:
        raise RuntimeError(f"Telegram sendVideo failed: {resp.status_code} {resp.text}")
    log.info("  -> Video delivered to Telegram.")
    return resp.json()


def send_message_to_telegram(text: str) -> None:
    log.info("  Sending copy-paste metadata to Telegram ...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    for piece in textwrap.wrap(text, 3800, replace_whitespace=False, break_long_words=False):
        resp = requests.post(
            url, data={"chat_id": TELEGRAM_CHAT_ID, "text": piece, "disable_web_page_preview": True},
            timeout=60,
        )
        if not resp.ok:
            raise RuntimeError(f"Telegram sendMessage failed: {resp.status_code} {resp.text}")
    log.info("  -> Metadata delivered to Telegram.")


def format_metadata_message(pkg: ScriptPackage, news: NewsItem, publish_at_utc: Optional[str] = None) -> str:
    hashtags_line = " ".join(pkg.hashtags)
    tags_line = ", ".join(pkg.tags)
    schedule_line = f"\n\n🗓️ SCHEDULED (YouTube, UTC): {publish_at_utc}" if publish_at_utc else "\n\n🗓️ YouTube: not scheduled (upload skipped)"
    return (
        f"📌 TITLE:\n{pkg.title}\n\n"
        f"📝 DESCRIPTION:\n{pkg.description}\n\n"
        f"🏷️ HASHTAGS:\n{hashtags_line}\n\n"
        f"🔑 SEO TAGS:\n{tags_line}\n\n"
        f"💡 THUMBNAIL IDEA:\n{pkg.thumbnail_idea}\n\n"
        f"📰 SOURCE HEADLINE ({news.source_name}):\n{news.title}"
        f"{schedule_line}"
    )


# ==============================================================================
# 13. CLEANUP
# ==============================================================================
def cleanup_temp_files() -> None:
    try:
        import shutil
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
        os.makedirs(TEMP_DIR, exist_ok=True)
    except Exception as e:
        log.warning(f"Cleanup warning: {e}")


# ==============================================================================
# 14. SINGLE-STORY ORCHESTRATION (called up to DAILY_STORY_TARGET times/batch)
# ==============================================================================
def process_single_story(news: NewsItem, slot_index: int) -> bool:
    """Full pipeline for one story: script -> voice -> footage -> captions ->
    render -> YouTube (scheduled) -> Telegram. Returns True on a produced,
    delivered video; False if skipped (fact-check) or failed before a local
    video file existed (safe to retry another day). Once the local video file
    exists, the headline is marked processed immediately - YouTube/Telegram
    delivery failures after that point are logged but never trigger a
    re-render of the same story."""
    budget = LLMCallBudget(MAX_LLM_CALLS_PER_CYCLE)
    try:
        pkg, voice_path, words, audio_duration = generate_with_duration_enforcement(news, budget)
        pkg = romanize_metadata_if_needed(pkg, budget)
    except CredibilitySkipError as e:
        log.warning(f"  Skipping headline (fact-check flagged it): {e.note}")
        mark_headline_processed(news.title)
        log_decision("skipped_factcheck", news.title, e.note)
        return False
    except Exception:
        log.error(f"  Script generation failed for '{news.title[:60]}':")
        log.error(traceback.format_exc())
        log_decision("failed_script_generation", news.title, traceback.format_exc()[-200:])
        return False

    _ensure_shorts_hashtag(pkg)

    try:
        caption_words, used_romanization = build_romanized_word_timings(words, pkg.script_romanized)
        # Pick the font AFTER knowing whether captions ended up Hinglish (Latin
        # script, the normal case) or fell back to Devanagari - using the
        # Devanagari font for Latin text (or vice versa) is exactly what
        # caused the box-caption/banner bug. Latin also covers the banner and
        # thumbnail, both pure-Roman text regardless of this story's outcome.
        font_path = find_caption_font(need_devanagari=not used_romanization)
        caption_text = pkg.script_romanized if used_romanization else pkg.script_en
        caption_clips = build_caption_clips(caption_words, audio_duration, caption_text, font_path)
        fallback_query = news.title.split(" - ")[0][:60]
        bg_video = build_synced_background_video(pkg.shot_list, audio_duration, fallback_query)

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        safe_slug = re.sub(r"[^a-zA-Z0-9]+", "_", news.title.lower())[:40].strip("_")
        final_path = os.path.join(OUTPUT_DIR, f"short_{safe_slug or 'story'}.mp4")
        assemble_final_video(bg_video, caption_clips, voice_path, final_path, banner_topic=pkg.title, font_path=find_caption_font())
    except Exception:
        log.error(f"  Video rendering failed for '{news.title[:60]}':")
        log.error(traceback.format_exc())
        log_decision("failed_render", news.title, traceback.format_exc()[-200:])
        return False

    # Local video file exists now - mark processed so delivery failures below
    # can never cause this story to be re-generated on a future cycle.
    mark_headline_processed(news.title)

    publish_at = compute_slot_datetime(slot_index)

    # Telegram BEFORE the YouTube attempt: (a) it's the more reliable of the
    # two delivery channels, so the video lands somewhere durable earliest,
    # and (b) its file_id becomes the retry queue's recovery path if YouTube
    # fails AND the local mp4 doesn't survive to the next day's fresh runner
    # (see retry_pending_youtube_uploads's docstring for why that matters).
    telegram_file_id = None
    try:
        short_caption = f"{pkg.title}\n\n{' '.join(pkg.hashtags[:8])}\n\nScheduled: {publish_at}"
        tg_response = send_video_to_telegram(final_path, caption=short_caption)
        telegram_file_id = extract_telegram_file_id(tg_response)
    except Exception as e:
        log.warning(f"  Telegram video delivery failed (story already fully processed otherwise): {e}")

    video_id = None
    try:
        video_id = upload_video_to_youtube(final_path, pkg, publish_at)
    except Exception as e:
        log.warning(f"  Unhandled YouTube upload error (video saved locally): {e}")

    if not video_id:
        queue_pending_youtube_upload(final_path, pkg, slot_index, telegram_file_id=telegram_file_id)
        log_decision("rendered_youtube_queued", news.title, f"telegram_ok={bool(telegram_file_id)}")
    else:
        # pkg.title is always Hinglish/Roman, unlike font_path which could be
        # the Devanagari font if THIS story's captions fell back - a fresh
        # Latin-default call here (cheap, no download) keeps the thumbnail
        # correct independent of that.
        thumb_path = generate_thumbnail(final_path, pkg, find_caption_font())
        if thumb_path:
            set_youtube_thumbnail(video_id, thumb_path)
        log_decision("produced", news.title, f"youtube_id={video_id} publish_at={publish_at}")

    try:
        send_message_to_telegram(format_metadata_message(pkg, news, publish_at if video_id else None))
    except Exception as e:
        log.warning(f"  Telegram metadata message failed (story already fully processed otherwise): {e}")

    log.info(f"  Story processed successfully: {news.title[:60]}")
    return True


# ==============================================================================
# 15. DAILY BATCH ORCHESTRATION
# ==============================================================================
def run_daily_batch() -> int:
    """One full daily cycle: gather candidates (queue + fresh RSS), rank them
    with a single NVIDIA LLM call, produce up to DAILY_STORY_TARGET videos from
    the best of them (with backfill from the ranked pool if a top pick is
    skipped/fails), schedule each to YouTube's next available slot, deliver
    to Telegram, and persist the rest to queued_news.txt for future days."""
    retry_pending_youtube_uploads()

    processed = load_processed_headlines()
    queue_items = load_queue()
    fresh_items = scan_fresh_candidates(processed, exclude_items=queue_items)

    candidates = (queue_items + fresh_items)[:MAX_CANDIDATES_TO_SCORE]
    if not candidates:
        log.info("No candidate stories available (queue empty, no fresh whitelisted headlines).")
        save_queue([])
        return 0

    scored = score_candidate_stories(candidates)
    pool = [item for item, _score in scored]

    produced = 0
    slot_index = 0
    attempts = 0

    while produced < DAILY_STORY_TARGET and pool and attempts < MAX_DAILY_ATTEMPTS:
        attempts += 1
        news = pool.pop(0)
        try:
            ok = process_single_story(news, slot_index)
        except Exception:
            log.error(f"Unhandled failure processing '{news.title[:60]}':")
            log.error(traceback.format_exc())
            ok = False
        if ok:
            produced += 1
            slot_index += 1

    save_queue(pool)  # whatever's left unprocessed/unpicked goes back to the queue
    log.info(f"Daily batch complete: {produced}/{DAILY_STORY_TARGET} videos produced, "
             f"{len(pool)} candidate(s) requeued for future days.")
    return produced


# ==============================================================================
# 16. MAIN (single batch or infinite scheduling loop)
# ==============================================================================
def main() -> int:
    try:
        validate_config()
        os.makedirs(OUTPUT_DIR, exist_ok=True)
    except Exception as e:
        log.error(f"Startup validation failed: {e}")
        return 1

    if AUTO_LOOP_INTERVAL_HOURS <= 0:
        try:
            run_daily_batch()
            return 0
        except Exception:
            log.error("Daily batch failed with an unhandled exception:")
            log.error(traceback.format_exc())
            return 1
        finally:
            cleanup_temp_files()

    log.info(f"Continuous mode enabled: one batch every {AUTO_LOOP_INTERVAL_HOURS}h. Ctrl+C to stop.")
    while True:
        try:
            run_daily_batch()
        except Exception:
            log.error("Batch failed with an unhandled exception (will retry next cycle):")
            log.error(traceback.format_exc())
        finally:
            cleanup_temp_files()

        try:
            log.info(f"Sleeping {AUTO_LOOP_INTERVAL_HOURS}h until next batch ...")
            time.sleep(AUTO_LOOP_INTERVAL_HOURS * 3600)
        except KeyboardInterrupt:
            log.info("Interrupted by user. Exiting cleanly.")
            return 0


if __name__ == "__main__":
    sys.exit(main())
