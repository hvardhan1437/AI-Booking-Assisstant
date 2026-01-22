import streamlit as st
import os
import sys
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from models.llm import get_chatgroq_model
from models.embeddings import build_vector_store
import tempfile
from models.embeddings import retrieve_context
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import streamlit as st
from models.llm import get_chatgroq_model
from db.database import init_db, save_booking
from utils.email_service import send_confirmation_email
from admin_dashboard import admin_dashboard
import json

from db.database import clear_database
from datetime import datetime, date, time, timedelta
from db.database import get_bookings_by_date
from utils.validation import (
    validate_field,
    validate_time,
    validate_date,
    validate_name,
    validate_email,
    validate_phone,
)



def refers_to_uploaded_document(text):
    keywords = [
        "document", "doc", "pdf", "file",
        "details", "information", "uploaded"
    ]
    return any(word in text.lower() for word in keywords)





def get_rag_context(query):
    vector_store = st.session_state.get("vector_store")
    if not vector_store:
        return ""

    docs = vector_store.similarity_search(query, k=3)
    return "\n\n".join(doc.page_content for doc in docs)




from datetime import time





def is_booking_intent(text):
    keywords = ["book", "booking", "appointment", "schedule", "reserve"]
    return any(word in text.lower() for word in keywords)


def get_missing_fields(booking_data):
    return [
        k for k, v in booking_data.items()
        if v is None and k not in ["confirmed", "started"]
    ]


def next_booking_question(field):
    questions = {
        "name": "May I know your full name?",
        "email": "Please provide your email address.",
        "phone": "Please provide your phone number.",
        "booking_type": "What type of appointment would you like to book?",
        "date": "Please enter the preferred date (YYYY-MM-DD).",
        "time": "Please enter the preferred time (HH:MM)."
    }
    return questions[field]

def update_booking_data(user_input):
    booking = st.session_state.booking_data
    missing = get_missing_fields(booking)

    if not missing:
        return

    booking[missing[0]] = user_input


def update_booking_data(user_input):
    booking = st.session_state.booking_data
    missing = get_missing_fields(booking)
    if missing:
        booking[missing[0]] = user_input


def booking_summary(booking):
    return f"""
### Please confirm your appointment details:

- **Name:** {booking['name']}
- **Email:** {booking['email']}
- **Phone:** {booking['phone']}
- **Booking Type:** {booking['booking_type']}
- **Date:** {booking['date']}
- **Time:** {booking['time']}

Reply **YES** to confirm or **NO** to cancel.
"""


def get_chat_response(chat_model, messages):
    """
    Handles normal chat + RAG-based Q&A.
    Remains general-purpose while using documents when relevant.
    """
    try:
        user_query = messages[-1]["content"]

        # Get RAG context (may be empty)
        rag_context = get_rag_context(user_query)

        system_prompt = f"""
You are a helpful AI assistant.

Guidelines:
- Respond naturally to greetings and casual conversation.
- If relevant document context is available, use it to answer accurately.
- The documents may relate to a clinic, doctors, services, or appointments.
- Do NOT force the conversation toward booking unless the user explicitly intends it.
- If the answer is not present in the documents, respond using general knowledge.

Document Context (if any):
{rag_context}
"""

        formatted_messages = [SystemMessage(content=system_prompt)]

        # Use last 20 messages for short-term memory
        for msg in messages[-20:]:
            if msg["role"] == "user":
                formatted_messages.append(HumanMessage(content=msg["content"]))
            else:
                formatted_messages.append(AIMessage(content=msg["content"]))

        response = chat_model.invoke(formatted_messages)
        return response.content

    except Exception as e:
        return "⚠️ Something went wrong while generating a response. Please try again."




def booking_started(booking):
    return any(
        v is not None for k, v in booking.items() if k not in ["confirmed"]
    )


import json


def extract_booking_from_pdf(query, chat_model):
    """
    Uses RAG context + LLM to extract booking-related fields from PDFs.
    Clinic-aware, but scoped ONLY to extraction (no effect on general chat).
    Returns a dictionary with extracted values (may be partial).
    """

    rag_context = get_rag_context(query)

    # If no relevant PDF content, exit early
    if not rag_context.strip():
        return {}

    extraction_prompt = f"""
You are an information extraction assistant.

The text below may contain clinic appointment booking details written in natural language.
Your task is to extract structured booking information if present.

Fields to extract:
- name            (patient name)
- email
- phone
- booking_type    (type of consultation or appointment)
- date
- time

Important rules:
- Return ONLY a valid JSON object.
- Use null if a field is missing.
- Do NOT guess or assume values.
- Convert dates to YYYY-MM-DD format.
- Convert time to HH:MM (24-hour format).

Field interpretation rules:
- "Mail" or "Email ID" means email
- "Contact number", "Mobile", or "Phone" means phone
- "Consultation", "Appointment", or "Visit" means booking_type
- Doctor name is NOT the patient name
- Ignore words like "Preferred" or "Tentative"

Text:
{rag_context}
"""

    response = None  # IMPORTANT: prevents UnboundLocalError

    try:
        response = chat_model.invoke([
            HumanMessage(content=extraction_prompt)
        ])

        raw = response.content.strip()

        # Clean markdown-style JSON if present
        if raw.startswith("```"):
            raw = raw.replace("```json", "").replace("```", "").strip()

        extracted = json.loads(raw)

        # Ensure only expected keys are returned
        allowed_keys = {"name", "email", "phone", "booking_type", "date", "time"}
        cleaned = {k: extracted.get(k) for k in allowed_keys}

        return cleaned

    except Exception as e:
        # Safe fallback + debug logging
        print("❌ Booking extraction failed")
        if response:
            print("LLM output:", response.content)
        print("Error:", e)
        return {}


def merge_booking_data(extracted, booking):
    """
    Merge extracted PDF booking details into booking state
    without overwriting existing user-provided values.
    """
    if not extracted:
        return

    for key in ["name", "email", "phone", "booking_type", "date", "time"]:
        if booking.get(key) is None and extracted.get(key):
            booking[key] = extracted[key]

def is_confirmation_intent(text):
    text = text.lower().strip()
    return text in ["yes", "confirm", "confirmed", "okay", "ok", "proceed", "done"]


def chat_page():
    """Main chat interface page"""
    st.title("🩺 AI Clinic Booking Assistant")

    # ---------- PDF UPLOAD ----------
    with st.container():
        st.subheader("📄 Upload Reference Documents")
        st.caption("Upload brochures, forms, or documents for AI-powered Q&A")

        uploaded_files = st.file_uploader(
            "Upload one or more PDFs",
            type=["pdf"],
            accept_multiple_files=True
        )


    if uploaded_files and "vector_store" not in st.session_state:
        with st.spinner("Processing PDFs..."):
            pdf_paths = []
            for file in uploaded_files:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(file.read())
                    pdf_paths.append(tmp.name)

            st.session_state.vector_store = build_vector_store(pdf_paths)
            st.success("PDFs processed successfully!")

    st.divider()

    # ---------- LLM ----------
    chat_model = get_chatgroq_model()

    # ---------- CHAT MEMORY ----------
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # ---------- BOOKING STATE ----------
    if "booking_data" not in st.session_state:
        st.session_state.booking_data = {
            "started": False,
            "name": None,
            "email": None,
            "phone": None,
            "booking_type": None,
            "date": None,
            "time": None,
            "confirmed": False
        }

    booking = st.session_state.booking_data

    # ---------- DISPLAY CHAT HISTORY ----------
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # ---------- CHAT INPUT ----------
    if prompt := st.chat_input("Type your message here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):

                # 🔹 CASE 1: Booking not started → detect intent
                if (
                    not booking["started"]
                    and (
                        is_booking_intent(prompt)
                        or refers_to_uploaded_document(prompt)
                    )
                ):
                    booking["started"] = True
                    extracted = extract_booking_from_pdf(prompt, chat_model)
                    merge_booking_data(extracted, booking)

                    missing = get_missing_fields(booking)
                    response = (
                        next_booking_question(missing[0])
                        if missing
                        else booking_summary(booking)
                    )
                # 🔹 CASE 2: Booking in progress
                elif booking["started"] and not booking["confirmed"]:
                    missing = get_missing_fields(booking)

                    # ---- Confirmation stage ----
                    if not missing:
                        if is_confirmation_intent(prompt):
                            try:
                                booking_id = save_booking(booking)
                                booking["confirmed"] = True
                            except ValueError as e:
                                booking["time"] = None
                                response=f"⚠️ {str(e)} Please choose a different time."
                                st.markdown(response)
                                return
                            email_sent = send_confirmation_email(
                                booking["email"],
                                booking_id,
                                booking
                            )

                            if email_sent:
                                response = f"""
                            
✅ **Appointment Confirmed Successfully**

Thank you, **{booking['name']}**. Your appointment has been scheduled with the following details:

🩺 **Service:** {booking['booking_type']}  
📅 **Date:** {booking['date']}  
⏰ **Time:** {booking['time']}  

📧 A confirmation email has been sent to **{booking['email']}**.

"""                 
                            else:
                                response = f"""
✅ **Appointment Confirmed**

Your appointment has been successfully scheduled.

⚠️ We were unable to send the confirmation email at the moment.
However, your booking is confirmed and safely recorded.

🩺 **Service:** {booking['booking_type']}  
📅 **Date:** {booking['date']}  
⏰ **Time:** {booking['time']}  

Please keep this information for your reference.
"""         


                            # 🔁 Reset booking state after completion
                            st.session_state.booking_data = {
                                "started": False,
                                "name": None,
                                "email": None,
                                "phone": None,
                                "booking_type": None,
                                "date": None,
                                "time": None,
                                "confirmed": False
                            }

                        elif prompt.lower() in ["no", "cancel"]:
                            st.session_state.booking_data = {
                                "started": False,
                                "name": None,
                                "email": None,
                                "phone": None,
                                "booking_type": None,
                                "date": None,
                                "time": None,
                                "confirmed": False
                            }
                            response = "❌ Appointment cancelled. You can start again anytime."
                        else:
                            response = booking_summary(booking)

                    # ---- Slot filling stage ----
                    else:
                        field = missing[0]
                        is_valid, error_msg = validate_field(field, prompt, booking)

                        if not is_valid:
                            response = error_msg
                        else:
                            booking[field] = prompt
                            remaining = get_missing_fields(booking)
                            response = (
                                next_booking_question(remaining[0])
                                if remaining
                                else booking_summary(booking)
                            )

                # 🔹 CASE 3: Normal chat (RAG)
                else:
                    response = get_chat_response(
                        chat_model,
                        st.session_state.messages
                    )

                st.markdown(response)

        st.session_state.messages.append(
            {"role": "assistant", "content": response}
        )

        # ---------- LIMIT MEMORY TO LAST 25 MESSAGES ----------
        st.session_state.messages = st.session_state.messages[-25:]



def main():
    init_db()
    st.set_page_config(
        page_title="🩺 AI Clinic Booking Assistant",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # ---------- SIDEBAR ----------
    with st.sidebar:
        st.markdown("## 🩺 AI Clinic Booking Assistant")
        

        st.divider()
        st.sidebar.caption("© 2026 AI Clinic Booking Assistant")
       #st.markdown(
    #"<small style='color:gray'>© 2026 AI Booking Assistant</small>",
    #unsafe_allow_html=True
    #)
        if st.sidebar.button("🗑️ Reset Database"):
            clear_database()
            st.success("Database cleared successfully.")


        # Navigation buttons
        if st.button("💬 Chat", use_container_width=True):
            st.session_state.page = "chat"

        if st.button("🛠️ Admin Dashboard", use_container_width=True):
            st.session_state.page = "admin"

        st.divider()

        # Optional utility
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    # ---------- PAGE ROUTING ----------
    if "page" not in st.session_state:
        st.session_state.page = "chat"

    if st.session_state.page == "chat":
        chat_page()
    elif st.session_state.page == "admin":
        admin_dashboard()

if __name__ == "__main__":
    main()