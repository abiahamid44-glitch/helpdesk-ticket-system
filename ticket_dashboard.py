import streamlit as st
import requests
import pandas as pd
import plotly.express as px

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Help Desk Ticket System", page_icon="🎫", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


if not st.session_state.logged_in:
    st.title("🔐 Help Desk Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        response = requests.post(
            f"{API_URL}/login",
            json={
                "username": username,
                "password": password
            }
        )

        if response.status_code == 200 and response.json()["success"]:
            st.session_state.logged_in = True
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid username or password.")

    st.info("Test login: username = admin, password = password123")
    st.stop()


col_title, col_logout = st.columns([4, 1])

with col_title:
    st.title("🎫 Help Desk Ticket System")

with col_logout:
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()


st.sidebar.header("Create New Ticket")

title = st.sidebar.text_input("Title")
description = st.sidebar.text_area("Description")
priority = st.sidebar.selectbox("Priority", ["Low", "Medium", "High"])

if st.sidebar.button("Submit Ticket"):
    if title.strip() == "" or description.strip() == "":
        st.sidebar.error("Please enter a title and description.")
    else:
        payload = {
            "title": title,
            "description": description,
            "priority": priority,
            "status": "Open"
        }

        response = requests.post(f"{API_URL}/tickets", json=payload)

        if response.status_code == 200:
            st.sidebar.success("Ticket created successfully!")
            st.rerun()
        else:
            st.sidebar.error("Something went wrong.")


response = requests.get(f"{API_URL}/tickets")

if response.status_code == 200:
    tickets = response.json()
else:
    tickets = []

df = pd.DataFrame(tickets)

st.subheader("📊 Dashboard Metrics")

if not df.empty:
    total = len(df)
    open_count = len(df[df["status"] == "Open"])
    progress_count = len(df[df["status"] == "In Progress"])
    resolved_count = len(df[df["status"] == "Resolved"])
    closed_count = len(df[df["status"] == "Closed"])

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Total Tickets", total)
    col2.metric("Open", open_count)
    col3.metric("In Progress", progress_count)
    col4.metric("Resolved", resolved_count)
    col5.metric("Closed", closed_count)
else:
    st.info("No tickets yet.")

st.divider()

if not df.empty:
    colA, colB = st.columns(2)

    with colA:
        st.subheader("Tickets by Priority")
        priority_counts = df["priority"].value_counts().reset_index()
        priority_counts.columns = ["Priority", "Count"]

        fig = px.bar(
            priority_counts,
            x="Priority",
            y="Count",
            text="Count",
            title="Priority Breakdown"
        )

        st.plotly_chart(fig, use_container_width=True)

    with colB:
        st.subheader("Tickets by Status")
        status_counts = df["status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]

        fig = px.pie(
            status_counts,
            names="Status",
            values="Count",
            title="Status Breakdown"
        )

        st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("🔍 Search and Filter Tickets")

search = st.text_input("Search by title or description")

status_filter = st.selectbox(
    "Filter by Status",
    ["All", "Open", "In Progress", "Resolved", "Closed"]
)

priority_filter = st.selectbox(
    "Filter by Priority",
    ["All", "Low", "Medium", "High"]
)

filtered_df = df.copy()

if not filtered_df.empty:
    if search:
        filtered_df = filtered_df[
            filtered_df["title"].str.contains(search, case=False, na=False) |
            filtered_df["description"].str.contains(search, case=False, na=False)
        ]

    if status_filter != "All":
        filtered_df = filtered_df[filtered_df["status"] == status_filter]

    if priority_filter != "All":
        filtered_df = filtered_df[filtered_df["priority"] == priority_filter]

st.divider()

st.subheader("📋 Current Tickets")

if not filtered_df.empty:
    display_df = filtered_df.copy()

    def format_priority(priority):
        if priority == "High":
            return "🔴 High"
        elif priority == "Medium":
            return "🟡 Medium"
        else:
            return "🟢 Low"

    display_df["priority"] = display_df["priority"].apply(format_priority)

    st.dataframe(display_df, use_container_width=True)
else:
    st.info("No tickets found.")

st.divider()

st.subheader("📝 Update Ticket Status")

if not df.empty:
    selected_id = st.selectbox("Select Ticket ID", df["id"].tolist())

    new_status = st.selectbox(
        "New Status",
        ["Open", "In Progress", "Resolved", "Closed"]
    )

    if st.button("Update Status"):
        response = requests.put(
            f"{API_URL}/tickets/{selected_id}",
            json={"status": new_status}
        )

        if response.status_code == 200:
            st.success("Ticket status updated!")
            st.rerun()
        else:
            st.error("Failed to update ticket.")

st.divider()

st.subheader("🗑️ Delete Ticket")

if not df.empty:
    delete_id = st.selectbox("Select Ticket ID to Delete", df["id"].tolist())

    if st.button("Delete Ticket"):
        response = requests.delete(f"{API_URL}/tickets/{delete_id}")

        if response.status_code == 200:
            st.success("Ticket deleted!")
            st.rerun()
        else:
            st.error("Failed to delete ticket.")

st.divider()

st.subheader("📜 Recent Activity")

activity_response = requests.get(f"{API_URL}/activity")

if activity_response.status_code == 200:
    logs = activity_response.json()

    if logs:
        for log in logs:
            st.write(f"• {log['action']} ({log['timestamp']})")
    else:
        st.info("No activity yet.")
else:
    st.error("Could not load activity logs.")