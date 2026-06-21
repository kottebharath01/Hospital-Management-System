# CarePoint Hospital Management System

A beginner-friendly hospital management website made with **Python, Flask, SQLite, HTML, CSS, and a little JavaScript**.

## Features

- Dashboard with useful hospital totals
- Add, search, edit, and delete patients
- Add, edit, and delete doctors
- Book appointments and update their status
- Create bills and track paid/unpaid status
- Responsive layout for desktop and mobile
- SQLite database that creates itself with sample data

## Project structure

```text
Hospital Management System/
├── app.py                 # Python application, routes, and database code
├── requirements.txt       # Python package list
├── hospital.db            # Created automatically on first run
├── static/
│   ├── style.css          # Page design
│   └── app.js             # Mobile menu and message behavior
├── templates/
│   ├── base.html          # Shared page layout
│   ├── dashboard.html
│   ├── patients/
│   ├── doctors/
│   ├── appointments/
│   └── bills/
└── .vscode/               # VS Code run settings
```

## Run the project in VS Code

### 1. Open the project

Open VS Code, choose **File → Open Folder**, and select this `Hospital Management System` folder.

You can also open PowerShell in this folder and run:

```powershell
code .
```

### 2. Create a virtual environment

In VS Code, choose **Terminal → New Terminal**, then run:

```powershell
python -m venv .hms-venv
```

If VS Code asks you to select a Python interpreter, choose the one inside `.hms-venv`.

### 3. Activate it

```powershell
.\.hms-venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use this once in the same terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.hms-venv\Scripts\Activate.ps1
```

### 4. Install Flask

```powershell
python -m pip install -r requirements.txt
```

### 5. Start the website

```powershell
python app.py
```

Open <http://127.0.0.1:5000> in your browser. Stop the server with **Ctrl+C**.

You can also press **F5** in VS Code and select **Run Hospital Management System**.

## How the project works

1. A browser requests a page such as `/patients`.
2. Flask runs the matching function in `app.py`.
3. The function reads or changes data in the SQLite database.
4. Flask fills an HTML template with that data.
5. Your browser displays the finished page using `style.css`.

## Reset the sample database

Stop the server, delete `hospital.db`, and run `python app.py` again. A fresh database and sample records will be created automatically.

## Important note

This is an educational project. A real hospital system also needs authentication, permissions, encrypted sensitive data, backups, auditing, tests, and compliance with local healthcare/privacy laws.

## Push the project to GitHub (optional)

Create an empty GitHub repository, then run these commands in the VS Code terminal. Replace the example URL with your repository URL.

```powershell
git init
git add .
git commit -m "Create hospital management system"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/hospital-management-system.git
git push -u origin main
```
