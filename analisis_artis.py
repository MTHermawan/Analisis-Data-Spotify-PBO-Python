from analisis import BaseAnalyzer

class ArtistAnalyzer(BaseAnalyzer):

    def analyze(self) -> dict:
        artist_map = {}
        for track in self._data:
            artist = track.artists

            if artist not in artist_map:
                artist_map[artist] = []

            artist_map[artist].append(track)

        avg_popularity = {}
        total_tracks = {}
        avg_energy = {}

        for artist, tracks in artist_map.items():
            total_tracks[artist] = len(tracks)

            avg_popularity[artist] = round(
                sum(t.popularity for t in tracks) / len(tracks),
                2
            )
            avg_energy[artist] = round(
                sum(t.energy for t in tracks) / len(tracks),
                4
            )

        return {
            "total_artists": len(artist_map),

            "most_productive": sorted(
                total_tracks.items(),
                key=lambda x: -x[1]
            )[:5],

            "most_popular": sorted(
                avg_popularity.items(),
                key=lambda x: -x[1]
            )[:5],

            "most_energetic": sorted(
                avg_energy.items(),
                key=lambda x: -x[1]
            )[:5]
        }

    def display(self) -> None:
        result = self.analyze()

        print("\n[4] ANALISIS PER ARTIS")
        print(f"Total Artis : {result['total_artists']}")
        print(f"Total Lagu  : {self.get_total():,}")

        print("\n5 Artis dengan Lagu Terbanyak")
        for i, (artist, total) in enumerate(result['most_productive'], 1):
            print(f"{i}. {artist:<40} {total} lagu")

        print("\n5 Artis Terpopuler")
        for i, (artist, pop) in enumerate(result['most_popular'], 1):
            print(f"{i}. {artist:<40} {pop}")

        print("\n5 Artis Paling Energik")
        for i, (artist, energy) in enumerate(result['most_energetic'], 1):
            print(f"{i}. {artist[:40]:<40} {energy}")