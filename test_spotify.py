import pytest
from dataclasses import fields
from typing import List

from model import SpotifyTrack, load_data
from analisis import BaseAnalyzer
from analisis_overall import (
    OverallStatistics, OverallCalculator, OverallFormatter, OverallAnalyzer
)
from analisis_popularitas import (
    PopularityBucket, PopularityCalculator, PopularityFormatter, PopularityAnalyzer
)
from analisis_genre import GenreAnalyzer
from analisis_artis import ArtistAnalyzer
from analisis_mood import MoodAnalyzer
from analisis_top import TopAnalyzer
from exporter import DataExporter

def make_track(
    track_id="T001", artists="Artist A", track_name="Song A",
    popularity=75, duration_ms=200000, explicit=False,
    danceability=0.7, energy=0.8, valence=0.75, tempo=120.0,
    track_genre="pop"
) -> SpotifyTrack:
    """Factory helper untuk membuat SpotifyTrack dengan nilai default."""
    return SpotifyTrack(
        track_id=track_id, artists=artists, track_name=track_name,
        popularity=popularity, duration_ms=duration_ms, explicit=explicit,
        danceability=danceability, energy=energy, valence=valence,
        tempo=tempo, track_genre=track_genre
    )


@pytest.fixture
def sample_tracks() -> List[SpotifyTrack]:
    """Dataset sampel standar: 8 lagu dengan variasi yang cukup untuk pengujian."""
    return [
        # Happy: valence >= 0.6 AND energy >= 0.6
        make_track("T1", "Artist A", "Happy Song",     82, 210000, False, 0.80, 0.85, 0.90, 128.0, "pop"),
        make_track("T2", "Artist A", "Dance Hit",      90, 195000, False, 0.90, 0.92, 0.88, 135.0, "pop"),
        # Sad: valence < 0.4 AND energy < 0.4
        make_track("T3", "Artist B", "Sad Ballad",     45, 240000, False, 0.30, 0.20, 0.15, 72.0,  "acoustic"),
        make_track("T4", "Artist B", "Lonely Night",   38, 225000, False, 0.25, 0.30, 0.20, 68.0,  "acoustic"),
        # Energetic: energy >= 0.6, valence < 0.6
        make_track("T5", "Artist C", "Power Anthem",   65, 185000, True,  0.55, 0.88, 0.40, 155.0, "rock"),
        make_track("T6", "Artist C", "Pump It Up",     70, 192000, True,  0.60, 0.91, 0.38, 160.0, "rock"),
        # Chill: tidak masuk kategori di atas
        make_track("T7", "Artist D", "Chill Vibes",    55, 230000, False, 0.50, 0.45, 0.55, 95.0,  "jazz"),
        make_track("T8", "Artist A;Artist B", "Collab Track", 80, 218000, False, 0.65, 0.70, 0.65, 110.0, "pop"),
    ]


@pytest.fixture
def single_track() -> List[SpotifyTrack]:
    """Dataset minimal: hanya 1 lagu — untuk edge case."""
    return [make_track()]


@pytest.fixture
def empty_tracks() -> List[SpotifyTrack]:
    """Dataset kosong — edge case paling ekstrem."""
    return []


@pytest.fixture
def explicit_tracks() -> List[SpotifyTrack]:
    """Dataset dengan campuran lagu eksplisit dan tidak eksplisit."""
    return [
        make_track("E1", explicit=True,  popularity=85),
        make_track("E2", explicit=True,  popularity=70),
        make_track("E3", explicit=False, popularity=50),
        make_track("E4", explicit=False, popularity=40),
    ]


# UNIT TESTING — Model (SpotifyTrack)

class TestSpotifyTrackModel:
    """Unit test untuk class SpotifyTrack di model.py."""

    def test_track_creation_stores_all_fields(self):
        """SpotifyTrack harus menyimpan semua 11 field dengan benar."""
        t = make_track(popularity=80, duration_ms=240000, explicit=True)
        assert t.popularity    == 80
        assert t.duration_ms   == 240000
        assert t.explicit      is True

    def test_is_popular_true_at_boundary(self):
        """is_popular() harus True tepat di nilai 70 (batas bawah inklusif)."""
        t = make_track(popularity=70)
        assert t.is_popular() is True

    def test_is_popular_true_above_threshold(self):
        """is_popular() harus True untuk nilai di atas 70."""
        t = make_track(popularity=95)
        assert t.is_popular() is True

    def test_is_popular_false_below_threshold(self):
        """is_popular() harus False untuk nilai di bawah 70."""
        t = make_track(popularity=69)
        assert t.is_popular() is False

    def test_is_popular_false_at_zero(self):
        """is_popular() harus False untuk skor 0 (batas minimum)."""
        t = make_track(popularity=0)
        assert t.is_popular() is False

    def test_get_duration_minutes_conversion(self):
        """get_duration_minutes() harus mengonversi ms ke menit dengan benar."""
        t = make_track(duration_ms=180000)   # 3 menit tepat
        assert t.get_duration_minutes() == 3.0

    def test_get_duration_minutes_rounding(self):
        """Hasil konversi durasi harus dibulatkan ke 2 desimal."""
        t = make_track(duration_ms=100000)   # 100000/60000 = 1.6667
        result = t.get_duration_minutes()
        assert result == round(100000 / 60000, 2)

    def test_get_mood_happy(self):
        """Mood Happy: valence >= 0.6 DAN energy >= 0.6."""
        t = make_track(valence=0.8, energy=0.8)
        assert t.get_mood() == "Happy"

    def test_get_mood_sad(self):
        """Mood Sad: valence < 0.4 DAN energy < 0.4."""
        t = make_track(valence=0.2, energy=0.2)
        assert t.get_mood() == "Sad"

    def test_get_mood_energetic(self):
        """Mood Energetic: energy >= 0.6 tapi valence < 0.6."""
        t = make_track(valence=0.3, energy=0.9)
        assert t.get_mood() == "Energetic"

    def test_get_mood_chill(self):
        """Mood Chill: tidak masuk kategori Happy, Sad, maupun Energetic."""
        t = make_track(valence=0.5, energy=0.4)
        assert t.get_mood() == "Chill"

    def test_get_mood_boundary_happy_exact(self):
        """Mood Happy: batas tepat valence=0.6 dan energy=0.6."""
        t = make_track(valence=0.6, energy=0.6)
        assert t.get_mood() == "Happy"

    def test_track_has_required_fields(self):
        """SpotifyTrack harus memiliki tepat 11 field yang diperlukan."""
        required = {
            "track_id", "artists", "track_name", "popularity", "duration_ms",
            "explicit", "danceability", "energy", "valence", "tempo", "track_genre"
        }
        actual = {f.name for f in fields(SpotifyTrack)}
        assert required == actual


# UNIT TESTING — Overall Statistics

class TestOverallCalculator:
    """Unit test untuk OverallCalculator."""

    def test_calculate_total_tracks(self, sample_tracks):
        """Jumlah total lagu harus sesuai panjang list input."""
        calc = OverallCalculator()
        result = calc.calculate(sample_tracks)
        assert result.total_tracks == len(sample_tracks)

    def test_calculate_total_genres(self, sample_tracks):
        """Total genre harus menghitung genre unik."""
        calc = OverallCalculator()
        result = calc.calculate(sample_tracks)
        expected = len({t.track_genre for t in sample_tracks})
        assert result.total_genres == expected

    def test_calculate_total_artists_splits_collaborations(self, sample_tracks):
        """Artis kolaborasi (dipisah ';') harus dihitung sebagai artis terpisah."""
        calc = OverallCalculator()
        result = calc.calculate(sample_tracks)
        expected = len({a.strip() for t in sample_tracks for a in t.artists.split(";")})
        assert result.total_artists == expected

    def test_calculate_avg_popularity_accuracy(self, sample_tracks):
        """Rata-rata popularity harus akurat (dibulatkan 2 desimal)."""
        calc = OverallCalculator()
        result = calc.calculate(sample_tracks)
        expected = round(sum(t.popularity for t in sample_tracks) / len(sample_tracks), 2)
        assert result.avg_popularity == expected

    def test_calculate_explicit_count(self, explicit_tracks):
        """Jumlah lagu eksplisit harus dihitung dengan benar."""
        calc = OverallCalculator()
        result = calc.calculate(explicit_tracks)
        assert result.explicit_count == 2
        assert result.explicit_pct   == 50.0

    def test_calculate_popular_count(self, sample_tracks):
        """Jumlah lagu populer (is_popular()) harus sesuai."""
        calc = OverallCalculator()
        result = calc.calculate(sample_tracks)
        expected = sum(1 for t in sample_tracks if t.is_popular())
        assert result.popular_count == expected

    def test_calculate_mood_distribution_covers_all_moods(self, sample_tracks):
        """Distribusi mood harus mencakup 4 kategori dan total = jumlah lagu."""
        calc = OverallCalculator()
        result = calc.calculate(sample_tracks)
        assert set(result.mood_dist.keys()) == {"Happy", "Sad", "Energetic", "Chill"}
        assert sum(result.mood_dist.values()) == len(sample_tracks)

    def test_calculate_avg_duration_minutes(self, sample_tracks):
        """Rata-rata durasi harus dikonversi dan dihitung dengan benar."""
        calc = OverallCalculator()
        result = calc.calculate(sample_tracks)
        expected = round(
            sum(t.get_duration_minutes() for t in sample_tracks) / len(sample_tracks), 2
        )
        assert result.avg_duration_min == expected

    def test_calculate_returns_overall_statistics_type(self, sample_tracks):
        """Hasil calculate() harus bertipe OverallStatistics."""
        calc = OverallCalculator()
        result = calc.calculate(sample_tracks)
        assert isinstance(result, OverallStatistics)


class TestOverallAnalyzer:
    """Unit test untuk OverallAnalyzer (Inheritance + Polimorfisme + DIP)."""

    def test_is_subclass_of_base_analyzer(self):
        """OverallAnalyzer harus merupakan subclass dari BaseAnalyzer (Inheritance)."""
        assert issubclass(OverallAnalyzer, BaseAnalyzer)

    def test_get_total_returns_correct_count(self, sample_tracks):
        """get_total() diwarisi dari BaseAnalyzer dan harus mengembalikan panjang data."""
        analyzer = OverallAnalyzer(sample_tracks)
        assert analyzer.get_total() == len(sample_tracks)

    def test_analyze_returns_overall_statistics(self, sample_tracks):
        """analyze() harus mengembalikan OverallStatistics (Polimorfisme)."""
        analyzer = OverallAnalyzer(sample_tracks)
        result   = analyzer.analyze()
        assert isinstance(result, OverallStatistics)

    def test_display_runs_without_exception(self, sample_tracks, capsys):
        """display() harus berjalan tanpa error dan mencetak output ke stdout."""
        OverallAnalyzer(sample_tracks).display()
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_custom_calculator_injected(self, sample_tracks):
        """DIP: calculator custom yang di-inject harus digunakan (bukan default)."""
        class DummyCalculator:
            def calculate(self, data):
                s = OverallStatistics()
                s.total_tracks = 999
                return s

        analyzer = OverallAnalyzer(sample_tracks, calculator=DummyCalculator())
        result   = analyzer.analyze()
        assert result.total_tracks == 999

    def test_data_encapsulation_protected(self, sample_tracks):
        """Enkapsulasi: _data seharusnya protected (prefix _), bukan public."""
        analyzer = OverallAnalyzer(sample_tracks)
        assert hasattr(analyzer, "_data")
        assert not hasattr(analyzer, "data")


# UNIT TESTING — Analisis Popularitas

class TestPopularityCalculator:
    """Unit test untuk PopularityCalculator."""

    def test_segments_tracks_into_correct_buckets(self, sample_tracks):
        """Setiap lagu harus masuk ke bucket yang sesuai berdasarkan popularitas."""
        calc   = PopularityCalculator()
        result = calc.calculate(sample_tracks)
        assert result["buckets"]["Sangat Populer"].count >= 1

    def test_top10_sorted_descending(self, sample_tracks):
        """Top 10 harus diurutkan dari popularity tertinggi ke terendah."""
        calc   = PopularityCalculator()
        result = calc.calculate(sample_tracks)
        pops = [t.popularity for t in result["top10"]]
        assert pops == sorted(pops, reverse=True)

    def test_bottom10_sorted_ascending(self, sample_tracks):
        """Bottom 10 harus berisi lagu dengan skor terendah."""
        calc   = PopularityCalculator()
        result = calc.calculate(sample_tracks)
        pops_bottom = [t.popularity for t in result["bottom10"]]
        all_pops    = sorted([t.popularity for t in sample_tracks])
        assert min(pops_bottom) <= min([t.popularity for t in result["top10"]])

    def test_avg_popularity_matches_manual(self, sample_tracks):
        """Rata-rata popularity di result harus sama dengan kalkulasi manual."""
        calc     = PopularityCalculator()
        result   = calc.calculate(sample_tracks)
        expected = round(sum(t.popularity for t in sample_tracks) / len(sample_tracks), 2)
        assert result["avg_popularity"] == expected

    def test_max_min_popularity_correct(self, sample_tracks):
        """max dan min popularity harus sesuai dengan nilai ekstrem di dataset."""
        calc   = PopularityCalculator()
        result = calc.calculate(sample_tracks)
        assert result["max_popularity"] == max(t.popularity for t in sample_tracks)
        assert result["min_popularity"] == min(t.popularity for t in sample_tracks)

    def test_bucket_count_sums_to_total(self, sample_tracks):
        """Total count semua bucket harus sama dengan total lagu."""
        calc   = PopularityCalculator()
        result = calc.calculate(sample_tracks)
        total  = sum(b.count for b in result["buckets"].values())
        assert total == len(sample_tracks)

    def test_top_artists_minimum_3_tracks(self, sample_tracks):
        """Top artis hanya muncul jika memiliki minimal 3 lagu."""
        calc   = PopularityCalculator()
        result = calc.calculate(sample_tracks)
        for _, _, count in result["top_artists"]:
            assert count >= 3

    def test_correlations_keys_correct(self, sample_tracks):
        """Korelasi harus mencakup keempat audio feature yang ditentukan."""
        calc   = PopularityCalculator()
        result = calc.calculate(sample_tracks)
        expected_keys = {"Danceability", "Energy", "Valence", "Tempo"}
        assert set(result["correlations"].keys()) == expected_keys

    def test_correlations_values_in_valid_range(self, sample_tracks):
        """Nilai korelasi Pearson harus berada di rentang [-1, 1]."""
        calc   = PopularityCalculator()
        result = calc.calculate(sample_tracks)
        for feature, r in result["correlations"].items():
            assert -1.0 <= r <= 1.0, f"Korelasi {feature} = {r} di luar rentang [-1, 1]"


class TestPopularityAnalyzer:
    """Unit test untuk PopularityAnalyzer."""

    def test_is_subclass_of_base_analyzer(self):
        """PopularityAnalyzer harus subclass dari BaseAnalyzer (Inheritance)."""
        assert issubclass(PopularityAnalyzer, BaseAnalyzer)

    def test_analyze_returns_dict(self, sample_tracks):
        """analyze() harus mengembalikan dict (Polimorfisme — override parent)."""
        analyzer = PopularityAnalyzer(sample_tracks)
        assert isinstance(analyzer.analyze(), dict)

    def test_display_runs_without_exception(self, sample_tracks, capsys):
        """display() harus berjalan tanpa error dan menghasilkan output."""
        PopularityAnalyzer(sample_tracks).display()
        captured = capsys.readouterr()
        assert "ANALISIS POPULARITAS" in captured.out

    def test_popularity_ordering_high_greater_than_low(self, sample_tracks):
        """Rata-rata 'Sangat Populer' harus lebih tinggi dari 'Tidak Populer'."""
        analyzer = PopularityAnalyzer(sample_tracks)
        result   = analyzer.analyze()
        buckets  = result["buckets"]
        if buckets["Sangat Populer"].count > 0 and buckets["Tidak Populer"].count > 0:
            assert buckets["Sangat Populer"].avg_score > buckets["Tidak Populer"].avg_score



# UNIT TESTING — Analyzer Lainnya

class TestGenreAnalyzer:
    """Unit test untuk GenreAnalyzer."""

    def test_total_genre_count_correct(self, sample_tracks):
        """Total genre harus menghitung genre unik di dataset."""
        analyzer = GenreAnalyzer(sample_tracks)
        result   = analyzer.analyze()
        expected = len({t.track_genre for t in sample_tracks})
        assert result["total_genre"] == expected

    def test_top_popular_has_max_5_entries(self, sample_tracks):
        """Top 5 genre terpopuler tidak boleh lebih dari 5 entri."""
        analyzer = GenreAnalyzer(sample_tracks)
        result   = analyzer.analyze()
        assert len(result["top_popular"]) <= 5

    def test_top_popular_sorted_descending(self, sample_tracks):
        """Top popular genre harus diurutkan dari nilai tertinggi."""
        analyzer = GenreAnalyzer(sample_tracks)
        result   = analyzer.analyze()
        vals = [v for _, v in result["top_popular"]]
        assert vals == sorted(vals, reverse=True)

    def test_display_shows_genre_header(self, sample_tracks, capsys):
        """Output display() harus mengandung header analisis genre."""
        GenreAnalyzer(sample_tracks).display()
        captured = capsys.readouterr()
        assert "ANALISIS PER GENRE" in captured.out


class TestArtistAnalyzer:
    """Unit test untuk ArtistAnalyzer."""

    def test_most_productive_max_5(self, sample_tracks):
        """Artis paling produktif yang ditampilkan maksimal 5."""
        analyzer = ArtistAnalyzer(sample_tracks)
        result   = analyzer.analyze()
        assert len(result["most_productive"]) <= 5

    def test_most_popular_sorted_descending(self, sample_tracks):
        """Artis terpopuler harus diurutkan dari rata-rata tertinggi."""
        analyzer = ArtistAnalyzer(sample_tracks)
        result   = analyzer.analyze()
        vals = [v for _, v in result["most_popular"]]
        assert vals == sorted(vals, reverse=True)

    def test_total_artists_positive(self, sample_tracks):
        """Jumlah artis harus lebih dari 0 untuk dataset non-kosong."""
        analyzer = ArtistAnalyzer(sample_tracks)
        result   = analyzer.analyze()
        assert result["total_artists"] > 0


class TestMoodAnalyzer:
    """Unit test untuk MoodAnalyzer."""

    def test_mood_distribution_sums_to_total(self, sample_tracks):
        """Total distribusi mood harus sama dengan total lagu."""
        analyzer = MoodAnalyzer(sample_tracks)
        result   = analyzer.analyze()
        total = sum(result["mood_distribution"].values())
        assert total == len(sample_tracks)

    def test_mood_details_avg_valence_in_range(self, sample_tracks):
        """Rata-rata valence per mood harus berada di [0, 1]."""
        analyzer = MoodAnalyzer(sample_tracks)
        result   = analyzer.analyze()
        for mood, details in result["mood_details"].items():
            assert 0.0 <= details["avg_valence"] <= 1.0, \
                f"Avg valence mood {mood} = {details['avg_valence']} di luar [0,1]"

    def test_mood_details_avg_energy_in_range(self, sample_tracks):
        """Rata-rata energy per mood harus berada di [0, 1]."""
        analyzer = MoodAnalyzer(sample_tracks)
        result   = analyzer.analyze()
        for mood, details in result["mood_details"].items():
            assert 0.0 <= details["avg_energy"] <= 1.0, \
                f"Avg energy mood {mood} = {details['avg_energy']} di luar [0,1]"

    def test_happy_mood_valence_above_sad(self, sample_tracks):
        """Rata-rata valence mood Happy harus lebih tinggi dari Sad."""
        analyzer = MoodAnalyzer(sample_tracks)
        result   = analyzer.analyze()
        details  = result["mood_details"]
        if "Happy" in details and "Sad" in details:
            assert details["Happy"]["avg_valence"] > details["Sad"]["avg_valence"]


class TestTopAnalyzer:
    """Unit test untuk TopAnalyzer."""

    def test_top_tracks_max_10(self, sample_tracks):
        """Top tracks tidak boleh melebihi 10 entri."""
        analyzer = TopAnalyzer(sample_tracks)
        result   = analyzer.analyze()
        assert len(result["tracks"]) <= 10

    def test_top_tracks_sorted_by_popularity(self, sample_tracks):
        """Top tracks harus diurutkan berdasarkan popularity secara descending."""
        analyzer = TopAnalyzer(sample_tracks)
        result   = analyzer.analyze()
        pops = [t.popularity for t in result["tracks"]]
        assert pops == sorted(pops, reverse=True)

    def test_top_artists_max_10(self, sample_tracks):
        """Top artists tidak boleh melebihi 10 entri."""
        analyzer = TopAnalyzer(sample_tracks)
        result   = analyzer.analyze()
        assert len(result["artists"]) <= 10


# DATA VALIDATION — Integritas & Konsistensi Data

class TestDataValidation:
    """Validasi integritas, tipe data, dan nilai yang masuk akal."""

    def test_popularity_range_0_to_100(self, sample_tracks):
        """Popularity setiap lagu harus berada di rentang valid [0, 100]."""
        for t in sample_tracks:
            assert 0 <= t.popularity <= 100, \
                f"Lagu '{t.track_name}' punya popularity={t.popularity} di luar [0,100]"

    def test_danceability_range_0_to_1(self, sample_tracks):
        """Danceability setiap lagu harus berada di rentang [0.0, 1.0]."""
        for t in sample_tracks:
            assert 0.0 <= t.danceability <= 1.0, \
                f"Lagu '{t.track_name}' punya danceability={t.danceability} di luar [0,1]"

    def test_energy_range_0_to_1(self, sample_tracks):
        """Energy setiap lagu harus berada di rentang [0.0, 1.0]."""
        for t in sample_tracks:
            assert 0.0 <= t.energy <= 1.0, \
                f"Lagu '{t.track_name}' punya energy={t.energy} di luar [0,1]"

    def test_valence_range_0_to_1(self, sample_tracks):
        """Valence setiap lagu harus berada di rentang [0.0, 1.0]."""
        for t in sample_tracks:
            assert 0.0 <= t.valence <= 1.0, \
                f"Lagu '{t.track_name}' punya valence={t.valence} di luar [0,1]"

    def test_tempo_positive(self, sample_tracks):
        """Tempo setiap lagu harus bernilai positif (> 0)."""
        for t in sample_tracks:
            assert t.tempo > 0, \
                f"Lagu '{t.track_name}' punya tempo={t.tempo} yang tidak valid"

    def test_duration_positive(self, sample_tracks):
        """Durasi dalam ms harus bernilai positif."""
        for t in sample_tracks:
            assert t.duration_ms > 0, \
                f"Lagu '{t.track_name}' punya duration_ms={t.duration_ms} yang tidak valid"

    def test_track_id_not_empty(self, sample_tracks):
        """track_id tidak boleh berupa string kosong."""
        for t in sample_tracks:
            assert len(t.track_id.strip()) > 0, \
                f"Ditemukan track_id kosong pada lagu '{t.track_name}'"

    def test_track_name_not_empty(self, sample_tracks):
        """track_name tidak boleh berupa string kosong."""
        for t in sample_tracks:
            assert len(t.track_name.strip()) > 0, \
                "Ditemukan track_name kosong"

    def test_artists_not_empty(self, sample_tracks):
        """Kolom artists tidak boleh kosong."""
        for t in sample_tracks:
            assert len(t.artists.strip()) > 0, \
                f"Lagu '{t.track_name}' tidak memiliki nama artis"

    def test_explicit_is_boolean(self, sample_tracks):
        """Field explicit harus bertipe boolean."""
        for t in sample_tracks:
            assert isinstance(t.explicit, bool), \
                f"Lagu '{t.track_name}' punya explicit={t.explicit!r} bukan bool"

    def test_popularity_is_integer(self, sample_tracks):
        """Popularity harus bertipe int."""
        for t in sample_tracks:
            assert isinstance(t.popularity, int), \
                f"Lagu '{t.track_name}' punya popularity bertipe {type(t.popularity)}"

    def test_duration_ms_is_integer(self, sample_tracks):
        """duration_ms harus bertipe int."""
        for t in sample_tracks:
            assert isinstance(t.duration_ms, int), \
                f"Lagu '{t.track_name}' punya duration_ms bertipe {type(t.duration_ms)}"

    def test_overall_avg_popularity_in_valid_range(self, sample_tracks):
        """Rata-rata popularity dari OverallCalculator harus dalam [0, 100]."""
        calc   = OverallCalculator()
        result = calc.calculate(sample_tracks)
        assert 0 <= result.avg_popularity <= 100

    def test_overall_explicit_pct_in_valid_range(self, sample_tracks):
        """Persentase lagu eksplisit harus dalam [0, 100]."""
        calc   = OverallCalculator()
        result = calc.calculate(sample_tracks)
        assert 0.0 <= result.explicit_pct <= 100.0

    def test_overall_popular_pct_in_valid_range(self, sample_tracks):
        """Persentase lagu populer harus dalam [0, 100]."""
        calc   = OverallCalculator()
        result = calc.calculate(sample_tracks)
        assert 0.0 <= result.popular_pct <= 100.0

    def test_genre_avg_popularity_per_genre_in_range(self, sample_tracks):
        """Rata-rata popularity per genre harus dalam [0, 100]."""
        analyzer = GenreAnalyzer(sample_tracks)
        result   = analyzer.analyze()
        for genre, avg_pop in result["top_popular"]:
            assert 0 <= avg_pop <= 100, \
                f"Genre '{genre}' punya avg_popularity={avg_pop} di luar [0,100]"

    def test_mood_distribution_no_negative_count(self, sample_tracks):
        """Jumlah lagu per mood tidak boleh negatif."""
        analyzer = MoodAnalyzer(sample_tracks)
        result   = analyzer.analyze()
        for mood, count in result["mood_distribution"].items():
            assert count >= 0, f"Mood '{mood}' punya count negatif: {count}"


# EDGE CASE TESTING — Kondisi Batas

class TestEdgeCases:
    """Pengujian kondisi batas dan skenario ekstrem."""

    def test_overall_empty_dataset_returns_default_stats(self, empty_tracks):
        """OverallCalculator pada dataset kosong harus mengembalikan nilai default (0)."""
        calc   = OverallCalculator()
        result = calc.calculate(empty_tracks)
        assert result.total_tracks == 0

    def test_popularity_empty_dataset_returns_empty_dict(self, empty_tracks):
        """PopularityCalculator pada dataset kosong harus mengembalikan dict kosong."""
        calc   = PopularityCalculator()
        result = calc.calculate(empty_tracks)
        assert result == {}

    def test_overall_display_empty_does_not_crash(self, empty_tracks, capsys):
        """display() pada dataset kosong tidak boleh raise exception."""
        try:
            OverallAnalyzer(empty_tracks).display()
        except Exception as e:
            pytest.fail(f"display() pada data kosong raise exception: {e}")

    def test_popularity_display_empty_does_not_crash(self, empty_tracks, capsys):
        """PopularityAnalyzer.display() pada dataset kosong tidak boleh crash."""
        try:
            PopularityAnalyzer(empty_tracks).display()
        except Exception as e:
            pytest.fail(f"display() pada data kosong raise exception: {e}")

    def test_get_total_empty_returns_zero(self, empty_tracks):
        """get_total() pada dataset kosong harus mengembalikan 0."""
        assert OverallAnalyzer(empty_tracks).get_total() == 0

    # Dataset Satu Lagu

    def test_overall_single_track_correct_total(self, single_track):
        """Dataset 1 lagu: total_tracks harus 1."""
        calc   = OverallCalculator()
        result = calc.calculate(single_track)
        assert result.total_tracks == 1

    def test_overall_single_track_avg_equals_value(self, single_track):
        """Dataset 1 lagu: rata-rata popularity = popularity lagu itu sendiri."""
        calc   = OverallCalculator()
        result = calc.calculate(single_track)
        assert result.avg_popularity == single_track[0].popularity

    def test_popularity_single_track_no_crash(self, single_track, capsys):
        """Dataset 1 lagu: PopularityAnalyzer tidak boleh crash."""
        PopularityAnalyzer(single_track).display()

    def test_genre_single_track_total_genre_one(self, single_track):
        """Dataset 1 lagu: total genre harus 1."""
        analyzer = GenreAnalyzer(single_track)
        result   = analyzer.analyze()
        assert result["total_genre"] == 1

    def test_mood_single_track_distribution_sums_to_one(self, single_track):
        """Dataset 1 lagu: total distribusi mood harus 1."""
        analyzer = MoodAnalyzer(single_track)
        result   = analyzer.analyze()
        assert sum(result["mood_distribution"].values()) == 1

    # Nilai Ekstrem pada Atribut

    def test_track_popularity_zero_is_valid(self):
        """Lagu dengan popularity 0 harus tetap valid dan tidak popular."""
        t = make_track(popularity=0)
        assert t.is_popular() is False
        assert t.popularity   == 0

    def test_track_popularity_100_is_valid(self):
        """Lagu dengan popularity 100 (maksimum) harus dianggap popular."""
        t = make_track(popularity=100)
        assert t.is_popular() is True

    def test_track_with_very_long_name(self):
        """SpotifyTrack dengan nama lagu panjang harus tetap tersimpan penuh."""
        long_name = "A" * 200
        t = make_track(track_name=long_name)
        assert t.track_name == long_name

    def test_track_with_semicolon_collaboration_artist(self):
        """Artis dengan ';' (kolaborasi) harus tetap disimpan sebagai satu string."""
        collab = "Artist One;Artist Two;Artist Three"
        t = make_track(artists=collab)
        assert t.artists == collab
        assert len(t.artists.split(";")) == 3

    def test_top_analyzer_fewer_than_10_tracks(self, single_track):
        """TopAnalyzer dengan < 10 lagu tidak boleh crash."""
        analyzer = TopAnalyzer(single_track)
        result   = analyzer.analyze()
        assert len(result["tracks"]) <= 10

    def test_mood_boundary_happy_exact_values(self):
        """Lagu tepat di batas Happy (valence=0.6, energy=0.6) harus Happy."""
        t = make_track(valence=0.6, energy=0.6)
        assert t.get_mood() == "Happy"

    def test_mood_boundary_sad_near_threshold(self):
        """Lagu dengan valence=0.399 dan energy=0.399 harus Sad."""
        t = make_track(valence=0.399, energy=0.399)
        assert t.get_mood() == "Sad"

    def test_popularity_bucket_avg_score_correct_single_entry(self):
        """Bucket dengan 1 lagu: avg_score harus sama dengan popularity lagu tersebut."""
        tracks = [make_track(popularity=85)]
        calc   = PopularityCalculator()
        result = calc.calculate(tracks)
        bucket = result["buckets"]["Sangat Populer"]
        assert bucket.count     == 1
        assert bucket.avg_score == 85.0

    def test_all_analyzers_handle_single_track(self, single_track):
        """Semua analyzer harus bisa memproses dataset 1 lagu tanpa exception."""
        analyzers = [
            OverallAnalyzer(single_track),
            PopularityAnalyzer(single_track),
            GenreAnalyzer(single_track),
            ArtistAnalyzer(single_track),
            MoodAnalyzer(single_track),
            TopAnalyzer(single_track),
        ]
        for analyzer in analyzers:
            try:
                analyzer.analyze()
            except Exception as e:
                pytest.fail(f"{type(analyzer).__name__}.analyze() crash: {e}")


# CODE QUALITY — Kontrak OOP & Prinsip SOLID

class TestCodeQuality:
    """Pengujian arsitektur: ABC, enkapsulasi, LSP, SRP, DIP."""

    def test_base_analyzer_is_abstract(self):
        """BaseAnalyzer (ABC) tidak boleh bisa di-instantiate langsung."""
        with pytest.raises(TypeError):
            BaseAnalyzer([])   # type: ignore

    def test_all_analyzers_implement_analyze(self, sample_tracks):
        """Semua concrete analyzer harus mengimplementasikan method analyze()."""
        analyzers = [
            OverallAnalyzer(sample_tracks),
            PopularityAnalyzer(sample_tracks),
            GenreAnalyzer(sample_tracks),
            ArtistAnalyzer(sample_tracks),
            MoodAnalyzer(sample_tracks),
            TopAnalyzer(sample_tracks),
            DataExporter(sample_tracks),
        ]
        for analyzer in analyzers:
            result = analyzer.analyze()
            assert result is not None, \
                f"{type(analyzer).__name__}.analyze() mengembalikan None"

    def test_all_analyzers_implement_display(self, sample_tracks, capsys):
        """Semua concrete analyzer harus mengimplementasikan method display()."""
        analyzers = [
            OverallAnalyzer(sample_tracks),
            PopularityAnalyzer(sample_tracks),
            GenreAnalyzer(sample_tracks),
            ArtistAnalyzer(sample_tracks),
            MoodAnalyzer(sample_tracks),
            TopAnalyzer(sample_tracks),
        ]
        for analyzer in analyzers:
            try:
                analyzer.display()
            except Exception as e:
                pytest.fail(f"{type(analyzer).__name__}.display() raise: {e}")

    def test_lsp_all_analyzers_substitutable(self, sample_tracks):
        """LSP: Semua subclass harus bisa digunakan sebagai BaseAnalyzer."""
        def use_as_base(analyzer: BaseAnalyzer) -> None:
            assert isinstance(analyzer.analyze(), (dict, OverallStatistics))
            assert isinstance(analyzer.get_total(), int)

        for AnalyzerClass in [
            OverallAnalyzer, PopularityAnalyzer, GenreAnalyzer,
            ArtistAnalyzer, MoodAnalyzer, TopAnalyzer
        ]:
            use_as_base(AnalyzerClass(sample_tracks))

    def test_encapsulation_data_is_protected(self, sample_tracks):
        """Enkapsulasi: _data harus ada sebagai protected; tidak ada atribut 'data'."""
        for AnalyzerClass in [OverallAnalyzer, PopularityAnalyzer, GenreAnalyzer]:
            analyzer = AnalyzerClass(sample_tracks)
            assert hasattr(analyzer, "_data"), \
                f"{AnalyzerClass.__name__} tidak memiliki _data"
            assert not hasattr(analyzer, "data"), \
                f"{AnalyzerClass.__name__} mengekspos 'data' secara publik"

    def test_dip_overall_accepts_custom_calculator(self, sample_tracks):
        """DIP: OverallAnalyzer harus menerima calculator eksternal (Dependency Injection)."""
        class FixedCalculator:
            def calculate(self, data):
                s = OverallStatistics()
                s.total_tracks = 42
                return s

        analyzer = OverallAnalyzer(sample_tracks, calculator=FixedCalculator())
        result   = analyzer.analyze()
        assert result.total_tracks == 42

    def test_dip_popularity_accepts_custom_calculator(self, sample_tracks):
        """DIP: PopularityAnalyzer harus menerima calculator eksternal."""
        class FixedCalculator:
            def calculate(self, data):
                return {"total_tracks": 99, "injected": True}

        analyzer = PopularityAnalyzer(sample_tracks, calculator=FixedCalculator())
        result   = analyzer.analyze()
        assert result.get("injected") is True

    def test_srp_overall_calculator_only_calculates(self, sample_tracks):
        """SRP: OverallCalculator tidak boleh memiliki method format/display."""
        calc = OverallCalculator()
        assert not hasattr(calc, "display")
        assert not hasattr(calc, "format")
        assert not hasattr(calc, "print")

    def test_srp_overall_formatter_only_formats(self):
        """SRP: OverallFormatter tidak boleh memiliki method calculate."""
        formatter = OverallFormatter()
        assert not hasattr(formatter, "calculate")
        assert not hasattr(formatter, "analyze")

    def test_get_total_consistent_with_data_length(self, sample_tracks):
        """get_total() harus konsisten dengan len(_data) di semua analyzer."""
        for AnalyzerClass in [
            OverallAnalyzer, PopularityAnalyzer, GenreAnalyzer,
            ArtistAnalyzer, MoodAnalyzer, TopAnalyzer
        ]:
            analyzer = AnalyzerClass(sample_tracks)
            assert analyzer.get_total() == len(sample_tracks), \
                f"{AnalyzerClass.__name__}.get_total() tidak konsisten"

    def test_overall_statistics_is_dataclass(self):
        """OverallStatistics harus merupakan dataclass Python."""
        from dataclasses import is_dataclass
        assert is_dataclass(OverallStatistics)

    def test_popularity_bucket_is_dataclass(self):
        """PopularityBucket harus merupakan dataclass Python."""
        from dataclasses import is_dataclass
        assert is_dataclass(PopularityBucket)

    def test_ocp_new_analyzer_subclass_works(self, sample_tracks):
        """OCP: Subclass baru dari BaseAnalyzer harus berfungsi tanpa ubah kode lama."""
        class NewAnalyzer(BaseAnalyzer):
            def analyze(self) -> dict:
                return {"custom_metric": self.get_total() * 2}
            def display(self) -> None:
                r = self.analyze()
                print(f"Custom: {r['custom_metric']}")

        analyzer = NewAnalyzer(sample_tracks)
        result   = analyzer.analyze()
        assert result["custom_metric"] == len(sample_tracks) * 2