import json
from analisis import BaseAnalyzer

class DataExporter(BaseAnalyzer):
    def analyze(self) -> dict:
        return {"total_exported": self.get_total()}

    def display(self) -> None:
        filename = "report.json"
        report_data = [
            {
                "track_name": t.track_name, 
                "artists": t.artists, 
                "popularity": t.popularity
            } for t in self._data
        ]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=4)
        print(f"\n[*] Data berhasil diekspor ke '{filename}'")