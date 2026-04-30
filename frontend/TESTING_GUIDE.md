# Sign Up & Login Testing Guide
**Date:** April 2, 2026  
**Component:** Authentication Flow (Sign Up → Login → Dashboard)

---

## 🎯 Pre-Testing Setup

### 1. Start Frontend (if not running)
```powershell
cd C:\Users\Syarifah\usm-autoimmune-ml-platform\frontend
npm run dev
```
**Expected:** Vite dev server starts at http://localhost:3000

### 2. Verify Backend is Running
Backend should be running at: `http://192.168.196.97:8001`

---

## ✅ Test Scenarios

### Test 1: Sign Up Page Navigation
**Steps:**
1. Open http://localhost:3000 → Should redirect to `/login`
2. Click **"Sign up"** button (top right)

**Expected:**
- ✅ Navigates to `/signup`
- ✅ Dark left panel with purple DNA blobs visible
- ✅ Right panel shows "Create your account" form
- ✅ Form has 5 input fields: Full name, Username, Email, Password, Confirm Password
- ✅ Terms checkbox is present
- ✅ "Already have an account? Sign in" link visible

---

### Test 2: Form Validation (Client-Side)
**Steps:** Try submitting empty form

**Expected Errors:**
- ❌ "Full name is required"
- ❌ "Username is required"
- ❌ "Email is required"
- ❌ "Password is required"
- ❌ "You must agree to the Terms and Privacy Policy"

**Steps:** Test individual field validations

| Field | Invalid Input | Expected Error |
|-------|---------------|----------------|
| Username | `ab` (too short) | "Username must be at least 3 characters" |
| Username | `user@123` (special chars) | "Username can only contain letters, numbers, and underscores" |
| Email | `notanemail` | "Please enter a valid email address" |
| Password | `Short1!` (7 chars) | "Password must be at least 8 characters" |
| Password | `lowercase1!` (no uppercase) | "Password must include uppercase, lowercase, number, and special character" |
| Confirm Password | `Different1!` (doesn't match) | "Passwords do not match" |

---

### Test 3: Successful Sign Up
**Test User Data:**
```
Full Name: Test Researcher
Username: testresearcher
Email: testresearcher@myaria.com
Password: ResearchTest2026!
Confirm Password: ResearchTest2026!
☑ Agree to Terms
```

**Steps:**
1. Fill all fields with valid data
2. Check the Terms checkbox
3. Click **"Create account"** button

**Expected:**
- ✅ Button shows "Creating account..." during submission
- ✅ Success: Redirects to `/login`
- ✅ Green success banner appears: "Account created! Please sign in."
- ✅ Banner auto-dismisses after 5 seconds

---

### Test 4: Duplicate User Registration (Error Handling)
**Steps:**
1. Go to `/signup` again
2. Use the SAME email/username from Test 3
3. Submit form

**Expected:**
- ❌ Red error banner appears
- ❌ Error message: "User with this email or username already exists"
- ❌ User stays on signup page
- ❌ Form data is preserved

---

### Test 5: Login with New Account
**Steps:**
1. On login page (after successful signup)
2. Enter credentials:
   - **Username:** `testresearcher`
   - **Password:** `ResearchTest2026!`
3. Click **"Sign in to MyAria-i"**

**Expected:**
- ✅ Button shows "Signing in..." during authentication
- ✅ Success: Redirects to `/dashboard`
- ✅ Dashboard shows user info in sidebar
- ✅ Session table shows active session with device info
- ✅ Stats cards display correct data

---

### Test 6: Forgot Password Link
**Steps:**
1. On login page, click **"Forgot password?"**

**Expected:**
- ✅ Navigates to `/forgot-password`
- ✅ Form accepts email input
- ✅ Dark left panel shows security message about 1-hour expiry

**Steps:** Submit email
1. Enter email: `testresearcher@myaria.com`
2. Click **"Send reset instructions"**

**Expected:**
- ✅ Shows success state with check icon
- ✅ Displays: "Reset link sent! We sent an email to: [email]"
- ✅ **Back to login** button returns to `/login`
- ✅ **Resend** button resets to form view

---

### Test 7: Navigation Between Pages
Test all navigation paths:

| From | Action | To | Works? |
|------|--------|-----|--------|
| `/login` | Click "Sign up" | `/signup` | ✅ |
| `/signup` | Click "Sign in" | `/login` | ✅ |
| `/login` | Click "Forgot password?" | `/forgot-password` | ✅ |
| `/forgot-password` | Click "Back to login" | `/login` | ✅ |
| `/forgot-password` | Submit email → Click "Back to login" | `/login` | ✅ |

---

### Test 8: Protected Route (Dashboard)
**Steps:**
1. Open NEW incognito window
2. Try to access http://localhost:3000/dashboard directly

**Expected:**
- ✅ Redirects to `/login` (no access without authentication)

**Steps:** After login
1. Login with valid credentials
2. Access `/dashboard`

**Expected:**
- ✅ Dashboard loads successfully
- ✅ Sidebar shows username
- ✅ Logout button present

---

### Test 9: Token Persistence (Remember Me)
**Steps:**
1. Login with **"Keep me signed in"** checked
2. Close browser
3. Re-open http://localhost:3000/dashboard

**Expected:**
- ✅ Dashboard loads directly (tokens persist in localStorage)
- ✅ No need to re-login

---

### Test 10: Logout Flow
**Steps:**
1. On dashboard, click **"Logout"** button in sidebar

**Expected:**
- ✅ Redirects to `/login`
- ✅ Tokens removed from localStorage
- ✅ Trying to access `/dashboard` redirects back to login

---

## 🎨 Visual Verification Checklist

### Clinical-Luxe Design Elements
- ✅ Purple accent color (#7B5CF0) on focus states
- ✅ Black CTA buttons (#0F0F11) - NOT purple filled
- ✅ Gray backgrounds: #EBEBEE (page) → #F5F5F7 (card) → #EFEFF2 (inputs)
- ✅ DNA blobs visible in dark panels with purple gradient
- ✅ Syne font for headings ("Create your account", "Welcome back")
- ✅ DM Sans font for body text and form labels
- ✅ Smooth hover animations (translateY -1px lift)
- ✅ Purple focus rings (3px shadow) on input fields
- ✅ Icons transition to purple when input is focused

### Animation Checks
- ✅ Page fade-up animation on load (0.6s cubic-bezier)
- ✅ Feature list staggered fade-in (left panel)
- ✅ Button hover lift effect
- ✅ Arrow icon slides right on button hover
- ✅ Input field smooth focus transition (180ms)

---

## 🐛 Common Issues & Solutions

### Issue 1: "Cannot POST /api/v1/auth/register"
**Cause:** Backend not running or wrong API base URL  
**Fix:** Check backend is at 192.168.196.97:8001

### Issue 2: CORS Error
**Cause:** Backend CORS not configured for localhost:3000  
**Fix:** Add localhost:3000 to backend CORS origins

### Issue 3: "Invalid credentials" after successful signup
**Cause:** Username/password mismatch  
**Fix:** Use exact credentials from signup (case-sensitive)

### Issue 4: Form validation not clearing
**Cause:** React state not updating  
**Fix:** Refresh page (should be auto-fixed in code)

### Issue 5: Success message not showing after signup
**Cause:** useLocation not reading state  
**Fix:** Already implemented in LoginPage with useEffect

---

## 📊 Backend Verification

### Check User Created Successfully
```bash
# SSH to server
ssh shaggy@192.168.196.97

# Access database
docker exec -it usm-autoimmune-postgres psql -U shaggy -d usm_autoimmune_ml

# Query users table
SELECT id, username, email, full_name, role, created_at
FROM users
WHERE username = 'testresearcher';
```

**Expected Output:**
```
 id |    username      |            email                |    full_name     | role |         created_at
----+------------------+---------------------------------+------------------+------+------------------------
  5 | testresearcher   | testresearcher@myaria.com       | Test Researcher  | user | 2026-04-02 ...
```

### Check Password Hash
```sql
SELECT username, hashed_password
FROM users
WHERE username = 'testresearcher';
```

**Expected:** Hashed password should start with `$2b$` (bcrypt hash)

---

## ✅ Test Results Template

Copy and fill this after testing:

```
## Test Results - April 2, 2026

✅ Test 1: Sign Up Page Navigation - PASSED
✅ Test 2: Form Validation - PASSED
✅ Test 3: Successful Sign Up - PASSED
✅ Test 4: Duplicate User Error - PASSED
✅ Test 5: Login with New Account - PASSED
✅ Test 6: Forgot Password Link - PASSED
✅ Test 7: Navigation Between Pages - PASSED
✅ Test 8: Protected Route - PASSED
✅ Test 9: Token Persistence - PASSED
✅ Test 10: Logout Flow - PASSED

Design Verification: ✅ All elements match clinical-luxe spec
Animation Verification: ✅ All animations smooth and correct

Notes:
- 

Issues Found:
- 

Tested by: Syarifah
```

---

## 🎬 Quick Test Script (Happy Path)

**5-Minute Full Flow Test:**
1. Open http://localhost:3000
2. Click "Sign up"
3. Fill form with test data (see Test 3)
4. Submit → See success message on login page
5. Login with new credentials
6. See dashboard load
7. Click logout
8. Back to login page ✅

**All working? Sprint 2 UI Phase Complete!** 🎉
