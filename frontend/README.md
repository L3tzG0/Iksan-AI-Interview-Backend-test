# Interview Preparation Platform – Brief README

## Overview
This platform provides an AI-powered interview practice environment for students, with structured feedback and performance reports. It supports **job interview preparation** and **university admission interview preparation**, while allowing **teachers and admins** to manage student accounts and monitor progress.

---

## User Roles
- **Student**
- **Teacher**
- **Admin**

---

## Student User Flow

### Sign Up & Login
- Students log in using a **system-generated Student ID** (e.g., `00100100001`) and password.
- Student accounts are created by **Teachers or Admins**, either individually or via **CSV bulk upload**.

### Landing Page
After login, students can:
- Start a new interview from **Interview Home**
- View **Session History**

---

### Interview Preparation Types

#### 1. Job Interview Preparation
1. Upload CV / resume / relevant document
2. Select field or industry (e.g., IT, Engineering, Accounting, Nutrition)
3. Enter target position
4. Set answer time per question (optional; penalties apply if exceeded)
5. Start interview
6. System generates:
   - 5 questions based on uploaded documents
   - 5 general job interview questions
7. Answer questions:
   - Questions can be skipped
   - Question 1 must be answered
   - Odd-numbered questions: **verbal only**
   - Even-numbered questions: **text or verbal**
8. Receive results page with scores and AI feedback
9. View session history from Interview Home

---

#### 2. University Admission Interview Preparation
1. Upload student academic record (PDF)
2. Enter up to 3 university choices
3. Enter desired major
4. Set answer time per question (optional; penalties apply if exceeded)
5. Start interview
6. System generates:
   - 5 university-related questions
   - 5 general admission interview questions
7. Answer questions:
   - Questions can be skipped
   - Question 1 must be answered
   - Odd-numbered questions: **verbal only**
   - Even-numbered questions: **text or verbal**
8. Receive results page with scores and AI feedback
9. View session history from Interview Home

---

### Reports & PDF Download
- Students can download a **PDF report** containing:
  - Student name
  - School, grade, and class
  - Major
  - Interview session results
  - Detailed feedback per question

---

## Teacher & Admin User Flow

### Sign Up
- **Teacher Sign Up:** Full name, work email, school (dropdown, auto updated for new data), password
- **Admin Sign Up:** Full name, organization/work name, work email, password
- Email verification handled by **Supabase** (to be implemented in later production stage)

---

### Login & Student Account Management
- Teachers and Admins log in using work email and password
- Access a dashboard showing students’ **latest interview sessions**
- Create student accounts:
  - Individually
  - Bulk upload via CSV

**Required student data:**
- Student name
- School
- Grade year (1 / 2 / 3)
- Class (A / B / C or 1 / 2 / 3)
- Major

**Student ID Generation**
- Pattern: `3-digit SchoolCode + 4-digit MajorCode + 5-digit sequence`
- Example:
  - `001000100001` → School 001, Engineering, first registered student

---

## Dashboards

### Teacher Dashboard
- View table of students’ **latest interview results** (same school only)
- View detailed answers and AI feedback per student
- *Future:* Filters by major and grade

### Admin Dashboard
- View **all students’ latest interview results** across schools
- View detailed results for any student
- View registered teacher accounts (Medium priority)
- *Future:* Filters by school, major, and grade

---

## Notes
- The system is designed to simulate **real interview behavior**, focusing on structured answers, clarity, and role alignment.
- Feedback emphasizes methodology, quantification, and professional communication.

---

## Deploy to Netlify

### Prereqs
- Push this repo to GitHub (or GitLab/Bitbucket) so Netlify can connect to it.

### Netlify settings
In Netlify:
1. **Add new site** → **Import an existing project**
2. Select your git provider + repository
3. Set:
   - **Base directory**: (leave empty)
   - **Build command**: `npm run build`
   - **Publish directory**: `dist`
4. Add environment variables (Site configuration → Environment variables):
   - `VITE_API_BASE` (optional; defaults to the Railway backend URL already in code)
5. Deploy

### Notes / troubleshooting
- This app uses React Router (`BrowserRouter`). Netlify needs an SPA fallback redirect so deep links like `/teacher/home` load correctly. This repo includes that via `netlify.toml`.
- If you set `VITE_API_BASE`, use an absolute URL including protocol (e.g. `https://iksan-ai-interview-backend-production.up.railway.app`). A value without `https://` can be treated as a relative path and end up prefixed by the current route.
