from analisis import BaseAnalyzer

class TopAnalyzer(BaseAnalyzer):
    def analyze(self) -> dict:
        top_tracks = sorted(self._data, key=lambda x: x.popularity, reverse=True)[:10]
        
        artist_counts = {}
        for track in self._data:
            artist_counts[track.artists] = artist_counts.get(track.artists, 0) + 1
        top_artists = sorted(artist_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {"tracks": top_tracks, "artists": top_artists}

    def display(self) -> None:
        result = self.analyze()
        print("\n[6] TOP TRACKS & ARTISTS")
        print(f"Total lagu diproses: {self.get_total():,}")
        
        print("\n=== 5 Lagu Terpopuler ===")
        for i, t in enumerate(result['tracks'][:5], 1):
            print(f"{i}. {t.track_name} oleh {t.artists} (Pop: {t.popularity})")
            
        print("\n=== 5 Artis dengan Lagu Terbanyak ===")
        for i, (artist, count) in enumerate(result['artists'][:5], 1):
            print(f"{i}. {artist}: {count} lagu")