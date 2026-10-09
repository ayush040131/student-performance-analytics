
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Student Performance Analytics",
    page_icon="📊",
    layout="wide"
)

# Excel file stored beside app.py
EXCEL_FILE = Path(__file__).parent / "students.xlsx"
ATTENDANCE_COLUMN = "Attendance"
PASS_MARKS = 40

st.title("Student Performance Analytics Dashboard")
st.caption("Excel-powered student performance analysis")

# Sidebar controls
st.sidebar.header("Data Controls")

if st.sidebar.button("Refresh Data", use_container_width=True):
    st.rerun()

st.sidebar.caption(
    "Edit students.xlsx in Excel, save it, "
    "then click Refresh Data."
)

# Check whether the workbook exists
if not EXCEL_FILE.exists():
    st.error("The file students.xlsx was not found.")
    st.info(
        "Save students.xlsx in the same folder as app.py, "
        "then rerun the dashboard."
    )
    st.stop()

# Read the latest saved Excel data
try:
    df = pd.read_excel(EXCEL_FILE, engine="openpyxl")
except Exception as error:
    st.error(f"Could not read the Excel file: {error}")
    st.info(
        "Save and close Excel if necessary, check the file name, "
        "and click Refresh Data again."
    )
    st.stop()

# Validate the spreadsheet structure
df.columns = df.columns.astype(str).str.strip()

if df.columns.duplicated().any():
    st.error("Your Excel file contains duplicate column names.")
    st.stop()

if "Student" not in df.columns:
    st.error("Your Excel sheet must contain a Student column.")
    st.stop()

if ATTENDANCE_COLUMN not in df.columns:
    st.error("Your Excel sheet must contain an Attendance column.")
    st.stop()

subjects = [
    col for col in df.columns
    if col not in ["Student", ATTENDANCE_COLUMN]
]

if not subjects:
    st.error("Add at least one subject column to your Excel sheet.")
    st.stop()

# Validate and clean data
df["Student"] = df["Student"].fillna("").astype(str).str.strip()

if (df["Student"] == "").any():
    st.error("Every student must have a name.")
    st.stop()

if df["Student"].duplicated().any():
    st.error("Student names must be unique in this version.")
    st.stop()

numeric_columns = subjects + [ATTENDANCE_COLUMN]

for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

if df.empty:
    st.warning("Your Excel sheet contains no student records.")
    st.stop()

if df[numeric_columns].isnull().any().any():
    st.error(
        "Marks and attendance must be numeric and filled in. "
        "Check the Excel sheet for blanks or invalid values."
    )
    st.stop()

for col in numeric_columns:
    if not df[col].between(0, 100).all():
        st.error(
            f"{col} must contain values between 0 and 100."
        )
        st.stop()

# Calculate analytics dynamically
df["Average"] = df[subjects].mean(axis=1).round(2)

# Pass if the overall average is 40 or above
df["Result"] = df["Average"].apply(
    lambda marks: "Pass" if marks >= PASS_MARKS else "Fail"
)

# Sidebar filters
st.sidebar.subheader("Dashboard Filters")

selected_subject = st.sidebar.selectbox(
    "Select subject",
    subjects
)

selected_result = st.sidebar.selectbox(
    "Filter by result",
    ["All", "Pass", "Fail"]
)

filtered_df = df.copy()

if selected_result != "All":
    filtered_df = filtered_df[
        filtered_df["Result"] == selected_result
    ]

if filtered_df.empty:
    st.warning("No students match the selected result filter.")
    st.stop()

# KPI cards
total_students = len(filtered_df)
average_marks = filtered_df["Average"].mean()
pass_percentage = (
    filtered_df["Result"].eq("Pass").mean() * 100
)
average_attendance = filtered_df[ATTENDANCE_COLUMN].mean()

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Students", total_students)
c2.metric("Average Marks", f"{average_marks:.2f}/100")
c3.metric("Pass Rate", f"{pass_percentage:.1f}%")
c4.metric("Average Attendance", f"{average_attendance:.1f}%")

st.divider()

# Subject averages
left, right = st.columns(2)

with left:
    st.subheader("Subject-wise Average Marks")

    subject_data = (
        filtered_df[subjects]
        .mean()
        .rename_axis("Subject")
        .reset_index(name="Average Marks")
    )

    fig1 = px.bar(
        subject_data,
        x="Subject",
        y="Average Marks",
        color="Subject",
        title="Average Marks by Subject"
    )

    fig1.update_yaxes(range=[0, 100])
    st.plotly_chart(fig1, use_container_width=True)

with right:
    st.subheader("Student Marks Distribution")

    fig2 = px.histogram(
        filtered_df,
        x="Average",
        color="Result",
        nbins=8,
        title="Distribution of Average Marks"
    )

    st.plotly_chart(fig2, use_container_width=True)

# Attendance versus performance
st.subheader("Attendance vs Academic Performance")

fig3 = px.scatter(
    filtered_df,
    x=ATTENDANCE_COLUMN,
    y="Average",
    color="Result",
    hover_name="Student",
    title="Attendance and Average Marks"
)

st.plotly_chart(fig3, use_container_width=True)

# Subject-specific student performance
st.subheader(f"{selected_subject}: Student Marks")

fig4 = px.bar(
    filtered_df.sort_values(selected_subject, ascending=False),
    x="Student",
    y=selected_subject,
    color="Result",
    title=f"Marks in {selected_subject}"
)

fig4.update_yaxes(range=[0, 100])
st.plotly_chart(fig4, use_container_width=True)

# Student table
st.subheader("Student Records")

display_columns = (
    ["Student"] + subjects
    + [ATTENDANCE_COLUMN, "Average", "Result"]
)

st.dataframe(
    filtered_df[display_columns].sort_values(
        "Average", ascending=False
    ),
    use_container_width=True,
    hide_index=True
)

# Automatically generated insight
top_student = filtered_df.loc[
    filtered_df["Average"].idxmax()
]

st.subheader("Key Insight")

st.write(
    f"Top-performing student in the current selection: "
    f"**{top_student['Student']}**, with an average of "
    f"**{top_student['Average']:.2f}/100**."
)

st.caption(
    f"Source: {EXCEL_FILE.name} | "
    f"Passing rule: at least {PASS_MARKS} marks in every subject."
)