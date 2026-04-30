# MyAria-i React Frontend - Quick Start Guide

🎨 **Clinical-Luxe Design System** | Built with React + Tailwind CSS

---

## 🚀 Quick Start (3 Steps)

### Step 1: Install Dependencies
```powershell
cd C:\Users\Syarifah\usm-autoimmune-ml-platform\frontend
npm install
```

### Step 2: Start Development Server
```powershell
npm run dev
```

### Step 3: Open Browser
Navigate to: **http://localhost:3000**

---

## 🎯 What You Get

### ✅ Login Page
- **Dark left panel** with DNA-themed purple gradients
- **Light right panel** with authentication form
- Social login buttons (Google, LinkedIn)
- JWT authentication with backend integration
- Smooth animations and transitions

### ✅ Dashboard Page
- Fixed sidebar navigation with purple accents
- User profile section with logout
- Active sessions monitoring
- Recent login history table
- Quick action cards for ML workflows

### ✅ Authentication System
- JWT token management with automatic refresh
- Protected routes with authentication guards
- Logout with token revocation
- Session monitoring and tracking

---

## 🎨 Design Tokens (Already Configured)

### Colors
```css
Purple Primary: #7B5CF0    /* Accents, borders, focus */
Purple Light:   #A78BFA    /* Hover states, secondary text */
Black CTA:      #0F0F11    /* Primary buttons (never purple!) */
Gray BG:        #EBEBEE    /* Page background */
Card:           #F5F5F7    /* Card surfaces */
Input BG:       #EFEFF2    /* Form fields */
```

### Typography
```css
Headings:  Syne 700       /* Brand name, CTAs, headlines */
Body:      DM Sans 400    /* All body text, labels */
Medium:    DM Sans 500    /* Links, navigation */
```

### Spacing
```css
xs:    6px     sm:   10px     md:   14px
lg:    22px    xl:   32px     2xl:  44px
panel: 64px
```

---

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   └── ProtectedRoute.jsx          # Auth guard
│   ├── pages/
│   │   ├── LoginPage.jsx               # Beautiful login UI
│   │   └── DashboardPage.jsx           # Main dashboard
│   ├── services/
│   │   └── api.js                      # JWT + Axios setup
│   ├── App.jsx                         # React Router
│   ├── main.jsx                        # Entry point
│   └── index.css                       # Global styles
├── package.json                        # Dependencies
├── tailwind.config.js                  # Design tokens
└── vite.config.js                      # Dev server + proxy
```

---

## 🔗 Backend Integration

### API Proxy (Automatic)
Vite automatically proxies `/api` requests to your FastAPI backend:
```
/api/v1/auth/login  → http://192.168.196.97:8001/api/v1/auth/login
```

### JWT Flow
1. **Login** → Get `access_token` + `refresh_token`
2. **Store** in `localStorage`
3. **Auto-add** to all API requests via Axios interceptor
4. **Auto-refresh** when access token expires
5. **Logout** → Revoke tokens on backend + clear localStorage

---

## 📝 Test Credentials

Use your existing backend users:
```
Username: testjwt
Password: Test1234!
```

---

## 🎯 Key Features

### 1. Automatic Token Refresh
```javascript
// Handled automatically by Axios interceptor
// No manual token management needed!
```

### 2. Protected Routes
```javascript
// Automatically redirects to login if not authenticated
<ProtectedRoute>
  <DashboardPage />
</ProtectedRoute>
```

### 3. Session Monitoring
```javascript
// Real-time display of active sessions
// Shows device info, expiry times, status
authAPI.getSessions()
```

---

## 🛠️ Available Scripts

```powershell
npm run dev        # Start dev server (http://localhost:3000)
npm run build      # Build for production
npm run preview    # Preview production build
npm run lint       # Check code quality
```

---

## 🎨 Component Examples

### Primary CTA Button
```jsx
<button className="btn-primary">
  Sign in to MyAria-i
  <ArrowRight className="arrow-icon" />
</button>
```

### Input Field with Icon
```jsx
<div className="relative">
  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 input-icon" />
  <input className="input-field w-full pl-12" placeholder="email@myaria.com" />
</div>
```

### Purple Badge
```jsx
<span className="badge-purple">Active</span>
```

### Ghost Button
```jsx
<button className="btn-ghost">
  <GoogleIcon />
  Google
</button>
```

---

## 🚨 Common Issues

### Issue: `npm install` fails
**Solution:** Update Node.js to latest LTS version (18+)

### Issue: API requests fail
**Solution:** Ensure backend is running on `http://192.168.196.97:8001`

### Issue: Port 3000 already in use
**Solution:** Change port in `vite.config.js`:
```javascript
server: {
  port: 3001,  // Use different port
}
```

---

## 🎯 Next Steps

### Phase 2 - Additional Pages
- [ ] User profile settings
- [ ] Session management page
- [ ] Admin monitoring dashboard
- [ ] Dataset upload interface
- [ ] ML model training UI

### Phase 3 - Advanced Features
- [ ] Real-time notifications
- [ ] Data visualization charts
- [ ] ML model comparison
- [ ] Patient data explorer
- [ ] Advanced analytics dashboard

---

## 📚 Tech Stack

- **React 18.2** - UI library
- **Vite 5.1** - Build tool & dev server
- **Tailwind CSS 3.4** - Utility-first styling
- **React Router 6.22** - Navigation
- **Axios 1.6** - HTTP client with interceptors
- **Lucide React 0.344** - Beautiful icon library

---

## 🎨 Design Philosophy

**"Clinical-Luxe"** - Medical precision meets premium PaaS

### The 3 Core Rules:
1. **Purple is never a fill** - only borders, focus rings, and subtle pills
2. **Gray backgrounds** create depth without heavy shadows
3. **Dark left panel** is the brand identity moment

### Interaction Patterns:
- All buttons/cards **lift** on hover (`translateY(-1px)`)
- Focus states use **purple border + shadow ring**
- Animations use **easing curves**, never linear
- Icons **transition color** on input focus

---

## 🌟 Demo Flow

1. **Open** http://localhost:3000
2. **See** beautiful login page with DNA theme
3. **Login** with testjwt / Test1234!
4. **Explore** dashboard with session monitoring
5. **Check** active sessions table
6. **Click** logout to test token revocation

---

**Built with ❤️ for MyAria-i**  
**Autoimmune Research AI Platform**

Version 1.0 | March 31, 2026
