# DaVinci Resolve run_script body: node 1 of <P>-out gets the CDL (from `resolve_take.py cdl`) and the skin
# LUT (from `resolve_take.py lut <name>`), then stills are exported for `resolve_take.py check`.
# CDL = None leaves the grade alone (pass-through stills for `cdl`); LUT = "" removes the LUT.
import time

P = "walmart-agents"
CDL = None  # the dict `resolve_take.py cdl` prints ({"NodeIndex": "1", "Slope": ..., "Saturation": "0.88"})
RESET = False  # True: node 1 back to unity CDL (for the pass-through frame `cdl` needs)
LUT = ""  # e.g. "MCP/walmart-agents-skin.cube" (relative to Resolve's LUT folder) or "" for none
STILLS_DIR = "/tmp"  # the session scratchpad
AT = ["01:00:10:00", "01:00:40:00"]

proj = resolve.GetProjectManager().GetCurrentProject()
out = [proj.GetTimelineByIndex(i) for i in range(1, proj.GetTimelineCount() + 1)]
out = next(t for t in out if t.GetName() == f"{P}-out")
proj.SetCurrentTimeline(out)
resolve.OpenPage("color")
item = out.GetItemListInTrack("video", 1)[0]
log = {}
if RESET:
    log["reset"] = item.SetCDL(
        {"NodeIndex": "1", "Slope": "1 1 1", "Offset": "0 0 0", "Power": "1 1 1", "Saturation": "1"}
    )
if CDL:
    log["cdl"] = item.SetCDL(CDL)
proj.RefreshLUTList()  # a .cube written by resolve_take.py is unknown to Resolve until refreshed
log["lut"] = item.GetNodeGraph().SetLUT(1, LUT)
# park elsewhere first: an export right after a grade change can return the cached, ungraded frame
out.SetCurrentTimecode("01:00:30:00")
time.sleep(2)
for tc in AT:
    out.SetCurrentTimecode(tc)
    time.sleep(2.5)
    name = f"{STILLS_DIR}/{P}-{tc.replace(':', '')}.png"
    log[name] = proj.ExportCurrentFrameAsStill(name)
result = log
