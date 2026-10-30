# DaVinci Resolve run_script body (MCP `run_script`; `resolve` is injected, `result` is returned).
# Builds one take's project: settings, the clip, and three timelines. Paste the constants that
# `scripts/resolve_take.py inspect` prints. Idempotent: existing timelines of the same name are reused.
#   <P>-source   the clip's audio: Dialogue Leveler + clip gain to TARGET_LUFS + PUSH_DB (Resolve's analysis)
#   <P>-limiter  audio only: <P>-source nested, Fairlight Limiter on the clip, -2 dB after it
#   <P>-out      video: the raw clip again (graded here, so colour is converted once);
#                audio: <P>-limiter nested, a linear trim (OUT_TRIM_DB) set from an audio-only test render
P = "walmart-agents"  # project + timeline prefix (the project slug)
SOURCE = "/Users/acme/Downloads/take.MOV"
MODE = "baked_rec709"  # baked_rec709 | apple_log | apple_log_2 (from `inspect`)
TARGET_LUFS = -14
LIMITER_TRIM_DB = -2.0  # on the <P>-limiter clip (the Limiter's ceiling is ~0 dBFS)
OUT_TRIM_DB = 0.0
PUSH_DB = 4.0  # into the Limiter: the render lands at TARGET_LUFS, peaks at about -2.2 dBTP (walmart-agents)

pm = resolve.GetProjectManager()
proj = pm.GetCurrentProject()
if proj is None or proj.GetName() != P:
    pm.SaveProject()  # switching projects must not drop unsaved work in the open one
    proj = pm.LoadProject(P) or pm.CreateProject(P)
mp = proj.GetMediaPool()
log = {}

clip = None
for c in mp.GetRootFolder().GetClipList():
    if c.GetClipProperty("File Path") == SOURCE:
        clip = c
if clip is None:
    clip = mp.ImportMedia([SOURCE])[0]
w, h = clip.GetClipProperty("Resolution").split("x")
frames = int(clip.GetClipProperty("Frames"))

settings = {
    "timelineResolutionWidth": w,
    "timelineResolutionHeight": h,
    "timelineFrameRate": str(int(float(clip.GetClipProperty("FPS")))),
}
if MODE == "baked_rec709":
    # already Rec.709: no colour management, the pixels pass through untouched
    settings.update(
        {
            "colorScienceMode": "davinciYRGB",
            "separateColorSpaceAndGamma": "0",
            "colorSpaceTimeline": "Rec.709 Gamma 2.4",
            "colorSpaceOutput": "Rec.709 Gamma 2.4",
        }
    )
else:
    # real log: RCM, DaVinci WG / Intermediate timeline, Rec.709 Gamma 2.4 out
    settings.update(
        {
            "colorScienceMode": "davinciYRGBColorManagedv2",
            "rcmPresetMode": "Custom",
            "separateColorSpaceAndGamma": "1",
            "isAutoColorManage": "0",
            "colorSpaceTimeline": "DaVinci WG",
            "colorSpaceTimelineGamma": "DaVinci Intermediate",
            "colorSpaceOutput": "Rec.709",
            "colorSpaceOutputGamma": "Gamma 2.4",
            "inputDRT": "DaVinci",
            "outputDRT": "DaVinci",
        }
    )
for k, v in settings.items():
    log[k] = proj.SetSetting(k, v)
if MODE == "apple_log_2":
    log["input"] = clip.SetClipProperty("Input Color Space", "Apple Log 2")  # gamma reads "Apple Log"


def timeline(name):
    for i in range(1, proj.GetTimelineCount() + 1):
        t = proj.GetTimelineByIndex(i)
        if t.GetName() == name:
            return t, False
    return mp.CreateEmptyTimeline(name), True


def pool_item(name):
    for c in mp.GetRootFolder().GetClipList():
        if c.GetClipProperty("Type") == "Timeline" and c.GetName() == name:
            return c
    return None


def append(t, item, media_type):
    proj.SetCurrentTimeline(t)
    mp.AppendToTimeline(
        [
            {
                "mediaPoolItem": item,
                "startFrame": 0,
                "endFrame": frames,
                "mediaType": media_type,
                "trackIndex": 1,
                "recordFrame": t.GetStartFrame(),
            }
        ]
    )


src, new = timeline(f"{P}-source")
if new:
    append(src, clip, 2)  # audio only: the picture is graded on <P>-out
proj.SetCurrentTimeline(src)
a = src.GetItemListInTrack("audio", 1)[0]
for k, v in [
    ("AudioDialogueLevelerEnabled", True),
    ("AudioDialogueLevelerMode", resolve.DIALOGUE_LEVELER_MODE_OPTIMIZE_MODERATE_LEVELS),
    ("AudioDialogueLevelerReduceLoudDialogue", True),
    ("AudioDialogueLevelerLiftSoftDialogue", True),
    ("AudioDialogueLevelerBackgroundReduction", False),
    ("AudioVolumeEnabled", True),
    ("AudioVolume", 0.0),
]:
    a.SetProperty(k, v)
before = a.AnalyzeAudioLevels("ITU-R BS.1770-4")["Integrated"]
gain = max(-100.0, min(30.0, TARGET_LUFS + PUSH_DB - before))
a.SetProperty("AudioVolume", gain)
log["source_gain_db"] = round(gain, 2)
log["source_analysis"] = a.AnalyzeAudioLevels("ITU-R BS.1770-4")

lim, new = timeline(f"{P}-limiter")
if new:
    append(lim, pool_item(f"{P}-source"), 2)
proj.SetCurrentTimeline(lim)
la = lim.GetItemListInTrack("audio", 1)[0]
if not la.GetEffects("audio"):
    la.AddEffect("audio", "Audio FX/Fairlight FX/Limiter")
la.SetProperty("AudioVolumeEnabled", True)
la.SetProperty("AudioVolume", LIMITER_TRIM_DB)

out, new = timeline(f"{P}-out")
if new:
    append(out, clip, 1)
    append(out, pool_item(f"{P}-limiter"), 2)
proj.SetCurrentTimeline(out)
oa = out.GetItemListInTrack("audio", 1)[0]
oa.SetProperty("AudioVolumeEnabled", True)
oa.SetProperty("AudioVolume", OUT_TRIM_DB)
log["out"] = {
    "video": [(x.GetName(), x.GetDuration()) for x in out.GetItemListInTrack("video", 1)],
    "audio": [(x.GetName(), x.GetDuration()) for x in out.GetItemListInTrack("audio", 1)],
}
result = log
