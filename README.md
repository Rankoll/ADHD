# ADHD
This project implements a clinical data (from the [dataset](https://www.kaggle.com/datasets/a7md19/adhd-dataset-4-classes-u2) available on Kaggle) management system using **MongoDB (NoSQL)**,  as it ensures flexibility and scalability for managing heterogeneous clinical data., to organize information from patients who completed the **SNAP-IV** questionnaire.

Developed in **Python** with a **Streamlit** interface, the system supports full **CRUD** operations and automatically classifies SNAP-IV scores based on clinical thresholds.

## Division in collection
Data is structured into three collections:
`subjects` (demographics): subject_id, Age, Gender, Educational_Level, and Family_History.

`indicators` (behavioral habits): subject_id, Sleep_Hours, Daily_Activity_Hours, Phone Usage, and Caffeine Consumption.

`assessments` (questionnaire + supportive variables): subject_id, name, Q1_1 to Q1_9 (assess Hyperactivity), Q2_1 to Q2_9 (assess Inattention), Focus_Score_Video (concentration ability), Difficulty_Organizing_Tasks, Learning_Difficulties, Anxiety_Depression_Levels, inattention_score, hyperactivity_score, inattention_severity, hyperactivity_severity.

## References
[SNAP-IV Teacher and Parent 18-Item Rating Scale](https://shared-care.ca/files/Scoring_for_SNAP_IV_Guide_18-item.pdf)

[SNAP IV Self Rating Scale](https://rudheathsenioracademy.org.uk/wp-content/uploads/2024/10/SNAP-IV-Self-Rating-Scale.pdf)

[SDAI - Scala di disattenzione e iperattività – Cornoldi 1996](https://www.icscanegrate.edu.it/uploads/files/LA_SCALA_SDAI.pdf)