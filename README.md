<<<<<<< HEAD
# ai-wellness-planner
=======
# 🚀 AI Wellness Planner

A modern GenAI-powered wellness application that provides personalized meal planning, workout generation, and AI nutrition coaching.

## ✨ Features

- 🍽️ **AI Meal Planning**: Personalized meal plans based on your goals and preferences
- 💪 **Smart Workouts**: AI-generated workout routines tailored to your fitness level
- 🤖 **AI Nutrition Coach**: Chat with an intelligent nutrition assistant
- 📊 **Progress Tracking**: Monitor your health and fitness journey
- 🛒 **Smart Grocery Lists**: Automatically generated shopping lists

## 🛠️ Tech Stack

- **Backend**: Django + Django REST Framework
- **Frontend**: React + Tailwind CSS
- **AI**: DeepSeek API / LocalAI / HuggingFace
- **Nutrition Data**: USDA FoodData Central + Edamam API
- **Database**: PostgreSQL / SQLite
- **Deployment**: Docker + Docker Compose

## 🚀 Quick Start

1. **Clone and setup**:
   ```bash
   git clone <your-repo>
   cd ai-wellness-planner
   cp config/.env.example .env
   # Edit .env with your API keys
   ```

2. **Run with Docker**:
   ```bash
   cd config
   docker-compose up
   ```

3. **Or run manually**:
   ```bash
   # Backend
   cd backend
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py runserver

   # Frontend (new terminal)
   cd frontend
   npm install
   npm start
   ```

4. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - AI Service: http://localhost:8001

## 📚 Documentation

- [API Documentation](docs/API_DOCS.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Contributing Guidelines](docs/CONTRIBUTING.md)

## 🔑 API Keys Setup

Get your free API keys:
- **USDA API**: https://fdc.nal.usda.gov/api-guide.html (Free)
- **DeepSeek API**: https://platform.deepseek.com/ ($10 free credit)
- **Edamam API**: https://developer.edamam.com/ (5000 calls/month free)

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.
>>>>>>> 233f7d6 (initial commit)
