from typing import List, Dict, Any


def evaluate(data: Dict[str, Any], minutes: int = None) -> List[str]:
    """Generic mage coaching when hero-specific logic is unavailable."""
    fb = []

    minutes = minutes or data.get('match_duration') or 15
    kills = int(data.get('kills', 0) or 0)
    deaths = max(1, int(data.get('deaths', 0) or 0))
    assists = int(data.get('assists', 0) or 0)
    kda = (kills + assists) / deaths

    gpm = int(data.get('gold_per_min', 0) or 0)
    tfp = int(data.get('teamfight_participation', 0) or 0)
    damage = int(data.get('hero_damage', 0) or 0)
    damage_taken = int(data.get('damage_taken', 0) or 0)

    # Baselines for generic mage
    GPM_BASE = 550
    TFP_MIN = 60
    DMG_PER_MIN = 4500

    if kda < 3.0:
        fb.append(("warning", f"KDA {kda:.1f} is low for a mage. Play around power spikes and avoid risky face-checks."))
    else:
        fb.append(("info", f"Solid impact (KDA {kda:.1f}). Keep enabling fights with safe poke."))

    # GPM scaling
    gpm_target = GPM_BASE * (0.9 if minutes < 10 else 1.1 if minutes > 20 else 1.0)
    if gpm < gpm_target:
        fb.append(("warning", f"Gold per minute {gpm} below target {int(gpm_target)}. Clear waves faster and rotate for plates/objectives."))

    # Teamfight participation
    if tfp < TFP_MIN:
        fb.append(("warning", f"Fight presence {tfp}% is low. Join skirmishes where your CC/burst can swing fights."))

    # Damage output
    dmg_needed = int(DMG_PER_MIN * minutes)
    if damage < dmg_needed:
        fb.append(("warning", f"Total damage {damage:,} lower than expected {dmg_needed:,}. Harass with safe combos before committing ulti."))

    # Positioning signal
    if damage > 0 and damage_taken > 0 and (damage / max(1, damage_taken)) < 2.0:
        fb.append(("warning", "Damage-to-taken ratio is low. Improve spacing; cast from fog and behind your frontline."))

    return [f"{sev}: {msg}" if sev != "info" else msg for sev, msg in fb]

