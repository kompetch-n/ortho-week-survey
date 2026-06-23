import pandas as pd
from pymongo import MongoClient
import streamlit as st

client = MongoClient(st.secrets["MONGO_URI"])

db = client[st.secrets["DATABASE"]]
collection = db[st.secrets["COLLECTION"]]

collection.create_index("submission_id", unique=True)


def parse_qa(text):

    if pd.isna(text):
        return {}

    lines = [line.strip() for line in str(text).split("\n") if line.strip()]

    result = {}

    i = 0

    while i < len(lines)-1:

        q = lines[i]
        a = lines[i+1]

        if q.startswith("Q") and a.startswith("A"):

            question = q.split(" ",1)[1]
            answer = a.split(" ",1)[1] if " " in a else ""

            result[question] = answer

        i += 2

    return result