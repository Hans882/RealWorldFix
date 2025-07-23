# Real World Fix 🏙️

A smart civic engagement platform that empowers citizens to report everyday problems like potholes, garbage dumps, broken streetlights, and waterlogging. The platform leverages AI to intelligently cluster similar reports, community voting to prioritize issues, and automated digest reports to keep local government bodies and NGOs informed.

## 🎯 Overview

CivicReport transforms how communities address civic problems by creating a transparent, data-driven approach to issue reporting and resolution. Citizens can easily report problems, vote on priorities, and track progress, while authorities receive organized, actionable insights through automated reports.

## ✨ Key Features

### 📱 Citizen Features

**Issue Reporting**
- Upload photos or use satellite imagery
- Automatic or manual location pinning
- Text input for problem descriptions

**Community Engagement**
- Interactive map view of nearby issues
- Upvote system to highlight priority problems
- Real-time progress tracking

**Progress Tracking**
- Receive updates when issues are resolved
- Status indicators: "Community Resolved" or "Sent to Authority"
- Historical view of personal contributions

### 🤖 AI-Powered Backend

**Smart Clustering Engine**
- NLP-based duplicate detection and merging
- Image similarity analysis for visual clustering
- Geographic clustering (e.g., streetlight issues within 300m radius)
- Automated categorization and tagging

**Image Classification**
- AI-powered problem type detection from photos
- Automatic tagging (pothole, trash, infrastructure, etc.)

**Automated Reporting**
- Weekly digest generation with top issues by area and votes
- Email delivery to city authorities
- PDF export capabilities for official documentation

### 🛠️ Administrative Tools

**Admin Dashboard**
- Comprehensive issue management interface
- Advanced filtering by area, type, date, and status
- Bulk actions and issue resolution tracking

**Authority Integration**
- Direct export to government systems
- Customizable report templates
- Real-time notification system

## 🧠 AI/ML Architecture

| Component | Purpose | Technology Stack |
|-----------|---------|------------------|
| **NLP Clustering** | Merge duplicate reports with similar descriptions | Sentence Transformers + DBSCAN |
| **Image Classifier** | Detect problem types from uploaded photos | MobileNetV2, YOLOv8 |
| **Geo Clustering** | Group nearby reports automatically | Scikit-learn (DBSCAN/HDBSCAN), GeoPy |

## 🏗️ Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React (Web) / Flutter (Mobile) |
| **Backend** | FastAPI / Django REST Framework |
| **Database** | PostgreSQL + PostGIS (geospatial support) |
| **File Storage** | Firebase Storage / AWS S3 |
| **ML Framework** | TensorFlow / PyTorch |
| **NLP Processing** | HuggingFace Transformers, spaCy, Sentence-BERT |
| **Mapping** | Mapbox / Leaflet / Google Maps API |
| **Authentication** | Firebase Auth / OAuth2 |
| **Task Queue** | Celery + Redis |

## 📊 Database Schema

```sql
-- Core Tables
User(id, name, email, location, role, created_at)
Report(id, user_id, title, description, category, photo_url, lat, lng, status, created_at, updated_at)
Vote(id, user_id, report_id, vote_type, created_at)
Comment(id, user_id, report_id, text, created_at)

-- AI/ML Tables
Cluster(id, cluster_id, report_ids, issue_type, center_lat, center_lng, confidence_score)
Classification(id, report_id, predicted_category, confidence, model_version)

-- Administration
Digest(id, week_number, area, top_issues, pdf_url, sent_to, created_at)
Authority(id, name, email, jurisdiction_area, contact_info)
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+ with PostGIS extension
- Redis server

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/civicreport.git
   cd civicreport
   ```

2. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   py -m uvicorn backend.app.main:app --reload
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm start
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Configure database, API keys, and storage settings
   ```

### Environment Variables
```env
DATABASE_URL=postgresql://user:password@localhost/civicreport
REDIS_URL=redis://localhost:6379
MAPBOX_ACCESS_TOKEN=your_mapbox_token
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
SMTP_HOST=your_smtp_host
SMTP_PORT=587
```

## 🌟 Impact & Goals

**Community Empowerment**
- Enable citizen participation in civic improvement
- Create transparent communication channels
- Build community awareness of local issues

**Government Efficiency**
- Reduce manual monitoring overhead
- Provide data-driven insights for resource allocation
- Improve response times through prioritization

**Transparency & Accountability**
- Maintain public records of civic issues
- Track resolution progress publicly
- Enable evidence-based policy decisions
