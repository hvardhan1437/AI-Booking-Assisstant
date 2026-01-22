import streamlit as st
import pandas as pd
from db.database import get_all_bookings


def admin_dashboard():
    st.title("🧑‍💼 Admin Dashboard")
    st.caption("Manage and monitor all customer bookings")

    bookings = get_all_bookings()

    if not bookings:
        st.info("No bookings found.")
        return

    # Convert to DataFrame
    df = pd.DataFrame(
        bookings,
        columns=[
            "Booking ID",
            "Name",
            "Email",
            "Phone",
            "Booking Type",
            "Date",
            "Time",
            "Status",
            "Created At"
        ]
    )

    # ---------- KPI METRICS ----------
    st.subheader("📊 Booking Overview")

    total_count = len(df)
    confirmed_count = len(df[df["Status"].str.lower() == "confirmed"])
    pending_count = len(df[df["Status"].str.lower() == "pending"])
    upcoming_count = len(df[df["Date"] >= pd.Timestamp.today().strftime("%Y-%m-%d")])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Bookings", total_count)
    col2.metric("Confirmed", confirmed_count)
    col3.metric("Pending", pending_count)
    col4.metric("Upcoming", upcoming_count)

    st.divider()

    # ---------- FILTERS ----------
    st.subheader("🔍 Filter Bookings")

    col1, col2, col3 = st.columns(3)

    with col1:
        name_filter = st.text_input("Filter by Name")

    with col2:
        email_filter = st.text_input("Filter by Email")

    with col3:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "Confirmed", "Pending"]
        )

    if name_filter:
        df = df[df["Name"].str.contains(name_filter, case=False, na=False)]

    if email_filter:
        df = df[df["Email"].str.contains(email_filter, case=False, na=False)]

    if status_filter != "All":
        df = df[df["Status"].str.lower() == status_filter.lower()]

    st.divider()

    # ---------- BOOKINGS TABLE ----------
    st.subheader("📋 All Bookings")

    st.dataframe(
        df.sort_values(by="Created At", ascending=False),
        use_container_width=True
    )

# ---------- OPTIONAL DETAIL VIEW ----------
    st.divider()
    st.subheader("🔎 View Booking Details")

    booking_id_input = st.text_input(
        "Enter Booking ID to view details",
        placeholder="e.g. 12"
    )

    if booking_id_input:
        try:
            booking_id_input = int(booking_id_input)
            booking_row = df[df["Booking ID"] == booking_id_input]

            if booking_row.empty:
                st.warning("No booking found with the given Booking ID.")
            else:
                st.json(booking_row.iloc[0].to_dict())

        except ValueError:
            st.warning("Please enter a valid numeric Booking ID.")



    # ---------- EXPORT TO CSV ----------
    st.divider()

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="⬇️ Export Bookings as CSV",
        data=csv,
        file_name="bookings_export.csv",
        mime="text/csv",
        use_container_width=True
    )

