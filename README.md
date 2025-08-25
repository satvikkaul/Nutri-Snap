# NutriSnap  

**NutriSnap** is a lightweight calorie and nutrition tracking app powered by computer vision. Users can upload or capture a photo of their meal, and the system estimates the calorie content in real-time using a TensorFlow model trained on the Food-101 dataset.  

---

## 🚀 Features
- **Image Classification:** TensorFlow model in Python recognizing 100+ food categories with ~85% accuracy.  
- **Calorie Mapping:** Custom nutrition database links recognized foods to calorie and macro estimates.  
- **Backend:** FastAPI service validating and processing 500+ image uploads, integrated with PostgreSQL for storing 1,000+ nutrition records across sessions.  
- **Frontend:** React/Vite UI supporting real-time photo capture, upload, and result display with <2s latency per classification via Axios calls.  

---

## 🛠️ Tech Stack
- **Machine Learning:** TensorFlow, Keras, NumPy, Pandas  
- **Backend:** FastAPI, PostgreSQL, SQLAlchemy, Python-Multipart  
- **Frontend:** React, Vite, Axios, SCSS Modules  
- **Infrastructure:** Docker, GitHub Actions (CI), Netlify/Vercel (frontend), Render/Railway (backend)  

---

## 📊 Model
- Dataset: [Food-101](https://data.vision.ee.ethz.ch/cvl/food-101.tar.gz)  
- Classes: 100+ food categories  
- Accuracy: ~85% top-1  
- Inference: <2s per image on CPU  

---

## ⚙️ Setup

### Clone the repository
```bash
git clone https://github.com/<your-username>/NutriSnap.git
cd NutriSnap
```
### Back-End Fast API
```bash
cd backend
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```
API will be live at http://localhost:8000.

### Fron-End React + Vite
```bash
cd frontend
npm install
npm run dev
```
Frontend will be live at http://localhost:5173.


### 🔗 API Endpoints

POST /analyze → Upload an image, returns classification + calorie estimate.

GET /history/{user_id} → Fetch past nutrition records.

GET /health → Health check endpoint.

📷 Screenshots

(Add UI screenshots or GIF demos here once hosted)

📝 Roadmap
Add user authentication and personalized dashboards
Expand the food database beyond Food-101 with regional cuisines
Mobile PWA support for offline calorie estimation
Integrate OCR for packaged food nutrition labels

🤝 Contributing

Contributions, issues, and feature requests are welcome!
Feel free to open an issue or submit a PR.

📄 License

MIT License © 2025 Satvik Kaul
