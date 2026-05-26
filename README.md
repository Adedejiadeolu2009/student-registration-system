# 🎓 Student Registration & Attendance System

A comprehensive Python GUI application for managing student registration, attendance tracking, and ID recovery. Built with Tkinter and SQLite3.

## Features

✨ **Student Management**

- Register new students with auto-generated IDs
- View, search, edit, and delete student records
- Store student information (name, age, email, courses)

📍 **Attendance Tracking**

- Real-time check-in/check-out system
- Daily attendance logs with timestamps
- Filter attendance records by date
- Visual status indicators (checked in/out)

🔑 **ID Recovery**

- Search for student IDs by name or email
- One-click copy-to-clipboard functionality
- Helpful prompts for unregistered students

📊 **Live Dashboard**

- Real-time statistics (total students, check-ins today, etc.)
- Most active student tracking
- Today's attendance overview
- One-click refresh

🎨 **Modern UI**

- Dark theme with blue accents
- Responsive tabbed interface
- Smooth hover effects and animations
- Professional color scheme

## Requirements

- Python 3.7 or higher
- tkinter (included with Python)
- sqlite3 (included with Python)

## Installation

1. Clone this repository:

```bash
git clone https://github.com/YOUR_USERNAME/student-registration-system.git
cd student-registration-system
```

2. No additional dependencies needed! (tkinter and sqlite3 are built-in)

## Usage

Run the application:

```bash
python student_registration.py
```

The app will automatically create a `school.db` database file on first run.

## File Structure

```
student-registration-system/
├── student_registration.py   # Main application file
├── school.db                 # SQLite database (created on first run)
├── .gitignore               # Git ignore file
└── README.md                # This file
```

## Features Breakdown

### 👤 Students Tab

- Register new students with auto-generated IDs (STU-0001, STU-0002, etc.)
- View all students in a searchable table
- Edit student information
- Delete student records and associated attendance data

### 🕐 Attendance Tab

- Quick check-in/check-out by student ID
- Press Enter to check in
- Real-time status messages
- Filter attendance logs by date
- View complete attendance history

### 🔑 ID Recovery Tab

- Search students by name or email
- Recover forgotten student IDs
- Copy IDs to clipboard for quick use

### 📊 Dashboard Tab

- Monitor live statistics
- See who's currently checked in
- Track total check-ins for the day
- Identify most active students
- View today's attendance log

## Database Schema

### Students Table

- `id`: Unique student ID (STU-XXXX format)
- `name`: Student's full name
- `age`: Student's age
- `email`: Email address
- `courses`: Comma-separated list of courses
- `registered_at`: Registration timestamp

### Attendance Table

- `record_id`: Auto-increment record ID
- `student_id`: Reference to student ID
- `student_name`: Cached student name
- `check_in`: Check-in time (HH:MM:SS)
- `check_out`: Check-out time (HH:MM:SS)
- `date`: Attendance date (YYYY-MM-DD)
- `status`: 'Checked In' or 'Checked Out'

## Color Scheme

- **Primary Blue**: Buttons, highlights (#4F8EF7)
- **Green**: Check-in, positive actions (#3DDC97)
- **Red**: Delete, danger actions (#F75F5F)
- **Dark Background**: Main UI (#0F1117)
- **Card Background**: Panels (#1A1D27)
- **Input Background**: Text fields (#252836)

## License

This project is open source and available under the MIT License.

## Contributing

Feel free to fork this project, make improvements, and submit pull requests!

## Support

If you encounter any issues, please:

1. Check that Python 3.7+ is installed
2. Ensure tkinter is available on your system
3. Clear the database file (`school.db`) and restart if you encounter database errors

## Author
ADEDEJI JOSEPH ADEOLU

Created as a student registration and attendance management solution.

---

**Last Updated**: May 26, 2026
