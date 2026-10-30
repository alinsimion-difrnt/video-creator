# TikTok candidates (discovered 2026-10-13)

The raw candidate lists that `studies/tiktok/sources.yaml` (the 200) is picked from. Ids and handles only.

- `creators.jsonl`: Robert's 50 accounts (Perplexity's list), checked with each account's creator embed
  (`tiktok.com/embed/@handle`). An account with `"videos": []` gave no videos: the handle does not exist on
  TikTok, or its embed did not load.
- `topics.jsonl`: TikTok discover pages for topic phrases (`tiktok.com/discover/<phrase>`). An empty list
  means the page had no video links for a headless browser.

Made with `node study/web/tiktok.cjs list <url>` (studies/README.md, "Find").
