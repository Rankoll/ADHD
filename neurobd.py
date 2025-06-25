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
    
def diagnosis_classify(category):
    if category == 0:
        return "No ADHD"
    elif category == 1:
        return "Inattentive type"
    elif category == 2:
        return "Hyperactive-Impulsive type"
    else:
        return "Hyperactive and Inattentive type"
    
def diagnosis_scorebased(inattention_score, hyperactivity_score):
    if inattention_score < 18 and hyperactivity_score < 18:
        return "No ADHD"
    elif inattention_score >= 18 and hyperactivity_score < 18:
        return "Inattentive type"
    elif inattention_score < 18 and hyperactivity_score >= 18:
        return "Hyperactive-Impulsive type"
    else:
        return "Hyperactive and Inattentive type"

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
                "hyperactivity_severity": classify_score(hyperactivity_score),
                "Diagnosis_Class": diagnosis_classify(row["Diagnosis_Class"])
            }
            assessments_col.insert_one(assessment_doc)

        # Check if indicators already exist
        if not indicators_col.find_one({"subject_id": subject_id}):
            indicators_doc = {
                "subject_id": subject_id,
                "Sleep_Hours": row["Sleep_Hours"],
                "Daily_Activity_Hours": row["Daily_Activity_Hours"],
                "Daily_Phone_Usage_Hours": row["Daily_Phone_Usage_Hours"],
                "Daily_Coffee_Tea_Consumption": row["Daily_Coffee_Tea_Consumption"],
                "Daily_Walking_Running_Hours": float(f"{row['Daily_Walking_Running_Hours']:.1f}")
            }
            indicators_col.insert_one(indicators_doc)

    print("Import completed.")
else:
    print("Database already populated. Import skipped.")

# Streamlit app
st.set_page_config(
    page_title="NeuroDB",
    page_icon="https://raw.githubusercontent.com/Rankoll/ADHD/refs/heads/main/logo-neurobd.png",
    layout="wide"
)

# Simply recoloring the Streamlit checkboxes
st.markdown(
    """
    <style>
    .st-do {border-left-color: rgb(75, 139, 190) !important;}
    .st-dp {border-right-color: rgb(75, 139, 190) !important;}
    .st-dr {border-bottom-color: rgb(75, 139, 190) !important;}
    .st-dq {border-top-color: rgb(75, 139, 190) !important;}
    .st-f8 {background-color: rgb(75, 139, 190) !important;}
    </style>
    """,
    unsafe_allow_html=True
)

with st.sidebar:
    st.markdown(
        "<div style='display: flex; justify-content: center; padding-bottom: 2rem'><img src='https://raw.githubusercontent.com/Rankoll/ADHD/refs/heads/main/logo-neurobd.png' width='150'></div>",
        unsafe_allow_html=True
    )
    menu = st.selectbox("Select operation", ["Create", "Read", "Update", "Delete", "JOIN"])
    collection = st.selectbox(
        "Collection",
        ["subjects", "assessments", "indicators"]
    )

st.markdown("<h1 style='text-align: center; color: #4B8BBE;'>Neurodevelopmental Disorders NeuroDB</h1>", unsafe_allow_html=True)

st.markdown("---")

if menu == "Create":
    st.subheader(f"Insert new element in **{collection.capitalize()}**")
    if collection == "subjects":
        # Progressive subject_id
        last_subject = subjects_col.find_one(sort=[("subject_id", -1)])
        next_id = (last_subject["subject_id"] + 1) if last_subject else 1

        st.info(f"The subject ID will be assigned automatically: {next_id}")
        age = st.number_input("Age", min_value=3, max_value=100)
        gender = st.selectbox("Gender", [1, 2], help="1 for male, 2 for female")
        educational_level = st.selectbox("Educational Level", ["Kindergarten", "Middle", "Primary", "Secondary", "University", "Working", "Not Working"])
        family_history = st.selectbox("Family History", ["No", "Yes", "Unknown"])
        if st.button("Insert Subject", use_container_width=True):
            if subjects_col.find_one({"subject_id": next_id}):
                st.error("Subject ID already exists!")
            else:
                subject_doc = {
                    "subject_id": next_id,
                    "age": age,
                    "gender": gender,
                    "educational_level": educational_level,
                    "family_history": family_history
                }
                subjects_col.insert_one(subject_doc)
                st.success("Subject inserted!")

    elif collection == "indicators":
        last_indicator = indicators_col.find_one(sort=[("subject_id", -1)])
        next_id = (last_indicator["subject_id"] + 1) if last_indicator else 1

        st.info(f"The subject ID for these indicators will be assigned automatically: {next_id}")
        sleep_hours = st.number_input("Sleep Hours", min_value=0, max_value=24)
        activity_hours = st.number_input("Daily Activity Hours", min_value=0, max_value=24)
        phone_hours = st.number_input("Daily Phone Usage Hours", min_value=0, max_value=24)
        coffee_tea = st.number_input("Daily Coffee/Tea Consumption", min_value=0)
        walking_running_hours = st.number_input(
            "Daily Walking/Running Hours", min_value=0.0, max_value=24.0, format="%.1f", step=0.1
        )
        if st.button("Insert Indicators", use_container_width=True):
            if not subjects_col.find_one({"subject_id": next_id}):
                st.error("Subject ID does not exist! Please insert the subject first.")
            elif indicators_col.find_one({"subject_id": next_id}):
                st.error("Indicators already exist for this subject!")
            else:
                indicators_doc = {
                    "subject_id": next_id,
                    "Sleep_Hours": sleep_hours,
                    "Daily_Activity_Hours": activity_hours,
                    "Daily_Phone_Usage_Hours": phone_hours,
                    "Daily_Coffee_Tea_Consumption": coffee_tea,
                    "Daily_Walking_Running_Hours": float(f"{walking_running_hours:.1f}")
                }
                indicators_col.insert_one(indicators_doc)
                st.success("Indicators inserted!")
            
    elif collection == "assessments":
        last_assessment = assessments_col.find_one(sort=[("subject_id", -1)])
        next_id = (last_assessment["subject_id"] + 1) if last_assessment else 1

        st.info(f"The subject ID for this assessment will be assigned automatically: {next_id}")
        name_assessment = st.selectbox("Assessment Name", ["SNAP-IV"])

        # Display Inattention and Hyperactivity as tables
        st.markdown("### Inattention Scores")
        inattention_keys = [f"Q1_{i}" for i in range(1, 10)]
        inattention_values = []
        cols_inatt = st.columns(9)
        for idx, k in enumerate(inattention_keys):
            with cols_inatt[idx]:
                st.markdown(f"<div style='text-align: center;'><b>Q1_{idx+1}</b><br><span style='font-size: 1.2em;'></span></div>", unsafe_allow_html=True)
                val = st.number_input(
                    f"{k}", min_value=0, max_value=3, key=f"inatt_{k}", label_visibility="collapsed"
                )
                inattention_values.append(val)

        st.markdown("### Hyperactivity Scores")
        hyperactivity_keys = [f"Q2_{i}" for i in range(1, 10)]
        hyperactivity_values = []
        cols_hyper = st.columns(9)
        for idx, k in enumerate(hyperactivity_keys):
            with cols_hyper[idx]:
                st.markdown(f"<div style='text-align: center;'><b>Q2_{idx+1}</b><br><span style='font-size: 1.2em;'></span></div>", unsafe_allow_html=True)
                val = st.selectbox(
                    f"{k}", [0,1,2,3], key=f"iper_{k}", label_visibility="collapsed"
                )
                hyperactivity_values.append(val)

        inattention_score = sum(inattention_values)
        hyperactivity_score = sum(hyperactivity_values)
        st.markdown(f"Diagnosis based on scores: {diagnosis_scorebased(sum(inattention_values), sum(hyperactivity_values))}")
        st.markdown("### Difficulties")
        focus_score = st.number_input("Focus Score Video", min_value=0, max_value=10)
        anx_dep = st.selectbox("Anxiety Depression Levels", [0,1,2,3])
        diff_org = st.checkbox("Difficulty Organizing Tasks")
        learn_diff = st.checkbox("Learning Difficulties")
        if st.button("Insert Assessment", use_container_width=True):
            if not subjects_col.find_one({"subject_id": next_id}):
                st.error("Subject ID does not exist! Please insert the subject first.")
            elif assessments_col.find_one({"subject_id": next_id, "name": name_assessment}):
                st.error("Assessment already exists for this subject with this name!")
            else:
                assessment_doc = {
                    "subject_id": next_id,
                    "name": name_assessment,
                    "inattention": {k: v for k, v in zip(inattention_keys, inattention_values)},
                    "hyperactivity": {k: v for k, v in zip(hyperactivity_keys, hyperactivity_values)},
                    "Focus_Score_Video": focus_score,
                    "Difficulty_Organizing_Tasks": diff_org,
                    "Learning_Difficulties": learn_diff,
                    "Anxiety_Depression_Levels": anx_dep,
                    "inattention_score": inattention_score,
                    "hyperactivity_score": hyperactivity_score,
                    "inattention_severity": classify_score(inattention_score),
                    "hyperactivity_severity": classify_score(hyperactivity_score)
                }
                assessments_col.insert_one(assessment_doc)
                st.success("Assessment inserted!")

elif menu == "Read":
    st.subheader(f"View data from **{collection.capitalize()}**")
    id = st.number_input("Filter by Subject ID", min_value=1, step=1, format="%d")
    if collection == "subjects":
        if id:
            subject = subjects_col.find_one({"subject_id": id})
            subjects = [subject] if subject else []
        else:
            subjects = list(subjects_col.find())
        if subjects:
            for subject in subjects:
                with st.expander(f"Subject ID: {subject.get('subject_id', '')}", expanded=True):
                    st.json(subject)
        else:
            st.warning("No subjects found.")

    elif collection == "assessments":
        if id:
            assessment = assessments_col.find_one({"subject_id": id})
            assessments = [assessment] if assessment else []
        else:
            assessments = list(assessments_col.find())
        if assessments:
            for assessment in assessments:
                with st.expander(f"Assessment: {assessment.get('name', '')} (ID: {assessment.get('subject_id', '')})", expanded=True):
                    st.json(assessment)
        else:
            st.warning("No assessments found.")

    elif collection == "indicators":
        if id:
            indicator = indicators_col.find_one({"subject_id": id})
            indicators = [indicator] if indicator else []
        else:
            indicators = list(indicators_col.find())
        if indicators:
            for indicator in indicators:
                with st.expander(f"Indicators for ID: {indicator.get('subject_id', '')}", expanded=True):
                    st.json(indicator)
        else:
            st.warning("No indicators found.")

elif menu == "Update":
    st.subheader(f"Update data in **{collection.capitalize()}**")
    id = st.number_input("Filter by Subject ID", min_value=1, value=1, step=1, format="%d")
    if collection == "subjects":
        subject = subjects_col.find_one({"subject_id": id})
        if subject:
            new_age = st.number_input("Age", min_value=3, max_value=100, value=subject.get("age", 3))
            new_gender = st.selectbox(
                "Gender",
                [1, 2],
                index=[1, 2].index(subject.get("gender", 1)) if subject.get("gender", 1) in [1, 2] else 0,
                help="1 for male, 2 for female"
            )
            educational_levels = ["Kindergarten", "Middle", "Primary", "Secondary", "University", "Working", "Not Working"]
            new_educational_level = st.selectbox(
                "Educational Level",
                educational_levels,
                index=educational_levels.index(subject.get("educational_level", educational_levels[0])) if subject.get("educational_level", educational_levels[0]) in educational_levels else 0
            )
            family_history_options = ["No", "Yes", "Unknown"]
            new_family_history = st.selectbox(
                "Family History",
                family_history_options,
                index=family_history_options.index(subject.get("family_history", family_history_options[0])) if subject.get("family_history", family_history_options[0]) in family_history_options else 0
            )
            if st.button("Update Subject", use_container_width=True):
                subjects_col.update_one(
                    {"subject_id": id},
                    {"$set": {
                        "age": new_age,
                        "gender": new_gender,
                        "educational_level": new_educational_level,
                        "family_history": new_family_history
                    }}
                )
                st.success("Subject updated!")
        else:
            st.warning("Subject not found.")

    elif collection == "assessments":
        assessment_name = st.selectbox("Assessment Name", ["SNAP-IV"])
        assessment = assessments_col.find_one({"subject_id": id, "name": assessment_name})
        if assessment:
            st.markdown("### Inattention Scores")
            inattention_keys = [f"Q1_{i}" for i in range(1, 10)]
            inattention_values = []
            cols_inatt = st.columns(9)
            for idx, k in enumerate(inattention_keys):
                with cols_inatt[idx]:
                    st.markdown(f"<div style='text-align: center;'><b>Q1_{idx+1}</b></div>", unsafe_allow_html=True)
                    val = st.number_input(
                        f"{k}",
                        min_value=0,
                        max_value=3,
                        value=assessment.get("inattention", {}).get(k, 0) if isinstance(assessment.get("inattention"), dict) else assessment.get(k, 0),
                        key=f"update_inatt_{k}",
                        label_visibility="collapsed"
                    )
                    inattention_values.append(val)

            st.markdown("### Hyperactivity Scores")
            hyperactivity_keys = [f"Q2_{i}" for i in range(1, 10)]
            hyperactivity_values = []
            cols_hyper = st.columns(9)
            for idx, k in enumerate(hyperactivity_keys):
                with cols_hyper[idx]:
                    st.markdown(f"<div style='text-align: center;'><b>Q2_{idx+1}</b></div>", unsafe_allow_html=True)
                    val = st.number_input(
                        f"{k}",
                        min_value=0,
                        max_value=3,
                        value=assessment.get("hyperactivity", {}).get(k, 0) if isinstance(assessment.get("hyperactivity"), dict) else assessment.get(k, 0),
                        key=f"update_iper_{k}",
                        label_visibility="collapsed"
                    )
                    hyperactivity_values.append(val)

            inattention_score = sum(inattention_values)
            hyperactivity_score = sum(hyperactivity_values)
            st.markdown(f"Diagnosis based on scores: {diagnosis_scorebased(inattention_score, hyperactivity_score)}")

            focus_score = st.number_input(
                "Focus Score Video",
                min_value=0,
                max_value=10,
                value=assessment.get("Focus_Score_Video", 0)
            )
            anx_dep = st.number_input(
                "Anxiety Depression Levels",
                min_value=0,
                max_value=3,
                value=assessment.get("Anxiety_Depression_Levels", 0)
            )
            diff_org = st.checkbox(
                "Difficulty Organizing Tasks",
                value=assessment.get("Difficulty_Organizing_Tasks", 0)
            )
            learn_diff = st.checkbox(
                "Learning Difficulties",
                value=assessment.get("Learning_Difficulties", 0)
            )

            if st.button("Update Assessment", use_container_width=True):
                assessments_col.update_one(
                    {"subject_id": id, "name": assessment_name},
                    {"$set": {
                        "inattention": {k: v for k, v in zip(inattention_keys, inattention_values)},
                        "hyperactivity": {k: v for k, v in zip(hyperactivity_keys, hyperactivity_values)},
                        "inattention_score": inattention_score,
                        "hyperactivity_score": hyperactivity_score,
                        "inattention_severity": classify_score(inattention_score),
                        "hyperactivity_severity": classify_score(hyperactivity_score),
                        "Focus_Score_Video": focus_score,
                        "Difficulty_Organizing_Tasks": diff_org,
                        "Learning_Difficulties": learn_diff,
                        "Anxiety_Depression_Levels": anx_dep
                    }}
                )
                st.success("Assessment updated!")
        else:
            st.warning("Assessment not found.")

    elif collection == "indicators":
        indicators = indicators_col.find_one({"subject_id": id})
        if indicators:
            sleep = st.number_input("Sleep Hours", min_value=0, value=indicators.get("Sleep_Hours", 0))
            activity = st.number_input("Daily Activity Hours", min_value=0, value=indicators.get("Daily_Activity_Hours", 0))
            phone = st.number_input("Daily Phone Usage Hours", min_value=0, value=indicators.get("Daily_Phone_Usage_Hours", 0))
            coffee = st.text_input("Daily Coffee/Tea Consumption", value=indicators.get("Daily_Coffee_Tea_Consumption", ""))
            walking_running_hours = st.number_input(
            "Daily Walking/Running Hours", min_value=0.0, max_value=24.0, format="%.1f", step=0.1, value=indicators.get("Daily_Walking_Running_Hours", 0.0)
            )
            if st.button("Update Indicators", use_container_width=True):
                indicators_col.update_one(
                    {"subject_id": id},
                    {"$set": {
                        "Sleep_Hours": sleep,
                        "Daily_Activity_Hours": activity,
                        "Daily_Phone_Usage_Hours": phone,
                        "Daily_Coffee_Tea_Consumption": coffee
                    }}
                )
                st.success("Indicators updated!")
        else:
            st.warning("Indicators not found.")

elif menu == "Delete":
    st.subheader(f"Delete data from **{collection.capitalize()}**")
    id = st.number_input("Filter by Subject ID", min_value=1, value=1, step=1, format="%d")
    if collection == "subjects":
        if st.button("Delete Subject and related data", use_container_width=True):
            subjects_col.delete_one({"subject_id": id})
            assessments_col.delete_many({"subject_id": id})
            indicators_col.delete_many({"subject_id": id})
            st.error("Subject and related data deleted.")
    elif collection == "assessments":
        assessment_name = st.selectbox("Assessment Name to delete", ["SNAP-IV"])
        if st.button("Delete Assessment", use_container_width=True):
            result = assessments_col.delete_one({"subject_id": id, "name": assessment_name})
            if result.deleted_count > 0:
                st.error("Assessment deleted.")
            else:
                st.warning("No assessment found with these details.")
    elif collection == "indicators":
        if st.button("Delete Indicators", use_container_width=True):
            result = indicators_col.delete_many({"subject_id": id})
            if result.deleted_count > 0:
                st.error("Indicators deleted.")
            else:
                st.warning("No indicators found for this subject.")

elif menu == "JOIN":
    st.subheader("View aggregated data (JOIN)")
    id = st.number_input("Filter by Subject ID", min_value=1, value=1, step=1, format="%d")
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
        with st.expander(f"Aggregated for ID: {doc.get('subject_id', '')}"):
            st.json(doc)
        found = True
    if not found:
        st.warning("No results found for the join.")