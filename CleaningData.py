import csv
import os
from dataclasses import dataclass
from typing import List, Tuple

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

    def __post_init__(self):
        if not 0 <= self.popularity <= 100:
            raise ValueError("popularity must be 0-100")
        if not 0.0 <= self.danceability <= 1.0:
            raise ValueError("danceability must be 0.0-1.0")
        if not 0.0 <= self.energy <= 1.0:
            raise ValueError("energy must be 0.0-1.0")
        if self.duration_ms <= 0:
            raise ValueError("duration must be positive")
        if self.tempo <= 0:
            raise ValueError("tempo must be positive")

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
        else:
            return "Chill"

    def __str__(self) -> str:
        return (f"SpotifyTrack('{self.track_name}' by {self.artists} "
                f"| Genre: {self.track_genre} | Popularity: {self.popularity})")


class DataCleaner:
    """
    Bertanggung jawab membersihkan data mentah dari CSV.
    Menerapkan prinsip Single Responsibility (SOLID):
    hanya menangani validasi & pembersihan data.
    """

    VALID_RANGES = {
        "popularity"      : (0, 100),
        "duration_ms"     : (10000, 600000),
        "danceability"    : (0.0, 1.0),
        "energy"          : (0.0, 1.0),
        "key"             : (0, 11),
        "loudness"        : (-60.0, 5.0),
        "mode"            : (0, 1),
        "speechiness"     : (0.0, 1.0),
        "acousticness"    : (0.0, 1.0),
        "instrumentalness": (0.0, 1.0),
        "liveness"        : (0.0, 1.0),
        "valence"         : (0.0, 1.0),
        "tempo"           : (30.0, 300.0),
        "time_signature"  : (1, 7),
    }

    REQUIRED_STRINGS = ["track_id", "artists", "track_name", "track_genre"]

    OUTPUT_FIELDS = [
        "track_id", "artists", "track_name", "popularity",
        "duration_ms", "explicit", "danceability", "energy",
        "valence", "tempo", "track_genre"
    ]

    def __init__(self, filepath: str, output_dir: str = "output"):
        self.__filepath = filepath
        self.__output_dir = output_dir
        self.__raw_data: List[dict] = []
        self.__cleaned_data: List[SpotifyTrack] = []

        self.__total_rows      = 0
        self.__dropped_missing = 0
        self.__dropped_range   = 0
        self.__dropped_invalid = 0
        self.__kept_rows       = 0

    def __load_raw(self) -> None:
        with open(self.__filepath, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.__raw_data = list(reader)
        self.__total_rows = len(self.__raw_data)

    def __has_missing_values(self, row: dict) -> Tuple[bool, str]:
        for col in self.REQUIRED_STRINGS:
            val = row.get(col, "")
            if val is None or str(val).strip() == "" or str(val).lower() == "nan":
                return True, col
        return False, ""

    def __has_range_violation(self, row: dict) -> Tuple[bool, str]:
        for col, (lo, hi) in self.VALID_RANGES.items():
            raw_val = row.get(col, "")
            if raw_val is None or str(raw_val).strip() == "":
                return True, col
            try:
                val = float(raw_val)
            except ValueError:
                return True, col
            if not (lo <= val <= hi):
                return True, col
        return False, ""

    def __parse_row(self, row: dict) -> SpotifyTrack:
        return SpotifyTrack(
            track_id    = str(row["track_id"]).strip(),
            artists     = str(row["artists"]).strip(),
            track_name  = str(row["track_name"]).strip(),
            popularity  = int(row["popularity"]),
            duration_ms = int(row["duration_ms"]),
            explicit    = str(row["explicit"]).strip().lower() == "true",
            danceability= float(row["danceability"]),
            energy      = float(row["energy"]),
            valence     = float(row["valence"]),
            tempo       = float(row["tempo"]),
            track_genre = str(row["track_genre"]).strip(),
        )

    def clean(self) -> List[SpotifyTrack]:
        print("[*] Memulai proses data cleaning...")
        self.__load_raw()
        print(f"    Total baris awal  : {self.__total_rows:,}")

        for row in self.__raw_data:
            has_missing, _ = self.__has_missing_values(row)
            if has_missing:
                self.__dropped_missing += 1
                continue

            has_violation, _ = self.__has_range_violation(row)
            if has_violation:
                self.__dropped_range += 1
                continue

            try:
                track = self.__parse_row(row)
                self.__cleaned_data.append(track)
                self.__kept_rows += 1
            except (ValueError, KeyError):
                self.__dropped_invalid += 1
                continue

        print(f"    Dibuang (missing) : {self.__dropped_missing:,} baris")
        print(f"    Dibuang (range)   : {self.__dropped_range:,} baris")
        print(f"    Dibuang (invalid) : {self.__dropped_invalid:,} baris")
        print(f"    Total dibuang     : {self.__get_total_dropped():,} baris")
        print(f"    Data bersih       : {self.__kept_rows:,} baris")
        print("[*] Data cleaning selesai.\n")

        return self.__cleaned_data

    def save_clean(self) -> None:
        """Simpan data bersih ke output/dataset_clean.csv"""
        if not self.__cleaned_data:
            print("[!] Belum ada data bersih. Jalankan clean() terlebih dahulu.")
            return

        os.makedirs(self.__output_dir, exist_ok=True)
        output_path = os.path.join(self.__output_dir, "dataset_clean.csv")

        with open(output_path, "w", newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.OUTPUT_FIELDS)
            writer.writeheader()
            for track in self.__cleaned_data:
                writer.writerow({
                    "track_id"    : track.track_id,
                    "artists"     : track.artists,
                    "track_name"  : track.track_name,
                    "popularity"  : track.popularity,
                    "duration_ms" : track.duration_ms,
                    "explicit"    : track.explicit,
                    "danceability": track.danceability,
                    "energy"      : track.energy,
                    "valence"     : track.valence,
                    "tempo"       : track.tempo,
                    "track_genre" : track.track_genre,
                })

        print(f"[*] Data bersih disimpan ke '{output_path}'")
        print(f"    Total tersimpan : {self.__kept_rows:,} baris\n")

    def __get_total_dropped(self) -> int:
        return self.__dropped_missing + self.__dropped_range + self.__dropped_invalid

    def get_summary(self) -> dict:
        return {
            "total_awal"     : self.__total_rows,
            "dropped_missing": self.__dropped_missing,
            "dropped_range"  : self.__dropped_range,
            "dropped_invalid": self.__dropped_invalid,
            "total_dropped"  : self.__get_total_dropped(),
            "data_bersih"    : self.__kept_rows,
            "persen_bersih"  : round(self.__kept_rows / self.__total_rows * 100, 2)
                               if self.__total_rows > 0 else 0,
        }

    def display_summary(self) -> None:
        s = self.get_summary()
        print("=" * 50)
        print("         HASIL DATA CLEANING")
        print("=" * 50)
        print(f"  Total baris awal      : {s['total_awal']:,}")
        print(f"  Dibuang (missing val) : {s['dropped_missing']:,} baris")
        print(f"  Dibuang (range error) : {s['dropped_range']:,} baris")
        print(f"  Dibuang (parse error) : {s['dropped_invalid']:,} baris")
        print(f"  Total dibuang         : {s['total_dropped']:,} baris")
        print("-" * 50)
        print(f"  Data bersih           : {s['data_bersih']:,} baris")
        print(f"  Persentase bersih     : {s['persen_bersih']}%")
        print("=" * 50)


if __name__ == "__main__":
    cleaner = DataCleaner("./data/dataset.csv", output_dir="output")
    cleaned_data = cleaner.clean()
    cleaner.display_summary()
    cleaner.save_clean()