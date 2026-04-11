import pandas as pd
import json
import os

def parse_mtsamples(csv_path):
    df = pd.read_csv(csv_path)
    
    # Rimuovi righe senza trascrizione
    df = df.dropna(subset=['transcription'])
    print(f"Documenti dopo pulizia: {len(df)}")
    
    records = []
    for _, row in df.iterrows():
        transcription = str(row['transcription']).strip()
        
        # Salta trascrizioni troppo corte
        if len(transcription) < 100:
            continue
        
        records.append({
            "specialty": str(row['medical_specialty']).strip(),
            "description": str(row['description']).strip(),
            "sample_name": str(row['sample_name']).strip(),
            "transcription": transcription[:3000],  # limite caratteri
            "keywords": str(row['keywords']).strip() if pd.notna(row['keywords']) else ""
        })
    
    return records

if __name__ == "__main__":
    csv_path = os.path.join(os.path.dirname(__file__), "mtsamples.csv")
    print("Parsing MTSamples...")
    
    records = parse_mtsamples(csv_path)
    print(f"Trovati {len(records)} documenti validi")
    
    output_path = os.path.join(os.path.dirname(__file__), "mtsamples_processed.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    
    print(f"Salvato in {output_path}")
    
    # Mostra esempio
    if records:
        print(f"\nEsempio:")
        print(f"Specialty: {records[0]['specialty']}")
        print(f"Description: {records[0]['description']}")
        print(f"Transcription: {records[0]['transcription'][:200]}...")
        
    # Mostra specializzazioni disponibili
    specialties = list(set([r['specialty'] for r in records]))
    print(f"\nSpecializzazioni ({len(specialties)}):")
    for s in sorted(specialties):
        print(f"  - {s}")