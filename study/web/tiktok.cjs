// TikTok through a headless Chromium (studies/README.md). TikTok's video pages and yt-dlp are blocked from
// the cloud; its discover/tag pages, creator embeds and the embed player are not (docs/external-facts.md).
//
//   node study/web/tiktok.cjs list <page url> [scrolls]     -> JSON [{id, handle}] of the videos linked
//   node study/web/tiktok.cjs meta <ids file> <out dir>      -> <out>/<id>.json (caption, stats, length)
//   node study/web/tiktok.cjs fetch <ids file> <out dir>     -> <id>.json and <id>.mp4 (skips existing)
//
// One browser serves a whole batch. Media goes to data/ (never committed).
const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

const PW = path.join(execSync("npm root -g").toString().trim(), "playwright");
const { chromium } = require(PW);
const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36";

async function browser() {
  const b = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium", args: ["--no-sandbox"] });
  const ctx = await b.newContext({ userAgent: UA, viewport: { width: 1280, height: 900 } });
  return { b, ctx };
}

async function list(url, scrolls) {
  const { b, ctx } = await browser();
  const p = await ctx.newPage();
  await p.goto(url, { waitUntil: "domcontentloaded", timeout: 45000 });
  await p.waitForTimeout(7000);
  for (let i = 0; i < scrolls; i++) { await p.mouse.wheel(0, 3000); await p.waitForTimeout(1500); }
  const hrefs = await p.$$eval("a", (as) => as.map((a) => a.href));
  const seen = new Map();
  for (const h of hrefs) {
    const m = h.match(/tiktok\.com\/@([^/?#]+)\/video\/(\d{15,})/);
    if (m && !seen.has(m[2])) seen.set(m[2], { id: m[2], handle: m[1] });
  }
  await b.close();
  return [...seen.values()];
}

function itemOf(state, id) {
  const data = state.source && state.source.data;
  const key = Object.keys(data || {}).find((k) => k.includes(id));
  const vd = key && data[key].videoData;
  if (!vd) return null;
  const it = vd.itemInfos, au = vd.authorInfos || {}, mu = vd.musicInfos || {};
  return {
    id: it.id, text: it.text, create_time: Number(it.createTime), duration_s: it.video.videoMeta.duration,
    width: it.video.videoMeta.width, height: it.video.videoMeta.height,
    plays: it.playCount, likes: it.diggCount, comments: it.commentCount, shares: it.shareCount,
    handle: au.uniqueId, nickname: au.nickName, music: mu.musicName, music_author: mu.authorName,
    music_original: mu.original,
  };
}

function videoUrls(state, id) {
  const data = state.source && state.source.data;
  const key = Object.keys(data || {}).find((k) => k.includes(id));
  const it = key && data[key].videoData && data[key].videoData.itemInfos;
  return (it && it.video && it.video.urls) || [];
}

async function embed(ctx, id, out, withMedia) {
  const jf = path.join(out, id + ".json"), vf = path.join(out, id + ".mp4");
  if (fs.existsSync(jf) && (!withMedia || fs.existsSync(vf))) return "cached";
  const p = await ctx.newPage();
  try {
    await p.goto("https://www.tiktok.com/embed/v2/" + id, { waitUntil: "domcontentloaded", timeout: 45000 });
    await p.waitForTimeout(3000);
    const raw = await p.evaluate(() => {
      const s = document.getElementById("__FRONTITY_CONNECT_STATE__");
      return s ? s.textContent : null;
    });
    const meta = raw && itemOf(JSON.parse(raw), id);
    if (!meta) return "no-data";
    meta.fetched_at = new Date().toISOString();
    if (withMedia) {
      // the item's own address (the page's first <video> is a TikTok promo clip, not this video)
      const urls = (raw && JSON.parse(raw).source) ? videoUrls(JSON.parse(raw), id) : [];
      let ok = false;
      for (const s of urls) {
        const r = await ctx.request.get(s, { headers: { Referer: "https://www.tiktok.com/" }, timeout: 90000 });
        const buf = await r.body();
        if (r.ok() && buf.length > 50000) { fs.writeFileSync(vf, buf); ok = true; break; }
      }
      if (!ok) return "no-media";
    }
    fs.writeFileSync(jf, JSON.stringify(meta, null, 1));
    return "ok";
  } catch (e) {
    return "error: " + String(e.message || e).split("\n")[0];
  } finally {
    await p.close();
  }
}

async function batch(idsFile, out, withMedia) {
  const ids = fs.readFileSync(idsFile, "utf8").split(/\s+/).filter(Boolean);
  fs.mkdirSync(out, { recursive: true });
  const { b, ctx } = await browser();
  const workers = Number(process.env.TIKTOK_PAGES || 3);  // pages open at once
  let next = 0;
  await Promise.all(Array.from({ length: workers }, async () => {
    while (next < ids.length) {
      const id = ids[next++];
      console.log(id, await embed(ctx, id, out, withMedia));
    }
  }));
  await b.close();
}

(async () => {
  const [cmd, a, c] = process.argv.slice(2);
  if (cmd === "list") console.log(JSON.stringify(await list(a, Number(c || 4))));
  else if (cmd === "meta") await batch(a, c, false);
  else if (cmd === "fetch") await batch(a, c, true);
  else { console.error("usage: tiktok.cjs list <url> [scrolls] | meta|fetch <ids file> <out dir>"); process.exit(2); }
})();
