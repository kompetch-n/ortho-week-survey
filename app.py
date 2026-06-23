import streamlit as st
import pandas as pd
from pymongo import MongoClient
import plotly.express as px
from io import BytesIO
from datetime import datetime

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
# Date Filter
# ==========================================

if "submitted_at" in df.columns:

    df["submitted_at"] = pd.to_datetime(df["submitted_at"])

    min_date = df["submitted_at"].min().date()
    max_date = df["submitted_at"].max().date()

    st.subheader("📅 Activity Date")

    date_range = st.date_input(
        "เลือกช่วงวันที่",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # ถ้ายังเลือกไม่ครบ 2 วัน
    if not isinstance(date_range, tuple) or len(date_range) != 2:
        st.info("📅 กรุณาเลือกวันเริ่มต้นและวันสิ้นสุดก่อน")
        st.stop()

    start_date, end_date = date_range

    df = df[
        (df["submitted_at"].dt.date >= start_date) &
        (df["submitted_at"].dt.date <= end_date)
    ]

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
    "📥 Last Update",
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

question_map = {
    "การจัดกิจกรรมในครั้งนี้ท่านได้รับประโยชน์และความรู้มากน้อยเพียงใด":
        "📚 ได้รับความรู้",

    "ท่านสามารถนำองค์ความรู้จากกิจกรรมนี้ไปประยุกต์ใช้ในชีวิตประจำวันได้มากน้อยเพียงใด":
        "💡 นำไปใช้ได้",

    "รูปแบบในการจัดกิจกรรมมีความเหมาะสม":
        "🎯 รูปแบบกิจกรรม",

    "สถานที่ในการจัดกิจกกรมมีความเหมาะสม":
        "📍 สถานที่"
}

show_cols = [
    c for c in score_columns
    if c in df.columns
]

for i, col in enumerate(show_cols):

    score = round(df[col].map(score_map).mean(), 2)
    percent = score / 5

    title = question_map[col]

    left, right = st.columns([5, 1])

    with left:
        st.markdown(f"**{title}**")
        st.progress(percent)

    with right:
        st.metric(
            label="",
            value=f"{score:.2f}"
        )

    # เส้นคั่นบาง ๆ
    if i < len(show_cols) - 1:
        st.divider()

# ==========================================
# Customer Intent
# ==========================================

st.subheader("🎯 Customer Intention")

intent_options = [
    "จะปรับเปลี่ยนพฤติกรรม",
    "จะแนะนำคนในครอบครัว/เพื่อน",
    "สนใจอยากนัดหมายพบแพทย์เฉพาะทาง Orthopedic"
]

if "หลังจากมาร่วมงานนี้แล้ว ท่านตั้งใจจะทำสิ่งใดต่อไปนี้" in df.columns:

    intent_data = []

    series = df[
        "หลังจากมาร่วมงานนี้แล้ว ท่านตั้งใจจะทำสิ่งใดต่อไปนี้"
    ].fillna("")

    for option in intent_options:

        count = series.str.contains(
            option,
            regex=False
        ).sum()

        intent_data.append({
            "Intent": option,
            "Count": count
        })

    intent_df = pd.DataFrame(intent_data)

    fig = px.bar(
        intent_df,
        x="Count",
        y="Intent",
        orientation="h",
        text="Count"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# ==========================================
# All Survey Data
# ==========================================

st.divider()
st.subheader("📄 Survey Data")

# -----------------------------
# Search
# -----------------------------
# keyword = st.text_input(
#     "🔍 Search",
#     placeholder="ค้นหาชื่อ, นามสกุล, เบอร์โทรศัพท์..."
# )

df_show = df.copy()

# -----------------------------
# Hide Personal Information
# -----------------------------
df_table = df_show.copy()

hide_columns = [
    "ชื่อ",
    "นามสกุล",
    "เบอร์โทรศัพท์"
]

df_table = df_table.drop(
    columns=[c for c in hide_columns if c in df_table.columns],
    errors="ignore"
)

# if keyword:

#     mask = df_show.astype(str).apply(
#         lambda x: x.str.contains(keyword, case=False, na=False)
#     ).any(axis=1)

#     df_show = df_show[mask]


# -----------------------------
# Total Records
# -----------------------------
st.caption(f"แสดงข้อมูล {len(df_show):,} จากทั้งหมด {len(df):,} รายการ")

# -----------------------------
# Table
# -----------------------------
st.dataframe(
    df_table,
    use_container_width=True,
    height=600,
    hide_index=True
)


# -----------------------------
# Export Excel
# -----------------------------
output = BytesIO()

with pd.ExcelWriter(output, engine="openpyxl") as writer:
    df_show.to_excel(
        writer,
        index=False,
        sheet_name="Survey"
    )

filename = f"survey_data_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.xlsx"

st.download_button(
    "⬇ Export Excel",
    data=output.getvalue(),
    file_name=filename,
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True
)