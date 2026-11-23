-- RuneHits: Old School RuneScape-style hitsplats for WoW Forever. A red blood splash for a hit, a blue one with 0 for
-- a miss (or a hit that does nothing), a red one with gold-tipped rays for a crit (OSRS' "max hit"). They sit on the
-- mob itself, as in OSRS: pinned to its nameplate (Forever won't let an addon measure a nameplate, but anchoring to
-- one is allowed) and lowered onto the body. Hits landing together take OSRS' places: center, above, below left,
-- below right; each stays LIFE seconds and is gone, no rising, no fading. A big number runs past the splat's edge,
-- as in OSRS. Art, digits and sounds: make_runehits_art.py and make_runehits_sounds.py (own work, no game files);
-- any .ogg dropped in sounds/ with the same name plays instead. Amounts come from UNIT_COMBAT; a secret one goes
-- whole to the font string.
-- /rh on/off  ·  /rh teste  ·  /rh som  ·  /rh escala 1.2  ·  /rh corpo 40  ·  /rh eu -20  ·  /rh blizz  ·  /rh debug
local ART = "Interface\\AddOns\\RuneHits\\art\\"
local SOUND = "Interface\\AddOns\\RuneHits\\sounds\\"
local FONT = "Interface\\AddOns\\RuneHits\\RuneHitsDigits.ttf"
local PX = 2                                       -- screen pixels per art pixel
local CELL = 32 * PX                               -- the splat's texture: a 32-pixel cell with the splat inside
local TEXT = 15                                    -- the digits' size: 9-pixel digits 13.5 tall on a 46-tall splat
local SLOTS = {{0, 0}, {0, 22}, {-12, -22}, {12, -22}} -- art pixels: where hits landing together go
local LIFE = 1.2                                   -- two game ticks of OSRS
local ART_OF = {hit = "red", crit = "max", miss = "blue"}
local QUIET = 0.08                                 -- seconds between two sounds: an AoE doesn't turn into noise
-- sounds/<name>.ogg played together for each event; drop your own file under the same name to replace one
local SOUNDS = {hit = {"magic", "goblin"}, crit = {"fire"}, miss = {"splash"}, taken = {"sword"}}
-- the game's own combat text: damage over mobs, DoTs, pets, heals, and the text on you (enableFloatingCombatText)
local CVARS = {"enableFloatingCombatText", "floatingCombatTextCombatDamage", "floatingCombatTextCombatDamage_v2",
    "floatingCombatTextCombatLogPeriodicSpells", "floatingCombatTextCombatLogPeriodicSpells_v2",
    "floatingCombatTextPetMeleeDamage", "floatingCombatTextPetMeleeDamage_v2", "floatingCombatTextPetSpellDamage",
    "floatingCombatTextPetSpellDamage_v2", "floatingCombatTextCombatHealing", "floatingCombatTextCombatHealing_v2"}

local DB
local pool, live, busy = {}, {}, {}                -- spare splats; splats shown; unit -> slot -> splat
local function secret(v) return issecretvalue and issecretvalue(v) end

-- a splat: the number (white, black shadow down-right) over the splash
local function newSplat()
    local s = CreateFrame("Frame", nil, UIParent)
    s:SetSize(CELL, CELL)
    s:SetFrameStrata("HIGH")
    s.art = s:CreateTexture(nil, "ARTWORK")
    s.art:SetAllPoints()
    s.text = s:CreateFontString(nil, "OVERLAY")
    s.text:SetFont(FONT, TEXT, "")                 -- a font pixel is a tenth of the size
    s.text:SetShadowColor(0, 0, 0, 1)
    s.text:SetShadowOffset(PX, -PX)
    s.text:SetPoint("CENTER", s, "CENTER", PX / 2, 0) -- the gap after the last digit, evened out
    return s
end

local lastSound = 0
local function sound(event)
    local now = GetTime()
    if DB.mute or now - lastSound < QUIET then return end
    lastSound = now
    for _, name in ipairs(SOUNDS[event]) do PlaySoundFile(SOUND .. name .. ".ogg", "SFX") end
end

local function free(s)
    s:Hide()
    live[s] = nil
    busy[s.unit][s.slot] = nil
    pool[#pool + 1] = s
end

-- where a unit's hits go: on the mob's body, under its nameplate; you, about where your character stands
local function anchor(unit)
    if unit == "player" then return UIParent, 0, DB.me or -20 end
    local plate = C_NamePlate and C_NamePlate.GetNamePlateForUnit(unit)
    if plate then return plate, 0, -(DB.body or 40) end
    return UIParent, 0, DB.noPlate or 80           -- nameplates off: a bit over the middle of the screen
end

local function spawn(unit, text, kind)
    local slots = busy[unit] or {}
    busy[unit] = slots
    local slot, oldest
    for i = 1, #SLOTS do
        if not slots[i] then slot = i break end
        if not oldest or slots[i].t0 < slots[oldest].t0 then oldest = i end
    end
    if not slot then
        slot = oldest
        free(slots[slot])
    end
    local s = table.remove(pool) or newSplat()
    s.text:SetFont(FONT, DB.font or TEXT, "")
    s.text:SetText(text)                           -- a secret only goes to SetText
    s.art:SetTexture(ART .. ART_OF[kind])
    sound(kind == "miss" and "miss" or unit == "player" and "taken" or kind)
    local size = DB.scale or 1
    local region, x, y = anchor(unit)
    local dx, dy = SLOTS[slot][1] * PX + x / size, SLOTS[slot][2] * PX + y / size
    s:SetScale(size)
    s:ClearAllPoints()
    if not pcall(s.SetPoint, s, "CENTER", region, "CENTER", dx, dy) then
        s:SetPoint("CENTER", UIParent, "CENTER", dx, SLOTS[slot][2] * PX + (DB.noPlate or 80) / size)
    end
    s:SetFrameLevel(10 + slot)
    s.unit, s.slot, s.t0 = unit, slot, GetTime()
    slots[slot], live[s] = s, true
    s:Show()
end

local driver = CreateFrame("Frame")
driver:SetScript("OnUpdate", function()
    local now = GetTime()
    for s in pairs(live) do
        if now - s.t0 >= LIFE then free(s) end
    end
end)

local function onCombat(unit, action, descriptor, amount)
    if not (DB and DB.on) then return end
    if DB.debug and not secret(action) then
        print("RuneHits:", unit, action, secret(amount) and "(secreto)" or amount,
            unit ~= "player" and (C_NamePlate.GetNamePlateForUnit(unit) and "na nameplate" or "sem nameplate") or "")
    end
    if unit ~= "player" and (unit ~= "target" or not UnitCanAttack("player", unit)) then return end
    if secret(action) then action = "WOUND" end
    if action == "HEAL" or action == "ENERGIZE" then return end -- OSRS has no splat for them
    if action ~= "WOUND" or amount == nil or (not secret(amount) and type(amount) == "number" and amount <= 0) then
        return spawn(unit, "0", "miss")            -- missed, dodged, parried, resisted, absorbed: a blue 0
    end
    local crit = not secret(descriptor) and descriptor == "CRITICAL"
    spawn(unit, amount, crit and "crit" or "hit")
end

-- the game's own combat text: off while RuneHits draws; your own settings come back with /rh blizz
local function blizzard(show)
    DB.saved = DB.saved or {}
    for _, cv in ipairs(CVARS) do
        local now = GetCVar(cv)
        if now ~= nil then -- a setting this client has
            if not show and DB.saved[cv] == nil and now ~= "0" then DB.saved[cv] = now end
            pcall(SetCVar, cv, show and (DB.saved[cv] or "1") or "0")
        end
    end
    if show then DB.saved = nil end
end

local f = CreateFrame("Frame")
f:RegisterEvent("PLAYER_LOGIN")
f:RegisterEvent("PLAYER_ENTERING_WORLD") -- the game can reapply its settings after login
f:RegisterEvent("UNIT_COMBAT")
f:SetScript("OnEvent", function(_, event, ...)
    if event == "UNIT_COMBAT" then return onCombat(...) end
    RuneHitsDB = RuneHitsDB or {on = true, hideBlizz = true}
    DB = RuneHitsDB
    if DB.on and DB.hideBlizz then blizzard(false) end
    if event == "PLAYER_LOGIN" and C_AddOns and C_AddOns.IsAddOnLoaded and C_AddOns.IsAddOnLoaded("MapleHits") then
        print("RuneHits: o MapleHits também está ligado, os dois vão desenhar. Desligue um na lista de addons.")
    end
end)

SLASH_RUNEHITS1 = "/rh"
SlashCmdList.RUNEHITS = function(msg)
    local cmd, arg = msg:match("^(%S*)%s*(.-)$")
    if cmd == "teste" then -- four at once on the target (a crit, two hits, a miss), one on you
        for _, v in ipairs({{78, "crit"}, {12, "hit"}, {0, "miss"}, {346, "hit"}}) do
            spawn("target", tostring(v[1]), v[2])
        end
        spawn("player", "7", "hit")
    elseif cmd == "som" then
        DB.mute = not DB.mute
        print("RuneHits: sons " .. (DB.mute and "desligados" or "ligados"))
    elseif cmd == "fonte" and tonumber(arg) then -- the digits' size (15; 20 fills the splat)
        DB.font = tonumber(arg)
    elseif cmd == "escala" and tonumber(arg) then
        DB.scale = tonumber(arg)
    elseif cmd == "corpo" and tonumber(arg) then -- how far under the nameplate: the mob's body
        DB.body = tonumber(arg)
    elseif cmd == "eu" and tonumber(arg) then -- your hits taken, from the screen's middle
        DB.me = tonumber(arg)
    elseif cmd == "debug" then
        DB.debug = not DB.debug
        print("RuneHits: debug " .. (DB.debug and "ligado" or "desligado"))
    elseif cmd == "blizz" then
        DB.hideBlizz = not DB.hideBlizz
        blizzard(not DB.hideBlizz)
        print("RuneHits: números do jogo " .. (DB.hideBlizz and "escondidos" or "de volta"))
    elseif cmd == "" then
        DB.on = not DB.on
        blizzard(not (DB.on and DB.hideBlizz))
        print("RuneHits: " .. (DB.on and "ligado" or "desligado"))
    else
        print("RuneHits: /rh  ·  teste  ·  som  ·  fonte 15  ·  escala 1.2  ·  corpo 40 (abaixo da nameplate)  ·  eu -20  ·  blizz  ·  debug")
    end
end
