from typing import List, Literal, Union, Annotated, Optional
from pydantic import BaseModel, Field
from datetime import datetime

# Pydantic models for type-safe data validation, mirroring Zod schemas.


class BaseMatch(BaseModel):
    """Common fields for all matches. Validation rules are defined here."""
    hero: str
    kills: Annotated[int, Field(ge=0)]
    deaths: Annotated[int, Field(ge=0)]
    assists: Annotated[int, Field(ge=0)]
    gold_per_min: Annotated[int, Field(ge=0)]
    hero_damage: Annotated[int, Field(ge=0)]
    turret_damage: Annotated[int, Field(ge=0)]
    damage_taken: Annotated[int, Field(ge=0)]
    teamfight_participation: Annotated[int, Field(ge=0, le=100)]
    positioning_rating: Literal['low', 'average', 'good']
    ult_usage: Literal['low', 'average', 'high']
    # Allow fractional minutes to support MM:SS parsing
    match_duration: Annotated[float, Field(ge=0.0)]
    # Optional hero-specific extras (kept for backward compatibility with rules)
    hooks_landed: Optional[int] = 0
    team_engages: Optional[int] = 0
    vision_score: Optional[int] = 0


# For broader hero coverage, accept any hero string. Keep optional
# Franco-specific metrics as soft fields on BaseMatch.
AnyMatch = BaseMatch


# A schema to validate the entire list of matches.
class Matches(BaseModel):
    """A schema to validate the entire list of matches."""
    data: List[AnyMatch]


# Meta data schemas for winrate leaderboard and hero analytics
class HeroMetaData(BaseModel):
    """Schema for individual hero meta statistics."""
    ranking: Annotated[int, Field(ge=1)]
    hero: str
    pick_rate: Annotated[float, Field(ge=0.0, le=100.0)]
    win_rate: Annotated[float, Field(ge=0.0, le=100.0)]
    ban_rate: Annotated[float, Field(ge=0.0, le=100.0)]
    counter_heroes: List[str]
    
    @property
    def meta_score(self) -> float:
        """Calculate overall meta strength score."""
        return (self.win_rate * 0.6) + (self.pick_rate * 0.3) + (min(self.ban_rate, 50) * 0.1)
    
    @property
    def tier(self) -> str:
        """Determine tier based on meta score and statistics."""
        if self.win_rate >= 55 and self.ban_rate >= 10:
            return "S"
        elif self.win_rate >= 52 and self.pick_rate >= 1.0:
            return "A"
        elif self.win_rate >= 50:
            return "B"
        elif self.win_rate >= 47:
            return "C"
        else:
            return "D"


class MetaLeaderboard(BaseModel):
    """Schema for complete meta leaderboard data."""
    data: List[HeroMetaData]
    last_updated: Optional[datetime] = None
    patch_version: Optional[str] = None
    
    @property
    def top_tier_heroes(self) -> List[HeroMetaData]:
        """Get S and A tier heroes."""
        return [hero for hero in self.data if hero.tier in ["S", "A"]]
    
    @property
    def most_banned_heroes(self) -> List[HeroMetaData]:
        """Get heroes with highest ban rates."""
        return sorted(self.data, key=lambda x: x.ban_rate, reverse=True)[:10]


class HeroRecommendation(BaseModel):
    """Schema for hero recommendation with reasoning."""
    hero: str
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    reasoning: str
    meta_data: HeroMetaData
    counter_effectiveness: Optional[float] = None
    
    
class RecommendationRequest(BaseModel):
    """Schema for hero recommendation request."""
    enemy_heroes: List[str] = []
    ally_heroes: List[str] = []
    role_preference: Optional[str] = None
    playstyle: Optional[str] = None
    
    
class PerformanceComparison(BaseModel):
    """Schema for comparing player performance vs meta."""
    hero: str
    player_winrate: Annotated[float, Field(ge=0.0, le=100.0)]
    meta_winrate: Annotated[float, Field(ge=0.0, le=100.0)]
    performance_gap: float
    percentile_rank: Optional[int] = None
    improvement_areas: List[str] = []
