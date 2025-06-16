
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
Open Terminal / CMD in the root directory of your project (e.g. AgricareAI)

Initialize Git (if not already done)

bash
Copy
Edit
git init
Add GitHub as the remote origin

bash
Copy
Edit
git remote add origin https://github.com/RajeshBasnet-dev/AgricareAI.git
Stage all files

bash
Copy
Edit
git add .
Commit with a meaningful message

bash
Copy
Edit
git commit -m "Initial commit: AgriCareAI - AI crop disease detection with Django + Gemini Vision API"
Set the default branch to main

bash
Copy
Edit
git branch -M main
Push to GitHub

bash
Copy
Edit
git push -u origin main

📜 License
This project is open-source and free to use under the MIT License.
