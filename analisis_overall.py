from dataclasses import dataclass, field
from typing import List
from analisis import BaseAnalyzer
from analisis_formatter import AnalyzerFormatter
from analisis_kalkulator import AnalyzerCalculator
from model import SpotifyTrack

@dataclass
class OverallStatistics:
    total_tracks    : int = 0
    total_genres    : int = 0
    total_artists   : int = 0
    avg_popularity  : float = 0
    avg_danceability: float = 0
    avg_energy      : float = 0
    avg_valence     : float = 0
    avg_tempo       : float = 0
    avg_duration_min: float = 0
    explicit_count  : int = 0
    explicit_pct    : float = 0
    popular_count   : int = 0
    popular_pct     : float = 0
    mood_dist       : dict = field(default_factory=lambda: {"Happy": 0, "Sad": 0, "Energetic": 0, "Chill": 0})

class OverallCalculator(AnalyzerCalculator):
    def calculate(self, data: List[SpotifyTrack]) -> OverallStatistics:
        overall_stats = OverallStatistics()
        
        n = len(data)
        if n == 0:
            return overall_stats

        overall_stats.total_tracks  = n
        overall_stats.total_genres = len({t.track_genre for t in data})
        overall_stats.total_artists = len({a.strip() for t in data for a in t.artists.split(";")})

        overall_stats.avg_popularity = round(sum(t.popularity    for t in data) / n, 2)
        overall_stats.avg_danceability = round(sum(t.danceability  for t in data) / n, 4)
        overall_stats.avg_energy = round(sum(t.energy        for t in data) / n, 4)
        overall_stats.avg_valence = round(sum(t.valence       for t in data) / n, 4)
        overall_stats.avg_tempo = round(sum(t.tempo         for t in data) / n, 2)
        overall_stats.avg_duration_min = round(sum(t.get_duration_minutes() for t in data) / n, 2)

        overall_stats.explicit_count = sum(1 for t in data if t.explicit)
        overall_stats.explicit_pct   = round(overall_stats.explicit_count / n * 100, 2)

        overall_stats.popular_count  = sum(1 for t in data if t.is_popular())
        overall_stats.popular_pct    = round(overall_stats.popular_count / n * 100, 2)

        for t in data:
            overall_stats.mood_dist[t.get_mood()] += 1

        return overall_stats

class OverallFormatter(AnalyzerFormatter):
    def format(self, stats: OverallStatistics) -> None:
        if not stats:
            print("Tidak ada data untuk ditampilkan.")
            return

        mood = stats.mood_dist

        print()
        print("OVERALL STATISTICS")
        print("=" * 45)
        print(f"  Total Lagu            : {stats.total_tracks:,}")
        print(f"  Total Genre           : {stats.total_genres}")
        print(f"  Total Artis Unik      : {stats.total_artists:,}")
        print()

        print("  --- Rata-rata Audio Features ---")
        print(f"  Popularity            : {stats.avg_popularity}")
        print(f"  Danceability          : {stats.avg_danceability}")
        print(f"  Energy                : {stats.avg_energy}")
        print(f"  Valence (Positivitas) : {stats.avg_valence}")
        print(f"  Tempo (BPM)           : {stats.avg_tempo}")
        print(f"  Durasi Rata-rata      : {stats.avg_duration_min} menit")
        print()

        print("  --- Konten Eksplisit ---")
        print(f"  Lagu Eksplisit        : {stats.explicit_count:,} ({stats.explicit_pct}%)")
        print()

        print("  --- Popularitas ---")
        print(f"  Lagu Populer (≥70)    : {stats.popular_count:,} ({stats.popular_pct}%)")
        print()

        print("  --- Distribusi Mood ---")
        total = stats.total_tracks
        for mood_label, count in mood.items():
            pct = round(count / total * 100, 1) if total > 0 else 0.0
            bar = ("█" * (count * 20 // total)) if total > 0 else ""
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