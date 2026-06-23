import streamlit as st
import pandas as pd
from pymongo import MongoClient, UpdateOne
from datetime import datetime
from io import BytesIO

# =====================================================
# MongoDB
# =====================================================
client = MongoClient(st.secrets["MONGO_URI"])

db = client[st.secrets["DATABASE"]]
collection = db[st.secrets["COLLECTION"]]

# สร้าง Unique Index (รันซ้ำได้)
collection.create_index("submission_id", unique=True)

# =====================================================
# Parse Function
# =====================================================
def parse_qa(text):

    if pd.isna(text):
        return {}

    lines = [line.strip() for line in str(text).split("\n") if line.strip()]

    result = {}

    i = 0

    while i < len(lines) - 1:

        q = lines[i]
        a = lines[i + 1]

        if q.startswith("Q") and a.startswith("A"):

            question = q.split(" ", 1)[1]

            answer = a.split(" ", 1)[1] if " " in a else ""

            result[question] = answer

        i += 2

    return result


# =====================================================
# Streamlit
# =====================================================
st.set_page_config(
    page_title="Survey Import",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Survey Excel Import")

uploaded = st.file_uploader(
    "Upload Excel",
    type=["xlsx"]
)

if uploaded:

    # =====================================================
    # Read Excel
    # =====================================================

    df = pd.read_excel(uploaded, engine="openpyxl")

    if "question_answer" not in df.columns:
        st.error("❌ ไม่พบคอลัมน์ question_answer")
        st.stop()

    if "submission_id" not in df.columns:
        st.error("❌ ไม่พบคอลัมน์ submission_id")
        st.stop()

    # =====================================================
    # Parse Question Answer
    # =====================================================

    qa_df = pd.json_normalize(
        df["question_answer"].apply(parse_qa)
    )

    df_final = pd.concat(
        [
            df.drop(columns=["question_answer"]),
            qa_df
        ],
        axis=1
    )

    st.success(f"พบข้อมูลทั้งหมด {len(df_final):,} รายการ")

    st.dataframe(
        df_final,
        use_container_width=True,
        height=500
    )

    # =====================================================
    # Download Excel
    # =====================================================

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_final.to_excel(writer, index=False)

    st.download_button(
        "⬇ Download Parsed Excel",
        data=output.getvalue(),
        file_name="output_parsed.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.divider()

    # =====================================================
    # Save MongoDB
    # =====================================================

    if st.button(
        "💾 Save to MongoDB",
        type="primary",
        use_container_width=True
    ):

        docs = df_final.fillna("").to_dict("records")

        operations = []

        for doc in docs:

            doc["import_time"] = datetime.utcnow()

            operations.append(

                UpdateOne(
                    {
                        "submission_id": doc["submission_id"]
                    },
                    {
                        "$setOnInsert": doc
                    },
                    upsert=True
                )

            )

        result = collection.bulk_write(
            operations,
            ordered=False
        )

        inserted = result.upserted_count
        duplicate = len(docs) - inserted
        
        # ==========================================
        # Import Log
        # ==========================================
        log_collection = db["import_logs"]

        log_collection.insert_one({
            "collection": st.secrets["COLLECTION"],
            "file_name": uploaded.name,
            "import_time": datetime.now(),
            "total_rows": len(docs),
            "inserted": inserted,
            "duplicate": duplicate
        })

        st.success("นำเข้าข้อมูลเรียบร้อย")

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "ทั้งหมด",
            f"{len(docs):,}"
        )

        c2.metric(
            "เพิ่มใหม่",
            f"{inserted:,}"
        )

        c3.metric(
            "ข้อมูลซ้ำ",
            f"{duplicate:,}"
        )