import re
from datetime import datetime, date, time, timedelta
def validate_name(name):
    if not name or len(name.strip()) < 2:
        return False, "Please enter a valid name (only letters, minimum 2 characters)."

    if not re.fullmatch(r"[A-Za-z ]+", name.strip()):
        return False, "Please enter a valid name (only letters, minimum 2 characters)."

    return True, None

def validate_email(email):
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    if not re.fullmatch(pattern, email.strip()):
        return False, "Please enter a valid email address (e.g., user@example.com)."
    return True, None


def validate_phone(phone):
    if not phone.isdigit() or len(phone) != 10:
        return False, "Phone number must contain exactly 10 digits."
    return True, None


from datetime import datetime, date

def validate_date(input_date):
    try:
        booking_date = datetime.strptime(input_date, "%Y-%m-%d").date()
    except ValueError:
        return False, "Please enter date in YYYY-MM-DD format."

    today = date.today()

    if booking_date <= today:
        return False, "Booking date must be a future date. Past or same-day bookings are not allowed."

    return True, None



def validate_time(input_time, booking_date):
    # ---------- Format check ----------
    try:
        t = datetime.strptime(input_time, "%H:%M").time()
    except ValueError:
        return False, "Please enter time in HH:MM (24-hour) format."

    # ---------- Working hours check (09:00–20:00) ----------
    if t < time(9, 0) or t > time(20, 0):
        return False, "Bookings are allowed only between 09:00 and 20:00."

    # ---------- Date must exist ----------
    if not booking_date:
        return False, "Please select a date before choosing a time."

    # ---------- Same-day past time check ----------
    today = date.today()
    if booking_date == today:
        now = datetime.now().time()
        if t <= now:
            return False, "Selected time has already passed. Please choose a future time."

    return True, None


def validate_field(field, value, booking):
    validators = {
        "name": validate_name,
        "email": validate_email,
        "phone": validate_phone,
        "date": validate_date,
        "time": lambda v: validate_time(v, booking.get("date")),
    }

    if field in validators:
        return validators[field](value)

    return True, None

