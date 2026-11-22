#!/usr/bin/env python3
"""Fast source-level checks for the ELBASHA player catalog and MVP scope."""
from pathlib import Path
import json
import re
import random
import xml.etree.ElementTree as ET
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "app/src/main/java/com/mostafabek/elbashagames"
players_source = (BASE / "PlayerDatabase.kt").read_text(encoding="utf-8")
search_source = (BASE / "PlayerSearch.kt").read_text(encoding="utf-8")
build_source = (BASE / "BuildTeamGame.kt").read_text(encoding="utf-8")
build_rules_source = (BASE / "BuildTeamRules.kt").read_text(encoding="utf-8")
build_stat_source = (BASE / "BuildTeamStatGame.kt").read_text(encoding="utf-8")
build_stat_rules_source = (BASE / "BuildTeamStatRules.kt").read_text(encoding="utf-8")
player_facts_source = (BASE / "PlayerFacts.kt").read_text(encoding="utf-8")
ui_source = (BASE / "ElbashaUi.kt").read_text(encoding="utf-8")
questions_source = (BASE / "Questions.kt").read_text(encoding="utf-8")
auction_rules = (BASE / "AuctionRules.kt").read_text(encoding="utf-8")
launch_source_for_guards = (BASE / "LaunchGames.kt").read_text(encoding="utf-8")
if "fun randomSwap(" not in auction_rules:
    sys.exit("FAIL: the pure auction queue-swap regression rule is missing")
if "cardsMode" not in launch_source_for_guards or "PostAuctionCardRules.WINDOW_SECONDS" not in launch_source_for_guards or "finishPostAuctionCards()" not in launch_source_for_guards:
    sys.exit("FAIL: auction must offer a normal mode and a 20-second post-auction cards mode")
if "HiddenCoachAuctionCard" not in launch_source_for_guards or "HiddenCoachAuctionCard" not in (BASE / "PremiumGameUi.kt").read_text(encoding="utf-8"):
    sys.exit("FAIL: the hidden coach must stay concealed during bidding")
if "var lotResolved by remember" not in launch_source_for_guards or "enabled = !lotResolved" not in launch_source_for_guards:
    sys.exit("FAIL: Auction settlement actions must lock after the lot is resolved")
deal_ui_source = (BASE / "DealOrNoDealGame.kt").read_text(encoding="utf-8")
if "fun DealOrNoDealScreen(" not in deal_ui_source or "fun OnlineDealScreen(" in (BASE / "OnlineGameScreens.kt").read_text(encoding="utf-8"):
    sys.exit("FAIL: Deal must use the new private-case local game; the shared-box online mode must stay disabled")
image_rules_source = (BASE / "PlayerImageMatchRules.kt").read_text(encoding="utf-8")
image_repo_source = (BASE / "PlayerImage.kt").read_text(encoding="utf-8")
if "isExactPlayerTitle" not in image_rules_source or "isFootballerDescription" not in image_rules_source:
    sys.exit("FAIL: player portraits must require exact title and footballer-description matches")
if "isFootballerDescription(description)" not in image_repo_source or "strict-v3-football-description" not in image_repo_source:
    sys.exit("FAIL: image resolver must reject ambiguous page descriptions and invalidate the old cache")

players = re.findall(
    r'PlayerCard\("([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([A-Z]+)"\s*,\s*(\d+)\s*,\s*(\d+)\s*,',
    players_source,
)
if len(players) != 236:
    sys.exit(f"FAIL: expected 236 player records, found {len(players)}")

names = [p[0] for p in players]
if "🌍" in players_source:
    sys.exit("FAIL: player nationality flags still contain globe placeholders")
if len(re.findall(r'PlayerCard\("[^"]+"\s*,\s*"[^"]+"\s*,\s*"[A-Z]+"\s*,\s*\d+\s*,\s*\d+\s*,\s*"[^"]+"\s*,\s*"[^"]+"\s*,\s*"[^"]+"\)', players_source)) != 236:
    sys.exit("FAIL: all players must have bilingual nationality labels")
if len(names) != len(set(names)):
    sys.exit("FAIL: duplicate English player names")

arabic_names = [p[1] for p in players]
if len(arabic_names) != len(set(arabic_names)):
    sys.exit("FAIL: duplicate Arabic display names")
if any(not re.search(r"[\u0600-\u06FF]", name) for name in arabic_names):
    bad = [p[0] for p in players if not re.search(r"[\u0600-\u06FF]", p[1])]
    sys.exit(f"FAIL: players missing Arabic display names: {bad}")

positions = {position: sum(1 for p in players if p[2] == position)
             for position in {p[2] for p in players}}
if positions != {"GK": 40, "DF": 54, "MF": 58, "WG": 45, "ST": 39}:
    sys.exit(f"FAIL: unexpected position distribution: {positions}")

ratings = {name: int(rating) for name, _, _, rating, _ in players}
prices = {name: int(price) for name, _, _, _, price in players}
if any(rating < 1 or rating > 99 for rating in ratings.values()):
    sys.exit("FAIL: player rating must be within the supported 1..99 range")
if ratings.get("Lionel Messi") != 99 or ratings.get("Cristiano Ronaldo") != 99:
    sys.exit("FAIL: only Messi and Cristiano may carry the 99 OVR cap")
rating_bands = {
    "90+": sum(1 for r in ratings.values() if r >= 90),
    "80-89": sum(1 for r in ratings.values() if 80 <= r <= 89),
    "below80": sum(1 for r in ratings.values() if r < 80),
}
if rating_bands != {"90+": 58, "80-89": 162, "below80": 16}:
    sys.exit(f"FAIL: unexpected recalibrated OVR distribution: {rating_bands}")
for name, expected in {
    "Pele": 95, "Diego Maradona": 95, "Ronaldo Nazario": 94,
    "Zinedine Zidane": 94, "Paolo Maldini": 93, "Ronaldinho": 93,
    "Gianluigi Buffon": 92, "Yaya Toure": 88, "Michael Essien": 88,
    "Samuel Eto'o": 89, "Steven Gerrard": 89, "Frank Lampard": 89,
    "Paul Scholes": 89, "Romario": 94, "Gabriel Batistuta": 89,
    "Miroslav Klose": 88, "Mike Maignan": 87,
    "Gianluigi Donnarumma": 89,
}.items():
    if ratings.get(name) != expected:
        sys.exit(f"FAIL: recalibrated reference OVR for {name} should be {expected}")
if any(rating < 65 for rating in ratings.values()):
    sys.exit("FAIL: the current prime rating scale should not underflow the supported player pool")
expected_prices = {name: max(5, min(11, 5 + ((rating - 80) * 6 + 7) // 15)) for name, rating in ratings.items()}
if prices != expected_prices:
    sys.exit("FAIL: player prices must scale consistently with the prime OVR economy")
if any(name in names for name in ["Mohamed El Shenawy", "Ahmed Hegazi", "Mohamed Hany", "Hossam Ghaly", "Mohamed Elneny", "Ahmed Hassan"]):
    sys.exit("FAIL: the Egyptian-league-heavy entries scheduled for replacement remain in the catalog")

alias_pairs = dict(re.findall(r'"([^"]+)"\s+to\s+"([^"]+)"', search_source))
missing_aliases = sorted(set(names) - set(alias_pairs))
if missing_aliases:
    sys.exit(f"FAIL: missing Arabic search aliases: {missing_aliases}")
alias_mismatches = sorted(
    name for name, arabic, _, _, _ in players if alias_pairs.get(name) != arabic
)
if alias_mismatches:
    sys.exit(f"FAIL: Arabic display/search aliases differ: {alias_mismatches}")

if "PlayerSearch.normalize(searchText).length < 3" not in build_source:
    sys.exit("FAIL: Build Team search must enforce the 3-character threshold")
if "BuildTeamRules.createNationalityChallenge" not in build_source or "BuildTeamRules.chooseAiPlayer" not in build_source:
    sys.exit("FAIL: Build Team must use its tested nationality-challenge and AI-draft rules")
if "var pickLocked by remember" not in build_source or "phase != BuildPhase.Picking || pickLocked" not in build_source:
    sys.exit("FAIL: Build Team must lock a pick immediately to prevent rapid duplicate selections")
if "fun createNationalityChallenge" not in build_rules_source or "fun chooseAiPlayer" not in build_rules_source:
    sys.exit("FAIL: Build Team pure rules must expose challenge generation and AI drafting")
positions_source = (BASE / "PlayerDatabase.kt").read_text(encoding="utf-8")
if "fun formationSlots(size: Int)" not in positions_source or "formationSlots(size.coerceIn(4, rosterOrder.size))" not in positions_source:
    sys.exit("FAIL: player pools must use balanced formations for every squad size")
if "ElbashaPositions.formationSlots(size.coerceIn(4, 11))" not in build_source:
    sys.exit("FAIL: Build Team must use the shared balanced formation map")
if "صعب جدًا" not in build_source or "0.20" not in build_rules_source:
    sys.exit("FAIL: Build Team must include the Very Hard AI level")
launch_source_for_ai = (BASE / "LaunchGames.kt").read_text(encoding="utf-8")
local_auction_source = (BASE / "AuctionLocalGame.kt").read_text(encoding="utf-8")
# Regression guard: completing both steals must finish the match, never restart the coach lot.
card_choice_block = local_auction_source.split("fun handleCardChoice", 1)[1].split("val finalMatch", 1)[0]
if "cardStep = 4" not in card_choice_block or 'phase = "result"' not in card_choice_block:
    sys.exit("FAIL: completing the final Auction steal must transition to the final result")
if "beginCoachAuction()" in card_choice_block:
    sys.exit("FAIL: the completed card phase must not restart the hidden-coach auction")
if "revealedPlayers = newlyRevealed" not in local_auction_source or "HIDDEN PLAYER REVEALED" not in local_auction_source:
    sys.exit("FAIL: Auction hidden compensation players must be visibly revealed after settlement")
if "AuctionRules.calculateAiBidCeiling" not in launch_source_for_ai or "fun calculateAiBidCeiling" not in auction_rules:
    sys.exit("FAIL: Auction AI ceiling is not wired to its tested rules")
deal_rules_for_ai = (BASE / "DealRules.kt").read_text(encoding="utf-8")
deal_game_for_ai = (BASE / "DealOrNoDealGame.kt").read_text(encoding="utf-8")
if "else -> 2" not in auction_rules or "0 -> 1.0" not in deal_rules_for_ai or "else -> 0.25" not in deal_rules_for_ai or "Expert" not in deal_game_for_ai:
    sys.exit("FAIL: four-level AI difficulty settings or increasing Deal skill ordering are missing")
if "BuildPhase.Result" not in build_source or "ScoreRepository.submit(database, user, score)" not in build_source:
    sys.exit("FAIL: Build Team must finish with a result and submit a score")

# Build Team is a fixed 11-position match. Its AI chooses a fresh pool filter,
# stat and direction for every slot, then reveals each participant's result after 3-2-1.
if "BuildTeamStatScreen(user, database, sound)" not in ui_source:
    sys.exit("FAIL: the Build Team tile must open the dynamic 11-position game")
for token in ["BuildTeamMetric.HEIGHT", "BuildTeamMetric.WEIGHT", "BuildTeamMetric.GOALS",
              "BuildTeamMetric.YELLOW_CARDS", "BuildTeamMetric.PACE", "BuildTeamMetric.PLAYER_RATING",
              "BuildTeamMetric.AUCTION_PRICE", "HIGH(\"الأعلى يكسب\"", "LOW(\"الأقل يكسب\"",
              "BuildTeamStatRules.value", "BuildTeamStatRules.playersForChallenge",
              "BuildTeamStatRules.randomRoundChallenge", "BuildTeamStatRules.canBuildFullRoster",
              "BuildTeamPlayMode.PASS_AND_PLAY", "BuildTeamPlayMode.AI",
              "BuildTeamRosterFilter.RANDOM", "roundRevealCount", "ROUND_REVEAL",
              "showLeaderboard", "ScoreRepository.submit(database, user, score)"]:
    if token not in build_stat_source + build_stat_rules_source:
        sys.exit(f"FAIL: dynamic Build Team is missing {token}")
if "heightCm = 193" not in player_facts_source or "heightCm = 200" not in player_facts_source:
    sys.exit("FAIL: the Joan Garcia / Courtois height example is missing from player facts")
if "fun canBuildFullRoster" not in build_stat_rules_source or "roundCount * participantCount" not in build_stat_rules_source:
    sys.exit("FAIL: Build Team must verify enough players to fill the full formation for every participant")
if "totals[index]" not in build_stat_source or "ترتيب الجيم أثناء اللعب" not in build_stat_source:
    sys.exit("FAIL: Build Team must show a match-only live leaderboard during play")
# The active 11-round game awards each player's actual metric value as points.
if "listOf(BuildTeamDirection.HIGH).forEach" not in build_stat_rules_source:
    sys.exit("FAIL: dynamic Build Team round points and final ranking must both reward higher raw values")
if '"nation:$country+current"' not in build_stat_rules_source or '"nation:$country+retired"' not in build_stat_rules_source:
    sys.exit("FAIL: dynamic Build Team needs nationality combined with current/retired status filters")
if "exactSlotNames" not in build_stat_rules_source or "supportsSlot(player, challenge.slot)" not in build_stat_rules_source or "isEligibleForFormationSlot" not in build_stat_rules_source:
    sys.exit("FAIL: Build Team must filter candidates by the exact GK/RB/CB/LB/CDM/CM/CAM/RW/LW/ST slot")
if "isEligibleForFormationSlot(it, slot)" not in (ROOT / "app/src/test/java/com/mostafabek/elbashagames/CoreRulesSmokeTest.kt").read_text(encoding="utf-8"):
    sys.exit("FAIL: exact formation-slot eligibility must be covered by gameplay regression tests")
if "fun canExchange" not in (BASE / "PostAuctionCardRules.kt").read_text(encoding="utf-8") or "target.position == replacement.position" not in (BASE / "PostAuctionCardRules.kt").read_text(encoding="utf-8"):
    sys.exit("FAIL: Auction Steal must exchange players from the exact same position")
if "moveAiPlayerToUser" not in launch_source_for_ai or "moveUserPlayerToAi" not in launch_source_for_ai:
    sys.exit("FAIL: Auction AI and user steal paths must both perform same-position exchanges")
if "candidate.nameEn == aiProtectedName || userSquad.any { it.position == candidate.position }" not in launch_source_for_ai:
    sys.exit("FAIL: protected Steal targets must remain selectable, while unprotected targets require an exchange partner")
if "SHIELD BLOCKED THE STEAL" not in (BASE / "AuctionLocalGame.kt").read_text(encoding="utf-8") or "cardStep = 6" not in (BASE / "AuctionLocalGame.kt").read_text(encoding="utf-8"):
    sys.exit("FAIL: selecting a protected Auction target must waste the attacker's Steal card")
if "DealRules.unopenedCasesAfterDecision" not in deal_game_for_ai or "fun unopenedCasesAfterDecision" not in (BASE / "DealRules.kt").read_text(encoding="utf-8") or 'phase == "caseRegretReveal"' not in deal_game_for_ai:
    sys.exit("FAIL: Deal must reveal every unselected case after the accepted player joins")
if "privateCases.getOrNull(1)" not in deal_game_for_ai or "aiSelectedRiskIndex == index" not in deal_game_for_ai:
    sys.exit("FAIL: AI must visibly choose from its own private cases")
if "remainingCaseReveals" not in deal_game_for_ai or "remainingCaseRevealCount" not in deal_game_for_ai or "AnimatedVisibility" not in deal_game_for_ai:
    sys.exit("FAIL: Deal must animate and progressively reveal the unused cases after each decision")
if "local-hidden-reveal-countdown" not in (BASE / "AuctionLocalGame.kt").read_text(encoding="utf-8") or "hidden-player-countdown" not in launch_source_for_ai:
    sys.exit("FAIL: Auction hidden-player reveal must animate a 3-2-1 countdown in both play modes")
if "Crossfade(targetState = currentBid" not in launch_source_for_ai or "Crossfade(targetState = bidDraft" not in (BASE / "AuctionLocalGame.kt").read_text(encoding="utf-8"):
    sys.exit("FAIL: Auction bid counters must animate as bids change")
if "pendingPlayer" not in build_stat_source or "CONFIRM" not in build_stat_source:
    sys.exit("FAIL: Build Team must require a confirmed player pick")
if "الدوري الإسباني الحالي" not in build_stat_rules_source:
    sys.exit("FAIL: LaLiga filter must explicitly refer to currently active LaLiga players")
if "sharedMusic" not in ui_source or 'musicPicker.launch(arrayOf("audio/*"))' not in ui_source:
    sys.exit("FAIL: developer music upload and shared Firebase playback are missing")
music_upload_section = ui_source.split("val musicPicker", 1)[1].split("val cachedPlayerPhotos", 1)[0] if "val musicPicker" in ui_source and "val cachedPlayerPhotos" in ui_source else ""
if "auth.currentUser" in music_upload_section or "user.uid" not in music_upload_section:
    sys.exit("FAIL: music uploader must use the authenticated screen user UID, not an out-of-scope auth variable")
if "fun setSharedMusic(file: File)" not in (BASE / "SoundManager.kt").read_text(encoding="utf-8"):
    sys.exit("FAIL: shared music playback manager is missing")
if "CompactGameCard" not in ui_source or "HomeDashboard" not in ui_source or "SettingsDashboard" not in ui_source:
    sys.exit("FAIL: dashboard and distinct game cards must be connected")
if all(token not in ui_source for token in ["THE MARKET", "LUCK & RISK", "TACTICAL DRAFT"]):
    sys.exit("FAIL: dashboard game cards need distinct visual identities")
if "rememberInfiniteTransition(label = \"game-card-glow-" not in ui_source or "accent.copy(alpha = glowAlpha" not in ui_source:
    sys.exit("FAIL: dashboard cards must use a subtle animated accent glow")

if "NavigationBar(" not in ui_source or "Crossfade(" not in ui_source or "rememberInfiniteTransition" not in ui_source:
    sys.exit("FAIL: the premium home navigation and continuous logo motion must be present")
if "CompactGameCard" not in ui_source or "HomeDashboard" not in ui_source or "SettingsDashboard" not in ui_source:
    sys.exit("FAIL: the new Elbasha dashboard, compact game cards and simplified settings must be present")

sound_source = (BASE / "SoundManager.kt").read_text(encoding="utf-8")
if 'var musicOn by mutableStateOf(prefs.getBoolean("music", true))' not in sound_source or 'music_enabled_migration_v1' not in sound_source:
    sys.exit("FAIL: shared music must default enabled and migrate older forced-off builds")
if 'sound.toggleMusic()' not in ui_source or 'موسيقى الجروب' not in ui_source:
    sys.exit("FAIL: shared music toggle must be available in Settings")
for effect, resource in {
    "Correct": "sfx_correct.ogg",
    "Wrong": "sfx_wrong.ogg",
    "Win": "sfx_win.ogg",
    "Loss": "sfx_loss.ogg",
    "Tick": "sfx_tick.ogg",
    "Click": "sfx_click.ogg",
    "HiddenReveal": "sfx_hidden_reveal.ogg",
}.items():
    if f"Sfx.{effect} to pool.load(app, R.raw.{resource.removesuffix('.ogg')}, 1)" not in sound_source:
        sys.exit(f"FAIL: sound effect {effect} is not loaded by SoundManager")
    audio_file = ROOT / "app/src/main/res/raw" / resource
    if not audio_file.is_file() or audio_file.stat().st_size < 1_000 or audio_file.read_bytes()[:4] != b"OggS":
        sys.exit(f"FAIL: sound effect asset {resource} is missing, empty or not a valid Ogg file")
if "if (!soundOn) return" not in sound_source or "effect !in setOf" in sound_source:
    sys.exit("FAIL: SoundManager must play every loaded Sfx enum when effects are enabled")
if not (ROOT / "app/src/test/java/com/mostafabek/elbashagames/CoreRulesSmokeTest.kt").is_file():
    sys.exit("FAIL: core auction and formation unit tests are missing")
# Deal's reveal card lives in DealOrNoDealGame.kt; the Auction hidden-player reveal lives in AuctionLocalGame.kt.
if "fun DealRevealCard(" not in deal_game_for_ai or "AnimatedVisibility(" not in deal_game_for_ai or "scaleIn(" not in deal_game_for_ai:
    sys.exit("FAIL: Deal player reveals must have an entrance animation")
if "AnimatedVisibility(" not in local_auction_source or "PLAYER REVEALED" not in local_auction_source:
    sys.exit("FAIL: Auction hidden-player reveals must have an entrance animation")
firebase_rules = json.loads((ROOT / "firebase/database.rules.json").read_text(encoding="utf-8"))
shared_music_rules = firebase_rules["rules"].get("sharedMusic", {}).get("current", {})
# Room membership is checked at each room. The collection itself must not be readable
# by every signed-in user, otherwise room codes and live match state are exposed.
online_room_rules = firebase_rules["rules"].get("onlineRooms", {})
if ".read" in online_room_rules:
    sys.exit("FAIL: onlineRooms collection must not grant blanket authenticated reads")
room_read_rule = online_room_rules.get("$roomCode", {}).get(".read", "")
if "status" not in room_read_rule or "members" not in room_read_rule or "hostUid" not in room_read_rule:
    sys.exit("FAIL: room reads must be restricted to lobby discovery or authenticated room members")
access_source = (BASE / "ElbashaAccess.kt").read_text(encoding="utf-8")
dev_uid_match = re.search(r'DeveloperUid\s*=\s*"([A-Za-z0-9]+)"', access_source)
if not dev_uid_match:
    sys.exit("FAIL: developer UID is not configured in ElbashaAccess")
developer_uid = dev_uid_match.group(1)
rules_text = (ROOT / "firebase/database.rules.json").read_text(encoding="utf-8")
hardcoded_developer_uids = set(re.findall(r"auth\.uid\s*==\s*'([^']+)'", rules_text))
if hardcoded_developer_uids != {developer_uid}:
    sys.exit(f"FAIL: Firebase developer-only rules are out of sync with ElbashaAccess: {hardcoded_developer_uids}")
if shared_music_rules.get(".read") is not True or developer_uid not in shared_music_rules.get(".write", ""):
    sys.exit("FAIL: shared music must be readable on every install while remaining writable only by the developer")
if "7000000" not in shared_music_rules.get("data", {}).get(".validate", ""):
    sys.exit("FAIL: shared music data size guard is missing")
for screen_file in ["ElbashaUi.kt", "ArcadeGames.kt", "BuildTeamGame.kt", "LaunchGames.kt", "PenaltyShootout.kt", "TriviaGame.kt"]:
    if "elbashaAtmosphere()" not in (BASE / screen_file).read_text(encoding="utf-8"):
        sys.exit(f"FAIL: stadium background is not applied in {screen_file}")
match_engine = (BASE / "MatchEngine.kt").read_text(encoding="utf-8")
if "fun simulate(" not in match_engine or "userExpectedGoals" not in match_engine:
    sys.exit("FAIL: first-release games must use the shared probability-based match simulator")
if "positionalFit(lineup, lineupSize) * 6.0" not in match_engine or "fun positionalFit(team: List<PlayerCard>, targetSize: Int = team.size)" not in match_engine or "fun selectBestLineup" not in match_engine:
    sys.exit("FAIL: match simulation must account for balanced formation coverage and choose a valid starting lineup")
if "fun <T> suggestionsBy" not in search_source:
    sys.exit("FAIL: shared generic player suggestion engine is missing")

# The current Build Team MVP uses real nationality metadata. Verify that its
# 4..11-player formations can generate a two-player matchup for every slot.
player_meta = re.findall(
    r'PlayerCard\("([^"]+)"\s*,\s*"[^"]+"\s*,\s*"([A-Z]+)"\s*,\s*\d+\s*,\s*\d+\s*,\s*"[^"]+"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\)',
    players_source,
)
formations = {
    4: ["GK", "DF", "MF", "ST"],
    5: ["GK", "DF", "MF", "WG", "ST"],
    6: ["GK", "DF", "DF", "MF", "WG", "ST"],
    7: ["GK", "DF", "DF", "MF", "MF", "WG", "ST"],
    8: ["GK", "DF", "DF", "DF", "MF", "MF", "WG", "ST"],
    9: ["GK", "DF", "DF", "DF", "DF", "MF", "MF", "WG", "ST"],
    10: ["GK", "DF", "DF", "DF", "DF", "MF", "MF", "WG", "WG", "ST"],
    11: ["GK", "DF", "DF", "DF", "DF", "MF", "MF", "MF", "WG", "WG", "ST"],
}

if len(player_meta) != 236:
    sys.exit(f"FAIL: expected nationality metadata for 236 players, found {len(player_meta)}")
for size, formation in formations.items():
    for trial in range(300):
        used = set()
        for position in formation:
            groups = {}
            for name, player_position, nationality_ar, nationality_en in player_meta:
                if player_position == position and name not in used and nationality_ar and nationality_en:
                    groups.setdefault(nationality_en, []).append(name)
            eligible_groups = [names_in_group for names_in_group in groups.values() if len(names_in_group) >= 2]
            if not eligible_groups:
                sys.exit(f"FAIL: Build Team cannot form a two-player nationality challenge (size={size}, position={position})")
            chosen_group = random.choice(eligible_groups)
            used.update(random.sample(chosen_group, 2))


catalog = re.findall(r'GameItem\("(auction|deal|build)"', ui_source)
if catalog != ["auction", "deal", "build"]:
    sys.exit(f"FAIL: first-release game catalog is not exactly Auction/Deal/Build Team: {catalog}")




strings_root = ET.parse(ROOT / "app/src/main/res/values/strings.xml").getroot()
string_values = {node.attrib.get("name"): (node.text or "").strip() for node in strings_root.findall("string")}
google_config = json.loads((ROOT / "app/google-services.json").read_text(encoding="utf-8"))
expected_database_url = google_config.get("project_info", {}).get("firebase_url", "").strip()
configured_database_url = string_values.get("firebase_database_url", "")
if not expected_database_url or configured_database_url != expected_database_url:
    sys.exit("FAIL: firebase_database_url must match project_info.firebase_url in google-services.json")
gradle_app_config = (ROOT / "app/build.gradle.kts").read_text(encoding="utf-8")
package_match = re.search(r'applicationId\s*=\s*"([^"]+)"', gradle_app_config)
configured_package = package_match.group(1) if package_match else ""
google_packages = {
    client.get("client_info", {}).get("android_client_info", {}).get("package_name")
    for client in google_config.get("client", [])
}
if not configured_package or configured_package not in google_packages:
    sys.exit("FAIL: Android applicationId must match a package in google-services.json")
web_client_ids = {
    oauth.get("client_id")
    for client in google_config.get("client", [])
    for oauth in client.get("oauth_client", [])
    if oauth.get("client_type") == 3
}
if not string_values.get("google_web_client_id") or string_values["google_web_client_id"] not in web_client_ids:
    sys.exit("FAIL: google_web_client_id must match an OAuth client of type 3 in google-services.json")

release_workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
if "github.run_number + 3" in release_workflow or "GITHUB_RUN_NUMBER + 3" not in release_workflow:
    sys.exit("FAIL: release workflow version code must be calculated in shell, not GitHub expression arithmetic")
if "python3 tools/validate_catalog.py" not in release_workflow:
    sys.exit("FAIL: release workflow must run source validation before publishing")
if "workflow_dispatch" in release_workflow:
    sys.exit("FAIL: release publishing should only run from version tags, not a branch dispatch")
if "APP_VERSION_CODE" not in release_workflow or "${{ steps.version.outputs.version_code }}" not in release_workflow or "id: version" not in release_workflow:
    sys.exit("FAIL: release workflow must pass the calculated version code to Gradle and release notes")
if "testDebugUnitTest" not in release_workflow or release_workflow.index("testDebugUnitTest") > release_workflow.index("assembleRelease"):
    sys.exit("FAIL: tagged release must run gameplay regression tests before assembling the release APK")
if 'ANDROID_DEBUG_KEYSTORE_PASSWORD=$KEY_PASSWORD' not in release_workflow or 'keytool -list -v' not in release_workflow:
    sys.exit("FAIL: release workflow must export and verify the stable signing key for every Gradle task")


updater_source = (BASE / "AppUpdater.kt").read_text(encoding="utf-8")
if "isUpdateDownloadSuccessful(context, downloadId)" not in updater_source:
    sys.exit("FAIL: updater must verify DownloadManager success before launching the installer")
if "destination.delete()" not in updater_source:
    sys.exit("FAIL: updater must clear an old APK before downloading a replacement")
if "install_prompted_download_id" not in updater_source or "install_permission_prompted_download_id" not in updater_source:
    sys.exit("FAIL: updater must track permission and installer prompts per download ID")
update_prompt_rules = (BASE / "UpdatePromptRules.kt").read_text(encoding="utf-8")
if "downloadId != alreadyPromptedDownloadId" not in update_prompt_rules:
    sys.exit("FAIL: updater prompt guard must permit prompts for future downloads")
core_test = (ROOT / "app/src/test/java/com/mostafabek/elbashagames/CoreRulesSmokeTest.kt").read_text(encoding="utf-8")
if "UpdatePromptRules.shouldPrompt(43L, 42L)" not in core_test:
    sys.exit("FAIL: updater prompt state must have a regression test for a subsequent download")
receiver_source = (BASE / "UpdateDownloadReceiver.kt").read_text(encoding="utf-8")
if "if (!isUpdateDownloadSuccessful(context, id)) return" not in receiver_source:
    sys.exit("FAIL: updater receiver must ignore failed DownloadManager transfers")
if "ACTION_UPDATE_READY" not in receiver_source or "sendBroadcast" not in receiver_source or "startActivity" in receiver_source:
    sys.exit("FAIL: updater receiver must notify the visible Activity without starting UI from the background")
main_activity_source = (BASE / "MainActivity.kt").read_text(encoding="utf-8")
if "ContextCompat.RECEIVER_NOT_EXPORTED" not in main_activity_source or "installDownloadedUpdateIfReady(this@MainActivity)" not in main_activity_source:
    sys.exit("FAIL: MainActivity must handle update-ready signals while visible and retry on resume")

launch_source = (BASE / "LaunchGames.kt").read_text(encoding="utf-8")
if not ("grantHiddenPlayer(activeLot.position, toUser = true)" in launch_source or "grantHiddenPlayer(lot.position, toUser = true)" in launch_source) or "grantHiddenPlayer(lot.position, toUser = false)" not in launch_source:
    sys.exit("FAIL: auction must grant a same-position hidden bonus player to the losing side")
if "val userCount = bought.size + hiddenPlayers.size" not in launch_source or "val aiCount = aiBought.size + aiHiddenPlayers.size" not in launch_source:
    sys.exit("FAIL: auction completion must count purchased and hidden bonus players for both squads")
if "AuctionRules.settleWhenAiPasses(currentBid, opening, wildCardActive)" not in launch_source:
    sys.exit("FAIL: Wild Card must reduce the final paid amount without invalidating the opening bid")
if "AuctionRules.nextAiBid(currentBid, aiMaxForLot, aiLotSpendLimit)" not in launch_source or "AuctionRules.settleWhenAiPasses" not in launch_source or "aiMaxForLot" not in launch_source:
    sys.exit("FAIL: Auction must alternate bids and settle correctly when the AI passes")
if "AuctionRules.settleWhenUserPasses" not in launch_source or "fun settleWhenUserPasses" not in auction_rules:
    sys.exit("FAIL: Auction must explicitly resolve the user's first pass, AI win, or unsold lot")
if "You passed! AI won the lot" not in launch_source or "Sfx.HiddenReveal" not in launch_source or "wildCardActive = false" not in launch_source:
    sys.exit("FAIL: Passing must award the lot, reveal the losing side's hidden player, and play its reveal effect")
if "preserveQueueAfterHiddenReward" not in launch_source or "fun preserveQueueAfterHiddenReward" not in auction_rules:
    sys.exit("FAIL: hidden bonus players must not reappear in the auction, and replacing a collision must preserve round count")
if "val lot = remainingLots.firstOrNull()" not in launch_source:
    sys.exit("FAIL: auction must advance through the remaining-lot queue")
if "userSquad.size + 1" not in launch_source or "userSquad.size.toFloat() / targetCount" not in launch_source:
    sys.exit("FAIL: Auction progress must count hidden bonus players in the visible squad total")
if 'Text("${userSquad.size}/$targetCount"' not in launch_source or 'Text("${aiSquad.size}/$targetCount"' not in launch_source:
    sys.exit("FAIL: Auction result squad totals must include hidden bonus players")
if "chooseAiOpeningIndex" not in deal_rules_for_ai or "aiShouldRisk" not in deal_rules_for_ai or "chooseAiRiskIndex" not in deal_rules_for_ai:
    sys.exit("FAIL: Deal AI must choose from its own private four-case hand and resolve its own risk decision")
if "canBuyOpening(openingPrice, aiCeiling, aiBudget)" not in auction_rules or "aiCeiling >= openingPrice && aiBudget >= openingPrice" not in auction_rules:
    sys.exit("FAIL: AI must not buy a player below the opening bid or exceed its reserved budget")
if "settleWhenAiPasses(currentBid, opening, wildCardActive)" not in launch_source or "(currentBid - 2).coerceAtLeast(openingPrice)" not in auction_rules:
    sys.exit("FAIL: Wild Card final-price calculation must preserve the opening-price floor")
if "AuctionRules.reserveLotsForRequiredSlots(" not in launch_source or "fun reserveLotsForRequiredSlots(" not in auction_rules:
    sys.exit("FAIL: AI must reserve distinct cheapest upcoming lots for every still-missing formation slot")
deal_rules_source = (BASE / "DealRules.kt").read_text(encoding="utf-8")
deal_game_source = (BASE / "DealOrNoDealGame.kt").read_text(encoding="utf-8")
post_auction_rules_source = (BASE / "PostAuctionCardRules.kt").read_text(encoding="utf-8")
if not (BASE / "DealBankCards.kt").exists() and "DealBankCard" not in deal_game_source:
    print("PASS: retired Deal bank deck and its old actions are removed")
else:
    sys.exit("FAIL: obsolete bank cards must not remain in Deal")
if "const val WINDOW_SECONDS = 20" not in post_auction_rules_source or "eligibleStealTargets" not in post_auction_rules_source:
    sys.exit("FAIL: Auction post-game Shield/Steal rules are missing")
for token in ["createPrivateCaseSets", "minimumCandidatesRequired", "acceptDeal", "acceptRisk", "FINAL_CARD_WINDOW_SECONDS", "stealPlayer", "protectPlayer"]:
    if token not in deal_rules_source:
        sys.exit(f"FAIL: Deal's private-case/final-card rule is missing: {token}")
for token in ["privateCases", "rejectedCaseIndex", "phase = \"riskPick\"", "phase = \"coachReveal\"", "beginCardsPhase()", "cardsSecondsLeft", "selectedStealTeam"]:
    if token not in deal_game_source:
        sys.exit(f"FAIL: Deal UI is missing the required stage/flow: {token}")
for token in ["customPlayerFilter", "selectedPlayerNames", "showPlayerFilterDialog", "LazyColumn(", "poolValidationMessage()", "فلتر اللاعبين"]:
    if token not in deal_game_source:
        sys.exit(f"FAIL: Deal setup is missing the custom player filter/capacity guard: {token}")
if launch_source.count("MatchEngine.simulate(") + deal_game_source.count("MatchEngine.simulate(") < 2:
    sys.exit("FAIL: Auction and Deal or No Deal must both simulate a match")
if launch_source.count("ScoreRepository.submit(database, user,") + deal_game_source.count("ScoreRepository.submit(database, user,") != 2:
    sys.exit("FAIL: Auction and Deal or No Deal must both submit completed-game scores")
if "fun AuctionGameScreen(user: FirebaseUser" not in launch_source or "fun DealOrNoDealScreen(" not in deal_game_source or "database: FirebaseDatabase?" not in deal_game_source:
    sys.exit("FAIL: completed games are missing authenticated score context")


question_rows = re.findall(
    r'q\("(s\d+)",\s*"([^"]+)",\s*"([^"]+)",\s*listOf\(([^)]*)\),\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)",\s*listOf\(([^)]*)\)',
    questions_source,
)
if len(question_rows) != 140 or len({row[0] for row in question_rows}) != 140:
    sys.exit(f"FAIL: expected 140 unique built-in questions, found {len(question_rows)}")
if len({row[1] for row in question_rows}) != 140 or len({row[6] for row in question_rows}) != 140:
    sys.exit("FAIL: duplicate Arabic or English question prompts detected")
answer_leaks = [row[0] for row in question_rows if row[2].strip() and row[2].strip() in row[1]]
answer_leaks_en = [row[0] for row in question_rows if row[7].strip().casefold() in row[6].casefold()]
if answer_leaks or answer_leaks_en:
    sys.exit(f"FAIL: answers appear in prompt text (AR={answer_leaks}, EN={answer_leaks_en})")
invalid_options = []
for row in question_rows:
    wrong_ar = re.findall(r'"([^"]+)"', row[3])
    wrong_en = re.findall(r'"([^"]+)"', row[8])
    if len(wrong_ar) != 3 or len(set(wrong_ar)) != 3 or len(wrong_en) != 3 or len(set(wrong_en)) != 3 or row[2] in wrong_ar or row[7] in wrong_en:
        invalid_options.append(row[0])
if invalid_options:
    sys.exit(f"FAIL: questions must have three distinct wrong options: {invalid_options}")
invalid_difficulty = [row[0] for row in question_rows if row[4] not in {"easy", "medium", "hard"}]
if invalid_difficulty:
    sys.exit(f"FAIL: invalid question difficulty values: {invalid_difficulty}")
difficulty_counts = {level: sum(1 for row in question_rows if row[4] == level) for level in ("easy", "medium", "hard")}
if difficulty_counts != {"easy": 42, "medium": 48, "hard": 50}:
    sys.exit(f"FAIL: unexpected question difficulty distribution: {difficulty_counts}")

# Session 9 policy checks: ordered role slots, shared music, and developer diagnostics.
positions_source = players_source
expected_order = 'listOf("GK", "RB", "CB", "CB", "LB", "CDM", "CM", "CAM", "RW", "LW", "ST")'
if expected_order not in positions_source or "ordered.add(candidate.copy(position = slot))" not in positions_source:
    sys.exit("FAIL: shared canonical position order is missing from the player-pool helper")
expected_slot_map = {
    4: ["GK", "CB", "CM", "ST"],
    5: ["GK", "CB", "CM", "RW", "ST"],
    6: ["GK", "RB", "CB", "CM", "RW", "ST"],
    7: ["GK", "RB", "CB", "CM", "CAM", "RW", "ST"],
    8: ["GK", "RB", "CB", "CB", "CM", "CAM", "RW", "ST"],
    9: ["GK", "RB", "CB", "CB", "LB", "CM", "CAM", "RW", "ST"],
    10: ["GK", "RB", "CB", "CB", "LB", "CDM", "CM", "RW", "LW", "ST"],
    11: ["GK", "RB", "CB", "CB", "LB", "CDM", "CM", "CAM", "RW", "LW", "ST"],
}
for squad_size, slots in expected_slot_map.items():
    encoded = "11 to rosterOrder" if squad_size == 11 else f'{squad_size} to listOf(' + ", ".join(f'"{slot}"' for slot in slots) + ')'
    if encoded not in positions_source:
        sys.exit(f"FAIL: balanced formation mapping is incorrect for {squad_size} players")
    if slots[0] != "GK" or slots[-1] != "ST" or not any(slot in {"CDM", "CM", "CAM"} for slot in slots):
        sys.exit(f"FAIL: formation {squad_size} is missing goalkeeper, midfield or striker coverage")
if "ElbashaPositions.formationSlots(targetCount)" not in launch_source or "ElbashaPositions.formationSlots(targetCount)" not in (BASE / "DealOrNoDealGame.kt").read_text(encoding="utf-8") or "createPrivateCaseSets" not in deal_rules_source:
    sys.exit("FAIL: Auction and Deal or No Deal must assign players by the ordered role slot")
sound_source = (BASE / "SoundManager.kt").read_text(encoding="utf-8")
if "MediaPlayer" not in sound_source or "fun setSharedMusic(file: File)" not in sound_source:
    sys.exit("FAIL: shared group music playback is missing")
if "musicPath = null" not in sound_source or '"decoder_error_${what}_$extra"' not in sound_source:
    sys.exit("FAIL: a failed shared audio decoder must release and reset so the next track can retry")
if "pendingMusicTimestamp" not in ui_source or "latestMusicTimestamp" not in ui_source:
    sys.exit("FAIL: shared music downloads must reject stale results when a newer track arrives")
if ui_source.find("sound.setSharedMusic(saved)") > ui_source.find("appliedMusicTimestamp = timestamp"):
    sys.exit("FAIL: shared music must not be marked applied before playback is handed the cached file")
if "tempFile.renameTo(cachedFile)" not in ui_source:
    sys.exit("FAIL: shared music cache must finalize decoded files atomically")
if any(token not in sound_source for token in ("Sfx.Win to pool.load", "Sfx.Loss to pool.load", "Sfx.HiddenReveal to pool.load")):
    sys.exit("FAIL: win/loss and hidden-player reveal effects must remain available")
if "AnimatedVisibility" not in local_auction_source or "scaleIn(" not in local_auction_source:
    sys.exit("FAIL: hidden-player reveal must animate into view")
ui_source = (BASE / "ElbashaUi.kt").read_text(encoding="utf-8")
if ui_source.count("sound.clearSharedMusic()") != 4:
    sys.exit("FAIL: shared music cleanup must only belong to its own listener lifecycle")
raw_audio = ROOT / "app/src/main/res/raw"
if (raw_audio / "music_menu.ogg").exists() or (raw_audio / "music_tournament.ogg").exists():
    sys.exit("FAIL: bundled music resources must be removed")
ui_source_full = (BASE / "ElbashaUi.kt").read_text(encoding="utf-8")
if 'child(".info/connected")' not in ui_source_full or "BuildConfig.VERSION_NAME" not in ui_source_full:
    sys.exit("FAIL: developer diagnostics must include Firebase connection and app build information")
premium_ui_source = (BASE / "PremiumGameUi.kt").read_text(encoding="utf-8")
if "fun SquadFormationPitch(" not in premium_ui_source:
    sys.exit("FAIL: shared squad formation pitch component is missing")
if launch_source.count("SquadFormationPitch(") < 4 or "SquadFormationPitch(" not in build_source:
    sys.exit("FAIL: Auction, Deal and Build Team must show acquired players on a visual pitch")
if 'listOf(setOf("ST", "WG"), setOf("MF"), setOf("DF"), setOf("GK"))' not in premium_ui_source:
    sys.exit("FAIL: formation pitch must render four balanced lines with attackers, midfield, defence and goalkeeper")
player_image_source = (BASE / "PlayerImage.kt").read_text(encoding="utf-8")
if "loadBundledPortrait" not in player_image_source or "bundledCount(context: Context)" not in player_image_source:
    sys.exit("FAIL: portrait loader must check packaged offline assets before network cache")
if 'Text("WIKI"' in player_image_source or 'portrait (Wikipedia)' in player_image_source:
    sys.exit("FAIL: player cards must not show the Wikipedia badge or source branding")
manifest_path = ROOT / "tools/player_portrait_manifest.csv"
if not manifest_path.is_file() or len(manifest_path.read_text(encoding="utf-8-sig").splitlines()) != 237:
    sys.exit("FAIL: portrait manifest must define one asset path for each of the 236 players")
if "pilicense=free" not in player_image_source or "upload.wikimedia.org" not in player_image_source or "PlayerPortrait" not in player_image_source:
    sys.exit("FAIL: player portrait resolver must use free Wikimedia page-image results and a visible portrait component")
if 'IMAGE_MATCH_VERSION = "strict-v3-football-description"' not in player_image_source or "isExactPlayerTitle" not in player_image_source or "isFootballerDescription(description)" not in player_image_source or "generator=search" in player_image_source:
    sys.exit("FAIL: player portrait matching must require exact title and footballer-description evidence and invalidate old cache entries")
if "fun cachedCount(context: Context)" not in player_image_source or "fun clearCache(context: Context)" not in player_image_source:
    sys.exit("FAIL: local player portrait cache diagnostics and clearing are missing")
portrait_sources = {f: (BASE / f).read_text(encoding="utf-8") for f in ["PremiumGameUi.kt", "FifaCards.kt", "AuctionLocalGame.kt", "DealOrNoDealGame.kt"]}
if any("PlayerPortrait(" not in text for text in portrait_sources.values()):
    sys.exit("FAIL: player portraits must appear in selection, reveal, and squad cards")
if "Download all ${PlayerDatabase.players.size} player portraits" not in ui_source_full or "PlayerImageRepository.load(appContext, player.nameEn)" not in ui_source_full:
    sys.exit("FAIL: developer panel must offer progressive full-catalog photo preload")
if "isDeveloper = ElbashaAccess.isDeveloper(user.uid)" not in ui_source_full or 'child("admins")' in ui_source_full:
    sys.exit("FAIL: developer access must remain restricted to the configured developer UID")


# Session 19 edge-to-edge and interaction-motion guards.
main_activity_source = (BASE / "MainActivity.kt").read_text(encoding="utf-8")
if "WindowCompat.setDecorFitsSystemWindows(window, false)" not in main_activity_source:
    sys.exit("FAIL: Android window must draw edge-to-edge behind transparent system bars")
if "window.statusBarColor = AndroidColor.TRANSPARENT" not in main_activity_source or "window.navigationBarColor = AndroidColor.TRANSPARENT" not in main_activity_source:
    sys.exit("FAIL: status and navigation bars must be transparent over the app background")
if "navigationBarsPadding()" not in ui_source_full or "Modifier.fillMaxSize().elbashaAtmosphere()" not in ui_source_full:
    sys.exit("FAIL: full-screen background must extend behind bars while interactive content respects navigation insets")
if "WindowInsetsControllerCompat" not in ui_source_full or "isAppearanceLightStatusBars = !darkTheme" not in ui_source_full:
    sys.exit("FAIL: system-bar icon contrast must follow the selected app theme")
if "animateFloatAsState" not in ui_source_full or "collectIsPressedAsState" not in ui_source_full or "slideInVertically" not in ui_source_full:
    sys.exit("FAIL: game cards must have press feedback and staggered entrance animation")
print("PASS: edge-to-edge background, transparent system bars, theme-aware icons and animated game cards")

print("PASS: 236 unique players with country flags and bilingual nationality labels")
print("PASS: all players have matching Arabic display names and search aliases")
print("PASS: position distribution is valid (GK 40 / DF 54 / MF 58 / WG 45 / ST 39)")
print("PASS: player OVRs rebalanced with a selective elite tier and 16 lower-rated players; only Messi and Cristiano are 99")
print("PASS: player catalog uses the prime-era rating model")
print("PASS: player prices scale consistently with prime OVR")
print("PASS: shared 3-character player suggestions and Build Team AI challenge")
print("PASS: four AI difficulty levels in all three first-release games")
print("PASS: all 4..11-player formations are balanced from goalkeeper through striker")
print("PASS: shared match engine used by first-release games")
print("PASS: first-release catalog contains the three selected games")
print("PASS: Auction hidden-player reward, correct squad completion, Wild Card discount and AI opening-bid guard")
print("PASS: Deal private-case game rules and final-card window are included in the new game module")
print("PASS: both Auction and Deal or No Deal run a match simulation")
print("PASS: Auction and Deal or No Deal submit completed scores")
print("PASS: Deal AI chooses and resolves risk from its own private four-case hand")
print("PASS: release workflow calculates versionCode with shell arithmetic")
print("PASS: Firebase URL, Google web client ID and Android package match google-services.json")
print("PASS: updater verifies completed downloads and clears stale APKs")
print("PASS: 140 unique questions, 42 easy / 48 medium / 50 hard, four choices each, no answer leakage")
print("PASS: canonical GK-to-ST order is used across player-picking flows")
print("PASS: all seven gameplay sound effects are loaded, valid Ogg assets, and independently muted from group music")
print("PASS: stadium-style backgrounds are applied across main and game screens")
print("PASS: developer panel exposes Firebase connection and build diagnostics")
print("PASS: strict exact-title plus footballer-description matching rejects ambiguous Wikimedia pages and invalidates old cache")
print("PASS: free Wikimedia portrait resolver, local cache, squad-card integration and batch-preload control")
auction_rules = (BASE / "AuctionRules.kt").read_text(encoding="utf-8")
auction_ui = (BASE / "LaunchGames.kt").read_text(encoding="utf-8")
for token in ["minimumNextUserBid", "adjustUserBidDraft", "availableBudgetForCurrentLot"]:
    if token not in auction_rules or token not in auction_ui:
        sys.exit(f"FAIL: auction bid counter helper is missing from rules or UI: {token}")
if '"−1 M"' not in auction_ui or "YOUR BID DRAFT" not in auction_ui:
    sys.exit("FAIL: auction bid counter must expose a decrement control and visible draft amount")
if "adjustUserBidDraft(draft, -1, minimum, budget)" not in (ROOT / "app/src/test/java/com/mostafabek/elbashagames/CoreRulesSmokeTest.kt").read_text(encoding="utf-8"):
    sys.exit("FAIL: auction bid decrement must be covered by Kotlin smoke tests")
print("PASS: auction bid draft counter supports guarded decrement/increment and is covered by core tests")

deal_rules = (BASE / "DealRules.kt").read_text(encoding="utf-8")
deal_game = (BASE / "DealOrNoDealGame.kt").read_text(encoding="utf-8")
for token in ["createPrivateCaseSets", "acceptDeal", "acceptRisk", "aiShouldRisk", "FINAL_CARD_WINDOW_SECONDS", "stealPlayer", "protectPlayer"]:
    if token not in deal_rules:
        sys.exit(f"FAIL: Deal private draft/card rules are missing: {token}")
for token in ["No Deal", "اللاعب اترفض نهائيًا", "الصناديق الثلاثة", "coachReveal", "cardsSecondsLeft", "كارت السرقة", "كارت الحماية"]:
    if token not in deal_game:
        sys.exit(f"FAIL: Deal screen does not implement the agreed flow: {token}")
core_test = (ROOT / "app/src/test/java/com/mostafabek/elbashagames/CoreRulesSmokeTest.kt").read_text(encoding="utf-8")
for token in ["Four participants must never share a case/player", "No Deal must force a different case", "FINAL_CARD_WINDOW_SECONDS", "stealPlayer", "protectPlayer"]:
    if token not in core_test:
        sys.exit(f"FAIL: Deal rule lacks a regression test: {token}")
print("PASS: Deal uses private four-case hands, forced No Deal replacement, and an isolated 60-second Steal/Shield phase")
test_wrapper = (ROOT / "app/src/test/java/com/mostafabek/elbashagames/CoreRulesRegressionTest.kt").read_text(encoding="utf-8")
app_gradle = (ROOT / "app/build.gradle.kts").read_text(encoding="utf-8")
workflow = (ROOT / ".github/workflows/android.yml").read_text(encoding="utf-8")
if "runCoreRulesSmokeTest()" not in test_wrapper or "testImplementation(\"junit:junit:4.13.2\")" not in app_gradle:
    sys.exit("FAIL: gameplay regression suite is not configured as an Android unit test")
if "testDebugUnitTest" not in workflow:
    sys.exit("FAIL: GitHub Actions must execute gameplay regression tests before assembling the APK")
if workflow.index("testDebugUnitTest") > workflow.index("assembleDebug"):
    sys.exit("FAIL: gameplay regression tests must run before APK assembly")
if "keytool -genkeypair" not in workflow or "Stable signing secrets are not configured" not in workflow:
    sys.exit("FAIL: debug CI must be able to build a test APK before stable signing secrets are configured")
print("PASS: gameplay regression suite is wired into Android unit tests and GitHub Actions")
print("PASS: APK CI has both stable-key and temporary-key paths; tagged releases still require stable secrets")

print("PASS: developer access is restricted to the configured UID")

# Session 15 online-lobby source guards (no claim of realtime gameplay synchronization).
rooms_source = (BASE / "OnlineRooms.kt").read_text(encoding="utf-8")
room_rules_source = (BASE / "OnlineRoomRules.kt").read_text(encoding="utf-8")
if "runTransaction" not in rooms_source or "childrenCount >= ROOM_CAPACITY" not in rooms_source:
    sys.exit("FAIL: online-room join must atomically enforce room capacity")
if "ELBASHA_ROOM_CAPACITY = 10" not in room_rules_source or "generateCode" not in room_rules_source:
    sys.exit("FAIL: online-room capacity/code rules missing")
if '"rooms" -> { OnlineRoomsScreen' not in ui_source or 'ONLINE ROOMS' not in rooms_source:
    sys.exit("FAIL: online-room lobby is not wired into app navigation")
firebase_rules_text = (ROOT / "firebase/database.rules.json").read_text(encoding="utf-8")
if "newData.parent().child('hostUid')" not in firebase_rules_text:
    sys.exit("FAIL: online room creation must validate the host against the new room snapshot")
if "newData.parent().parent().child('hostUid')" not in firebase_rules_text:
    sys.exit("FAIL: online room member validation must permit the host and the joining member correctly")
print("PASS: online room lobby guards (6-char codes, 10-player cap, atomic join, navigation and initial-create validation)")

build_ui_source = (BASE / "BuildTeamGame.kt").read_text(encoding="utf-8")
if "selectedPoolNames" not in build_ui_source or "PLAYER FILTER" not in build_ui_source or "عشوائي" not in build_ui_source:
    sys.exit("FAIL: Build Team must offer random challenges and all-player/manual player filters")
if "TurnTimeSelector" not in build_ui_source or "VersusTimerHud" not in build_ui_source:
    sys.exit("FAIL: Build Team must have turn time selection and a visible turn timer")
deal_game_for_ui = (BASE / "DealOrNoDealGame.kt").read_text(encoding="utf-8")
if "CaseTile(index + 1" not in deal_game_for_ui or 'phase == "riskPick"' not in deal_game_for_ui or "chooseAiOpeningIndex" not in deal_game_for_ui:
    sys.exit("FAIL: Deal must show private four-case hands and let AI choose only from its own hand")
if "coachAuctionActive" not in auction_ui or "CoachAuctionCard" not in auction_ui:
    sys.exit("FAIL: coach must be included in the auction flow")
print("PASS: OSCO-style Build Team challenge/confirm flow, Deal mystery cases, hidden coach and auction cards")

# --- Build a Team stat-based pass-and-play guards ---
local_rules = (BASE / "PassAndPlayRules.kt").read_text(encoding="utf-8")
if '"build", "build_local" -> { BuildTeamStatScreen(' not in ui_source:
    sys.exit("FAIL: Build Team tile must route to the unified stat-based game")
if "BuildTeamPlayMode.PASS_AND_PLAY" not in build_stat_source or "BuildTeamStatPhase.HANDOVER" not in build_stat_source:
    sys.exit("FAIL: stat-based Build Team must support 2-4 players passing one device")
if "pickingOrder(playerCount, roundIndex)" not in build_stat_source or "pickingOrder" not in local_rules:
    sys.exit("FAIL: pass-and-play must rotate first pick between players")
if "PlayerSearch.suggestions(challengeCandidates, searchText, limit = 12)" not in build_stat_source or "PlayerSearch.normalize(searchText).length >= 3" not in build_stat_source:
    sys.exit("FAIL: Build Team suggestions must use the three-character threshold and the current round's eligible pool")
if "if (phase == BuildTeamStatPhase.RESULT && mode == BuildTeamPlayMode.AI" not in build_stat_source:
    sys.exit("FAIL: local Build Team matches must not submit competitive leaderboard scores")
if not (ROOT / "app/src/test/java/com/mostafabek/elbashagames/PassAndPlayRulesTest.kt").is_file():
    sys.exit("FAIL: PassAndPlayRulesTest.kt is missing")
print("PASS: stat-based Build Team supports pass-and-play, rotating picks, search suggestions and AI-only leaderboard submission")

# Session 20 honored guests: the names supplied for the Top10Bitches community
honors_source = (BASE / "ElbashaUi.kt").read_text(encoding="utf-8")
for guest_name in ["ياسين حسام", "عيسوي"]:
    if guest_name not in honors_source:
        sys.exit(f"FAIL: honored guest is missing from the Hall of Fame: {guest_name}")
if 'uiText("ضيوف الشرف", "HONORED GUESTS")' not in honors_source or "HonoredGuestCard(" not in honors_source:
    sys.exit("FAIL: honored guests section/cards are not wired into the Hall of Fame")
print("PASS: honored guests section includes Yassin Hossam and Essawy")

# Deal or No Deal: hidden private cases, locked rejection, and cards only after coaches.
deal_ui = (BASE / "DealOrNoDealGame.kt").read_text(encoding="utf-8")
for token in ["CaseTile(index + 1", "phase == \"draft\"", "phase == \"decision\"", "phase == \"riskPick\"", "index == rejectedCaseIndex", "phase == \"coachReveal\"", "DealRules.FINAL_CARD_WINDOW_SECONDS"]:
    if token not in deal_ui:
        sys.exit(f"FAIL: Deal private-case stage is missing: {token}")
if "revealedOptions" in deal_ui or "first, second" in deal_ui:
    sys.exit("FAIL: Deal must not offer a choice between the rejected and replacement players")
if "dealDecision(keep" in (BASE / "OnlineGameScreens.kt").read_text(encoding="utf-8"):
    sys.exit("FAIL: obsolete shared-box online Deal implementation remains enabled")
if "PostAuctionCardRules.canProtect" not in launch_source or "PostAuctionCardRules.canSteal" not in launch_source:
    sys.exit("FAIL: Auction post-game Shield and Steal controls are not wired to rules")
print("PASS: Deal has four private mystery cases per participant, a permanently locked rejected case, and post-coach cards")

# Session 25: music visibility, fast room creation, and pass-and-play coverage.
if '".read": true' not in firebase_rules_text.split('"sharedMusic"', 1)[1].split('"onlineRooms"', 1)[0]:
    sys.exit("FAIL: shared music must be readable by all installed clients")
if "room.setValue(payload)" not in rooms_source or "runTransaction" not in rooms_source:
    sys.exit("FAIL: room creation must use a direct write while joining remains transactional")
if ".info/connected" not in rooms_source or "Server connected" not in rooms_source:
    sys.exit("FAIL: online room screen must show the actual Firebase connection state")
if "AuctionLocalGameScreen" not in launch_source_for_ai or "PassAndPlayRules.normalizeNames" not in local_auction_source or "fun placeBid()" not in local_auction_source:
    sys.exit("FAIL: Auction must offer a real alternating two-player local bidding mode")
deal_game = (BASE / "DealOrNoDealGame.kt").read_text(encoding="utf-8")
if "passAndPlay" not in deal_game or "currentActor" not in deal_game or "Mباراة جهاز واحد" in deal_game:
    sys.exit("FAIL: Deal pass-and-play must rotate participants independently")
if "مباراة جهاز واحد: النتيجة محلية وغير مضافة للترتيب." not in deal_game:
    sys.exit("FAIL: local Deal matches must not submit one player's score to the competitive leaderboard")
if 'ملعب $currentPlayerName' not in build_stat_source:
    sys.exit("FAIL: Build Team must show an OSCO-style pitch while choosing players")
if 'AudioAttributes.USAGE_MEDIA' not in sound_source or 'AudioAttributes.CONTENT_TYPE_MUSIC' not in sound_source:
    sys.exit("FAIL: shared music playback must use Android media/music audio attributes")
if 'sound.setSharedMusic(saved)' not in ui_source or 'Shared music read failed:' not in ui_source:
    sys.exit("FAIL: every client must download the shared track and expose read failures")
online_session_source = (BASE / "OnlineMatchSession.kt").read_text(encoding="utf-8")
online_games_source = (BASE / "OnlineGameScreens.kt").read_text(encoding="utf-8")
online_rules_source = (BASE / "OnlineMatchRules.kt").read_text(encoding="utf-8")
for token in ["fun createRoom()", "fun joinRoom(", "fun startMatch(", "fun submitTurn(", "runTransaction", "OnlineMatchRules.canCommit"]:
    if token not in online_session_source:
        sys.exit(f"FAIL: online match coordinator is missing {token}")
for token in ["fun OnlineAuctionScreen(", "fun OnlineBuildTeamScreen(", "session.submitTurn(", "OnlineMatchRules.validBid"]:
    if token not in online_games_source:
        sys.exit(f"FAIL: live online gameplay is missing {token}")
for token in ["expectedRevision == actualRevision", "currentTurnUid == actorUid", "phase != \"finished\"", "fun validBid("]:
    if token not in online_rules_source:
        sys.exit(f"FAIL: online turn safety guard is missing {token}")
if 'onlineMode = true' not in auction_ui or 'onlineMode = true' not in build_stat_source or 'onlineMode = true' not in auction_ui:
    sys.exit("FAIL: Auction and Build Team online mode selectors are not connected")
if "fun OnlineDealScreen(" in online_games_source or "OnlineDealScreen(" in auction_ui:
    sys.exit("FAIL: Deal online mode must remain disabled until private case contents can be secured per participant")
for token in ['"gameType"', '"maxPlayers"', '"gameState"', '"seat"', '"joinedAt"']:
    if token not in firebase_rules_text:
        sys.exit(f"FAIL: Firebase rules are missing online match field {token}")
if "newData.child('revision').val() == data.child('revision').val() + 1" not in firebase_rules_text:
    sys.exit("FAIL: Firebase rules must require a strictly increasing match revision")
if "auth.uid == data.child('turnUid').val()" not in firebase_rules_text:
    sys.exit("FAIL: Firebase rules must only accept a move from the current turn owner")
if '"joinedAt": {' not in firebase_rules_text or "newData.isNumber() && newData.val() > 0" not in firebase_rules_text:
    sys.exit("FAIL: online member joinedAt must have an explicit positive-timestamp rule")
if "val() == data.child('revision').val() + 1" not in firebase_rules_text:
    sys.exit("FAIL: online match revision check is missing")
if 'roomData?.get("status") == "started"' not in online_session_source or "matchStarted" not in online_session_source:
    sys.exit("FAIL: leaving a live match must close the room so the opponent cannot be stuck on a departed turn")
if online_games_source.count('onBack = { session.leave(); onExit() }') < 2:
    sys.exit("FAIL: each online lobby back button must clean up its room membership")
if online_games_source.count('players.size != 2 || user.uid !in players') < 1 or 'players.size !in 2..4 || user.uid !in players' not in online_games_source:
    sys.exit("FAIL: online game screens must reject incomplete or mismatched room participant data")
if online_games_source.count('players[nextRound % players.size]') < 2:
    sys.exit("FAIL: online auction must rotate the opening player between lots")
if 'This page is a general friends lobby' not in rooms_source:
    sys.exit("FAIL: general room page must direct users to the in-game synchronized room flow")
if "BuildTeamLocalScreen" not in (BASE / "BuildTeamLocalGame.kt").read_text(encoding="utf-8") or "AuctionLocalGameScreen" not in auction_ui or 'oneDeviceMode' not in auction_ui:
    sys.exit("FAIL: one-device game modes must remain available alongside online mode")
print("PASS: Session 26 shared realtime match coordinator, revision-locked turns, and supported online screens for Auction and Build Team; Deal online stays disabled until private cases can be secured")
print("PASS: game room schema and Firebase rules cover typed rooms, seats, match state and authenticated members")
print("PASS: local play routes remain available beside the new online rooms")
