# resume-ats-scanner
AI-powered Resume ATS Scanner that analyzes resumes against job descriptions using NLP and pretrained models. It generates ATS compatibility scores, identifies skill gaps, and provides intelligent suggestions to improve resume quality.

# Best View in Light Mode and Desktop Site (Recommended)

# 🤖 AI Resume ATS Scanner & Compatibility Analyzer

### 🌴 A Smart AI Tool for Resume Analysis, ATS Scoring & Job Matching 🌴

![GitHub repo size](https://img.shields.io/github/repo-size/your-username/your-repo)
![GitHub stars](https://img.shields.io/github/stars/your-username/your-repo)
![License](https://img.shields.io/badge/license-MIT-blue)

🔗 **View Demo** · **Installation** · **Documentation**

---

## 🚀 Built by Dnyanesh Patil

### (AI/ML Engineer | Data Science Enthusiast)

---

## 📌 About the Project

This project simulates a **real-world Applicant Tracking System (ATS)** used by companies to filter resumes.

The system analyzes resumes against job descriptions using **NLP + Pretrained AI Models**, calculates ATS compatibility scores, identifies skill gaps, and provides intelligent suggestions to improve resumes.

It is designed to be **accurate, scalable, and industry-ready**.

---

## 🧠 Key Features

### 📄 Resume Analysis

* Extracts information from PDF resumes
* Parses:

  * Skills
  * Experience
  * Education
  * Projects
  * Certifications
* Uses **spaCy + NLP + OCR fallback**

---

### 📊 ATS Scoring System

* Generates **ATS Compatibility Score (0–100%)**
* Provides:

  * Skill Match %
  * Keyword Match %
  * Experience Relevance Score
  * Education Match Score
  * Formatting Score

---

### 🎯 Skill Matching Engine

* Exact matching
* Synonym matching (ML → Machine Learning)
* Semantic similarity (Sentence Transformers)
* TF-IDF keyword matching
* Missing skills detection

---

### ⚠️ Skill Gap Analysis

* Shows:

  * Matched skills
  * Missing skills
  * Recommended skills to add

---

### 🧾 ATS Resume Checker

* Detects:

  * Bad formatting
  * Missing sections
  * Poor structure
  * ATS-unfriendly elements

---

### ✨ AI Resume Improvement Mode

* Suggests:

  * Better bullet points
  * Strong action verbs
  * Improved project descriptions
  * Resume optimization tips

---

### 📥 PDF Report Generation

* Download professional ATS report including:

  * Score breakdown
  * Skill analysis
  * Suggestions

---

## 🎯 Scope

i. Helps candidates improve resumes based on ATS standards
ii. Provides structured resume insights for recruiters
iii. Can be used by colleges for placement analysis
iv. Enables resume benchmarking against job roles
v. Useful for career guidance and skill improvement
vi. Can be extended into SaaS product

---

## 🛠️ Tech Stack

### 🔹 Frontend

* React.js
* Tailwind CSS

### 🔹 Backend

* FastAPI

### 🔹 AI / ML / NLP

* spaCy (`en_core_web_lg`)
* Sentence Transformers (`all-mpnet-base-v2`)
* TF-IDF + Cosine Similarity
* Skill Ontology Dataset

### 🔹 Tools & Libraries

* pdfplumber
* pytesseract (OCR)
* reportlab
* rapidfuzz

### 🔹 Database (Optional)

* MongoDB

---

## ⚙️ Features Breakdown

### 👤 User Side

* Upload Resume PDF
* Input Job Description
* Get ATS Score Dashboard
* View:

  * Matched Skills
  * Missing Skills
  * Suggestions
* Download ATS Report

---

### 📊 Analysis Includes

* Skill Matching
* Keyword Matching
* Experience Relevance
* Education Matching
* Resume Formatting Check

---

## 📂 Project Structure

```
resume_ats_scanner/
│── backend/
│── frontend/
│── dataset/
│── sample_data/
│── README.md
```

---

## 🧪 Requirements

* Python 3.9+
* Node.js
* MongoDB (optional)
* Tesseract OCR installed

---

## ⚡ Setup & Installation

1. Backend Setup
cd resume_ats_scanner/backend
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac

1. pip install -r requirements.txt
python -m spacy download en_core_web_lg
2. Create Sample Resume (Optional)
cd resume_ats_scanner
pip install reportlab
python create_sample_resume.py
3. Frontend Setup
cd resume_ats_scanner/frontend
npm install
4. Environment (Optional)
cp .env.example .env
# Add OPENAI_API_KEY for AI enhancement (optional)
# Add MONGODB_URI for database (optional)
Running the Application
Terminal 1 - Backend
cd resume_ats_scanner/backend
python main.py

Terminal 2 - Frontend
cd resume_ats_scanner/frontend
npm run dev

Open: http://localhost:5173



## 🚀 Usage

1. Upload your Resume (PDF)
2. Paste or Upload Job Description
3. Click **Analyze**
4. View ATS Score & Insights
5. Download Report

---

## 🛣️ Roadmap

* Add real-time JD scraping (LinkedIn, Naukri)
* Add multilingual resume support
* Add resume ranking system
* Deploy as SaaS platform
* Add user authentication & dashboard

---

## 🤝 Contributing

Pull requests are welcome.
For major changes, please open an issue first.

---

## 📌 Acknowledgement

* spaCy NLP
* Sentence Transformers
* Open-source NLP community

---

## 💡 Preview

### 📊 Dashboard
<img width="1919" height="878" alt="image" src="https://github.com/user-attachments/assets/16309d1f-124a-4e17-8e36-e0840f32c8f1" />



### 📄 Resume Analysis

<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/f27b232a-64c2-44e0-adcb-32fabfee5a86" />
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/460cd10f-6f7b-4b91-97e4-e738edbffe41" />



---

## ⭐ If you like this project, give it a star!

---

🔥 **Built with passion to bridge the gap between resumes and job opportunities**
