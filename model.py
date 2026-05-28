import csv
from dataclasses import dataclass
from typing import List


@dataclass
class SpotifyTrack:
    track_id: str
    artists: str
    track_name: str
    popularity: int
    duration_ms: int
    explicit: bool
    danceability: float
    energy: float
    valence: float
    tempo: float
    track_genre: str

    def is_popular(self) -> bool:
        return self.popularity >= 70

    def get_duration_minutes(self) -> float:
        return round(self.duration_ms / 60000, 2)

    def get_mood(self) -> str:
        if self.valence >= 0.6 and self.energy >= 0.6:
            return "Happy"
        elif self.valence < 0.4 and self.energy < 0.4:
            return "Sad"
        elif self.energy >= 0.6:
            return "Energetic"
        return "Chill"


def load_data(filepath: str) -> List[SpotifyTrack]:
    tracks = []
    with open(filepath, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            try:
                tracks.append(SpotifyTrack(
                    track_id    = row["track_id"].strip(),
                    artists     = row["artists"].strip(),
                    track_name  = row["track_name"].strip(),
                    popularity  = int(row["popularity"]),
                    duration_ms = int(row["duration_ms"]),
                    explicit    = row["explicit"].strip().lower() == "true",
                    danceability= float(row["danceability"]),
                    energy      = float(row["energy"]),
                    valence     = float(row["valence"]),
                    tempo       = float(row["tempo"]),
                    track_genre = row["track_genre"].strip(),
                ))
            except (ValueError, KeyError):
                continue
    return tracks