
# 🌿 AgriCareAI – Crop Disease Detection Platform

AgriCareAI is an AI-powered web platform designed to help farmers and agricultural professionals detect crop diseases quickly by uploading plant or leaf images. It uses Google’s Gemini Vision API to analyze the image and return disease diagnosis, explanation, confidence, and treatment advice — all in real time.

---

## 🚀 Features

- 📷 Upload crop or plant images
- 🤖 AI-powered disease detection using Gemini Vision API
- ✅ Returns:
  - Plant type
  - Disease name
  - Confidence level (%)
  - Detailed explanation
  - Cure/Treatment suggestions
- 💾 Saves analysis results and images in PostgreSQL
- 🖼️ Media stored locally
- 🧪 Mock response if API fails or not configured

---

## 🧠 Tech Stack

| Component       | Technology                         |
|----------------|-------------------------------------|
| Backend         | Django, Django REST Framework       |
| AI Model        | Google Gemini Vision API            |
| Frontend        | HTML, CSS, Bootstrap                |
| Database        | PostgreSQL                          |
| Storage         | Local media/ directory              |


---

## 🔧 Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone https://github.com/RajeshBasnet-dev/agricareai.git
   cd agricareai
Create Virtual Environment

bash
Copy
Edit
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install Requirements

bash
Copy
Edit
pip install -r requirements.txt
Set up .env file

ini
Copy
Edit
GEMINI_API_KEY=your_google_gemini_api_key
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
Run Migrations

bash
Copy
Edit
python manage.py makemigrations
python manage.py migrate
Run Server

bash
Copy
Edit
python manage.py runserver

📜 License
This project is open-source and free to use under the MIT License.
