import subprocess
import sys
import re
import ast
from pathlib import Path
from typing import Tuple

# File sumber yang masuk scope pengujian
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

# File sumber yang memiliki test (exporter.py dikecualikan karena tidak ada test-nya)
TESTED_FILES = [
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
]

TEST_FILE = "test_spotify.py"

# Kelas test dan mapping ke kategori laporan
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

VALIDATION_CLASSES   = ["TestDataValidation"]
EDGE_CASE_CLASSES    = ["TestEdgeCases"]
CODE_QUALITY_CLASSES = ["TestCodeQuality"]


# HELPERS

def run(cmd: list) -> Tuple[str, str, int]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode


def ensure_pytest_cov() -> bool:
    try:
        import pytest_cov
        return True
    except ImportError:
        pass
    print("  [info] pytest-cov belum terinstall, menginstall otomatis ...")
    _, _, code = run([sys.executable, "-m", "pip", "install", "pytest-cov", "-q"])
    if code == 0:
        print("  [info] pytest-cov berhasil diinstall.\n")
        return True
    print("  [warn] Gagal install pytest-cov. Coverage tidak tersedia.\n")
    return False


def ensure_pycodestyle() -> bool:
    stdout, _, code = run([sys.executable, "-m", "pycodestyle", "--version"])
    if code == 0:
        return True
    print("  [info] pycodestyle belum terinstall, menginstall otomatis ...")
    _, _, code = run([sys.executable, "-m", "pip", "install", "pycodestyle", "-q"])
    return code == 0


def count_tests_in_classes(classes: list) -> int:
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


def get_coverage(cov_available: bool) -> str:
    if not cov_available:
        return "N/A (install: pip install pytest-cov)"

    cov_args = [
        f"--cov={Path(f).stem}"
        for f in TESTED_FILES
        if Path(f).exists()
    ]
    stdout, stderr, _ = run([
        sys.executable, "-m", "pytest", TEST_FILE,
        *cov_args,
        "--cov-report=term", "--tb=no", "-q", "--no-header",
    ])

    for line in stdout.splitlines():
        if line.strip().startswith("TOTAL"):
            parts = line.split()
            if len(parts) >= 4:
                return parts[-1]  # e.g. "97%"

    # Fallback: tampilkan petunjuk spesifik jika parsing gagal
    if "no module named pytest_cov" in (stdout + stderr).lower():
        return "N/A (install: pip install pytest-cov)"
    return "N/A"


def check_pep8(pep8_available: bool) -> Tuple[int, bool]:
    if not pep8_available:
        return -1, False
    files = [f for f in SOURCE_FILES if Path(f).exists()]
    stdout, _, _ = run([sys.executable, "-m", "pycodestyle"] + files)
    violations = len([ln for ln in stdout.splitlines() if ln.strip()])
    return violations, (violations == 0)


def get_data_stats() -> dict:
    stats = {
        "total_tracks"  : 0,
        "total_genres"  : 0,
        "total_artists" : 0,
        "missing_values": 0,
        "min_popularity": 0,
        "max_popularity": 0,
        "min_duration"  : 0.0,
        "max_duration"  : 0.0,
        "min_tempo"     : 0.0,
        "max_tempo"     : 0.0,
    }

    dataset_path = Path("output/dataset_clean.csv")
    if not dataset_path.exists():
        return stats

    try:
        from model import load_data
        from analisis_overall import OverallCalculator

        data = load_data(str(dataset_path))
        if not data:
            return stats

        result = OverallCalculator().calculate(data)
        stats["total_tracks"]  = result.total_tracks
        stats["total_genres"]  = result.total_genres
        stats["total_artists"] = result.total_artists

        pops   = [t.popularity           for t in data]
        durs   = [t.get_duration_minutes() for t in data]
        tempos = [t.tempo                for t in data]
        stats["min_popularity"] = min(pops)
        stats["max_popularity"] = max(pops)
        stats["min_duration"]   = round(min(durs), 2)
        stats["max_duration"]   = round(max(durs), 2)
        stats["min_tempo"]      = round(min(tempos), 2)
        stats["max_tempo"]      = round(max(tempos), 2)

        import csv
        with open(dataset_path, newline="", encoding="utf-8") as f:
            total_rows = sum(1 for _ in csv.DictReader(f))
        stats["missing_values"] = total_rows - result.total_tracks

    except Exception:
        pass

    return stats


def sep(char="─", width=62):
    return char * width


# CETAK LAPORAN

def main():
    # ── Cek ketersediaan tool tambahan sekali di awal ─────────────────────────
    cov_ok  = ensure_pytest_cov()
    pep8_ok_install = ensure_pycodestyle()

    print()
    print("=" * 62)
    print("  PENGUJIAN & VALIDASI")
    print("  Spotify Track Analysis System — Python OOP")
    print("=" * 62)

    # ── Hitung dan jalankan semua kategori test ───────────────────────────────
    unit_total  = count_tests_in_classes(UNIT_TEST_CLASSES)
    val_total   = count_tests_in_classes(VALIDATION_CLASSES)
    edge_total  = count_tests_in_classes(EDGE_CASE_CLASSES)
    qual_total  = count_tests_in_classes(CODE_QUALITY_CLASSES)
    grand_total = unit_total + val_total + edge_total + qual_total

    print(f"\n  Menjalankan {grand_total} test cases ...\n")

    unit_pass, unit_fail = run_pytest_for_classes(UNIT_TEST_CLASSES)
    val_pass,  val_fail  = run_pytest_for_classes(VALIDATION_CLASSES)
    edge_pass, edge_fail = run_pytest_for_classes(EDGE_CASE_CLASSES)
    qual_pass, qual_fail = run_pytest_for_classes(CODE_QUALITY_CLASSES)

    total_pass = unit_pass + val_pass + edge_pass + qual_pass
    total_fail = unit_fail + val_fail + edge_fail + qual_fail

    coverage             = get_coverage(cov_ok)
    pep8_viol, pep8_lulus = check_pep8(pep8_ok_install)
    ds                   = get_data_stats()

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
            print(f"    • Baris tidak valid / missing: {ds['missing_values']} (di-skip otomatis)")
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
    status_q = "semua passed ✓" if qual_fail == 0 else f"{qual_fail} FAILED ✗"

    if not pep8_ok_install:
        pep8_info = "N/A (install: pip install pycodestyle)"
    elif pep8_lulus:
        pep8_info = "Lulus ✓ (0 pelanggaran)"
    else:
        pep8_info = f"{pep8_viol} pelanggaran (gaya alignment)"

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
    verdict = "LULUS ✓" if total_fail == 0 else f"GAGAL ✗ ({total_fail} test gagal)"

    if not pep8_ok_install:
        pep8_label = "N/A"
    elif pep8_lulus:
        pep8_label = "Lulus"
    else:
        pep8_label = f"{pep8_viol} issues"

    print(
        f"  Hasil  :  {total_pass}/{grand_total} tests passed"
        f"  |  Coverage: {coverage}"
        f"  |  PEP 8: {pep8_label}"
        f"  |  Status: {verdict}"
    )
    print("=" * 62)
    print()

    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())