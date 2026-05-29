from model import load_data
from analisis_genre import GenreAnalyzer
from analisis_top import TopAnalyzer
from exporter import DataExporter
from analisis_artis import ArtistAnalyzer
from analisis_overall import OverallAnalyzer
from analisis_popularitas import PopularityAnalyzer
from analisis_mood import MoodAnalyzer

data = load_data("output/dataset_clean.csv")

def mainmenu():
    pilihan = ""
    while pilihan != "0":
        print("SPOTIFY TRACK ANALYSIS SYSTEM")
        print("[1] Overall Statistics")
        print("[2] Analisis Popularitas")
        print("[3] Analisis per Genre")
        print("[4] Analisis per Artis")
        print("[5] Analisis Mood Lagu")
        print("[6] Top Tracks & Artists")
        print("[7] Export Report to JSON")
        print("[0] Keluar")
        pilihan = input("Masukkan pilihan: ")

        match pilihan:
            case "1":
                OverallAnalyzer(data).display()
            case "2":
                PopularityAnalyzer(data).display()
            case "3":
                GenreAnalyzer(data).display()
            case "4":
                ArtistAnalyzer(data).display()
            case "5":
                MoodAnalyzer(data).display()
            case "6":
                TopAnalyzer(data).display()
            case "7":
                DataExporter(data).display()
            case "0":
                continue
            case _:
                print("Pilihan tidak valid!")
        input()