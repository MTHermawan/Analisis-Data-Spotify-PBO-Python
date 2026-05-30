from dataclasses import dataclass, field
from typing import List, Tuple
from analisis import BaseAnalyzer
from analisis_formatter import AnalyzerFormatter
from analisis_kalkulator import AnalyzerCalculator
from model import SpotifyTrack

@dataclass
class PopularityBucket:
    label     : str
    min_score : int
    max_score : int
    count     : int = 0
    avg_score : float = 0.0
    top_tracks: list = field(default_factory=list)

class PopularityCalculator(AnalyzerCalculator):
    _thresholds: List[Tuple[str, int, int]] = [
        ("Sangat Populer" , 80, 100),
        ("Populer"        , 60,  79),
        ("Cukup Populer"  , 40,  59),
        ("Kurang Populer" , 20,  39),
        ("Tidak Populer"  ,  0,  19),
    ]

    def calculate(self, data: List[SpotifyTrack]) -> dict:
        n = len(data)
        if n == 0:
            return {}

        buckets = {
            label: PopularityBucket(label=label, min_score=lo, max_score=hi)
            for label, lo, hi in self._thresholds
        }
        for track in data:
            for label, lo, hi in self._thresholds:
                if lo <= track.popularity <= hi:
                    buckets[label].count += 1
                    buckets[label].top_tracks.append(track)
                    break

        for bucket in buckets.values():
            if bucket.count > 0:
                bucket.avg_score = round(
                    sum(t.popularity for t in bucket.top_tracks) / bucket.count, 2
                )
                bucket.top_tracks = sorted(
                    bucket.top_tracks, key=lambda t: -t.popularity
                )[:3]

        sorted_by_pop = sorted(data, key=lambda t: -t.popularity)
        top10    = sorted_by_pop[:10]
        bottom10 = sorted_by_pop[-10:]

        artist_tracks: dict = {}
        for track in data:
            for artist in track.artists.split(";"):
                artist = artist.strip()
                if artist not in artist_tracks:
                    artist_tracks[artist] = []
                artist_tracks[artist].append(track.popularity)

        top_artists = sorted(
            [
                (artist, round(sum(pops) / len(pops), 2), len(pops))
                for artist, pops in artist_tracks.items()
                if len(pops) >= 3
            ],
            key=lambda x: -x[1]
        )[:10]

        def pearson_r(xs, ys) -> float:
            n_   = len(xs)
            mx   = sum(xs) / n_
            my   = sum(ys) / n_
            num  = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
            den  = (
                sum((x - mx) ** 2 for x in xs) *
                sum((y - my) ** 2 for y in ys)
            ) ** 0.5
            return round(num / den, 4) if den != 0 else 0.0

        pops   = [t.popularity    for t in data]
        dance  = [t.danceability  for t in data]
        energy = [t.energy        for t in data]
        valence= [t.valence       for t in data]
        tempo  = [t.tempo         for t in data]

        correlations = {
            "Danceability" : pearson_r(pops, dance),
            "Energy"       : pearson_r(pops, energy),
            "Valence"      : pearson_r(pops, valence),
            "Tempo"        : pearson_r(pops, tempo),
        }

        return {
            "total_tracks" : n,
            "avg_popularity": round(sum(pops) / n, 2),
            "max_popularity": max(pops),
            "min_popularity": min(pops),
            "buckets"      : buckets,
            "top10"        : top10,
            "bottom10"     : bottom10,
            "top_artists"  : top_artists,
            "correlations" : correlations,
        }

class PopularityFormatter(AnalyzerFormatter):
    def format(self, stats: dict) -> None:
        if not stats:
            print("Tidak ada data untuk ditampilkan.")
            return

        print()
        print("ANALISIS POPULARITAS")
        print("=" * 55)
        print(f"  Total Lagu         : {stats['total_tracks']:,}")
        print(f"  Rata-rata Skor     : {stats['avg_popularity']}")
        print(f"  Skor Tertinggi     : {stats['max_popularity']}")
        print(f"  Skor Terendah      : {stats['min_popularity']}")
        print()

        print("  --- Distribusi Segmen Popularitas ---")
        total = stats["total_tracks"]
        for label, lo, hi in PopularityCalculator._thresholds:
            bucket: PopularityBucket = stats["buckets"][label]
            pct = round(bucket.count / total * 100, 1) if total else 0
            bar = "█" * (bucket.count * 25 // total) if total else ""
            print(
                f"  {label:<18} ({lo:>3}–{hi:<3}): "
                f"{bucket.count:>7,} ({pct:>5.1f}%) {bar}"
            )
        print()

        print("  --- Top 10 Lagu Terpopuler ---")
        for i, t in enumerate(stats["top10"], 1):
            nama = (t.track_name[:33] + "..") if len(t.track_name) > 35 else t.track_name
            artis = (t.artists[:28] + "..") if len(t.artists) > 30 else t.artists
            print(f"  {i:>2}. [{t.popularity:>3}] {nama:<35} - {artis}")
        print()

        print("  --- 10 Lagu dengan Skor Terendah ---")
        for i, t in enumerate(stats["bottom10"], 1):
            nama = (t.track_name[:33] + "..") if len(t.track_name) > 35 else t.track_name
            artis = (t.artists[:28] + "..") if len(t.artists) > 30 else t.artists
            print(f"  {i:>2}. [{t.popularity:>3}] {nama:<35} - {artis}")
        print()

        print("  --- Top 10 Artis (Rata-rata Popularitas, min. 3 lagu) ---")
        max_artist_len = max((len(artist) for artist, _, _ in stats["top_artists"]), default=0)
        for i, (artist, avg, cnt) in enumerate(stats["top_artists"], 1):
            nama = (artist[:max_artist_len] + "..") if len(artist) > max_artist_len else artist
            print(f"  {i:>2}. {nama:<{max_artist_len + 2}} {avg:<6} ({cnt} lagu)")
        print()

        print("  --- Korelasi dengan Popularitas (Pearson r) ---")
        for feature, r in stats["correlations"].items():
            arah = "↑ positif" if r > 0.05 else ("↓ negatif" if r < -0.05 else "~ netral")
            print(f"  {feature:<15}: {r:>7.4f}  {arah}")
        print("=" * 55)

class PopularityAnalyzer(BaseAnalyzer):
    def __init__(self, data: List[SpotifyTrack], calculator: AnalyzerCalculator = None, formatter: AnalyzerFormatter = None):
        super().__init__(data)
        self._calculator = calculator or PopularityCalculator()
        self._formatter  = formatter or PopularityFormatter()

    def analyze(self) -> dict:
        return self._calculator.calculate(self._data)

    def display(self) -> None:
        stats = self.analyze()
        self._formatter.format(stats)