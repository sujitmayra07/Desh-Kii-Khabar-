#!/usr/bin/env python3
"""
Standalone kill-switch for the India pipeline: given one or more YouTube
video IDs, sets each back to `private`, which cancels any pending scheduled
`publishAt` so it will NOT go public automatically.

Use this if the Telegram review copy of a video turns up something wrong
before its scheduled time hits - the pipeline schedules ahead of time
specifically to leave this window open (see news_to_video_india.py's
changelog, "round 2" entry, for why a real-time approve/reject gate wasn't
built into the automated pipeline itself instead of this).

Cancelling does NOT remove the headline from processed_news_india.txt, so
the story will not be re-attempted automatically - deliberately simple,
re-run it by hand later if you actually want a redo.

USAGE (local):
    python cancel_upload.py VIDEO_ID [VIDEO_ID ...]
    python cancel_upload.py "id1, id2, id3"          # comma/space separated also works

USAGE (GitHub Actions, no local setup needed):
    Actions tab -> "India: Cancel a scheduled upload" -> Run workflow ->
    paste the video ID(s).

Must sit in the SAME directory as news_to_video_india.py - it imports
get_youtube_service() from there directly rather than duplicating the OAuth
logic, so it always stays in sync with however the main script authenticates
(same GitHub Secrets, no separate credential setup). Because of that import,
this script also needs every package news_to_video_india.py imports at
module level to be installed, even though it only actually calls the
YouTube-auth function - see india_geo_cancel.yml's pip install line, which
mirrors the main workflow's for exactly this reason.
"""
import sys

from news_to_video_india import get_youtube_service


def cancel_upload(video_id: str) -> bool:
    """Sets a video's privacyStatus to 'private', which per the YouTube Data
    API's documented videos.update behavior also cancels any pending
    scheduled publishAt on that video."""
    try:
        youtube = get_youtube_service()
        youtube.videos().update(
            part="status",
            body={"id": video_id, "status": {"privacyStatus": "private"}},
        ).execute()
        print(f"OK: {video_id} set to private - it will NOT auto-publish.")
        return True
    except Exception as e:
        print(f"FAILED: {video_id} - {e}")
        return False


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python cancel_upload.py VIDEO_ID [VIDEO_ID ...]")
        return 1
    ids = [
        v.strip()
        for arg in sys.argv[1:]
        for v in arg.replace(",", " ").split()
        if v.strip()
    ]
    if not ids:
        print("No video IDs given.")
        return 1
    results = [cancel_upload(v) for v in ids]
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
