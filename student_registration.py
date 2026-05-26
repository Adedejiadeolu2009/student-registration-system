# ===== IMPORTS =====
# tkinter (tk): Main GUI framework for creating windows, buttons, labels, and other UI elements
import tkinter as tk
# ttk: Provides themed widgets (modern looking buttons, tabs, treeview), messagebox: For popup dialogs
from tkinter import ttk, messagebox
# sqlite3: Database library for storing and retrieving student data persistently
import sqlite3
# os: For file and directory operations (not actively used in this code)
import os
# datetime: For handling dates and times (timestamps for check-in/check-out)
from datetime import datetime

# ===== THEME CONSTANTS =====
# These color constants define the dark theme used throughout the entire application
# Background colors
BG_DARK = "#0F1117"  # Very dark background for main window (almost black)
BG_CARD = "#1A1D27"  # Slightly lighter background for cards/panels/sections
BG_INPUT = "#252836"  # Background color for input fields (text boxes)
# Accent colors (used to highlight important UI elements)
ACCENT = "#4F8EF7"  # Primary blue accent color for buttons and highlights
# Secondary green accent color for positive actions (check-in)
ACCENT2 = "#3DDC97"
DANGER = "#F75F5F"  # Red color for delete/danger actions (delete button)
# Text colors
# Main text color (light gray, readable on dark background)
TEXT_WHITE = "#EAEAEA"
# Subdued/faded text color for less important info (labels, hints)
TEXT_MUTED = "#7B7F8E"
TEXT_HEAD = "#FFFFFF"  # Heading text color (pure white, highest contrast)
BORDER = "#2C2F3E"  # Color for borders and divider lines between elements
# Font definitions: (font_family, size, [optional: "bold"])
FONT_BODY = ("Consolas", 11)           # Regular body text font (main content)
FONT_HEAD = ("Consolas", 13, "bold")   # Heading font (bold, slightly larger)
# Large title font (bold, for section titles)
FONT_TITLE = ("Consolas", 16, "bold")
# Small text font (for hints and secondary info)
FONT_SMALL = ("Consolas", 9)

# Database file name - this file will store all student and attendance data
DB_FILE = "school.db"

# ===== DATABASE MANAGER CLASS =====
# This class handles all database operations using SQLite3
# It manages student registration, updates, deletion, and attendance records


class DatabaseManager:
    """Handles all SQLite3 database operations."""

    def __init__(self):
        # Establish a connection to the SQLite database file
        self.conn = sqlite3.connect(DB_FILE)
        # Create a cursor object to execute SQL commands
        self.cursor = self.conn.cursor()
        # Create database tables on initialization if they don't exist
        self._create_tables()

    def _create_tables(self):
        """Create tables if they don't already exist. Called once during app startup."""
        # Create 'students' table to store student information
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id            TEXT PRIMARY KEY,        -- Unique student ID (e.g., STU-0001), must be unique
                name          TEXT NOT NULL,         -- Student's full name (required field)
                age           INTEGER,               -- Student's age as a number
                email         TEXT,                  -- Student's email address (optional)
                courses       TEXT,                  -- Comma-separated list of enrolled courses
                registered_at TEXT                  -- Timestamp when student was registered (YYYY-MM-DD HH:MM:SS)
            )
        """)
        # Create 'attendance' table to store check-in/check-out records
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                record_id    INTEGER PRIMARY KEY AUTOINCREMENT,  -- Auto-incrementing unique ID for each record
                student_id   TEXT NOT NULL,                     -- Reference to student ID (links to students table)
                student_name TEXT NOT NULL,                     -- Student's name (cached here for faster display)
                check_in     TEXT,                              -- Check-in time (HH:MM:SS format)
                check_out    TEXT,                              -- Check-out time (HH:MM:SS format)
                date         TEXT,                              -- Date of attendance (YYYY-MM-DD format)
                status       TEXT DEFAULT 'Checked In',         -- Current status: 'Checked In' or 'Checked Out'
                FOREIGN KEY (student_id) REFERENCES students(id)  -- Links this record to a student
            )
        """)
        # Permanently save the changes to the database file
        self.conn.commit()

    # ===== STUDENT ID MANAGEMENT =====
    def generate_student_id(self):
        """
        Auto-generate the next student ID in the format STU-0001, STU-0002, etc.
        This ensures each student gets a unique sequential ID.
        """
        # Query the database for the highest existing student ID
        self.cursor.execute(
            "SELECT id FROM students WHERE id LIKE 'STU-%' ORDER BY id DESC LIMIT 1")
        row = self.cursor.fetchone()  # Get the first (and only) result from the query
        if row:  # If a previous ID exists
            try:
                # Split the ID by "-" and extract the number part (e.g., '0001' from 'STU-0001')
                last_num = int(row[0].split("-")[1])
                # Increment the number by 1 and format it as 4 digits with leading zeros
                # :04d means format as 4-digit number with zeros
                return f"STU-{last_num + 1:04d}"
            except (IndexError, ValueError):
                # If parsing fails, fall through to return the default
                pass
        # Return first ID if no students exist yet in the database
        return "STU-0001"

    # ===== STUDENT SEARCH =====
    def recover_id(self, keyword):
        """
        Find students matching a name or email keyword.
        Used for the ID Recovery feature to help students find their ID.
        Returns a list of matching student records.
        """
        # Add % wildcards to search for partial matches
        # e.g., if keyword is 'john', this becomes '%john%'
        kw = f"%{keyword}%"
        # Query students by name or email that contain the keyword (LIKE = case-insensitive matching)
        self.cursor.execute("""
            SELECT id, name, email, registered_at
            FROM students
            WHERE name LIKE ? OR email LIKE ?  -- Search in both name and email columns
            ORDER BY name                       -- Sort results alphabetically by name
        """, (kw, kw))  # ? are placeholders that get filled with the kw values
        # Return all matching rows
        return self.cursor.fetchall()

    # ===== STUDENT CRUD OPERATIONS (Create, Read, Update, Delete) =====
    def add_student(self, student_id, name, age, email, courses):
        """
        Add a new student to the database.
        Returns a tuple: (success: boolean, message: string explaining the result)
        """
        try:
            # Insert a new student record into the students table
            self.cursor.execute("""
                INSERT INTO students (id, name, age, email, courses, registered_at)
                VALUES (?, ?, ?, ?, ?, ?)  -- ? are placeholders to prevent SQL injection attacks
            """, (
                student_id.upper(),                              # Convert ID to uppercase for consistency
                # Capitalize name properly (e.g., 'John Doe')
                name.title(),
                age,                                             # Student's age as an integer
                email,                                           # Email address
                courses,                                         # Course list
                # Get current date and time as timestamp
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            # Save the insert operation to the database file
            self.conn.commit()
            return True, "Student registered successfully."
        except sqlite3.IntegrityError:
            # This error is raised if the student ID already exists (PRIMARY KEY violation)
            return False, f"ID '{student_id.upper()}' is already registered."

    def get_all_students(self):
        """Retrieve all students from the database, sorted alphabetically by name."""
        self.cursor.execute("""
            SELECT id, name, age, email, courses, registered_at 
            FROM students 
            ORDER BY name  -- Sort results alphabetically
        """)
        # Fetch and return all rows from the query result
        return self.cursor.fetchall()

    def get_student_by_id(self, student_id):
        """
        Retrieve a specific student record by their ID.
        Returns the student record or None if not found.
        """
        self.cursor.execute("""
            SELECT * FROM students 
            WHERE id = ?  -- ? placeholder for the student_id parameter
        """, (student_id.upper(),))  # Convert ID to uppercase for consistency
        # Return the first (and only) matching record
        return self.cursor.fetchone()

    def update_student(self, student_id, name, age, email, courses):
        """Update an existing student's information (name, age, email, courses)."""
        self.cursor.execute("""
            UPDATE students SET        -- Modify an existing record
                name=?,                -- Update the name field
                age=?,                 -- Update the age field
                email=?,               -- Update the email field
                courses=?              -- Update the courses field
            WHERE id=?                 -- Only update the student with this ID
        """, (name.title(), age, email, courses, student_id.upper()))
        # Save the update to the database file
        self.conn.commit()

    def delete_student(self, student_id):
        """
        Delete a student and all their attendance records.
        This ensures data consistency (no orphaned attendance records).
        """
        # Delete student from the students table
        self.cursor.execute("""
            DELETE FROM students 
            WHERE id=?  -- Only delete this specific student
        """, (student_id.upper(),))
        # Also delete all attendance records for this student (cleanup to avoid orphaned data)
        self.cursor.execute("""
            DELETE FROM attendance 
            WHERE student_id=?  -- Remove all check-in/check-out records for this student
        """, (student_id.upper(),))
        # Save both deletions to the database file
        self.conn.commit()

    def search_students(self, keyword):
        """
        Search for students by ID or name. Returns all matching records.
        This is used in the Students tab to find students quickly.
        """
        # Add % wildcards for partial/fuzzy matching
        # e.g., 'stu' will match 'STU-0001', 'student-01', etc.
        kw = f"%{keyword}%"
        # Query for students matching the keyword in ID or name columns
        self.cursor.execute("""
            SELECT id, name, age, email, courses, registered_at
            FROM students 
            WHERE id LIKE ? OR name LIKE ?  -- Search both ID and name columns
            ORDER BY name                   -- Sort alphabetically by name
        """, (kw, kw))
        return self.cursor.fetchall()

    # ===== ATTENDANCE OPERATIONS =====
    def check_in(self, student_id):
        """
        Record a student's check-in time for today.
        Returns a tuple: (success: boolean, message: string)
        """
        # Get the student record to verify the ID exists and get the name
        student = self.get_student_by_id(student_id)
        if not student:
            return False, "Student ID not found."

        # Get today's date in YYYY-MM-DD format
        today = datetime.now().strftime("%Y-%m-%d")
        # Check if this student is already checked in today
        self.cursor.execute("""
            SELECT * FROM attendance
            WHERE student_id=? AND date=? AND status='Checked In'  -- Look for active check-in
        """, (student_id.upper(), today))
        existing = self.cursor.fetchone()
        # If student is already checked in, don't allow duplicate check-in
        if existing:
            return False, f"{student[1]} is already checked in today."

        # Record the current time as check-in time
        now = datetime.now().strftime("%H:%M:%S")  # Format: HH:MM:SS
        # Insert a new attendance record with check-in information
        self.cursor.execute("""
            INSERT INTO attendance (student_id, student_name, check_in, date, status)
            VALUES (?, ?, ?, ?, 'Checked In')  -- Set status as 'Checked In'
        """, (student_id.upper(), student[1], now, today))
        # Save the check-in record
        self.conn.commit()
        return True, f"✅  {student[1]} checked in at {now}"

    def check_out(self, student_id):
        """
        Record a student's check-out time for today.
        Returns a tuple: (success: boolean, message: string)
        """
        # Get today's date
        today = datetime.now().strftime("%Y-%m-%d")
        # Find the student's active check-in record from today
        self.cursor.execute("""
            SELECT record_id, student_name FROM attendance
            WHERE student_id=? AND date=? AND status='Checked In'  -- Find checked-in record
        """, (student_id.upper(), today))
        record = self.cursor.fetchone()
        # If no active check-in found, the student needs to check in first
        if not record:
            return False, "No active check-in found for today."

        # Record the current time as check-out time
        now = datetime.now().strftime("%H:%M:%S")
        # Update the attendance record with check-out time and status change
        self.cursor.execute("""
            UPDATE attendance SET check_out=?, status='Checked Out'  -- Add check-out time
            WHERE record_id=?  -- Update only this record
        """, (now, record[0]))
        # Save the check-out update
        self.conn.commit()
        return True, f"👋  {record[1]} checked out at {now}"

    def get_attendance_log(self, date_filter=None):
        """
        Get attendance records, optionally filtered by date.
        If date_filter is None, get all records; otherwise get only records from that date.
        """
        if date_filter:
            # Query attendance records for a specific date, ordered newest first
            self.cursor.execute("""
                SELECT record_id, student_id, student_name, check_in, check_out, date, status
                FROM attendance WHERE date=? ORDER BY check_in DESC  -- DESC = descending order
            """, (date_filter,))
        else:
            # Query all attendance records, ordered by date (newest first), then by check-in time
            self.cursor.execute("""
                SELECT record_id, student_id, student_name, check_in, check_out, date, status
                FROM attendance ORDER BY date DESC, check_in DESC
            """)
        return self.cursor.fetchall()

    def get_stats(self):
        """
        Get dashboard statistics:
        - Total number of students
        - Number of students checked in today
        - Total check-ins today
        - Most active student (most check-ins)
        """
        # Count total number of students in database
        self.cursor.execute("SELECT COUNT(*) FROM students")
        total_students = self.cursor.fetchone()[0]  # [0] gets the count value

        # Get today's date
        today = datetime.now().strftime("%Y-%m-%d")
        # Count students currently checked in (have check-in but no check-out)
        self.cursor.execute("""
            SELECT COUNT(*) FROM attendance WHERE date=? AND status='Checked In'
        """, (today,))
        checked_in_today = self.cursor.fetchone()[0]

        # Count total check-ins/check-outs today
        self.cursor.execute("""
            SELECT COUNT(*) FROM attendance WHERE date=?
        """, (today,))
        total_today = self.cursor.fetchone()[0]

        # Find the student with the most visits (most active)
        self.cursor.execute("""
            SELECT student_name, COUNT(*) as visits
            FROM attendance GROUP BY student_id ORDER BY visits DESC LIMIT 1
        """)
        top = self.cursor.fetchone()
        # Use "N/A" if no attendance records exist yet
        top_student = top[0] if top else "N/A"

        # Return all statistics as a dictionary for easy access
        return {
            "total_students":   total_students,
            "checked_in_today": checked_in_today,
            "total_today":      total_today,
            "top_student":      top_student,
        }

    def close(self):
        """Close the database connection. Called when app closes to save and release resources."""
        self.conn.close()


# ===== REUSABLE UI HELPER FUNCTIONS =====
# These functions create styled UI components that look consistent throughout the app

def styled_label(parent, text, font=FONT_BODY, fg=TEXT_WHITE, **kw):
    """Create a label with consistent styling. **kw allows extra parameters."""
    return tk.Label(
        parent,
        text=text,                           # Text to display
        font=font,                          # Font to use
        fg=fg,                              # Foreground (text) color
        bg=parent.cget("bg"),               # Background color (matches parent)
        **kw                                # Any other parameters passed in
    )


def styled_entry(parent, textvariable=None, show=None, width=30):
    """Create a text entry field with styling and focus effects."""
    e = tk.Entry(
        parent,
        # Variable to store text content
        textvariable=textvariable,
        font=FONT_BODY,                                    # Font for text
        bg=BG_INPUT,                                       # Input field background color
        fg=TEXT_WHITE,                                     # Text color
        insertbackground=TEXT_WHITE,                       # Cursor color
        relief="flat",                                     # No 3D border effect
        # Border width = 0 (no border)
        bd=0,
        width=width,                                       # Width in characters
        # For passwords, show "*" instead of text
        show=show or ""
    )
    # Change border color when entry field gets focus (user starts typing)
    e.bind("<FocusIn>", lambda ev: e.config(
        highlightthickness=1,           # Show highlight border when focused
        highlightbackground=ACCENT,     # Highlight color
        highlightcolor=ACCENT
    ))
    # Change border color when entry field loses focus (user clicks away)
    e.bind("<FocusOut>", lambda ev: e.config(
        highlightthickness=1,           # Show highlight border when not focused
        highlightbackground=BORDER,     # Normal border color
        highlightcolor=BORDER
    ))
    # Set initial border color (when not focused)
    e.config(highlightthickness=1, highlightbackground=BORDER)
    return e


def styled_button(parent, text, command, color=ACCENT, width=18, **kw):
    """Create a button with styling and hover effects."""
    btn = tk.Button(
        parent,
        text=text,                         # Button label text
        command=command,                   # Function to call when clicked
        font=FONT_BODY,                    # Font for button text
        bg=color,                          # Button background color
        fg=TEXT_HEAD,                      # Button text color
        activebackground=color,            # Background color when button is active/clicked
        activeforeground=TEXT_HEAD,        # Text color when button is active/clicked
        relief="flat",                     # No 3D border effect
        bd=0,                              # Border width = 0
        cursor="hand2",                    # Show hand cursor when hovering
        padx=10,                           # Horizontal padding inside button
        pady=6,                            # Vertical padding inside button
        width=width,                       # Width in characters
        **kw                               # Any other parameters
    )
    # When mouse enters button, lighten the button color
    btn.bind("<Enter>", lambda e: btn.config(bg=_lighten(color)))
    # When mouse leaves button, restore original button color
    btn.bind("<Leave>", lambda e: btn.config(bg=color))
    return btn


def _lighten(hex_color):
    """
    Return a slightly lighter version of a hex color.
    Used for button hover effects to create visual feedback.
    """
    # Extract RGB values from hex color (e.g., #4F8EF7)
    # Red: bytes 1-3, add 30 brightness
    r = min(255, int(hex_color[1:3], 16) + 30)
    # Green: bytes 3-5, add 30 brightness
    g = min(255, int(hex_color[3:5], 16) + 30)
    # Blue: bytes 5-7, add 30 brightness
    b = min(255, int(hex_color[5:7], 16) + 30)
    # min(255, ...) ensures value doesn't exceed max (255 = brightest)
    # Return the new lighter color in hex format
    return f"#{r:02x}{g:02x}{b:02x}"


def card_frame(parent, **kw):
    """
    Create a styled frame (container) used as a card/panel.
    Cards are used to group related UI elements together.
    """
    return tk.Frame(
        parent,
        bg=BG_CARD,                        # Card background color
        relief="flat",                     # No 3D effect
        highlightthickness=1,              # Show 1px highlight border
        highlightbackground=BORDER,        # Border color
        **kw                               # Any other parameters
    )


def section_title(parent, text):
    """Create a styled section title within a card."""
    f = tk.Frame(parent, bg=BG_CARD)
    # Add the title text in a large, blue, bold font
    tk.Label(f, text=text, font=FONT_TITLE,
             fg=ACCENT, bg=BG_CARD).pack(side="left")
    return f


def build_treeview(parent, columns, col_widths, height=12):
    """
    Create a styled table (treeview) with scrollbar.
    Used to display lists of students and attendance records.
    """
    # Create a style object to customize the table appearance
    style = ttk.Style()
    style.theme_use("clam")  # Use the clam theme as base
    # Configure table appearance
    style.configure("Custom.Treeview",
                    background=BG_INPUT,              # Table background
                    foreground=TEXT_WHITE,            # Table text color
                    fieldbackground=BG_INPUT,         # Field background
                    rowheight=28,                     # Height of each row in pixels
                    font=FONT_BODY,                   # Font for table content
                    borderwidth=0)                    # No border
    # Configure table header appearance
    style.configure("Custom.Treeview.Heading",
                    background=BG_CARD,               # Header background
                    # Header text color (blue)
                    foreground=ACCENT,
                    font=FONT_HEAD,                   # Header font (bold)
                    relief="flat")                    # No 3D effect
    # Configure selection colors (what happens when you click a row)
    style.map("Custom.Treeview",
              # Selected row background (blue)
              background=[("selected", ACCENT)],
              # Selected row text (white)
              foreground=[("selected", TEXT_HEAD)])

    # Create a container frame to hold table and scrollbar
    container = tk.Frame(parent, bg=BG_DARK)
    # Create the treeview (table) widget
    tree = ttk.Treeview(
        container,
        columns=columns,                  # Column names/headers
        show="headings",                  # Show the header row
        height=height,                    # Height in rows
        style="Custom.Treeview",          # Use our custom styling
        selectmode="browse"               # Only allow selecting one row at a time
    )
    # Create vertical scrollbar
    vsb = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
    # Connect scrollbar to table (when you scroll the bar, table scrolls)
    tree.configure(yscrollcommand=vsb.set)

    # Configure each column (set heading and width)
    for col, width in zip(columns, col_widths):
        # Set column header text
        tree.heading(col, text=col)
        # Set column width and alignment
        tree.column(col, width=width, anchor="w", minwidth=40)

    # Pack (arrange) table and scrollbar side by side
    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")
    return container, tree


# ===== TAB 1: STUDENT REGISTRATION =====
# This tab allows you to register new students, view all students, and manage their information

class RegistrationTab(tk.Frame):
    """UI for registering students and viewing the student list."""

    def __init__(self, parent, db: DatabaseManager):
        # Initialize the frame with dark background
        super().__init__(parent, bg=BG_DARK)
        self.db = db  # Store reference to database manager
        self._build()  # Create the UI

    def _build(self):
        """Build the Registration tab UI with form on left, table on right."""
        # ── LEFT SIDE: REGISTRATION FORM ──────────────
        # Create left panel with padding
        left = card_frame(self, padx=24, pady=24)
        left.pack(side="left", fill="y", padx=(20, 10), pady=20)

        # Add section title "Register Student"
        section_title(left, "  Register Student").pack(
            anchor="w", pady=(0, 20))

        # ── Student ID Display (auto-generated) ────
        styled_label(left, "Student ID  (auto-assigned)",
                     fg=TEXT_MUTED).pack(anchor="w", pady=(8, 2))
        self.id_var = tk.StringVar()  # Variable to store the generated ID
        # Container for ID field and button
        id_row = tk.Frame(left, bg=BG_CARD)
        id_row.pack(anchor="w", pady=(0, 4))

        # Display auto-generated ID in a read-only field
        id_display = tk.Entry(
            id_row,
            textvariable=self.id_var,          # Bind to id_var
            font=FONT_HEAD,                    # Large bold font
            bg=BG_INPUT,                       # Input background
            fg=ACCENT2,                        # Green text for ID
            insertbackground=ACCENT2,
            relief="flat",
            bd=0,
            width=16,
            # Make read-only (can't edit directly)
            state="readonly",
            readonlybackground=BG_INPUT
        )
        id_display.pack(side="left", padx=(0, 8))
        id_display.config(highlightthickness=1, highlightbackground=BORDER)
        # Button to generate a new ID
        styled_button(id_row, "↺ New ID", self._refresh_id,
                      color=BG_INPUT, width=9).pack(side="left")
        self._refresh_id()  # Generate initial ID

        # ── REGISTRATION FORM FIELDS ──────────────
        # Define the form fields: (label, variable_key)
        fields = [
            ("Full Name",   "name"),
            ("Age",         "age"),
            ("Email",       "email"),
            ("Courses",     "courses"),
        ]
        self.vars = {}  # Dictionary to store all form field values

        # Create input field for each form field
        for label, key in fields:
            styled_label(left, label, fg=TEXT_MUTED).pack(
                anchor="w", pady=(8, 2))
            var = tk.StringVar()  # Create variable to store field value
            self.vars[key] = var  # Store in dictionary
            entry = styled_entry(left, textvariable=var, width=32)
            entry.pack(anchor="w", pady=(0, 4))
            # Add helper text for courses field
            if key == "courses":
                styled_label(left, "Separate with commas  e.g. Math, Physics",
                             font=FONT_SMALL, fg=TEXT_MUTED).pack(anchor="w")

        # ── REGISTER AND CLEAR BUTTONS ──────────
        btn_row = tk.Frame(left, bg=BG_CARD)
        btn_row.pack(fill="x", pady=(20, 0))
        styled_button(btn_row, "Register", self._register,
                      color=ACCENT).pack(side="left", padx=(0, 8))
        styled_button(btn_row, "Clear", self._clear,
                      color=BG_INPUT).pack(side="left")

        # ── RIGHT SIDE: STUDENTS TABLE ────────────
        right = tk.Frame(self, bg=BG_DARK)
        right.pack(side="right", fill="both",
                   expand=True, padx=(10, 20), pady=20)

        # Top bar with title and refresh button
        top_bar = tk.Frame(right, bg=BG_DARK)
        top_bar.pack(fill="x", pady=(0, 10))
        styled_label(top_bar, "All Students", font=FONT_TITLE,
                     fg=ACCENT).pack(side="left")
        styled_button(top_bar, "Refresh", self._load_table,
                      color=BG_INPUT, width=10).pack(side="right")

        # ── SEARCH BAR ────────────────────────────
        search_row = tk.Frame(right, bg=BG_DARK)
        search_row.pack(fill="x", pady=(0, 10))
        self.search_var = tk.StringVar()  # Variable for search input
        search_entry = styled_entry(
            search_row, textvariable=self.search_var, width=28)
        search_entry.pack(side="left", padx=(0, 8))
        styled_button(search_row, "Search", self._search,
                      width=10).pack(side="left")
        styled_button(search_row, "Show All", self._load_table,
                      color=BG_INPUT, width=10).pack(side="left", padx=8)

        # ── STUDENTS TABLE (TREEVIEW) ─────────────
        cols = ("ID", "Name", "Age", "Email", "Courses", "Registered")
        widths = (80, 150, 50, 170, 180, 130)
        tree_frame, self.tree = build_treeview(right, cols, widths, height=14)
        tree_frame.pack(fill="both", expand=True)

        # ── ACTION BUTTONS (Edit/Delete) ───────────
        action_row = tk.Frame(right, bg=BG_DARK)
        action_row.pack(fill="x", pady=(10, 0))
        styled_button(action_row, "Edit Selected", self._edit_selected,
                      color=ACCENT2, width=14).pack(side="left", padx=(0, 8))
        styled_button(action_row, "Delete Selected", self._delete_selected,
                      color=DANGER, width=14).pack(side="left")

        # Load and display all students in the table
        self._load_table()

    def _load_table(self):
        """Load all students from database and display in the table."""
        # Clear all existing rows from the table
        self.tree.delete(*self.tree.get_children())
        # Get all students from database
        for row in self.db.get_all_students():
            # Insert each student as a row in the table
            self.tree.insert("", "end", values=row)

    def _search(self):
        """Search for students by name or ID and display results."""
        kw = self.search_var.get().strip()  # Get search keyword and remove whitespace
        if not kw:  # If search box is empty, do nothing
            return
        # Clear the table
        self.tree.delete(*self.tree.get_children())
        # Search database and display matching students
        for row in self.db.search_students(kw):
            self.tree.insert("", "end", values=row)

    def _refresh_id(self):
        """Generate a new student ID and display it in the ID field."""
        self.id_var.set(self.db.generate_student_id())

    def _register(self):
        """
        Validate form input and register a new student.
        Shows success or error messages.
        """
        # Get all form field values and remove extra whitespace
        v = {k: var.get().strip() for k, var in self.vars.items()}
        student_id = self.id_var.get().strip()

        # Validate required fields (name and age are required)
        if not all([v["name"], v["age"]]):
            messagebox.showwarning(
                "Missing Fields", "Name and Age are required.")
            return

        # Validate age is a number
        if not v["age"].isdigit():
            messagebox.showwarning("Invalid Age", "Age must be a number.")
            return

        # Try to register the student in the database
        ok, msg = self.db.add_student(
            student_id, v["name"], int(v["age"]), v["email"], v["courses"]
        )

        if ok:  # If registration successful
            messagebox.showinfo(
                "Success", f"Registered! Student ID: {student_id}")
            self._clear()  # Clear the form
            self._load_table()  # Refresh the table to show the new student
        else:  # If registration failed
            messagebox.showerror("Error", msg)

    def _clear(self):
        """Clear all form fields and generate a new ID."""
        for var in self.vars.values():
            var.set("")  # Clear each field
        self._refresh_id()  # Generate a new ID

    def _edit_selected(self):
        """Open edit window for the selected student."""
        selected = self.tree.focus()  # Get currently selected row
        if not selected:
            messagebox.showwarning(
                "No Selection", "Please select a student to edit.")
            return
        # Get the data from the selected row
        row = self.tree.item(selected)["values"]
        # Open the edit window (defined below)
        EditStudentWindow(self, self.db, row, self._load_table)

    def _delete_selected(self):
        """Delete the selected student after confirmation."""
        selected = self.tree.focus()  # Get currently selected row
        if not selected:
            messagebox.showwarning(
                "No Selection", "Please select a student to delete.")
            return
        # Get the data from the selected row
        row = self.tree.item(selected)["values"]
        # Ask for confirmation before deleting
        if messagebox.askyesno("Confirm Delete", f"Delete student '{row[1]}' ({row[0]})?"):
            self.db.delete_student(row[0])  # Delete from database
            self._load_table()  # Refresh the table


# ===== EDIT STUDENT POPUP WINDOW =====

class EditStudentWindow(tk.Toplevel):
    """Popup window for editing a student's information."""

    def __init__(self, parent, db, row, refresh_cb):
        # Create a new popup window
        super().__init__(parent)
        self.db = db  # Reference to database
        self.row = row  # The student row being edited
        self.refresh_cb = refresh_cb  # Callback function to refresh the main table

        # Configure the window
        self.title("Edit Student")
        self.geometry("420x380")
        self.configure(bg=BG_CARD)
        self.resizable(False, False)  # Don't allow resizing
        self._build()

    def _build(self):
        """Build the edit window UI."""
        # Title
        tk.Label(self, text="Edit Student", font=FONT_TITLE,
                 fg=ACCENT, bg=BG_CARD).pack(pady=(20, 10))

        # Pre-fill fields with current student data
        fields = [
            ("Full Name", self.row[1]),  # row[1] is the name
            ("Age",       self.row[2]),  # row[2] is the age
            ("Email",     self.row[3]),  # row[3] is the email
            ("Courses",   self.row[4]),  # row[4] is the courses
        ]

        self.vars = {}
        keys = ["name", "age", "email", "courses"]

        # Create editable fields with current values
        for (label, default), key in zip(fields, keys):
            tk.Label(self, text=label, font=FONT_BODY, fg=TEXT_MUTED,
                     bg=BG_CARD).pack(anchor="w", padx=30)
            # Set current value
            var = tk.StringVar(value=default if default else "")
            self.vars[key] = var
            styled_entry(self, textvariable=var, width=38).pack(
                padx=30, pady=(2, 8))

        # Save button
        styled_button(self, "Save Changes", self._save,
                      color=ACCENT).pack(pady=10)

    def _save(self):
        """Validate and save the student changes."""
        name = self.vars["name"].get().strip()
        age_str = self.vars["age"].get().strip()
        email = self.vars["email"].get().strip()
        courses = self.vars["courses"].get().strip()

        # Validate required fields
        if not name or not age_str.isdigit():
            messagebox.showwarning(
                "Invalid", "Name and valid Age are required.", parent=self)
            return

        # Update student in database
        self.db.update_student(self.row[0], name, int(age_str), email, courses)
        messagebox.showinfo(
            "Updated", "Student updated successfully.", parent=self)

        # Refresh main table and close this window
        self.refresh_cb()
        self.destroy()


# ===== TAB 2: CHECK-IN / CHECK-OUT =====

class AttendanceTab(tk.Frame):
    """UI for checking students in/out and viewing attendance logs."""

    def __init__(self, parent, db: DatabaseManager):
        super().__init__(parent, bg=BG_DARK)
        self.db = db
        self._build()

    def _build(self):
        """Build the Attendance tab UI."""
        # ── TOP PANEL WITH CHECK-IN/OUT BUTTONS ───
        top = card_frame(self, padx=30, pady=24)
        top.pack(fill="x", padx=20, pady=(20, 10))

        section_title(
            top, "  Check-In / Check-Out").pack(anchor="w", pady=(0, 20))

        # Row with student ID input and buttons
        row = tk.Frame(top, bg=BG_CARD)
        row.pack(fill="x")

        styled_label(row, "Student ID:", fg=TEXT_MUTED).pack(side="left")
        self.id_var = tk.StringVar()  # Variable for student ID input
        entry = styled_entry(row, textvariable=self.id_var, width=20)
        entry.pack(side="left", padx=(8, 16))
        # Allow pressing Enter to check in
        entry.bind("<Return>", lambda e: self._check_in())

        # Check-in and check-out buttons
        styled_button(row, "✅  Check In", self._check_in,
                      color=ACCENT2, width=14).pack(side="left", padx=(0, 8))
        styled_button(row, "👋  Check Out", self._check_out,
                      color=ACCENT, width=14).pack(side="left", padx=(0, 8))
        styled_button(row, "Refresh", self._load_log,
                      color=BG_INPUT, width=10).pack(side="right")

        # ── STATUS MESSAGE ─────────────────────────
        # Displays check-in/out messages
        self.status_var = tk.StringVar(value="")
        status_label = tk.Label(top, textvariable=self.status_var,
                                font=FONT_HEAD, fg=ACCENT2, bg=BG_CARD, anchor="w")
        status_label.pack(fill="x", pady=(16, 0))

        # ── DATE FILTER ────────────────────────────
        filter_row = tk.Frame(self, bg=BG_DARK)
        filter_row.pack(fill="x", padx=20, pady=(0, 8))
        styled_label(filter_row, "Filter by date:",
                     fg=TEXT_MUTED).pack(side="left")
        self.date_var = tk.StringVar(
            value=datetime.now().strftime("%Y-%m-%d"))  # Default to today
        styled_entry(filter_row, textvariable=self.date_var,
                     width=14).pack(side="left", padx=(8, 8))
        styled_button(filter_row, "Apply", self._filter_log,
                      width=10).pack(side="left", padx=(0, 6))
        styled_button(filter_row, "Show All", self._load_log,
                      color=BG_INPUT, width=10).pack(side="left")

        # ── ATTENDANCE TABLE ───────────────────────
        cols = ("#", "Student ID", "Student Name",
                "Check-In", "Check-Out", "Date", "Status")
        widths = (40, 90, 150, 90, 90, 100, 100)
        tree_frame, self.tree = build_treeview(self, cols, widths, height=14)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self._load_log()  # Load initial attendance data

    def _load_log(self):
        """Load and display all attendance records."""
        # Clear the table
        self.tree.delete(*self.tree.get_children())
        # Get all attendance records from database
        for row in self.db.get_attendance_log():
            # Color code: green for checked in, gray for checked out
            tag = "out" if row[6] == "Checked Out" else "in"
            self.tree.insert("", "end", values=row, tags=(tag,))
        # Configure colors for the tags
        # Green for checked in
        self.tree.tag_configure("in",  foreground=ACCENT2)
        # Gray for checked out
        self.tree.tag_configure("out", foreground=TEXT_MUTED)

    def _filter_log(self):
        """Filter attendance records by selected date."""
        date = self.date_var.get().strip()
        # Clear the table
        self.tree.delete(*self.tree.get_children())
        # Get attendance records for the selected date
        for row in self.db.get_attendance_log(date_filter=date):
            tag = "out" if row[6] == "Checked Out" else "in"
            self.tree.insert("", "end", values=row, tags=(tag,))
        # Configure colors for the tags
        self.tree.tag_configure("in",  foreground=ACCENT2)
        self.tree.tag_configure("out", foreground=TEXT_MUTED)

    def _check_in(self):
        """Record a student's check-in."""
        sid = self.id_var.get().strip()  # Get student ID from input
        if not sid:
            self.status_var.set("⚠  Please enter a Student ID.")
            return
        # Try to check in the student
        ok, msg = self.db.check_in(sid)
        self.status_var.set(msg)  # Display result message
        if ok:
            self._load_log()  # Refresh the table
            self.id_var.set("")  # Clear the input

    def _check_out(self):
        """Record a student's check-out."""
        sid = self.id_var.get().strip()  # Get student ID from input
        if not sid:
            self.status_var.set("⚠  Please enter a Student ID.")
            return
        # Try to check out the student
        ok, msg = self.db.check_out(sid)
        self.status_var.set(msg)  # Display result message
        if ok:
            self._load_log()  # Refresh the table
            self.id_var.set("")  # Clear the input


# ===== TAB 3: ID RECOVERY =====

class IDRecoveryTab(tk.Frame):
    """UI for recovering a student's ID by searching name or email."""

    def __init__(self, parent, db: DatabaseManager):
        super().__init__(parent, bg=BG_DARK)
        self.db = db
        self._build()

    def _build(self):
        """Build the ID Recovery tab UI."""
        # ── HEADER ─────────────────────────────────
        styled_label(self, "  🔍  Forgot Your Student ID?",
                     font=FONT_TITLE, fg=ACCENT).pack(anchor="w", padx=24, pady=(24, 4))
        styled_label(self, "  Search by your full name or email address to recover your ID.",
                     font=FONT_BODY, fg=TEXT_MUTED).pack(anchor="w", padx=24, pady=(0, 20))

        # ── SEARCH CARD ────────────────────────────
        card = card_frame(self, padx=30, pady=28)
        card.pack(fill="x", padx=24, pady=(0, 16))

        row = tk.Frame(card, bg=BG_CARD)
        row.pack(fill="x")

        styled_label(row, "Name or Email:", fg=TEXT_MUTED).pack(side="left")
        self.search_var = tk.StringVar()
        search_entry = styled_entry(
            row, textvariable=self.search_var, width=32)
        search_entry.pack(side="left", padx=(10, 14))
        # Allow pressing Enter to search
        search_entry.bind("<Return>", lambda e: self._search())
        styled_button(row, "🔍  Search", self._search,
                      color=ACCENT, width=12).pack(side="left")
        styled_button(row, "Clear", self._clear, color=BG_INPUT,
                      width=8).pack(side="left", padx=(8, 0))

        # ── RESULT AREA ────────────────────────────
        self.result_frame = tk.Frame(self, bg=BG_DARK)
        self.result_frame.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        # Initial message (before any search)
        self.no_result_label = styled_label(
            self.result_frame,
            "Enter your name or email above and press Search.",
            fg=TEXT_MUTED, font=FONT_BODY
        )
        self.no_result_label.pack(pady=30)

        # Results table (hidden until search is performed)
        cols = ("Student ID", "Full Name", "Email", "Registered On")
        widths = (110, 200, 220, 160)
        tree_frame, self.tree = build_treeview(
            self.result_frame, cols, widths, height=8)
        self.tree_frame_widget = tree_frame

        # ── COPY ID BUTTON ─────────────────────────
        self.copy_btn = styled_button(
            self.result_frame, "📋  Copy Selected ID",
            self._copy_id, color=ACCENT2, width=20
        )

        # ── HELPFUL TIP ────────────────────────────
        tip = card_frame(self, padx=20, pady=14)
        tip.pack(fill="x", padx=24, pady=(0, 20))
        styled_label(tip, "💡  Tip:", font=FONT_HEAD,
                     fg=ACCENT2).pack(anchor="w")
        styled_label(tip,
                     "If your name or email returns no results, you may not be registered yet.\n"
                     "Please visit the Students tab to register and get your ID.",
                     fg=TEXT_MUTED, font=FONT_SMALL, justify="left"
                     ).pack(anchor="w", pady=(4, 0))

    def _search(self):
        """Search for students by name or email."""
        keyword = self.search_var.get().strip()
        if not keyword:
            return

        # Search database
        results = self.db.recover_id(keyword)

        # Clear previous results from display
        self.no_result_label.pack_forget()
        self.tree_frame_widget.pack_forget()
        self.copy_btn.pack_forget()
        self.tree.delete(*self.tree.get_children())

        # Display results or "not found" message
        if not results:
            self.no_result_label.config(
                text=f'❌  No student found matching "{keyword}".\n\nDouble-check your spelling or try a partial name.',
                fg=DANGER
            )
            self.no_result_label.pack(pady=30)
            return

        # Insert search results into table
        for row in results:
            self.tree.insert("", "end", values=row)

        # Show success message with result count
        count = len(results)
        self.no_result_label.config(
            text=f"✅  Found {count} result{'s' if count > 1 else ''} — select a row and click Copy ID.",
            fg=ACCENT2
        )
        self.no_result_label.pack(pady=(0, 10))
        self.tree_frame_widget.pack(fill="both", expand=True)
        self.copy_btn.pack(pady=(10, 0))

    def _copy_id(self):
        """Copy the selected student's ID to clipboard."""
        selected = self.tree.focus()  # Get selected row
        if not selected:
            messagebox.showwarning(
                "No Selection", "Please select a row first.")
            return
        # Extract the student ID from the selected row
        student_id = self.tree.item(selected)["values"][0]
        # Copy to clipboard
        self.clipboard_clear()
        self.clipboard_append(student_id)
        messagebox.showinfo(
            "Copied!", f"Student ID  '{student_id}'  copied to clipboard.\nYou can now paste it in the Check-In field.")

    def _clear(self):
        """Clear search results and reset the tab."""
        self.search_var.set("")  # Clear search input
        self.tree.delete(*self.tree.get_children())  # Clear results table
        self.tree_frame_widget.pack_forget()  # Hide results table
        self.copy_btn.pack_forget()  # Hide copy button
        self.no_result_label.config(
            text="Enter your name or email above and press Search.",
            fg=TEXT_MUTED
        )
        self.no_result_label.pack(pady=30)  # Show initial message


# ===== TAB 4: DASHBOARD =====

class DashboardTab(tk.Frame):
    """Display live statistics and today's attendance log."""

    def __init__(self, parent, db: DatabaseManager):
        super().__init__(parent, bg=BG_DARK)
        self.db = db
        self._build()

    def _build(self):
        """Build the Dashboard tab UI."""
        # ── TITLE ──────────────────────────────────
        styled_label(self, "  📊  Live Dashboard",
                     font=FONT_TITLE, fg=ACCENT).pack(anchor="w", padx=24, pady=(20, 16))

        # ── STAT CARDS ROW ─────────────────────────
        cards_frame = tk.Frame(self, bg=BG_DARK)
        cards_frame.pack(fill="x", padx=20)

        self.stat_labels = {}
        # Define the 4 statistics to display
        stat_defs = [
            ("total_students",   "Total\nStudents",    ACCENT),
            ("total_today",      "Check-ins\nToday",   ACCENT2),
            ("checked_in_today", "Currently\nInside",  "#F7A74F"),
            ("top_student",      "Most Active\nStudent", "#C36EF7"),
        ]

        # Create a card for each statistic
        for key, title, color in stat_defs:
            card = card_frame(cards_frame, padx=20, pady=16, width=170)
            card.pack(side="left", padx=(0, 14), fill="y")
            card.pack_propagate(False)  # Keep card at fixed size
            # Add stat title
            tk.Label(card, text=title, font=FONT_BODY, fg=TEXT_MUTED,
                     bg=BG_CARD, justify="center").pack()
            # Add large stat value (placeholder initially)
            val_lbl = tk.Label(card, text="—", font=(
                "Consolas", 26, "bold"), fg=color, bg=BG_CARD)
            val_lbl.pack(pady=(6, 0))
            # Store reference to update later
            self.stat_labels[key] = val_lbl

        # Refresh button
        styled_button(cards_frame, "⟳  Refresh", self._refresh,
                      color=BG_INPUT, width=12).pack(side="right", anchor="n")

        # ── TODAY'S ATTENDANCE TABLE ───────────────
        styled_label(self, "  Today's Attendance Log",
                     font=FONT_HEAD, fg=TEXT_MUTED).pack(anchor="w", padx=24, pady=(24, 8))

        cols = ("#", "Student ID", "Student Name",
                "Check-In", "Check-Out", "Status")
        widths = (40, 90, 160, 100, 100, 110)
        tree_frame, self.today_tree = build_treeview(
            self, cols, widths, height=10)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self._refresh()  # Load initial data

    def _refresh(self):
        """Update all statistics and today's attendance data."""
        # Get statistics from database
        stats = self.db.get_stats()
        # Update each stat card with current values
        for key, label in self.stat_labels.items():
            label.config(text=str(stats[key]))

        # Get today's attendance records
        today = datetime.now().strftime("%Y-%m-%d")
        self.today_tree.delete(*self.today_tree.get_children())  # Clear table
        # Load today's records
        for row in self.db.get_attendance_log(date_filter=today):
            # Format: (record_id, student_id, student_name, check_in, check_out, date, status)
            # We only want: (record_id, student_id, student_name, check_in, check_out, status)
            r = (row[0], row[1], row[2], row[3], row[4], row[6])
            # Color code: green for checked in, gray for checked out
            tag = "out" if row[6] == "Checked Out" else "in"
            self.today_tree.insert("", "end", values=r, tags=(tag,))
        # Configure colors
        self.today_tree.tag_configure(
            "in",  foreground=ACCENT2)    # Green for checked in
        self.today_tree.tag_configure(
            "out", foreground=TEXT_MUTED)  # Gray for checked out


# ===== MAIN APPLICATION CLASS =====

class App(tk.Tk):
    """Main application window that brings everything together."""

    def __init__(self):
        # Initialize the root window
        super().__init__()

        # Configure main window
        self.title("🎓  Student Registration & Attendance System")
        self.geometry("1100x720")  # Width x Height
        self.minsize(900, 600)  # Minimum window size
        self.configure(bg=BG_DARK)

        # Initialize database
        self.db = DatabaseManager()

        # Build the UI
        self._build_header()  # Create top header with title and clock
        self._build_notebook()  # Create tabbed interface

        # Set the close protocol
        # Call _on_close when closing
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_header(self):
        """Build the header bar at the top with title and clock."""
        # Create header frame
        header = tk.Frame(self, bg=BG_CARD, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)  # Keep fixed height

        # Add title on the left
        tk.Label(header, text="🎓  STUDENT SYSTEM",
                 font=("Consolas", 15, "bold"), fg=ACCENT, bg=BG_CARD).pack(side="left", padx=24)

        # Add clock on the right
        self.clock_var = tk.StringVar()
        tk.Label(header, textvariable=self.clock_var,
                 font=FONT_BODY, fg=TEXT_MUTED, bg=BG_CARD).pack(side="right", padx=24)
        self._update_clock()  # Start the clock

        # Add a separator line below header
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

    def _update_clock(self):
        """Update the clock display every second."""
        # Format current time
        now = datetime.now().strftime("%A, %B %d %Y   %H:%M:%S")
        self.clock_var.set(now)  # Update the clock label
        # Schedule this function to run again in 1000ms (1 second)
        self.after(1000, self._update_clock)

    def _build_notebook(self):
        """Build the tabbed interface with 4 tabs."""
        # Create style for the notebook
        style = ttk.Style()
        style.theme_use("clam")

        # Configure notebook appearance
        style.configure("Dark.TNotebook",
                        background=BG_DARK, borderwidth=0, tabmargins=[0, 0, 0, 0])
        # Configure notebook tab appearance
        style.configure("Dark.TNotebook.Tab",
                        background=BG_CARD,        # Tab background when not selected
                        foreground=TEXT_MUTED,     # Tab text when not selected
                        font=FONT_HEAD,
                        padding=[20, 10],
                        borderwidth=0)
        # Configure tab appearance when selected
        style.map("Dark.TNotebook.Tab",
                  # Selected tab background
                  background=[("selected", BG_DARK)],
                  # Selected tab text
                  foreground=[("selected", ACCENT)])

        # Create the notebook (tabbed container)
        nb = ttk.Notebook(self, style="Dark.TNotebook")
        nb.pack(fill="both", expand=True)

        # Create each tab (instance of each tab class)
        reg_tab = RegistrationTab(nb, self.db)
        att_tab = AttendanceTab(nb, self.db)
        rec_tab = IDRecoveryTab(nb, self.db)
        dash_tab = DashboardTab(nb, self.db)

        # Add tabs to notebook with labels and emojis
        nb.add(reg_tab,  text="  👤  Students  ")
        nb.add(att_tab,  text="  🕐  Attendance  ")
        nb.add(rec_tab,  text="  🔑  ID Recovery  ")
        nb.add(dash_tab, text="  📊  Dashboard  ")

    def _on_close(self):
        """Handle application closing - cleanup and exit."""
        self.db.close()  # Close the database connection
        self.destroy()  # Destroy the window and exit


# ===== ENTRY POINT =====
# This code runs only when the script is executed directly (not imported)
if __name__ == "__main__":
    app = App()  # Create the application
    app.mainloop()  # Start the application event loop (keeps window open)
