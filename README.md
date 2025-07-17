# 🗺️ Political Violence Incident Tracker

A real-time web app to monitor political violence incidents across Bangladesh. Visualize events on an interactive map, filter by party/location/casualties, and trigger live crawlers to fetch breaking news.

---

## 🚀 Features

* 🗺️ Interactive Leaflet map with marker clustering
* 🔍 Filter by political party, location, and minimum casualties
* 📊 Real-time stats: total incidents, deaths, injuries, unique locations
* ⚡ One-click crawler triggers (today or custom date range)
* 📱 Fully responsive UI with TailwindCSS & smooth animations
* 🔔 Live notifications for crawl status & user feedback
* 🍔 Mobile-friendly hamburger menu

---

## 🛠️ Tech Stack

* **Frontend**: HTML, TailwindCSS, Vanilla JS, Leaflet.js, FontAwesome
* **Backend**: FastAPI (Python) for API + scraping
* **Data**: JSON via REST endpoints
* **Maps**: OpenStreetMap tiles with Leaflet

---

## 🧪 Local Development

### Backend Setup

1. **Clone repo** and enter backend folder:

   ```bash
   git clone <repo-url>
   cd backend
   ```

2. **Create and activate virtual environment**:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/macOS
   # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Run FastAPI server**:

   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. Open [http://localhost:8000/docs](http://localhost:8000/docs) to explore the API.

---

### Frontend Setup

1. Open `index.html` in your browser *(or use a static server like `live-server`, `http-server`, etc.)*

2. Make sure the `API_BASE` URL in JS points to your backend (default is `http://localhost:8000`).

---

## 🐳 Dockerized Backend

Want no-hassle setup? Docker's got you.

1. **Build image** from root directory:

   ```bash
   docker build -t political-violence-app .
   ```

2. **Run container** exposing port 8000:

   ```bash
   docker run -p 8000:8000 political-violence-app
   ```

3. Backend now live at [http://localhost:8000](http://localhost:8000) — match frontend `API_BASE` to this.


---

## 🧭 Usage Guide

* 🔁 **Crawl Today** — triggers news scraping for today
* 🗓️ **Date Range** — custom date crawler
* 📊 **Statistics** — live incident summary
* 🔎 **Filters** — by party, location, or casualties
* ♻️ **Clear Filters** — resets all filters
* 🧭 **Map Markers** — click to view incident details

---

## 📡 API Endpoints

| Method | Endpoint       | Description                     |
| ------ | -------------- | ------------------------------- |
| `GET`  | `/incidents`   | List all incidents (filterable) |
| `GET`  | `/stats`       | Summary stats                   |
| `GET`  | `/filters`     | Get party/location filters      |
| `POST` | `/crawl`       | Trigger today’s crawl           |
| `POST` | `/crawl/range` | Crawl for custom date range     |

👉 Full docs at `/docs` via Swagger UI.

---

## 📬 Contact

Wanna collab or got feedback?
**Showrin Rahman**
📧 Email: `showrinrahman@example.com` *(replace with real)*
💻 GitHub: [github.com/showrinrahman](https://github.com/showrinrahman)

---
