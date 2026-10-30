# DaVinci Resolve run_script body: render <P>-out. AUDIO_ONLY=True is a 3 s loudness test (measure it with
# `resolve_take.py check`); the master is H.265 Main10 2160x3840 with 24-bit PCM. Waits up to 55 s
# (the tool's limit is 60); a full 62 s 4K render takes ~32 s on this Mac. Re-run to keep waiting.
import time

P = "walmart-agents"
TARGET_DIR = "/Users/acme/Downloads"
NAME = f"{P}-graded"
AUDIO_ONLY = False

proj = resolve.GetProjectManager().GetCurrentProject()
out = [proj.GetTimelineByIndex(i) for i in range(1, proj.GetTimelineCount() + 1)]
out = next(t for t in out if t.GetName() == f"{P}-out")
proj.SetCurrentTimeline(out)
resolve.OpenPage("deliver")
for j in proj.GetRenderJobList():
    proj.DeleteRenderJob(j["JobId"])
# ExportVideo is sticky across jobs: set it explicitly BEFORE the format (an audio-only test left it off once)
proj.SetRenderSettings({"ExportVideo": not AUDIO_ONLY, "ExportAudio": True})
proj.SetCurrentRenderFormatAndCodec("mov", "H265")
proj.SetRenderSettings(
    {
        "SelectAllFrames": True,
        "TargetDir": TARGET_DIR,
        "CustomName": NAME + ("-audiotest" if AUDIO_ONLY else ""),
        "FormatWidth": int(proj.GetSetting("timelineResolutionWidth")),
        "FormatHeight": int(proj.GetSetting("timelineResolutionHeight")),
        "EncodingProfile": "Main10",
        "AudioCodec": "lpcm",
        "AudioBitDepth": 24,
        "AudioSampleRate": 48000,
    }
)
jid = proj.AddRenderJob()
job = next(j for j in proj.GetRenderJobList() if j["JobId"] == jid)
proj.StartRendering([jid])
t0 = time.time()
while proj.IsRenderingInProgress() and time.time() - t0 < 55:
    time.sleep(2)
result = {
    "timeline": job["TimelineName"],
    "video": job["IsExportVideo"],
    "codec": job["VideoCodec"],
    "file": f"{TARGET_DIR}/{job['OutputFilename']}",
    "status": proj.GetRenderJobStatus(jid),
}
