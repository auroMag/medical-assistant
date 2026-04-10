import os
import xml.etree.ElementTree as ET
import json

def parse_medquad(base_path):
    qa_pairs = []
    
    # Scorri tutte le cartelle
    for folder in os.listdir(base_path):
        folder_path = os.path.join(base_path, folder)
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
                            "answer": answer[:2000],  # limite caratteri
                            "source": folder
                        })
            except Exception as e:
                print(f"Errore nel file {filepath}: {e}")
    
    return qa_pairs

if __name__ == "__main__":
    base_path = os.path.join(os.path.dirname(__file__), "MedQuAD")
    print("Parsing MedQuAD...")
    
    qa_pairs = parse_medquad(base_path)
    print(f"Trovate {len(qa_pairs)} coppie Q&A")
    
    # Salva come JSON
    output_path = os.path.join(os.path.dirname(__file__), "medquad_processed.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(qa_pairs, f, ensure_ascii=False, indent=2)
    
    print(f"Salvato in {output_path}")
    
    # Mostra un esempio
    if qa_pairs:
        print("\nEsempio:")
        print(f"Focus: {qa_pairs[0]['focus']}")
        print(f"Question: {qa_pairs[0]['question']}")
        print(f"Answer: {qa_pairs[0]['answer'][:200]}...")