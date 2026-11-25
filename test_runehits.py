"""Runs RuneHits on Lua 5.1 against stubbed WoW APIs; checks the art and font exist. Needs: py -m pip install lupa"""
from pathlib import Path

from lupa.lua51 import LuaRuntime

DIR = Path(__file__).parent
for kind in ("red", "blue", "max"):
    assert (DIR / "art" / f"{kind}.tga").exists(), kind  # make_runehits_art.py draws them
for name in ("magic", "goblin", "fire", "splash", "sword"):
    assert (DIR / "sounds" / f"{name}.ogg").exists(), name  # make_runehits_sounds.py makes them
assert (DIR / "RuneHitsDigits.ttf").exists()

STUBS = r"""
NOW, FRAMES, CVAR, PLATES, ENEMY = 100, {}, {}, {}, {target = true}
SECRET = setmetatable({}, {__add = error, __sub = error, __mul = error, __div = error, __lt = error, __le = error,
    __concat = error, __len = error, __unm = error})   -- a secret value: no math, no comparing, no joining
function GetTime() return NOW end
SOUNDS = {}
function PlaySoundFile(f, ch) SOUNDS[#SOUNDS + 1] = f:match("sounds\\(%w+)%.ogg$"); assert(ch == "SFX") end
function issecretvalue(v) return v == SECRET end
CVAR.enableFloatingCombatText, CVAR.floatingCombatTextCombatDamage = "1", "1"
function SetCVar(k, v) CVAR[k] = v end
function GetCVar(k) return CVAR[k] end
function UnitCanAttack(_, u) return ENEMY[u] or false end
C_NamePlate = {GetNamePlateForUnit = function(u) return PLATES[u] end}
local mt = {}
function mock() return setmetatable({}, mt) end
local function set(k) return function(self, ...) rawset(self, "_" .. k, {...}) end end
mt.__index = function(_, k)
    if k == "SetText" then return function(self, s) rawset(self, "text", s) end end
    if k == "SetTexture" or k == "SetPoint" or k == "SetScale" or k == "SetFont" then return set(k) end
    if k == "Show" then return function(self) rawset(self, "on", true); SHOWN = self end end
    if k == "Hide" then return function(self) rawset(self, "on", false) end end
    if k == "SetShown" then return function(self, v) rawset(self, "on", v and true or false) end end
    if k == "SetScript" then return function(self, name, fn) rawset(self, name, fn) end end
    return function() return mock() end
end
UIParent, PLATE = mock(), mock()
SlashCmdList = {}
SPLATS = {}
function CreateFrame(_, _, parent)
    local o = mock()
    FRAMES[#FRAMES + 1] = o
    if parent == UIParent then SPLATS[#SPLATS + 1] = o end
    return o
end
"""

SCENARIO = r"""
local driver, events = FRAMES[1], FRAMES[2]
local function ev(...) events.OnEvent(events, ...) end
local function tick() driver.OnUpdate(driver, 0.01) end
local function art(s) return rawget(s.art, "_SetTexture")[1]:match("art\\(%w+)$") end
local function at(s) local p = rawget(s, "_SetPoint"); return p[2], p[4], p[5] end
ev("PLAYER_LOGIN")
assert(CVAR.floatingCombatTextCombatDamage == "0" and CVAR.enableFloatingCombatText == "0")
PLATES.target = PLATE
local function cast() ev("UNIT_SPELLCAST_SUCCEEDED", "player", "Cast-1", 133) end
cast()
ev("UNIT_COMBAT", "target", "WOUND", "", 120, 1)                -- a hit: red, just over the mob's nameplate
local a = SHOWN
assert(art(a) == "red" and rawget(a.text, "text") == 120 and rawget(a.text, "_SetFont")[2] == 15)
local region, x, y = at(a)
assert(region == PLATE and rawget(a, "_SetPoint")[3] == "TOP" and x == 0 and y == 26, tostring(y))
assert(SOUNDS[1] == "magic" and SOUNDS[2] == "goblin")             -- your cast's hit: the spell and the goblin
ev("UNIT_COMBAT", "target", "WOUND", "CRITICAL", 78, 1)          -- a crit: the gold rim, over the first, left
local b = SHOWN
assert(art(b) == "max" and select(2, at(b)) == -24 and select(3, at(b)) == 26 + 44)
assert(#SOUNDS == 2)                                             -- same instant: one sound, not a wall of noise
ev("UNIT_COMBAT", "target", "DODGE", "", 0, 1)                   -- a miss: blue 0, over the first, right
local c = SHOWN
assert(art(c) == "blue" and rawget(c.text, "text") == "0" and select(2, at(c)) == 24)
ev("UNIT_COMBAT", "target", "WOUND", "", 0, 1)                   -- a hit for nothing: blue 0 too, on top
assert(art(SHOWN) == "blue" and select(2, at(SHOWN)) == 0 and select(3, at(SHOWN)) == 26 + 88)
NOW = NOW + 0.1
ev("UNIT_COMBAT", "target", "WOUND", SECRET, SECRET, 1)          -- a fifth: takes the oldest's place, the first
local s = a                                                      -- the same frame, reused: no new one
assert(#SPLATS == 4 and rawget(s.text, "text") == SECRET and art(s) == "red" and select(3, at(s)) == 26)
ev("UNIT_COMBAT", "player", "WOUND", "", 30, 1)                 -- on you: over your head
local region2, _, y2 = at(SHOWN)
assert(region2 == UIParent and y2 == 90)
local n = #SPLATS
ev("UNIT_COMBAT", "target", "HEAL", "", 50, 1)                  -- heals: nothing
ENEMY.target = false; ev("UNIT_COMBAT", "target", "WOUND", "", 10, 1); ENEMY.target = true
assert(#SPLATS == n)
NOW = NOW + 1.15; tick()                                         -- the first four go after 1.2 s, the rest stay
assert(rawget(b, "on") == false and rawget(c, "on") == false and rawget(s, "on") == true)
NOW = NOW + 1; tick(); assert(rawget(s, "on") == false)
PLATES.target = nil
ev("UNIT_COMBAT", "target", "WOUND", "", 5, 1)                   -- nameplates off: over the middle of the screen
local region3, _, y3 = at(SHOWN)
assert(region3 == UIParent and y3 == 80 and #SPLATS == n)
RuneHitsDB.scale = 2; PLATES.target = PLATE; NOW = NOW + 2; tick()
ev("UNIT_COMBAT", "target", "WOUND", "", 5, 1)                   -- scaled: the offsets stay on screen
assert(select(3, at(SHOWN)) == 13)
NOW = NOW + 1; ev("UNIT_COMBAT", "player", "WOUND", "", 3, 1); assert(SOUNDS[#SOUNDS] == "sword")  -- hit on you: a sword
NOW = NOW + 1; cast(); ev("UNIT_COMBAT", "target", "PARRY", "", 0, 1); assert(SOUNDS[#SOUNDS] == "splash")
NOW = NOW + 1; cast(); ev("UNIT_COMBAT", "target", "WOUND", "CRITICAL", 9, 1); assert(SOUNDS[#SOUNDS] == "fire")
local heard = #SOUNDS
NOW = NOW + 1; cast(); NOW = NOW + 1.4; ev("UNIT_COMBAT", "target", "WOUND", "", 9, 1)  -- a bolt in flight: heard
assert(#SOUNDS == heard + 2); heard = #SOUNDS
NOW = NOW + 1; ev("UNIT_COMBAT", "target", "WOUND", "", 4, 1)    -- the DoT it left ticking: a splat, no sound
NOW = NOW + 3; ev("UNIT_COMBAT", "target", "WOUND", "", 4, 1)    -- a tick with no cast at all
NOW = NOW + 1; cast(); NOW = NOW + 1.6; ev("UNIT_COMBAT", "target", "WOUND", "", 4, 1)  -- a cast long gone
assert(#SOUNDS == heard)
ev("UNIT_SPELLCAST_CHANNEL_START", "player")                     -- Drain Life: each tick heard, a DoT between not
for i = 1, 3 do NOW = NOW + 1; ev("UNIT_COMBAT", "target", "WOUND", "", 6, 1) end
NOW = NOW + 0.3; ev("UNIT_COMBAT", "target", "WOUND", "", 4, 1)
assert(#SOUNDS == heard + 6); heard = #SOUNDS
ev("UNIT_SPELLCAST_CHANNEL_STOP", "player"); NOW = NOW + 1; ev("UNIT_COMBAT", "target", "WOUND", "", 4, 1)
assert(#SOUNDS == heard)
SlashCmdList.RUNEHITS("som"); NOW = NOW + 1; cast(); ev("UNIT_COMBAT", "target", "WOUND", "", 9, 1)
assert(#SOUNDS == heard); SlashCmdList.RUNEHITS("som")          -- muted
SlashCmdList.RUNEHITS("fonte 12"); NOW = NOW + 1; ev("UNIT_COMBAT", "target", "WOUND", "", 9, 1)
assert(rawget(SHOWN.text, "_SetFont")[2] == 12)
assert(rawget(SHOWN.text, "_SetFont")[1] == "Interface\\AddOns\\RuneHits-main\\RuneHitsDigits.ttf")  -- files from its own folder
SlashCmdList.RUNEHITS("altura 60"); assert(RuneHitsDB.above == 60)
SlashCmdList.RUNEHITS("blizz"); assert(CVAR.floatingCombatTextCombatDamage == "1" and RuneHitsDB.saved == nil)
SlashCmdList.RUNEHITS("debug"); ev("UNIT_COMBAT", "target", "WOUND", "", 8, 1); SlashCmdList.RUNEHITS("debug")
SlashCmdList.RUNEHITS("teste")
"""

lua = LuaRuntime()
lua.execute(STUBS)
load = lua.eval("function(src, name) return assert(loadstring(src, name)) end")
assert (DIR / "RuneHits.toc").read_bytes() == (DIR / "RuneHits-main.toc").read_bytes()  # GitHub's zip folder: same toc
load((DIR / "RuneHits.lua").read_text(encoding="utf-8"), "RuneHits.lua")("RuneHits-main", lua.table())
lua.execute(SCENARIO)
print("ok")
