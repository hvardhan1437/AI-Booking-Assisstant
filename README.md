# 🩺 AI Clinic Booking Assistant



## 🔐 Environment & Secrets Setup

##  Create `.streamlit/secrets.toml`

```toml
GROQ_API_KEY = "your_groq_api_key"

EMAIL_USER = "your_email@gmail.com"
EMAIL_PASS = "your_app_password"
```

---


## ⚠️ IMPORTANT

Use Gmail App Password, NOT your real email password.

Never commit secrets.toml to GitHub.


## 📦 Installation & Setup
### 1️⃣ Clone the Repository
```
git clone https://github.com/<your-username>/AI-Clinic-Booking-Assistant.git
cd AI-Clinic-Booking-Assistant
```

### 2️⃣ Create Virtual Environment
```
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 3️⃣ Install Dependencies
```
pip install -r requirements.txt
```

### ▶️ Run the Application Locally
```
streamlit run app.py
```

### App will be available at:

```
http://localhost:8501
```
---
## 🧪 Sample Usage

1. Upload a clinic PDF (brochure / appointment form)

2. Ask questions like:
```
“What services are available?”
```
3. Book an appointment:
```
“I want to book an appointment”
```
4. Confirm details

5. Receive email confirmation
---
