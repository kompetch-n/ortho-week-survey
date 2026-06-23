import streamlit as st
import pandas as pd
from pymongo import MongoClient
import plotly.express as px

# ==========================================
# Page Config
# ==========================================
st.set_page_config(
    page_title="Survey Dashboard",
    page_icon="📊",
    layout="wide"
)

# ==========================================
# MongoDB
# ==========================================
client = MongoClient(st.secrets["MONGO_URI"])
db = client[st.secrets["DATABASE"]]
collection = db[st.secrets["COLLECTION"]]

log_collection = db["import_logs"]

# ==========================================
# Load Data
# ==========================================
data = list(collection.find({}, {"_id": 0}))

# ==========================================
# Last Import
# ==========================================

latest_import = log_collection.find_one(
    {
        "collection": st.secrets["COLLECTION"]
    },
    sort=[
        ("import_time",-1)
    ]
)

if len(data) == 0:
    st.title("📊 Survey Dashboard")
    st.warning("ยังไม่มีข้อมูล")
    st.stop()

df = pd.DataFrame(data)

# ==========================================
# Score Mapping
# ==========================================
score_map = {
    "มากที่สุด": 5,
    "มาก": 4,
    "ปานกลาง": 3,
    "น้อย": 2,
    "น้อยที่สุด": 1
}

score_columns = [
    "การจัดกิจกรรมในครั้งนี้ท่านได้รับประโยชน์และความรู้มากน้อยเพียงใด",
    "ท่านสามารถนำองค์ความรู้จากกิจกรรมนี้ไปประยุกต์ใช้ในชีวิตประจำวันได้มากน้อยเพียงใด",
    "รูปแบบในการจัดกิจกรรมมีความเหมาะสม",
    "สถานที่ในการจัดกิจกกรมมีความเหมาะสม"
]

score = []

for col in score_columns:
    if col in df.columns:
        score.extend(
            df[col].map(score_map).dropna().tolist()
        )

avg_score = round(sum(score)/len(score),2) if len(score) else 0

# ==========================================
# Header
# ==========================================
st.title("📊 Satisfaction Dashboard")

if latest_import:

    st.info(f"""
### 📥 Last Import

**📄 File :** {latest_import['file_name']}

**🕒 Date :** {latest_import['import_time'].strftime("%d/%m/%Y %H:%M:%S")}

**✅ New Records :** {latest_import['inserted']:,}

**♻ Duplicate :** {latest_import['duplicate']:,}
""")

# ==========================================
# KPI
# ==========================================
c1,c2,c3,c4,c5 = st.columns(5)

c1.metric(
    "👥 Responses",
    f"{len(df):,}"
)

c2.metric(
    "⭐ Average Score",
    f"{avg_score}/5"
)

very_good = 0

for col in score_columns:
    if col in df.columns:
        very_good += (
            df[col].isin(["มาก","มากที่สุด"])
        ).sum()

total_answer = len(df)*len(score_columns)

percent = round((very_good/total_answer)*100,1)

c3.metric(
    "😊 Satisfaction",
    f"{percent}%"
)

recommend = 0

if "หลังจากมาร่วมงานนี้แล้ว ท่านตั้งใจจะทำสิ่งใดต่อไปนี้" in df.columns:

    recommend = df[
        "หลังจากมาร่วมงานนี้แล้ว ท่านตั้งใจจะทำสิ่งใดต่อไปนี้"
    ].str.contains(
        "แนะนำ",
        na=False
    ).sum()

recommend_percent = round(recommend/len(df)*100,1)

c4.metric(
    "👍 Recommend",
    f"{recommend_percent}%"
)

st.divider()

if latest_import:
    latest_time = latest_import["import_time"].strftime("%d/%m %H:%M")
else:
    latest_time = "-"

c5.metric(
    "📥 Last Import",
    latest_time
)

# ==========================================
# Row 1
# ==========================================
left,right = st.columns(2)

# ---------------- Gender ----------------

with left:

    st.subheader("👤 Gender")

    if "เพศ" in df.columns:

        gender = (
            df["เพศ"]
            .value_counts()
            .reset_index()
        )

        gender.columns=["Gender","Count"]

        fig = px.pie(
            gender,
            names="Gender",
            values="Count",
            hole=.55
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# ---------------- Age ----------------

with right:

    st.subheader("🎂 Age")

    if "อายุ" in df.columns:

        age = (
            df["อายุ"]
            .value_counts()
            .reset_index()
        )

        age.columns=["Age","Count"]

        fig = px.bar(
            age,
            x="Age",
            y="Count",
            text_auto=True
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# ==========================================
# Row 2
# ==========================================

left,right = st.columns(2)

# ---------------- Channel ----------------

with left:

    st.subheader("📣 Marketing Channel")

    if "ช่องทางที่ท่านทราบการจัดกิจกรรม" in df.columns:

        source = (
            df["ช่องทางที่ท่านทราบการจัดกิจกรรม"]
            .value_counts()
            .reset_index()
        )

        source.columns=["Channel","Count"]

        fig = px.bar(
            source,
            x="Count",
            y="Channel",
            orientation="h",
            text_auto=True
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# ---------------- Bone ----------------

with right:

    st.subheader("🦴 Bone Problem")

    if "ปัจจุบันท่านหรือคนใกล้ชิด มีปัญหาในด้านกระดูกและข้อหรือไม่" in df.columns:

        bone = (
            df[
                "ปัจจุบันท่านหรือคนใกล้ชิด มีปัญหาในด้านกระดูกและข้อหรือไม่"
            ]
            .value_counts()
            .reset_index()
        )

        bone.columns=["Status","Count"]

        fig = px.pie(
            bone,
            names="Status",
            values="Count",
            hole=.55
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# ==========================================
# Satisfaction Score
# ==========================================

st.subheader("⭐ Satisfaction Score")

score_result=[]

for col in score_columns:

    if col in df.columns:

        score_result.append({

            "Question":col,

            "Score":round(
                df[col].map(score_map).mean(),
                2
            )

        })

score_df=pd.DataFrame(score_result)

fig=px.bar(
    score_df,
    x="Question",
    y="Score",
    text_auto=True,
    range_y=[0,5]
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ==========================================
# Customer Intent
# ==========================================

st.subheader("🎯 Customer Intention")

if "หลังจากมาร่วมงานนี้แล้ว ท่านตั้งใจจะทำสิ่งใดต่อไปนี้" in df.columns:

    intent=(
        df[
            "หลังจากมาร่วมงานนี้แล้ว ท่านตั้งใจจะทำสิ่งใดต่อไปนี้"
        ]
        .value_counts()
        .reset_index()
    )

    intent.columns=["Intent","Count"]

    fig=px.pie(
        intent,
        names="Intent",
        values="Count",
        hole=.55
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# ==========================================
# Latest Responses
# ==========================================

st.subheader("📄 Latest Responses")

show_columns=[]

for col in [

    "ชื่อ",

    "นามสกุล",

    "เพศ",

    "อายุ",

    "ช่องทางที่ท่านทราบการจัดกิจกรรม"

]:

    if col in df.columns:
        show_columns.append(col)

st.dataframe(
    df[show_columns].tail(10),
    use_container_width=True
)