import os
import json
import xml.etree.ElementTree as ET
import pandas as pd

BASE_PATH = os.path.dirname(__file__)

def parse_medquad():
    print("\n=== Parsing MedQuAD ===")
    medquad_path = os.path.join(BASE_PATH, "MedQuAD")
    qa_pairs = []

    for folder in os.listdir(medquad_path):
        folder_path = os.path.join(medquad_path, folder)
        if not os.path.isdir(folder_path):
            continue
        for filename in os.listdir(folder_path):
            if not filename.endswith(".xml"):
                continue
            filepath = os.path.join(folder_path, filename)
            try:
                tree = ET.parse(filepath)
                root = tree.getroot()
                focus = root.findtext("Focus", default="")
                for qa in root.findall(".//QAPair"):
                    question = qa.findtext("Question", default="").strip()
                    answer = qa.findtext("Answer", default="").strip()
                    if question and answer and len(answer) > 50:
                        qa_pairs.append({
                            "focus": focus,
                            "question": question,
                            "answer": answer[:2000],
                            "source": folder
                        })
            except Exception as e:
                print(f"Errore nel file {filepath}: {e}")

    output_path = os.path.join(BASE_PATH, "medquad_processed.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(qa_pairs, f, ensure_ascii=False, indent=2)

    print(f"Trovate {len(qa_pairs)} coppie Q&A")
    print(f"Salvato in {output_path}")
    return qa_pairs

def parse_mtsamples():
    print("\n=== Parsing MTSamples ===")
    csv_path = os.path.join(BASE_PATH, "mtsamples.csv")
    df = pd.read_csv(csv_path)
    df = df.dropna(subset=['transcription'])

    records = []
    for _, row in df.iterrows():
        transcription = str(row['transcription']).strip()
        if len(transcription) < 100:
            continue
        records.append({
            "specialty": str(row['medical_specialty']).strip(),
            "description": str(row['description']).strip(),
            "sample_name": str(row['sample_name']).strip(),
            "transcription": transcription[:3000],
            "keywords": str(row['keywords']).strip() if pd.notna(row['keywords']) else ""
        })

    output_path = os.path.join(BASE_PATH, "mtsamples_processed.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"Trovati {len(records)} documenti validi")
    print(f"Salvato in {output_path}")
    return records

if __name__ == "__main__":
    print("Preprocessing dataset medici...")
    medquad = parse_medquad()
    mtsamples = parse_mtsamples()
    print(f"   Completato!")
    print(f"   MedQuAD: {len(medquad)} Q&A")
    print(f"   MTSamples: {len(mtsamples)} trascrizioni")