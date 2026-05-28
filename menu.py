def mainmenu():
    pilihan = ""
    while (pilihan != "0"):
        print("[1] Overall Statistics")
        print("[2] Analisis Popularitas")
        print("[3] Analisis per Genre")
        print("[4] Analisis per Artis")
        print("[5] Analisis Mood Lagu")
        print("[6] Top Tracks & Artists")
        print("[7] Export Report to jason")
        print("[0] Keluar")
        pilihan = input("Masukkan pilihan:  ")
        
        match pilihan:
            case "1":
                input()
            case "2":
                input()
            case "3":
                input()
            case "4":
                input()
            case "5":
                input()
            case "6":
                input()
            case "7":
                input()
            case "0":
                continue
            case _:
                input("Pilihan tidak valid!")
        print()
