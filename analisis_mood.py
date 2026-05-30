from analisis import BaseAnalyzer

class MoodAnalyzer(BaseAnalyzer):
    def analyze(self) -> dict:
        mood_map = {}
        mood_details = {}
        
        for track in self._data:
            mood = track.get_mood()
            if mood not in mood_map:
                mood_map[mood] = 0
                mood_details[mood] = {
                    "tracks": [],
                    "avg_valence": 0,
                    "avg_energy": 0,
                    "avg_tempo": 0,
                    "avg_popularity": 0,
                }
            mood_map[mood] += 1
            mood_details[mood]["tracks"].append(track)
        
        # Calculate averages for each mood
        for mood, details in mood_details.items():
            tracks = details["tracks"]
            details["avg_valence"] = round(sum(t.valence for t in tracks) / len(tracks), 4)
            details["avg_energy"] = round(sum(t.energy for t in tracks) / len(tracks), 4)
            details["avg_tempo"] = round(sum(t.tempo for t in tracks) / len(tracks), 2)
            details["avg_popularity"] = round(sum(t.popularity for t in tracks) / len(tracks), 2)
        
        return {
            "mood_distribution": mood_map,
            "mood_details": mood_details,
        }
    
    def display(self) -> None:
        r = self.analyze()
        print("[5] ANALISIS MOOD LAGU")
        print(f"Total Lagu: {self.get_total():,}\n")
        
        # Menampilkan penyebaran mood
        print("Distribusi Mood Lagu:")
        total = sum(r["mood_distribution"].values())
        for mood, count in sorted(r["mood_distribution"].items(), key=lambda x: -x[1]):
            percentage = (count / total) * 100
            print(f"  {mood:<12} : {count:>5} lagu ({percentage:>5.1f}%)")
        
        # Menampilkan statistik detail untuk setiap mood
        print("\nStatistik Detail Per Mood:")
        for mood in sorted(r["mood_details"].keys()):
            details = r["mood_details"][mood]
            print(f"\n  {mood}:")
            print(f"    Jumlah Lagu     : {len(details['tracks'])}")
            print(f"    Avg Valence     : {details['avg_valence']}")
            print(f"    Avg Energy      : {details['avg_energy']}")
            print(f"    Avg Tempo       : {details['avg_tempo']} BPM")
            print(f"    Avg Popularity  : {details['avg_popularity']}")
        
        # Menampilkan top lagu per mood
        print("\nTop 3 Lagu Per Mood (by popularity):")
        for mood in sorted(r["mood_details"].keys()):
            details = r["mood_details"][mood]
            tracks = sorted(details["tracks"], key=lambda t: -t.popularity)[:3]
            print(f"\n  {mood}:")
            for i, track in enumerate(tracks, 1):
                print(f"    {i}. {track.track_name} - {track.artists} ({track.popularity})")