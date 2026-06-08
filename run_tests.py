import subprocess
import sys
import re
import ast
import tokenize
import io
from pathlib import Path
from typing import Tuple

SOURCE_FILES = [
    "model.py",
    "analisis.py",
    "analisis_formatter.py",
    "analisis_kalkulator.py",
    "analisis_overall.py",
    "analisis_popularitas.py",
    "analisis_genre.py",
    "analisis_artis.py",
    "analisis_mood.py",
    "analisis_top.py",
    "exporter.py",
]

TEST_FILE = "test_spotify.py"

# ── Kelas test dan mapping ke kategori laporan ────────────────────────────────
UNIT_TEST_CLASSES = [
    "TestSpotifyTrackModel",
    "TestOverallCalculator",
    "TestOverallAnalyzer",
    "TestPopularityCalculator",
    "TestPopularityAnalyzer",
    "TestGenreAnalyzer",
    "TestArtistAnalyzer",
    "TestMoodAnalyzer",
    "TestTopAnalyzer",
]

VALIDATION_CLASSES  = ["TestDataValidation"]
EDGE_CASE_CLASSES   = ["TestEdgeCases"]
CODE_QUALITY_CLASSES = ["TestCodeQuality"]


# =============================================================================
# HELPERS
# =============================================================================

def run(cmd: list) -> Tuple[str, str, int]:
    """Jalankan perintah shell, kembalikan (stdout, stderr, returncode)."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode


def count_tests_in_classes(classes: list) -> int:
    """Hitung jumlah test method dalam kelas-kelas yang ditentukan."""
    total = 0
    try:
        src = Path(TEST_FILE).read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name in classes:
                total += sum(
                    1 for n in node.body
                    if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")
                )
    except Exception:
        pass
    return total


def run_pytest_for_classes(classes: list) -> Tuple[int, int]:
    """Jalankan pytest hanya untuk kelas tertentu, return (passed, failed)."""
    patterns = " or ".join(classes)
    stdout, _, _ = run([
        sys.executable, "-m", "pytest", TEST_FILE,
        "-k", patterns, "--tb=no", "-q", "--no-header"
    ])
    passed = failed = 0
    for line in stdout.splitlines():
        m = re.search(r"(\d+) passed", line)
        if m:
            passed = int(m.group(1))
        m = re.search(r"(\d+) failed", line)
        if m:
            failed = int(m.group(1))
    return passed, failed


def get_coverage() -> str:
    """Jalankan pytest dengan coverage hanya pada file sumber, kembalikan persentase."""
    cov_args = [f"--cov={Path(f).stem}" for f in SOURCE_FILES if Path(f).exists()]
    stdout, _, _ = run([
        sys.executable, "-m", "pytest", TEST_FILE,
        *cov_args,
        "--cov-report=term", "--tb=no", "-q", "--no-header",
    ])
    for line in stdout.splitlines():
        if line.strip().startswith("TOTAL"):
            parts = line.split()
            if len(parts) >= 4:
                return parts[-1]   # e.g. "96%"
    return "N/A"


def check_pep8() -> Tuple[int, bool]:
    """Cek PEP 8 dengan pycodestyle. Return (jumlah_pelanggaran, lulus)."""
    files = [f for f in SOURCE_FILES if Path(f).exists()]
    stdout, _, code = run([sys.executable, "-m", "pycodestyle"] + files)
    violations = len([l for l in stdout.splitlines() if l.strip()])
    return violations, (violations == 0)


def get_data_stats() -> dict:
    """Ambil statistik dataset dari OverallCalculator secara langsung."""
    stats = {
        "total_tracks"   : 0,
        "total_genres"   : 0,
        "total_artists"  : 0,
        "missing_values" : 0,
        "explicit_count" : 0,
        "popular_count"  : 0,
        "mood_dist"      : {},
        "min_popularity" : 0,
        "max_popularity" : 0,
        "min_duration"   : 0.0,
        "max_duration"   : 0.0,
        "min_tempo"      : 0.0,
        "max_tempo"      : 0.0,
    }

    dataset_path = Path("output/dataset_clean.csv")
    if not dataset_path.exists():
        return stats

    try:
        from model import load_data, SpotifyTrack
        from analisis_overall import OverallCalculator

        data = load_data(str(dataset_path))
        if not data:
            return stats

        result = OverallCalculator().calculate(data)
        stats["total_tracks"]  = result.total_tracks
        stats["total_genres"]  = result.total_genres
        stats["total_artists"] = result.total_artists
        stats["explicit_count"]= result.explicit_count
        stats["popular_count"] = result.popular_count
        stats["mood_dist"]     = result.mood_dist

        pops     = [t.popularity          for t in data]
        durs     = [t.get_duration_minutes() for t in data]
        tempos   = [t.tempo               for t in data]
        stats["min_popularity"] = min(pops)
        stats["max_popularity"] = max(pops)
        stats["min_duration"]   = round(min(durs), 2)
        stats["max_duration"]   = round(max(durs), 2)
        stats["min_tempo"]      = round(min(tempos), 2)
        stats["max_tempo"]      = round(max(tempos), 2)

        # Hitung baris yang gagal di-load (missing/corrupt)
        import csv
        total_rows = 0
        with open(dataset_path, newline="", encoding="utf-8") as f:
            total_rows = sum(1 for _ in csv.DictReader(f))
        stats["missing_values"] = total_rows - result.total_tracks

    except Exception:
        pass

    return stats

def sep(char="─", width=62):
    return char * width

def main():
    print()
    print("=" * 62)
    print("  PENGUJIAN & VALIDASI")
    print("  Spotify Track Analysis System — Python OOP")
    print("=" * 62)

    unit_total   = count_tests_in_classes(UNIT_TEST_CLASSES)
    val_total    = count_tests_in_classes(VALIDATION_CLASSES)
    edge_total   = count_tests_in_classes(EDGE_CASE_CLASSES)
    qual_total   = count_tests_in_classes(CODE_QUALITY_CLASSES)
    grand_total  = unit_total + val_total + edge_total + qual_total

    print(f"\n  Menjalankan {grand_total} test cases ...\n")

    unit_pass,  unit_fail  = run_pytest_for_classes(UNIT_TEST_CLASSES)
    val_pass,   val_fail   = run_pytest_for_classes(VALIDATION_CLASSES)
    edge_pass,  edge_fail  = run_pytest_for_classes(EDGE_CASE_CLASSES)
    qual_pass,  qual_fail  = run_pytest_for_classes(CODE_QUALITY_CLASSES)

    total_pass = unit_pass + val_pass + edge_pass + qual_pass
    total_fail = unit_fail + val_fail + edge_fail + qual_fail

    coverage   = get_coverage()
    pep8_viol, pep8_ok = check_pep8()
    ds         = get_data_stats()

    # 1. UNIT TESTING
    status_u = "semua passed ✓" if unit_fail == 0 else f"{unit_fail} FAILED ✗"
    print(sep())
    print(f"  Unit Testing (pytest)")
    print(f"  {unit_total} test cases — {status_u}")
    print()
    print(f"  Cakupan pengujian:")
    print(f"    • SpotifyTrack model   : is_popular(), get_mood(), get_duration_minutes()")
    print(f"    • OverallAnalyzer      : kalkulasi avg, mood dist, artis unik")
    print(f"    • PopularityAnalyzer   : segmentasi bucket, korelasi Pearson, top/bottom")
    print(f"    • GenreAnalyzer        : top 5 genre, urutan descending")
    print(f"    • ArtistAnalyzer       : artis produktif & terpopuler")
    print(f"    • MoodAnalyzer         : distribusi mood, avg valence & energy")
    print(f"    • TopAnalyzer          : top 10 tracks & artists")

    # 2. DATA VALIDATION
    status_v = "semua passed ✓" if val_fail == 0 else f"{val_fail} FAILED ✗"
    print()
    print(sep())
    print(f"  Data Validation")
    print(f"  {val_total} test cases — {status_v}")
    print()
    if ds["total_tracks"] > 0:
        print(f"  Statistik dataset (output/dataset_clean.csv):")
        print(f"    • Total lagu berhasil dimuat : {ds['total_tracks']:,}")
        if ds["missing_values"] > 0:
            print(f"    • Baris tidak valid / missing: {ds['missing_values']} baris (di-skip otomatis)")
        else:
            print(f"    • Baris tidak valid / missing: 0 (dataset bersih)")
        print(f"    • Total genre unik           : {ds['total_genres']}")
        print(f"    • Total artis unik           : {ds['total_artists']:,}")
        print(f"    • Rentang popularity         : {ds['min_popularity']} – {ds['max_popularity']}")
        print(f"    • Rentang durasi             : {ds['min_duration']} – {ds['max_duration']} menit")
        print(f"    • Rentang tempo              : {ds['min_tempo']} – {ds['max_tempo']} BPM")
    else:
        print(f"  Dataset tidak ditemukan — validasi dijalankan dengan data sampel.")
    print()
    print(f"  Validasi yang dilakukan:")
    print(f"    • Rentang nilai  : popularity ∈ [0,100], danceability/energy/valence ∈ [0,1]")
    print(f"    • Tipe data      : explicit → bool, popularity → int, duration_ms → int")
    print(f"    • Kelengkapan    : track_id, track_name, artists tidak boleh kosong")
    print(f"    • Konsistensi    : sum(mood_dist) == total_tracks, explicit_pct ∈ [0,100]")

    # 3. EDGE CASE TESTING
    status_e = "semua passed ✓" if edge_fail == 0 else f"{edge_fail} FAILED ✗"
    print()
    print(sep())
    print(f"  Edge Case Testing")
    print(f"  {edge_total} test cases — {status_e}")
    print()
    print(f"  Skenario yang diuji:")
    print(f"    • Dataset kosong    : semua analyzer tidak crash, return nilai default")
    print(f"    • Dataset 1 lagu    : kalkulasi avg = nilai lagu itu sendiri")
    print(f"    • Popularity = 0    : is_popular() → False  (batas minimum)")
    print(f"    • Popularity = 100  : is_popular() → True   (batas maksimum)")
    print(f"    • Mood tepat batas  : valence=0.6 & energy=0.6 → Happy")
    print(f"    • Nama lagu 200 chr : disimpan penuh tanpa terpotong")
    print(f"    • Artis kolaborasi  : 'A;B;C' terhitung sebagai 3 artis terpisah")
    print(f"    • TopAnalyzer < 10  : tidak crash saat data lebih sedikit dari batas")
    print(f"    • Bucket 1 lagu     : avg_score = popularity lagu tersebut")

    # 4. CODE QUALITY
    status_q  = "semua passed ✓" if qual_fail == 0 else f"{qual_fail} FAILED ✗"
    pep8_info = f"Lulus ✓ (0 pelanggaran)" if pep8_ok else f"{pep8_viol} pelanggaran (gaya alignment)"
    print()
    print(sep())
    print(f"  Code Quality")
    print(f"  {qual_total} test cases — {status_q}")
    print()
    print(f"  Hasil pemeriksaan:")
    print(f"    • Coverage (pytest-cov) : {coverage}")
    print(f"    • PEP 8 (pycodestyle)   : {pep8_info}")
    print()
    print(f"  Kontrak OOP yang diverifikasi:")
    print(f"    • Abstraksi  : BaseAnalyzer tidak bisa di-instantiate langsung")
    print(f"    • LSP        : semua subclass bisa menggantikan BaseAnalyzer")
    print(f"    • Enkapsulasi: _data protected, tidak ada atribut 'data' publik")
    print(f"    • DIP        : calculator & formatter dapat di-inject dari luar")
    print(f"    • SRP        : Calculator tidak punya display(), Formatter tidak punya calculate()")
    print(f"    • OCP        : subclass baru dari BaseAnalyzer langsung berfungsi")

    # RINGKASAN AKHIR
    print()
    print("=" * 62)
    all_pass = (total_fail == 0)
    verdict  = "LULUS ✓" if all_pass else f"GAGAL ✗ ({total_fail} test gagal)"

    print(f"  Hasil  :  {total_pass}/{grand_total} tests passed  |  Coverage: {coverage}  "
          f"|  PEP 8: {'Lulus' if pep8_ok else f'{pep8_viol} issues'}  |  Status: {verdict}")
    print("=" * 62)
    print()

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())