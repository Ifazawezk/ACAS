# ACAS - Advanced Comment Analysis System 🎯

A modern, fully-featured comment analysis platform with sentiment detection, routing, and comprehensive dashboard built with FastAPI and React.

## ✨ Key Features

### 🔐 Authentication & Security
- **Secure JWT-based authentication** with bcrypt password hashing
- **Three user roles**: Admin, Manager, User
- **Username-based login** with optional email
- **Profile management** with role display
- Automatic logout on token expiration

### 🌍 Internationalization (i18n)
- **Full Arabic & English support**
- **RTL (Right-to-Left) support** for Arabic
- **Language switcher** in both login and dashboard
- **90+ translated strings** including UI, errors, and messages
- Persistent language preference (localStorage)

### 📊 Dashboard
- **Real-time analytics** with charts and metrics
- **6 comprehensive tabs**: Overview, Comments, Tickets, Analytics, Reports, Help
- **KPI widgets** showing total comments, tickets, sentiment, active users
- **Interactive charts**:
  - Sentiment distribution (Doughnut chart)
  - Comments timeline (Line chart)
  - Routing categories (Pie chart)
  - Ticket status (Bar chart)
- **Responsive design** for mobile and desktop
- **Dark mode support** with theme switcher

### 💬 Comment Management
- View and analyze all comments
- Sentiment classification (Positive, Neutral, Negative)
- Automatic routing to categories
- Comment filtering and search
- Multiclass emotion detection

### 🎫 Ticket System
- Create and manage support tickets
- Status tracking (Open, In Progress, Closed)
- Priority levels
- Assignment tracking
- Automatic ticket generation from comments

### 👥 User Management
- Role-based access control (RBAC)
- User profile management
- Account registration with role selection
- Manager account provisioning
- Default demo accounts for testing

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip or poetry
- SQLite3

### Installation

1. **Clone and setup**:
   ```bash
   cd advanced_comment_analysis
   python -m venv .venv
   .venv\Scripts\activate  # On Windows
   source .venv/bin/activate  # On macOS/Linux
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize database**:
   ```bash
   python tools/seed_users.py
   ```

4. **Start the server**:
   ```bash
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

5. **Access the application**:
   - **Login**: http://127.0.0.1:8000/frontend/login_improved.html
   - **Dashboard**: http://127.0.0.1:8000/frontend/dashboard_improved.html
   - **API Docs**: http://127.0.0.1:8000/docs

---

## 👤 Default Accounts

| Role | Username | Password | Use Case |
|------|----------|----------|----------|
| 👔 Manager | `maha_ebeid` | `<SEED_MANAGER_PASSWORD>` | Manager demo account |
| 👨‍💼 Admin | `admin` | `admin@123` | System administration |
| 👤 User | `demo_user` | `demo@123` | Regular user testing |

---

## 📁 Project Structure

```
advanced_comment_analysis/
├── app/
│   ├── main.py                 # FastAPI app entry point
│   ├── api/
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── comments.py        # Comment endpoints
│   │   ├── tickets.py         # Ticket endpoints
│   │   └── ...
│   ├── models/
│   │   ├── user.py            # User model with 3 roles
│   │   ├── comment.py         # Comment model
│   │   ├── ticket.py          # Ticket model
│   │   └── ...
│   ├── schemas/
│   │   ├── auth.py            # Auth request/response schemas
│   │   ├── comment.py         # Comment schemas
│   │   └── ...
│   ├── services/
│   │   ├── auth_service.py    # Auth business logic
│   │   ├── ai_service.py      # Sentiment analysis
│   │   └── ...
│   ├── utils/
│   │   ├── security.py        # JWT & password hashing
│   │   ├── logging_config.py  # Logging setup
│   │   └── ...
│   └── database/
│       └── session.py         # Database connection
├── frontend/
│   ├── login_improved.html    # 🆕 Professional login page with i18n
│   ├── dashboard_improved.html # 🆕 Modern dashboard with i18n
│   ├── static_index.html      # Original dashboard (legacy)
│   ├── login.html             # Original login page (legacy)
│   ├── i18n.js               # 🆕 Internationalization system
│   ├── translations/
│   │   ├── en.json           # 🆕 English translations
│   │   ├── ar.json           # 🆕 Arabic translations
│   │   └── ...
│   └── static/
│       ├── styles.css        # Static assets
│       └── ...
├── tools/
│   ├── seed_users.py         # Create default user accounts
│   ├── seed_demo_db.py       # Load sample data
│   ├── endpoint_test.py      # API testing
│   └── ...
├── tests/
│   ├── test_ai_service.py    # Service tests
│   └── ...
├── data/
│   └── dev.db               # SQLite database (auto-created)
└── requirements.txt          # Python dependencies
```

---

## 🔌 API Endpoints

### Authentication

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/auth/register` | Create new account |
| POST | `/auth/token` | Login and get JWT token |
| GET | `/auth/me` | Get current user profile |

**Request Body (Register)**:
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123",
  "role": "user"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user_id": 1,
  "username": "john_doe",
  "role": "user"
}
```

### Comments

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/comments/` | List all comments |
| POST | `/comments/` | Create new comment |
| GET | `/comments/{id}` | Get comment details |
| PUT | `/comments/{id}` | Update comment |
| DELETE | `/comments/{id}` | Delete comment |

### Tickets

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/tickets/` | List all tickets |
| POST | `/tickets/` | Create ticket |
| GET | `/tickets/{id}` | Get ticket details |
| PUT | `/tickets/{id}` | Update ticket status |

---

## 🌍 Translation System (i18n)

### Features
- Easy multi-language support
- Dynamic language switching without page reload
- RTL/LTR automatic detection
- Persistent language preference
- 90+ translated strings

### How to Use

**In HTML** (data attributes):
```html
<h1 data-i18n="dashboard.title">Dashboard</h1>
<input placeholder="Username" data-i18n-placeholder="auth.username">
```

**In JavaScript**:
```javascript
// Get translated string
const text = i18n.t('auth.login'); // Returns "Login" or "تسجيل الدخول"

// With parameters
const greeting = i18n.tf('greeting', { name: 'John' });

// Switch language
await i18n.switchLanguage('ar'); // Switch to Arabic

// Check current language
if (i18n.isArabic()) { /* RTL styles */ }
```

### Supported Languages
- **English** (en) - Left-to-Right
- **Arabic** (ar) - Right-to-Left

### Adding New Translations
1. Edit `frontend/translations/en.json` and `frontend/translations/ar.json`
2. Add new keys following the existing structure
3. Use in HTML with `data-i18n="key.path"` or in JS with `i18n.t('key.path')`

---

## 🎨 Styling & Theme

### Modern Design Features
- **Gradient backgrounds** using CSS variables
- **Smooth animations** and transitions
- **Glass-morphism effects** with backdrop blur
- **Responsive grid layout** for all screen sizes
- **Dark mode** by default, with light mode toggle
- **Professional color scheme**:
  - Primary: `#667eea` (Purple)
  - Secondary: `#764ba2` (Deep Purple)
  - Success: `#4caf50`
  - Warning: `#ff9800`
  - Danger: `#f44336`

### RTL Support
- Automatic text direction switching
- Responsive sidebar for mobile
- Proper spacing for Arabic text
- Icons adapt to RTL context

---

## 🔒 Security Features

### Password Security
- Bcrypt hashing (industry standard)
- Password strength indicator during registration
- Minimum 6 character requirement
- Validation on both client and server

### Authentication
- JWT tokens with expiration
- Automatic logout on token expiration
- Secure token storage in localStorage
- CORS support for cross-origin requests

### Input Validation
- Server-side validation for all inputs
- Email format verification
- Username uniqueness check
- File size limits for uploads

---

## 📊 Data Models

### User
```python
{
  "id": int,
  "username": str (unique, required),
  "email": str (optional),
  "hashed_password": str,
  "role": enum ["admin", "manager", "user"],
  "is_active": bool,
  "created_at": datetime
}
```

### Comment
```python
{
  "id": int,
  "content": str,
  "sentic_scores": dict,
  "multiclass_emotion": str,
  "final_route_category": str,
  "certainty_score": float,
  "created_at": datetime,
  "updated_at": datetime
}
```

### Ticket
```python
{
  "id": int,
  "comment_id": int,
  "title": str,
  "description": str,
  "status": enum ["open", "in_progress", "closed"],
  "priority": str,
  "assigned_to": int (user_id),
  "created_at": datetime,
  "closed_at": datetime
}
```

---

## 🧪 Testing

### Run Tests
```bash
pytest tests/
pytest tests/test_ai_service.py -v
```

### Test Endpoints
```bash
python tools/endpoint_test.py
python tools/smoke_test.py
```

---

## 📝 Environment Variables

Create a `.env` file in the root directory:

```env
# Database
DATABASE_URL=sqlite:///./data/dev.db

# JWT
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# OpenAI (for sentiment analysis)
OPENAI_API_KEY=your-api-key-here

# CORS
ALLOWED_ORIGINS=["http://localhost:3000", "http://127.0.0.1:8000"]
```

---

## 🐛 Troubleshooting

### Issue: Login page not loading
**Solution**: Ensure `/frontend/login_improved.html` is accessible. Check that the server is running on port 8000.

### Issue: Charts not displaying
**Solution**: The dashboard includes fallback sample data. Check browser console for API errors. Ensure auth token is valid.

### Issue: Language not switching
**Solution**: Clear browser cache and localStorage. Verify translation files exist in `/frontend/translations/`.

### Issue: Database errors on startup
**Solution**: Delete `data/dev.db` and run `python tools/seed_users.py` again to reinitialize the database.

---

## 🚀 Advanced Usage

### Customize Sentiment Analysis
Edit `app/services/ai_service.py` to change:
- Emotion detection model
- Routing logic
- Score calculations

### Add New User Roles
1. Update `UserRole` enum in `app/models/user.py`
2. Update role options in `frontend/translations/`
3. Add role-based logic in services

### Integrate External APIs
See `app/services/openai_client.py` for API integration patterns.

---

## 📚 Documentation

- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc (Alternative API docs)
- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md)
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Commit changes: `git commit -m 'Add new feature'`
3. Push to branch: `git push origin feature/your-feature`
4. Open Pull Request

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 👥 Team

- **Created by**: Advanced Computing Systems Lab
- **Last Updated**: April 2026
- **Version**: 2.0.0 (Major revision with i18n and improved UI)

---

## 🎉 What's New in v2.0

✅ **Internationalization (i18n)** - Full Arabic & English support  
✅ **Improved Login Page** - Modern design with RTL support  
✅ **Modern Dashboard** - Better layout and responsive design  
✅ **Language Switcher** - Easy toggle between languages  
✅ **Better Error Messages** - User-friendly validation feedback  
✅ **Enhanced Charts** - Improved data visualization  
✅ **Dark Mode Support** - Professional theme switching  
✅ **Mobile Responsive** - Works on all device sizes  
✅ **Bcrypt Security** - Upgraded password hashing  

---

## 📞 Support

For issues and questions:
- 📧 Email: support@acas-system.com
- 🐛 GitHub Issues: [Create an issue]
- 💬 Discussion: [Start a discussion]

---

**Built with ❤️ using FastAPI, SQLAlchemy, and modern JavaScript**

*Last Updated: April 2026*
