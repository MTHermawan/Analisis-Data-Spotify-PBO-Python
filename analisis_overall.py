from dataclasses import dataclass
from typing import List

from analisis import BaseAnalyzer
from analisis_formatter import AnalyzerFormatter
from analisis_kalkulator import AnalyzerCalculator
from model import SpotifyTrack

@dataclass
class OverallStatistics:
    total_tracks    : int
    total_genres    : int
    total_artists   : int
    avg_popularity  : float
    avg_danceability: float
    avg_energy      : float
    avg_valence     : float
    avg_tempo       : float
    avg_duration_min: float
    explicit_count  : int
    explicit_pct    : float
    popular_count   : int
    popular_pct     : float
    mood_dist       : dict

class OverallCalculator(AnalyzerCalculator):
    def calculate(self, data: List[SpotifyTrack]) -> dict:
        n = len(data)
        if n == 0:
            return {}

        genres   = {t.track_genre for t in data}
        artists  = {a.strip() for t in data for a in t.artists.split(";")}

        avg_pop   = round(sum(t.popularity    for t in data) / n, 2)
        avg_dance = round(sum(t.danceability  for t in data) / n, 4)
        avg_en    = round(sum(t.energy        for t in data) / n, 4)
        avg_val   = round(sum(t.valence       for t in data) / n, 4)
        avg_tempo = round(sum(t.tempo         for t in data) / n, 2)
        avg_dur   = round(sum(t.get_duration_minutes() for t in data) / n, 2)

        explicit_count = sum(1 for t in data if t.explicit)
        explicit_pct   = round(explicit_count / n * 100, 2)

        popular_count  = sum(1 for t in data if t.is_popular())
        popular_pct    = round(popular_count / n * 100, 2)

        mood_dist: dict = {"Happy": 0, "Sad": 0, "Energetic": 0, "Chill": 0}
        for t in data:
            mood_dist[t.get_mood()] += 1

        return {
            "total_tracks"    : n,
            "total_genres"    : len(genres),
            "total_artists"   : len(artists),
            "avg_popularity"  : avg_pop,
            "avg_danceability": avg_dance,
            "avg_energy"      : avg_en,
            "avg_valence"     : avg_val,
            "avg_tempo"       : avg_tempo,
            "avg_duration_min": avg_dur,
            "explicit_count"  : explicit_count,
            "explicit_pct"    : explicit_pct,
            "popular_count"   : popular_count,
            "popular_pct"     : popular_pct,
            "mood_dist"       : mood_dist,
        }

class OverallFormatter(AnalyzerFormatter):
    def format(self, stats: dict) -> None:
        if not stats:
            print("Tidak ada data untuk ditampilkan.")
            return

        mood = stats["mood_dist"]

        print()
        print("OVERALL STATISTICS")
        print("=" * 45)
        print(f"  Total Lagu          : {stats['total_tracks']:,}")
        print(f"  Total Genre         : {stats['total_genres']}")
        print(f"  Total Artis Unik    : {stats['total_artists']:,}")
        print()

        print("  --- Rata-rata Audio Features ---")
        print(f"  Popularity          : {stats['avg_popularity']}")
        print(f"  Danceability        : {stats['avg_danceability']}")
        print(f"  Energy              : {stats['avg_energy']}")
        print(f"  Valence (Positivitas): {stats['avg_valence']}")
        print(f"  Tempo (BPM)         : {stats['avg_tempo']}")
        print(f"  Durasi Rata-rata    : {stats['avg_duration_min']} menit")
        print()

        print("  --- Konten Eksplisit ---")
        print(f"  Lagu Eksplisit      : {stats['explicit_count']:,} ({stats['explicit_pct']}%)")
        print()

        print("  --- Popularitas ---")
        print(f"  Lagu Populer (≥70)  : {stats['popular_count']:,} ({stats['popular_pct']}%)")
        print()

        print("  --- Distribusi Mood ---")
        total = stats["total_tracks"]
        for mood_label, count in mood.items():
            pct = round(count / total * 100, 1)
            bar = "█" * (count * 20 // total)
            print(f"  {mood_label:<12}: {count:>6,} ({pct:>5.1f}%) {bar}")

        print("=" * 45)

class OverallAnalyzer(BaseAnalyzer):
    def __init__(self, data: List[SpotifyTrack], calculator: AnalyzerCalculator = None, formatter: AnalyzerFormatter = None):
        super().__init__(data)
        self._calculator = calculator or OverallCalculator()
        self._formatter  = formatter or OverallFormatter()

    def analyze(self) -> dict:
        return self._calculator.calculate(self._data)

    def display(self) -> None:
        stats = self.analyze()
        self._formatter.format(stats)