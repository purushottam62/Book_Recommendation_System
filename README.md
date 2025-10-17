# 📚 Book Recommendation System using STAMP

## 🧠 Overview
This project is developed as part of the **Intelligent Computing Project**.  
It implements a **Book Recommendation System** using the **STAMP (Short-Term Attention/Memory Priority)** model.  
The system intelligently recommends books based on user interaction sequences and preferences derived from the Kaggle dataset.

## 🚀 Features
- Personalized book recommendations based on user history.
- Implementation of **STAMP** model for sequence-based recommendation.
- Data preprocessing and feature extraction from Kaggle dataset.
- Integration-ready backend for recommendation API.
- Interactive frontend for exploring book suggestions.

## 🗂️ Tech Stack
- **Machine Learning:** STAMP model (TensorFlow / PyTorch)
- **Backend:** Django / FastAPI (for API serving)
- **Frontend:** React.js
- **Database:** SQLite / PostgreSQL
- **Dataset Source:** Kaggle Book Recommendation Dataset

## 👨‍💻 Team Members

| Role | Name | Roll Number | GitHub ID |
|------|------|--------------|-----------|
| ⭐ **Team Leader & ML Analyst (Backend)** | **Atul Kumar Pandey** | 23074006 | [Atul625-py](https://github.com/Atul625-py) |
| 🤝 **Frontend & Backend Developer** | **Chukka Chamantej** | 23074028 | [Chamantej](https://github.com/Chamantej) |
| 🎨 **Frontend & Backend Developer** | **Purushottam Lal** | 23075061 | [Purushottam620xyz](https://github.com/Purushottam620xyz) |

## 📈 Model Summary (STAMP)
STAMP (Short-Term Attention/Memory Priority) captures both **short-term interests** and **long-term preferences** of users.  
It uses attention mechanisms to model recent behavior patterns, making it ideal for sequential recommendation tasks.

## 🧩 Folder Structure
```
BookRecommendationSystem/
│
├── data/                # Kaggle dataset files
├── model/               # STAMP model training scripts
├── backend/             # API & server logic
├── frontend/            # React frontend code
├── notebooks/           # Jupyter experiments and analysis
└── README.md
```

## ⚙️ Setup Instructions
1. Clone this repository:
   ```bash
   git clone https://github.com/Atul625-py/BookRecommendationSystem.git
   cd BookRecommendationSystem
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the backend:
   ```bash
   python manage.py runserver
   ```
4. Start the frontend:
   ```bash
   npm start
   ```

## 📊 Dataset Source
[Kaggle - Book Recommendation Dataset](https://www.kaggle.com/datasets/arashnic/book-recommendation-dataset)

## 🧩 Future Scope
- Add hybrid recommendation (content + collaborative).
- Include multilingual support for book titles.
- Deploy with Docker and integrate with cloud storage.
- Add user authentication and dynamic profiling.

---

### 🧑‍🏫 Project for Intelligent Computing Course
**IIT (BHU) Varanasi**
