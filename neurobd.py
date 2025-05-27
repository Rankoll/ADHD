import streamlit as st
import pandas as pd
from pymongo import MongoClient

# Connection to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["neurobd"]

# Read CSV
df = pd.read_csv("dataset/adhd_data.csv")

# Collections
subjects_col = db["subjects"]
assessments_col = db["assessments"]
indicators_col = db["indicators"]

# Function to classify scores
def classify_score(score):
    if score < 13:
        return "Symptoms not clinically significant"
    elif 13 <= score <= 17:
        return "Mild symptoms"
    elif 18 <= score <= 22:
        return "Moderate symptoms"
    else:
        return "Severe symptoms"

# Data insertion only if database is empty (first run)
if subjects_col.count_documents({}) == 0 and assessments_col.count_documents({}) == 0 and indicators_col.count_documents({}) == 0:
    for idx, row in df.iterrows():
        subject_id = idx + 1  # progressive counter

        # Check if subject already exists
        if not subjects_col.find_one({"subject_id": subject_id}):
            subject_doc = {
                "subject_id": subject_id,
                "age": row["Age"],
                "gender": row["Gender"],
                "educational_level": row["Educational_Level"],
                "family_history": row["Family_History"]
            }
            subjects_col.insert_one(subject_doc)

        # Check if assessment already exists
        if not assessments_col.find_one({"subject_id": subject_id, "name": "SNAP-IV"}):
            inattention_keys = [f"Q1_{i}" for i in range(1, 10)]
            hyperactivity_keys = [f"Q2_{i}" for i in range(1, 10)]

            inattention_score = sum(row[key] for key in inattention_keys)
            hyperactivity_score = sum(row[key] for key in hyperactivity_keys)

            assessment_doc = {
                "subject_id": subject_id,
                "name": "SNAP-IV",
                **{k: row[k] for k in inattention_keys + hyperactivity_keys},
                "Focus_Score_Video": row["Focus_Score_Video"],
                "Difficulty_Organizing_Tasks": row["Difficulty_Organizing_Tasks"],
                "Learning_Difficulties": row["Learning_Difficulties"],
                "Anxiety_Depression_Levels": row["Anxiety_Depression_Levels"],
                "inattention_score": inattention_score,
                "hyperactivity_score": hyperactivity_score,
                "inattention_severity": classify_score(inattention_score),
                "hyperactivity_severity": classify_score(hyperactivity_score)
            }
            assessments_col.insert_one(assessment_doc)

        # Check if indicators already exist
        if not indicators_col.find_one({"subject_id": subject_id}):
            indicators_doc = {
                "subject_id": subject_id,
                "Sleep_Hours": row["Sleep_Hours"],
                "Daily_Activity_Hours": row["Daily_Activity_Hours"],
                "Daily_Phone_Usage_Hours": row["Daily_Phone_Usage_Hours"],
                "Daily_Coffee_Tea_Consumption": row["Daily_Coffee_Tea_Consumption"]
            }
            indicators_col.insert_one(indicators_doc)

    print("Importazione completata.")
else:
    print("Database già popolato. Importazione saltata.")

st.title("Gestione NeuroDB - Disturbi del Neurosviluppo")

menu = st.sidebar.selectbox("Seleziona operazione", ["Crea", "Visualizza", "Aggiorna", "Elimina", "JOIN"])

collezione = st.sidebar.selectbox(
    "Collezione",
    ["subjects", "assessments", "indicators"]
)

if menu == "Crea":
    if collezione == "subjects":
        id = st.text_input("ID Soggetto")
        nome = st.text_input("Nome")
        età = st.number_input("Età", min_value=0)
        diagnosi = st.text_input("Diagnosi (separate da virgola)")
        if st.button("Inserisci Subject"):
            if subjects_col.find_one({"subject_id": id}):
                st.error("ID soggetto già presente!")
            else:
                subjects_col.insert_one({
                    "subject_id": id,
                    "name": nome,
                    "age": età,
                    "diagnosis": [d.strip() for d in diagnosi.split(",")]
                })
                st.success("Soggetto inserito!")
            
    elif collezione == "indicators":
        subject_id = st.text_input("ID Soggetto per Indicators")
        sleep_hours = st.number_input("Ore di Sonno", min_value=0.0)
        activity_hours = st.number_input("Ore Attività Giornaliera", min_value=0.0)
        phone_hours = st.number_input("Ore Uso Telefono", min_value=0.0)
        coffee_tea = st.text_input("Consumo Giornaliero Caffè/Tè")
        if st.button("Inserisci Indicators"):
            if not subjects_col.find_one({"subject_id": subject_id}):
                st.error("ID soggetto non esistente! Inserire prima il soggetto.")
            elif indicators_col.find_one({"subject_id": subject_id}):
                st.error("Indicators già presenti per questo soggetto!")
            else:
                indicators_col.insert_one({
                    "subject_id": subject_id,
                    "Sleep_Hours": sleep_hours,
                    "Daily_Activity_Hours": activity_hours,
                    "Daily_Phone_Usage_Hours": phone_hours,
                    "Daily_Coffee_Tea_Consumption": coffee_tea
                })
                st.success("Indicators inseriti!")
            
    elif collezione == "assessments":
        subject_id = st.text_input("ID Soggetto per Assessment")
        nome_assessment = st.text_input("Nome Assessment")
        inattention_score = st.number_input("Punteggio Inattenzione", min_value=0)
        hyperactivity_score = st.number_input("Punteggio Iperattività", min_value=0)
        if st.button("Inserisci Assessment"):
            if not subjects_col.find_one({"subject_id": subject_id}):
                st.error("ID soggetto non esistente! Inserire prima il soggetto.")
            elif assessments_col.find_one({"subject_id": subject_id, "name": nome_assessment}):
                st.error("Assessment già presente per questo soggetto con questo nome!")
            else:
                assessments_col.insert_one({
                    "subject_id": subject_id,
                    "name": nome_assessment,
                    "inattention_score": inattention_score,
                    "hyperactivity_score": hyperactivity_score,
                    "inattention_severity": classify_score(inattention_score),
                    "hyperactivity_severity": classify_score(hyperactivity_score)
                })
                st.success("Assessment inserito!")

elif menu == "Visualizza":
    id = st.number_input("Filtra per ID soggetto (opzionale)", min_value=0, step=1, format="%d")
    if collezione == "subjects":
        if id:
            subject = subjects_col.find_one({"subject_id": id})
            subjects = [subject] if subject else []
        else:
            subjects = list(subjects_col.find())
        if subjects:
            st.write("Lista Soggetti:")
            for subject in subjects:
                st.json(subject)
        else:
            st.info("Nessun soggetto trovato.")

    elif collezione == "assessments":
        if id:
            assessment = assessments_col.find_one({"subject_id": id})
            assessments = [assessment] if assessment else []
        else:
            assessments = list(assessments_col.find())
        if assessments:
            st.write("Lista Assessments:")
            for assessment in assessments:
                st.json(assessment)
        else:
            st.info("Nessun assessment trovato.")

    elif collezione == "indicators":
        if id:
            indicator = indicators_col.find_one({"subject_id": id})
            indicators = [indicator] if indicator else []
        else:
            indicators = list(indicators_col.find())
        if indicators:
            st.write("Lista Indicators:")
            for indicator in indicators:
                st.json(indicator)
        else:
            st.info("Nessun indicator trovato.")

elif menu == "Aggiorna":
    if collezione == "subjects":
        id = st.number_input("Filtra per ID soggetto (opzionale)", min_value=0, step=1, format="%d")
        subject = subjects_col.find_one({"subject_id": id})
        if subject:
            nuovo_nome = st.text_input("Nome", value=subject.get("name", ""))
            nuova_età = st.number_input("Età", min_value=0, value=subject.get("age", 0))
            nuovo_livello = st.text_input("Educational Level", value=subject.get("educational_level", ""))
            nuova_storia = st.text_input("Family History", value=subject.get("family_history", ""))
            nuovo_genere = st.text_input("Gender", value=subject.get("gender", ""))
            if st.button("Aggiorna Subject"):
                subjects_col.update_one(
                    {"subject_id": id},
                    {"$set": {
                        "name": nuovo_nome,
                        "age": nuova_età,
                        "educational_level": nuovo_livello,
                        "family_history": nuova_storia,
                        "gender": nuovo_genere
                    }}
                )
                st.success("Subject aggiornato!")
        else:
            st.info("Soggetto non trovato.")

    elif collezione == "assessments":
        id = st.number_input("Filtra per ID soggetto (opzionale)", min_value=0, step=1, format="%d")
        nome_assessment = st.text_input("Nome Assessment")
        assessment = assessments_col.find_one({"subject_id": id, "name": nome_assessment})
        if assessment:
            inatt = st.number_input("Punteggio Inattenzione", min_value=0, value=assessment.get("inattention_score", 0))
            iper = st.number_input("Punteggio Iperattività", min_value=0, value=assessment.get("hyperactivity_score", 0))
            focus = st.number_input("Focus Score Video", min_value=0, value=assessment.get("Focus_Score_Video", 0))
            diff_org = st.text_input("Difficulty Organizing Tasks", value=str(assessment.get("Difficulty_Organizing_Tasks", "")))
            learn_diff = st.text_input("Learning Difficulties", value=str(assessment.get("Learning_Difficulties", "")))
            anx_dep = st.text_input("Anxiety Depression Levels", value=str(assessment.get("Anxiety_Depression_Levels", "")))
            if st.button("Aggiorna Assessment"):
                assessments_col.update_one(
                    {"subject_id": id, "name": nome_assessment},
                    {"$set": {
                        "inattention_score": inatt,
                        "hyperactivity_score": iper,
                        "inattention_severity": classify_score(inatt),
                        "hyperactivity_severity": classify_score(iper),
                        "Focus_Score_Video": focus,
                        "Difficulty_Organizing_Tasks": diff_org,
                        "Learning_Difficulties": learn_diff,
                        "Anxiety_Depression_Levels": anx_dep
                    }}
                )
                st.success("Assessment aggiornato!")
        else:
            st.info("Assessment non trovato.")

    elif collezione == "indicators":
        id = st.number_input("Filtra per ID soggetto (opzionale)", min_value=0, step=1, format="%d")
        indicators = indicators_col.find_one({"subject_id": id})
        if indicators:
            sleep = st.number_input("Ore di Sonno", min_value=0, value=indicators.get("Sleep_Hours", 0))
            activity = st.number_input("Ore Attività Giornaliera", min_value=0, value=indicators.get("Daily_Activity_Hours", 0))
            phone = st.number_input("Ore Uso Telefono", min_value=0, value=indicators.get("Daily_Phone_Usage_Hours", 0))
            coffee = st.text_input("Consumo Giornaliero Caffè/Tè", value=indicators.get("Daily_Coffee_Tea_Consumption", ""))
            if st.button("Aggiorna Indicators"):
                indicators_col.update_one(
                    {"subject_id": id},
                    {"$set": {
                        "Sleep_Hours": sleep,
                        "Daily_Activity_Hours": activity,
                        "Daily_Phone_Usage_Hours": phone,
                        "Daily_Coffee_Tea_Consumption": coffee
                    }}
                )
                st.success("Indicators aggiornati!")
        else:
            st.info("Indicators non trovati.")

elif menu == "Elimina":
    if collezione == "subjects":
        id = st.number_input("Filtra per ID soggetto (opzionale)", min_value=0, step=1, format="%d")
        if st.button("Elimina Subject e dati correlati"):
            subjects_col.delete_one({"subject_id": id})
            assessments_col.delete_many({"subject_id": id})
            indicators_col.delete_many({"subject_id": id})
            st.warning("Soggetto e dati correlati eliminati.")
    elif collezione == "assessments":
        id = st.number_input("Filtra per ID soggetto (opzionale)", min_value=0, step=1, format="%d")
        nome_assessment = st.text_input("Nome Assessment da eliminare")
        if st.button("Elimina Assessment"):
            result = assessments_col.delete_one({"subject_id": id, "name": nome_assessment})
            if result.deleted_count > 0:
                st.warning("Assessment eliminato.")
            else:
                st.info("Nessun assessment trovato con questi dati.")
    elif collezione == "indicators":
        id = st.number_input("Filtra per ID soggetto (opzionale)", min_value=0, step=1, format="%d")
        if st.button("Elimina Indicators"):
            result = indicators_col.delete_many({"subject_id": id})
            if result.deleted_count > 0:
                st.warning("Indicators eliminati.")
            else:
                st.info("Nessun indicators trovato per questo soggetto.")

elif menu == "JOIN":
    id = st.number_input("Filtra per ID soggetto (opzionale)", min_value=0, step=1, format="%d")
    match_stage = []
    if id:
        match_stage = [{"$match": {"subject_id": id}}]
    result = db.assessments.aggregate(
        match_stage +
        [
            {"$lookup": {
                "from": "subjects",
                "localField": "subject_id",
                "foreignField": "subject_id",
                "as": "subject_info"
            }},
            {"$lookup": {
                "from": "indicators",
                "localField": "subject_id",
                "foreignField": "subject_id",
                "as": "indicators_info"
            }}
        ]
    )
    found = False
    for doc in result:
        st.json(doc)
        found = True
    if not found:
        st.info("Nessun risultato trovato per la join.")