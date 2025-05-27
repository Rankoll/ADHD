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

# Data insertion
for idx, row in df.iterrows():
    subject_id = idx + 1  # progressive counter

    # Insert into subjects
    subject_doc = {
        "subject_id": subject_id,
        "age": row["Age"],
        "gender": row["Gender"],
        "educational_level": row["Educational_Level"],
        "family_history": row["Family_History"]
    }
    subjects_col.insert_one(subject_doc)

    # Score calculation
    inattention_keys = [f"Q1_{i}" for i in range(1, 10)]
    hyperactivity_keys = [f"Q2_{i}" for i in range(1, 10)]

    inattention_score = sum(row[key] for key in inattention_keys)
    hyperactivity_score = sum(row[key] for key in hyperactivity_keys)

    # Insert into assessments
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

    # Insert into indicators
    indicators_doc = {
        "subject_id": subject_id,
        "Sleep_Hours": row["Sleep_Hours"],
        "Daily_Activity_Hours": row["Daily_Activity_Hours"],
        "Daily_Phone_Usage_Hours": row["Daily_Phone_Usage_Hours"],
        "Daily_Coffee_Tea_Consumption": row["Daily_Coffee_Tea_Consumption"]
    }
    indicators_col.insert_one(indicators_doc)

print("Importazione completata.")