import os
import sqlite3
import csv
from datetime import datetime, date, timedelta
import hashlib
import uuid 

# Database setup
conn = sqlite3.connect('time_tracker.db')
cursor = conn.cursor()

def setup_database():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS time_entries (
            id INTEGER PRIMARY KEY,
            project_id INTEGER,
            user_id INTEGER,
            date TEXT,
            hours INTEGER,
            category TEXT,
            notes TEXT,
            FOREIGN KEY (project_id) REFERENCES projects (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            created_at TEXT,
            last_accessed TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.commit()

# Llamar a esta función al inicio del programa
setup_database()

# Para captura de teclas sin Enter
if os.name == 'nt':  # Para Windows
    import msvcrt
else:  # Para sistemas Unix
    import sys
    import tty
    import termios

def get_key():
    if os.name == 'nt':
        return msvcrt.getch().decode('utf-8')
    else:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_session(user_id):
    session_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO sessions (id, user_id, created_at, last_accessed)
        VALUES (?, ?, ?, ?)
    ''', (session_id, user_id, now, now))
    conn.commit()
    return session_id

def get_active_session():
    cursor.execute('''
        SELECT id, user_id, created_at, last_accessed
        FROM sessions
        ORDER BY last_accessed DESC
        LIMIT 1
    ''')
    return cursor.fetchone()

def update_session_access(session_id):
    now = datetime.now().isoformat()
    cursor.execute('''
        UPDATE sessions
        SET last_accessed = ?
        WHERE id = ?
    ''', (now, session_id))
    conn.commit()

def delete_session(session_id):
    cursor.execute('DELETE FROM sessions WHERE id = ?', (session_id,))
    conn.commit()

def logout(session_id):
    delete_session(session_id)
    print("You have been logged out.")

# Predefined categories
CATEGORIES = ["Programming", "Project Management", "Business Development", "Design", "Marketing"]

def create_account():
    clear_console()
    print("Create a new account")
    username = input("Enter username: ")
    password = input("Enter password: ")
    first_name = input("Enter first name: ")
    last_name = input("Enter last name: ")

    hashed_password = hash_password(password)

    try:
        cursor.execute('''
            INSERT INTO users (username, password, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (username, hashed_password, first_name, last_name))
        conn.commit()
        print("Account created successfully!")
    except sqlite3.IntegrityError:
        print("Username already exists. Please choose a different username.")
    input("Press Enter to continue...")

def login():
    clear_console()
    print("Login")
    username = input("Enter username: ")
    password = input("Enter password: ")

    hashed_password = hash_password(password)

    cursor.execute('''
        SELECT id, first_name, last_name FROM users
        WHERE username = ? AND password = ?
    ''', (username, hashed_password))
    user = cursor.fetchone()

    if user:
        print(f"Welcome, {user[1]} {user[2]}!")
        session_id = create_session(user[0])
        return user, session_id
    else:
        print("Invalid username or password.")
        return None, None

def input_date():
    while True:
        print("\nSelect a date option:")
        print("1. Today")
        print("2. Yesterday")
        print("3. Enter custom date")
        choice = get_key()
        print(f"Selected: {choice}")

        if choice == '1':
            return date.today()
        elif choice == '2':
            return date.today() - timedelta(days=1)
        elif choice == '3':
            return enter_custom_date()
        else:
            print("Invalid choice. Please try again.")

def enter_custom_date():
    current_year = date.today().year
    
    while True:
        day = input("Enter day (1-31): ")
        try:
            day = int(day)
            if 1 <= day <= 31:
                break
            else:
                print("Invalid day. Please enter a number between 1 and 31.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    
    while True:
        month = input("Enter month (1-12): ")
        try:
            month = int(month)
            if 1 <= month <= 12:
                break
            else:
                print("Invalid month. Please enter a number between 1 and 12.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    
    try:
        return date(current_year, month, day)
    except ValueError:
        print("Invalid date. Please try again.")
        return enter_custom_date()

def select_category():
    print("\nSelect a category:")
    for i, category in enumerate(CATEGORIES, 1):
        print(f"{i}. {category}")
    
    while True:
        choice = get_key()
        try:
            index = int(choice) - 1
            if 0 <= index < len(CATEGORIES):
                print(f"Selected: {CATEGORIES[index]}")
                return CATEGORIES[index]
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a number.")

def create_project():
    clear_console()
    name = input("Enter project name: ")
    cursor.execute("INSERT INTO projects (name) VALUES (?)", (name,))
    conn.commit()
    print(f"Project '{name}' created successfully.")

def list_projects():
    cursor.execute("SELECT * FROM projects")
    projects = cursor.fetchall()
    if not projects:
        print("No projects found.")
    else:
        for project in projects:
            print(f"ID: {project[0]}, Name: {project[1]}")

def update_project():
    clear_console()
    list_projects()
    project_id = int(input("\nEnter the ID of the project to update: "))
    new_name = input("Enter the new project name: ")
    cursor.execute("UPDATE projects SET name = ? WHERE id = ?", (new_name, project_id))
    conn.commit()
    print(f"Project updated successfully.")
    input("Press Enter to continue...")

def create_time_entry(user_id):
    clear_console()
    list_projects()
    project_id = int(input("\nEnter the project ID: "))
    print("Enter the date for the time entry:")
    entry_date = input_date()
    hours = int(input("Enter the number of hours: "))
    category = select_category()
    notes = input("Enter any notes (if any): ")

    cursor.execute('''
        INSERT INTO time_entries (project_id, user_id, date, hours, category, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (project_id, user_id, entry_date.strftime("%Y-%m-%d"), hours, category, notes))
    conn.commit()
    print("Time entry created successfully.")

def update_time_entry():
    clear_console()
    list_time_entries()
    entry_id = int(input("Enter the ID of the time entry to update: "))
    print("Enter the new date for the time entry:")
    new_date = input_date()
    hours = int(input("Enter the new number of hours: "))
    category = select_category()
    notes = input("Enter the new notes: ")

    cursor.execute('''
        UPDATE time_entries 
        SET date = ?, hours = ?, category = ?, notes = ?
        WHERE id = ?
    ''', (new_date.strftime("%Y-%m-%d"), hours, category, notes, entry_id))
    conn.commit()
    print("Time entry updated successfully.")

def list_time_entries(user_id):
    clear_console()
    cursor.execute('''
        SELECT time_entries.id, projects.name, time_entries.date, time_entries.hours, time_entries.category, time_entries.notes, users.first_name, users.last_name
        FROM time_entries 
        JOIN projects ON time_entries.project_id = projects.id
        JOIN users ON time_entries.user_id = users.id
        WHERE time_entries.user_id = ?
        ORDER BY time_entries.date DESC, time_entries.id DESC
    ''', (user_id,))
    entries = cursor.fetchall()
    
    if not entries:
        print("No time entries found.")
        return

    current_date = None
    current_week_start = None
    daily_total = 0
    weekly_total = 0

    for entry in entries:
        entry_date = datetime.strptime(entry[2], "%Y-%m-%d").date()
        
        # Check if it's a new date
        if entry_date != current_date:
            if current_date:
                print(f"Daily total: {daily_total} hours")
            
            # Check if it's a new week
            if not current_week_start or entry_date < current_week_start:
                if current_week_start:
                    print(f"Weekly total: {weekly_total} hours\n")
                current_week_start = entry_date - timedelta(days=entry_date.weekday())
                weekly_total = 0
            
            print(f"\nDate: {entry_date.strftime('%Y-%m-%d')} ({entry_date.strftime('%A')})")
            current_date = entry_date
            daily_total = 0

        print(f"ID: {entry[0]}, Project: {entry[1]}, Hours: {entry[3]}, Category: {entry[4]}, Notes: {entry[5]}")
        print(f"User: {entry[6]} {entry[7]}")
        
        daily_total += entry[3]
        weekly_total += entry[3]

    if current_date:
        print(f"Daily total: {daily_total} hours")
        print(f"Weekly total: {weekly_total} hours")

def delete_time_entry():
    clear_console()
    list_time_entries()
    entry_id = int(input("Enter the ID of the time entry to delete: "))
    print(f"Are you sure you want to delete this time entry? This action cannot be undone.")
    print("1. Yes")
    print("2. No")
    
    while True:
        choice = get_key()
        if choice == '1':
            cursor.execute("DELETE FROM time_entries WHERE id = ?", (entry_id,))
            conn.commit()
            print("Time entry deleted successfully.")
            break
        elif choice == '2':
            print("Deletion cancelled.")
            break
        else:
            print("Invalid choice. Please try again.")

def get_report_parameters(user_id):
    list_projects()
    project_id = int(input("\nEnter the project ID for the report (0 for all projects): "))
    
    print("\nSelect users to include in the report:")
    print("1. Only me")
    print("2. All users")
    print("3. Select specific users")
    user_choice = get_key()
    print(f"Selected option: {['Only me', 'All users', 'Select specific users'][int(user_choice) - 1]}")

    selected_users = []
    if user_choice == '3':
        selected_users = select_specific_users(project_id)
    elif user_choice == '1':
        selected_users = [user_id]

    date_range = get_date_range()
    
    return project_id, user_choice, selected_users, date_range

def select_specific_users(project_id):
    users = get_project_users(project_id)
    selected_users = []
    
    print("\nAvailable users:")
    for i, user in enumerate(users, 1):
        print(f"{i}. {user[1]} {user[2]}")
    
    while True:
        choice = input("Enter user numbers to include (comma-separated) or 'done' to finish: ")
        if choice.lower() == 'done':
            break
        try:
            selections = [int(x.strip()) for x in choice.split(',')]
            for selection in selections:
                if 1 <= selection <= len(users):
                    selected_users.append(users[selection - 1][0])
                else:
                    print(f"Invalid selection: {selection}. Ignored.")
        except ValueError:
            print("Invalid input. Please enter numbers separated by commas.")
    
    return selected_users

def get_project_users(project_id):
    if project_id == 0:
        cursor.execute("SELECT DISTINCT users.id, users.first_name, users.last_name FROM users JOIN time_entries ON users.id = time_entries.user_id")
    else:
        cursor.execute("""
            SELECT DISTINCT users.id, users.first_name, users.last_name 
            FROM users 
            JOIN time_entries ON users.id = time_entries.user_id 
            WHERE time_entries.project_id = ?
        """, (project_id,))
    return cursor.fetchall()

def get_date_range():
    print("\nSelect a date range for the report:")
    print("1. This month")
    print("2. Last month")
    print("3. This year")
    print("4. Custom date range")
    
    while True:
        choice = get_key()
        if choice in ['1', '2', '3', '4']:
            print(f"Selected option: {choice}")
            break
        else:
            print("Invalid choice. Please select 1, 2, 3, or 4.")
    
    today = date.today()
    if choice == '1':
        return today.replace(day=1), today
    elif choice == '2':
        last_month = today.replace(day=1) - timedelta(days=1)
        return last_month.replace(day=1), last_month
    elif choice == '3':
        return today.replace(month=1, day=1), today
    elif choice == '4':
        print("Enter the start date for the report:")
        start_date = input_date()
        print("Enter the end date for the report:")
        end_date = input_date()
        return start_date, end_date

def get_report_data(project_id, user_choice, selected_users, date_range):
    start_date, end_date = date_range
    query = '''
        SELECT time_entries.id, time_entries.project_id, time_entries.date, time_entries.hours, 
               time_entries.category, time_entries.notes, projects.name as project_name, 
               users.first_name, users.last_name
        FROM time_entries
        JOIN projects ON time_entries.project_id = projects.id
        JOIN users ON time_entries.user_id = users.id
        WHERE time_entries.date BETWEEN ? AND ?
    '''
    params = [start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")]

    if project_id != 0:
        query += ' AND time_entries.project_id = ?'
        params.append(project_id)

    if user_choice in ['1', '3'] and selected_users:
        placeholders = ', '.join('?' * len(selected_users))
        query += f' AND time_entries.user_id IN ({placeholders})'
        params.extend(selected_users)

    query += ' ORDER BY time_entries.date DESC, time_entries.id DESC'

    cursor.execute(query, params)
    return cursor.fetchall()

def print_report(entries, project_id, date_range):
    start_date, end_date = date_range
    total_hours = sum(float(entry[3]) for entry in entries)

    print(f"\nReport for {'all projects' if project_id == 0 else f'Project ID {project_id}'} from {start_date} to {end_date}")
    print(f"Total Hours: {total_hours:.2f}")
    
    current_date = None
    current_week_start = None
    daily_total = 0
    weekly_total = 0

    # Imprimir encabezados de columnas
    print("\n{:3} | {:7} | {:5} | {:22} | {:20} | {}".format("ID", "Project", "Hours", "Category", "User", "Notes"))
    print("-" * 100)

    for entry in entries:
        entry_date = datetime.strptime(entry[2], "%Y-%m-%d").date()
        
        if entry_date != current_date:
            if current_date:
                print("Daily total: {:.2f} hours".format(daily_total))
            
            if not current_week_start or entry_date < current_week_start:
                if current_week_start:
                    print("Weekly total: {:.2f} hours\n".format(weekly_total))
                current_week_start = entry_date - timedelta(days=entry_date.weekday())
                weekly_total = 0
            
            print("\nDate: {} ({})".format(entry_date.strftime('%Y-%m-%d'), entry_date.strftime('%A')))
            print("-" * 100)
            current_date = entry_date
            daily_total = 0

        # Imprimir toda la información en una sola línea con espaciado consistente
        print("{:3} | {:7} | {:5.2f} | {:22} | {:20} | {}".format(
            entry[0],
            entry[6],
            float(entry[3]),
            entry[4],
            f"{entry[7]} {entry[8]}",
            entry[5]
        ))
        
        daily_total += float(entry[3])
        weekly_total += float(entry[3])

    if current_date:
        print("Daily total: {:.2f} hours".format(daily_total))
        print("Weekly total: {:.2f} hours".format(weekly_total))

def export_to_csv(entries, project_id):
    print("\nDo you want to export this report to CSV? (y/N)")
    export_choice = get_key().lower()
    print(f"Selected option: {'Yes' if export_choice == 'y' else 'No'}")
    
    if export_choice == 'y':
        project_name = "All_Projects" if project_id == 0 else entries[0][6].replace(" ", "_")
        filename = f"{project_name}_{date.today().strftime('%Y%m%d')}.csv"
        
        with open(filename, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(['Date', 'Project', 'Hours', 'Category', 'Notes', 'User'])
            for entry in entries:
                csvwriter.writerow([entry[2], entry[6], float(entry[3]), entry[4], entry[5], f"{entry[7]} {entry[8]}"])
        
        print(f"Report exported to {filename}")

def generate_report(user_id):
    clear_console()
    project_id, user_choice, selected_users, date_range = get_report_parameters(user_id)
    entries = get_report_data(project_id, user_choice, selected_users, date_range)
    print_report(entries, project_id, date_range)
    export_to_csv(entries, project_id)
    input("\nPress Enter to continue...")

def get_user_by_id(user_id):
    cursor.execute('''
        SELECT id, first_name, last_name 
        FROM users 
        WHERE id = ?
    ''', (user_id,))
    return cursor.fetchone()

def main_menu():
    while True:
        session = get_active_session()
        if session:
            session_id, user_id, _, _ = session
            user = get_user_by_id(user_id)
            if user:
                update_session_access(session_id)
                logged_in_menu(user, session_id)
                continue
        
        clear_console()
        print("Time Tracker Menu")
        print("1. Login")
        print("2. Create Account")
        choice = get_key()
        print(f"Selected: {choice}")

        if choice == '1':
            user, new_session_id = login()
            if user:
                logged_in_menu(user, new_session_id)
        elif choice == '2':
            create_account()
        else:
            print("Invalid choice. Please try again.")
            input("Press Enter to continue...")

def logged_in_menu(user, session_id):
    while True:
        clear_console()
        print(f"Welcome, {user[1]} {user[2]}!")
        print("1. Manage Projects")
        print("2. Manage Time Entries")
        print("3. Generate Report")
        print("4. Logout")
        choice = get_key()
        print(f"Selected: {choice}")

        if choice == '1':
            project_menu()
        elif choice == '2':
            time_entry_menu(user[0])
        elif choice == '3':
            generate_report(user[0])
        elif choice == '4':
            logout(session_id)
            return
        else:
            print("Invalid choice. Please try again.")
        input("Press Enter to continue...")
        update_session_access(session_id)

def project_menu():
    while True:
        clear_console()
        print("Project Management")
        print("1. Create Project")
        print("2. List Projects")
        print("3. Update Project")
        print("4. Back to Main Menu")
        choice = get_key()
        print(f"Selected: {choice}")

        if choice == '1':
            create_project()
            input("Press Enter to continue...")
        elif choice == '2':
            list_projects()
            input("Press Enter to continue...")
        elif choice == '3':
            update_project()
        elif choice == '4':
            break
        else:
            print("Invalid choice. Please try again.")
            input("Press Enter to continue...")

def time_entry_menu(user_id):
    while True:
        clear_console()
        print("Time Entry Management")
        print("1. Create Time Entry")
        print("2. List Time Entries")
        print("3. Update Time Entry")
        print("4. Delete Time Entry")
        print("5. Back to Main Menu")
        choice = get_key()
        print(f"Selected: {choice}")

        if choice == '1':
            create_time_entry(user_id)
        elif choice == '2':
            list_time_entries(user_id)
        elif choice == '3':
            update_time_entry()
        elif choice == '4':
            delete_time_entry()
        elif choice == '5':
            break
        else:
            print("Invalid choice. Please try again.")
        input("Press Enter to continue...")  

if __name__ == "__main__":
    setup_database()
    main_menu()
    conn.close()