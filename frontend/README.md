# MyAria-i Frontend

**Autoimmune Research AI Platform** - Clinical-luxe React interface

## Design System

### Color Palette
- **Purple Primary**: `#7B5CF0` - Accents, focus, pills
- **Purple Light**: `#A78BFA` - Hover glow, left panel text
- **Purple Dim**: `rgba(123,92,240,0.12)` - Badge bg, focus ring base
- **Black CTA**: `#0F0F11` - Primary button bg
- **Gray BG**: `#EBEBEE` - Page background
- **Card**: `#F5F5F7` - Main card surface
- **In bg**: `#EFEFF2` - Form fields

### Typography
- **Display/Brand**: Syne 700 - Headings, brand name, CTA
- **Body**: DM Sans 400 - Body copy, labels, form text
- **Medium**: DM Sans 500 - Links, pill text, nav items

### Key Design Rules
1. **Black buttons only** - never purple-filled CTAs. Purple is accent only.
2. **Gray page bg** with slightly lighter card surface - no pure white backgrounds.
3. **Dark left panel** with purple radial blobs - the brand identity side.
4. **All interactive elements** lift `translateY(-1px)` on hover. Never scale.
5. **Focus state always**: border switches to #7B5CF0 + box-shadow focus ring.

## Tech Stack
- **React 18** with Vite
- **Tailwind CSS** - Utility-first styling
- **Lucide React** - Beautiful icons
- **Axios** - API requests with interceptors
- **React Router** - Navigation

## Setup Instructions

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Start Development Server
```bash
npm run dev
```

Frontend will run on: **http://localhost:3000**

### 3. Build for Production
```bash
npm run build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   └── ProtectedRoute.jsx    # Route guard for authentication
│   ├── pages/
│   │   ├── LoginPage.jsx          # Login with dark left panel
│   │   └── DashboardPage.jsx      # Main dashboard with sidebar
│   ├── services/
│   │   └── api.js                 # Axios instance + JWT interceptors
│   ├── App.jsx                    # Router setup
│   ├── main.jsx                   # Entry point
│   └── index.css                  # Tailwind + custom styles
├── index.html                     # HTML template with Google Fonts
├── package.json                   # Dependencies
├── tailwind.config.js             # Design system tokens
└── vite.config.js                 # Vite config with API proxy
```

## API Integration

### Backend Proxy
Vite proxies `/api` requests to FastAPI backend:
```javascript
proxy: {
  '/api': {
    target: 'http://192.168.196.97:8001',
    changeOrigin: true,
  }
}
```

### JWT Authentication Flow
1. **Login** → Store `access_token` + `refresh_token` in localStorage
2. **API Requests** → Axios interceptor adds Bearer token
3. **Token Expires** → Interceptor automatically refreshes using refresh_token
4. **Refresh Fails** → Redirect to login page

### API Endpoints Used
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user
- `GET /api/v1/auth/sessions` - View user sessions
- `POST /api/v1/auth/logout` - Logout (blacklist tokens)
- `POST /api/v1/auth/refresh` - Refresh access token

## Features Implemented

### ✅ Login Page
- Dark left panel with DNA-themed purple blobs
- Light right panel with login form
- Google + LinkedIn social login buttons (UI only)
- Email/password authentication with JWT
- "Remember me" checkbox
- Forgot password link
- Smooth animations (fade-up, staggered features)

### ✅ Dashboard Page
- Fixed sidebar navigation with purple accent
- User profile section with logout
- Active sessions counter
- Recent sessions table with status badges
- Quick action cards for ML workflows
- Real-time token version display

### ✅ Authentication
- JWT token storage in localStorage
- Automatic token refresh on 401 errors
- Protected routes with redirect
- Logout functionality with token revocation

## Design Implementation

### Component Styles
All components follow the clinical-luxe aesthetic:

**Primary CTA Button:**
```jsx
<button className="btn-primary">
  Sign in to MyAria-i
  <ArrowRight className="arrow-icon" />
</button>
```

**Input with Focus State:**
```jsx
<input className="input-field" />
```

**Purple Badge/Pill:**
```jsx
<span className="badge-purple">Active</span>
```

**Ghost/Social Button:**
```jsx
<button className="btn-ghost">
  <GoogleIcon />
  Google
</button>
```

## Testing Credentials

Use existing backend users:
```
Username: testjwt
Password: Test1234!
```

## Next Steps

### Phase 2: Additional Pages
- [ ] User profile page
- [ ] Session management page
- [ ] Admin dashboard (token stats)
- [ ] Dataset upload interface
- [ ] ML model training interface
- [ ] EDA visualization dashboard

### Phase 3: Advanced Features
- [ ] Real-time notifications
- [ ] Dark mode toggle
- [ ] Advanced data visualizations
- [ ] ML model comparison charts
- [ ] Patient data explorer

## Development Notes

### Hot Reload
Vite provides instant HMR (Hot Module Replacement) during development.

### Styling Approach
Using Tailwind utility classes + custom CSS components in `index.css`. The design system tokens are centralized in `tailwind.config.js`.

### Animation
All animations follow the design spec:
- Page enter: `fadeUp 0.6s cubic-bezier(0.22,1,0.36,1)`
- Feature stagger: delays at 0.15s / 0.25s / 0.35s
- Hover lift: `translateY(-1px) 0.14s ease`
- Focus transition: `180ms` for border/shadow

---

**Built with ❤️ for MyAria-i**  
**Autoimmune Research AI Platform**
