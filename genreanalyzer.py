from abc import ABC, abstractmethod
from typing import List
from model import SpotifyTrack

class BaseAnalyzer(ABC):
    def __init__(self, data: List[SpotifyTrack]):
        self._data = data 

    @abstractmethod
    def analyze(self) -> dict:
        pass

    def get_total(self) -> int:
        return len(self._data)

class GenreAnalyzer(BaseAnalyzer):
    def analyze(self) -> dict:
        genre_map = {}
        for track in self._data:
            g = track.track_genre
            if g not in genre_map:
                genre_map[g] = []
            genre_map[g].append(track)

        avg_pop, avg_dance, avg_energy = {}, {}, {}
        for g, v in genre_map.items():
            avg_pop[g]    = round(sum(t.popularity   for t in v) / len(v), 2)
            avg_dance[g]  = round(sum(t.danceability for t in v) / len(v), 4)
            avg_energy[g] = round(sum(t.energy       for t in v) / len(v), 4)

        return {
            "total_genre"  : len(genre_map),
            "top_popular"  : sorted(avg_pop.items(),    key=lambda x: -x[1])[:5],
            "top_danceable": sorted(avg_dance.items(),  key=lambda x: -x[1])[:5],
            "top_energetic": sorted(avg_energy.items(), key=lambda x: -x[1])[:5],
        }

    def display(self) -> None:
        r = self.analyze()
        print("[3] ANALISIS PER GENRE")
        print(f"Total Genre : {r['total_genre']}")
        print(f"Total Lagu  : {self.get_total():,}")

        print("Top 5 Genre Terpopuler")
        for i, (genre, val) in enumerate(r['top_popular'], 1):
            print(f"  {i}. {genre:<20} {val}")

        print("\nTop 5 Genre Paling Danceable")
        for i, (genre, val) in enumerate(r['top_danceable'], 1):
            print(f"  {i}. {genre:<20} {val}")

        print("\nTop 5 Genre Paling Energik")
        for i, (genre, val) in enumerate(r['top_energetic'], 1):
            print(f"  {i}. {genre:<20} {val}")
