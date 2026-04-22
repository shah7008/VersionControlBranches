import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime
import calendar

class CalendarDialog(tk.Toplevel):
    def __init__(self, parent, title="Select Date"):
        super().__init__(parent)
        self.title(title)
        self.geometry("250x250")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.selected_date = None
        
        now = datetime.datetime.now()
        self.current_year = now.year
        self.current_month = now.month

        self.setup_ui()
        self.wait_window()

    def setup_ui(self):
        # Header for Month/Year
        header_frame = tk.Frame(self)
        header_frame.pack(fill=tk.X, pady=5)

        tk.Button(header_frame, text="<", command=self.prev_month).pack(side=tk.LEFT, padx=10)
        self.month_year_label = tk.Label(header_frame, text="", font=("Arial", 10, "bold"))
        self.month_year_label.pack(side=tk.LEFT, expand=True)
        tk.Button(header_frame, text=">", command=self.next_month).pack(side=tk.RIGHT, padx=10)

        # Days of week header
        days_frame = tk.Frame(self)
        days_frame.pack(fill=tk.X)
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day in enumerate(days):
            tk.Label(days_frame, text=day, width=3).grid(row=0, column=i)

        # Calendar grid
        self.calendar_frame = tk.Frame(self)
        self.calendar_frame.pack(fill=tk.BOTH, expand=True)

        self.update_calendar()

    def update_calendar(self):
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()

        self.month_year_label.config(text=f"{calendar.month_name[self.current_month]} {self.current_year}")

        cal = calendar.monthcalendar(self.current_year, self.current_month)
        
        for r, week in enumerate(cal):
            for c, day in enumerate(week):
                if day != 0:
                    btn = tk.Button(self.calendar_frame, text=str(day), width=3, 
                                    command=lambda d=day: self.select_date(d))
                    btn.grid(row=r, column=c, padx=1, pady=1)

    def prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.update_calendar()

    def next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.update_calendar()

    def select_date(self, day):
        self.selected_date = f"{self.current_year}-{self.current_month:02d}-{day:02d}"
        self.destroy()

class StudyPlannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Study Planner")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        self.db_name = "study_planner.db"
        self.apply_styles()
        self.setup_database()
        self.create_ui()
        self.load_subjects()
        self.load_daily_tasks()
        self.update_progress()

    def apply_styles(self):
        self.root.configure(bg="#f4f7f6")
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except:
            pass
        
        style.configure("TFrame", background="#f4f7f6")
        style.configure("TLabelframe", background="#f4f7f6", foreground="#2a9d8f", font=("Segoe UI", 12, "bold"))
        style.configure("TLabelframe.Label", background="#f4f7f6", foreground="#2a9d8f")
        style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff", rowheight=25, font=("Segoe UI", 10), borderwidth=0)
        style.configure("Treeview.Heading", background="#e9ecef", foreground="#495057", font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[('selected', '#2a9d8f')], foreground=[('selected', 'white')])
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=5)
        
    def setup_database(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                deadline TEXT,
                priority TEXT,
                est_hours REAL,
                completed_hours REAL DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_tasks (
                id INTEGER PRIMARY KEY,
                subject_id INTEGER,
                date TEXT,
                planned_hours REAL,
                is_completed INTEGER DEFAULT 0,
                FOREIGN KEY(subject_id) REFERENCES subjects(id)
            )
        ''')
        
        # Insert default subjects if none exist
        cursor.execute("SELECT COUNT(*) FROM subjects")
        if cursor.fetchone()[0] == 0:
            today = datetime.datetime.now()
            default_deadline = (today + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
            
            defaults = [
                ("Probability & Statistics", default_deadline, "High", 30.0),
                ("Database Systems", default_deadline, "High", 30.0),
                ("Software Development & Construction", default_deadline, "High", 35.0),
                ("Software Design & Architecture", default_deadline, "High", 35.0),
                ("Understanding of Holy Quran", default_deadline, "Low", 10.0),
                ("Professional Practices", default_deadline, "Low", 10.0),
                ("Pakistan Studies", default_deadline, "Low", 10.0)
            ]
            
            cursor.executemany('''
                INSERT INTO subjects (name, deadline, priority, est_hours)
                VALUES (?, ?, ?, ?)
            ''', defaults)
            
        conn.commit()
        conn.close()

    def create_ui(self):
        # --- Top: Input Panel ---
        input_frame = ttk.LabelFrame(self.root, text="Manage Subjects", padding=10)
        input_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(input_frame, text="Subject:", bg="#f4f7f6").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.subject_var = tk.StringVar()
        tk.Entry(input_frame, textvariable=self.subject_var, width=25, relief=tk.FLAT, highlightbackground="#ccc", highlightthickness=1).grid(row=0, column=1, padx=5, pady=2)
        
        tk.Label(input_frame, text="Deadline:", bg="#f4f7f6").grid(row=0, column=2, sticky=tk.W, pady=2, padx=(10,0))
        self.deadline_var = tk.StringVar()
        self.deadline_entry = tk.Entry(input_frame, textvariable=self.deadline_var, width=12, state="readonly", relief=tk.FLAT, highlightbackground="#ccc", highlightthickness=1)
        self.deadline_entry.grid(row=0, column=3, padx=5, pady=2)
        tk.Button(input_frame, text="📅", command=self.pick_date, relief=tk.FLAT, bg="#e9ecef", cursor="hand2").grid(row=0, column=4)
        
        tk.Label(input_frame, text="Total Hours:", bg="#f4f7f6").grid(row=0, column=5, sticky=tk.W, padx=(15, 0), pady=2)
        self.hours_var = tk.StringVar()
        tk.Spinbox(input_frame, from_=1, to=200, textvariable=self.hours_var, width=5, relief=tk.FLAT).grid(row=0, column=6, padx=5, pady=2)
        
        tk.Label(input_frame, text="Priority:", bg="#f4f7f6").grid(row=0, column=7, sticky=tk.W, padx=(15, 0), pady=2)
        self.priority_var = tk.StringVar(value="Medium")
        ttk.Combobox(input_frame, textvariable=self.priority_var, values=["High", "Medium", "Low"], width=8, state="readonly").grid(row=0, column=8, padx=5, pady=2)
        
        # Action Buttons
        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=1, column=0, columnspan=9, pady=15)
        
        tk.Button(btn_frame, text="Add / Update", bg="#2a9d8f", fg="white", font=("Segoe UI", 10, "bold"), relief=tk.FLAT, cursor="hand2", padx=10, command=self.add_subject).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete Selected", bg="#e76f51", fg="white", font=("Segoe UI", 10, "bold"), relief=tk.FLAT, cursor="hand2", padx=10, command=self.delete_subject).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Clear Fields", command=self.clear_inputs, bg="#e9ecef", font=("Segoe UI", 10, "bold"), relief=tk.FLAT, cursor="hand2", padx=10).pack(side=tk.LEFT, padx=5)
        
        # --- Middle Layout ---
        mid_frame = ttk.Frame(self.root)
        mid_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        # Left: Subject List
        list_frame = ttk.LabelFrame(mid_frame, text="Subject Overview", padding=5)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.tree = ttk.Treeview(list_frame, columns=("ID", "Name", "Deadline", "Priority", "Progress"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Name", text="Subject Name")
        self.tree.heading("Deadline", text="Deadline")
        self.tree.heading("Priority", text="Priority")
        self.tree.heading("Progress", text="Progress")
        
        self.tree.column("ID", width=30, anchor=tk.CENTER)
        self.tree.column("Name", width=150)
        self.tree.column("Deadline", width=80, anchor=tk.CENTER)
        self.tree.column("Priority", width=70, anchor=tk.CENTER)
        self.tree.column("Progress", width=80, anchor=tk.CENTER)
        
        # Add color tags
        self.tree.tag_configure('urgent', background='#ffe8e8') # Red for high/close
        self.tree.tag_configure('normal', background='#ffffff')
        self.tree.tag_configure('low', background='#e8f5e9') # Green for low
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", self.on_subject_select)
        
        # Right: Daily Tasks
        task_frame = ttk.LabelFrame(mid_frame, text="Today's Study Plan", padding=5)
        task_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        plan_control_frame = ttk.Frame(task_frame)
        plan_control_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(plan_control_frame, text="Hours available today:", bg="#f4f7f6").pack(side=tk.LEFT)
        self.daily_hours_var = tk.StringVar(value="4")
        tk.Spinbox(plan_control_frame, from_=1, to=24, textvariable=self.daily_hours_var, width=4, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        tk.Button(plan_control_frame, text="Generate Plan", bg="#264653", fg="white", font=("Segoe UI", 10, "bold"), relief=tk.FLAT, cursor="hand2", padx=10, command=self.generate_plan).pack(side=tk.RIGHT)
        
        self.task_tree = ttk.Treeview(task_frame, columns=("ID", "Subject", "Hours", "Status"), show="headings", height=8)
        self.task_tree.heading("ID", text="ID")
        self.task_tree.heading("Subject", text="Subject")
        self.task_tree.heading("Hours", text="Time")
        self.task_tree.heading("Status", text="Status")
        
        self.task_tree.column("ID", width=30, anchor=tk.CENTER)
        self.task_tree.column("Subject", width=150)
        self.task_tree.column("Hours", width=60, anchor=tk.CENTER)
        self.task_tree.column("Status", width=80, anchor=tk.CENTER)
        
        self.task_tree.pack(fill=tk.BOTH, expand=True)
        
        tk.Button(task_frame, text="✔ Mark Selected Complete", bg="#2a9d8f", fg="white", font=("Segoe UI", 10, "bold"), relief=tk.FLAT, cursor="hand2", pady=5, command=self.mark_complete).pack(fill=tk.X, pady=10)
        
        # --- Bottom: Progress & Warnings ---
        bottom_frame = tk.Frame(self.root, padx=15, pady=10, bg="#f4f7f6")
        bottom_frame.pack(fill=tk.X)
        
        self.warning_label = tk.Label(bottom_frame, text="Suggestions: Keep up the good work!", fg="#264653", bg="#f4f7f6", font=("Segoe UI", 10, "italic"))
        self.warning_label.pack(anchor=tk.W, pady=2)
        
        progress_frame = tk.Frame(bottom_frame, bg="#f4f7f6")
        progress_frame.pack(fill=tk.X, pady=5)
        tk.Label(progress_frame, text="Overall Progress:", bg="#f4f7f6", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", mode="determinate", length=600)
        self.progress_bar.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        self.progress_label = tk.Label(progress_frame, text="0%", bg="#f4f7f6", font=("Segoe UI", 10, "bold"))
        self.progress_label.pack(side=tk.LEFT)

    def pick_date(self):
        dlg = CalendarDialog(self.root)
        if dlg.selected_date:
            self.deadline_var.set(dlg.selected_date)

    def load_subjects(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
            
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, deadline, priority, est_hours, completed_hours FROM subjects")
        
        today = datetime.datetime.now().date()
        warnings = []
        
        for row in cursor.fetchall():
            s_id, name, deadline_str, priority, est, comp = row
            progress_str = f"{comp:.1f}/{est:.1f}h"
            
            # Determine color tag
            tag = 'normal'
            if priority == "High":
                tag = 'urgent'
            elif priority == "Low":
                tag = 'low'
                
            if deadline_str:
                try:
                    deadline_date = datetime.datetime.strptime(deadline_str, "%Y-%m-%d").date()
                    days_left = (deadline_date - today).days
                    if days_left <= 3 and comp < est:
                        tag = 'urgent'
                        warnings.append(f"Urgent: {name} deadline is close!")
                except ValueError:
                    pass
            
            self.tree.insert("", tk.END, values=(s_id, name, deadline_str, priority, progress_str), tags=(tag,))
            
        conn.close()
        
        if warnings:
            self.warning_label.config(text=" | ".join(warnings), fg="#e76f51")
        else:
            self.warning_label.config(text="Suggestions: Review subjects requiring more time.", fg="#2a9d8f")

    def load_daily_tasks(self):
        for row in self.task_tree.get_children():
            self.task_tree.delete(row)
            
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT t.id, s.name, t.planned_hours, t.is_completed 
            FROM daily_tasks t
            JOIN subjects s ON t.subject_id = s.id
            WHERE t.date = ?
        ''', (today_str,))
        
        for row in cursor.fetchall():
            t_id, name, hours, is_completed = row
            status = "Done" if is_completed else "Pending"
            self.task_tree.insert("", tk.END, values=(t_id, name, f"{hours:.1f}h", status))
            
        conn.close()

    def update_progress(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(est_hours), SUM(completed_hours) FROM subjects")
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            total_est = result[0]
            total_comp = result[1] if result[1] else 0
            pct = (total_comp / total_est) * 100
            pct = min(pct, 100.0) # Cap at 100%
            self.progress_bar["value"] = pct
            self.progress_label.config(text=f"{pct:.1f}%")
        else:
            self.progress_bar["value"] = 0
            self.progress_label.config(text="0%")

    def add_subject(self):
        name = self.subject_var.get().strip()
        deadline = self.deadline_var.get()
        hours_str = self.hours_var.get()
        priority = self.priority_var.get()
        
        if not name or not deadline or not hours_str:
            messagebox.showerror("Error", "Please fill all fields.")
            return
            
        try:
            hours = float(hours_str)
        except ValueError:
            messagebox.showerror("Error", "Total hours must be a number.")
            return
            
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            # Check if exists (update)
            cursor.execute("SELECT id FROM subjects WHERE name=?", (name,))
            if cursor.fetchone():
                cursor.execute("UPDATE subjects SET deadline=?, priority=?, est_hours=? WHERE name=?", 
                               (deadline, priority, hours, name))
            else:
                cursor.execute("INSERT INTO subjects (name, deadline, priority, est_hours) VALUES (?, ?, ?, ?)",
                               (name, deadline, priority, hours))
            conn.commit()
            self.clear_inputs()
            self.load_subjects()
            self.update_progress()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", str(e))
        finally:
            conn.close()

    def delete_subject(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a subject to delete.")
            return
            
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this subject?"):
            item = self.tree.item(selected[0])
            s_id = item['values'][0]
            
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM daily_tasks WHERE subject_id=?", (s_id,))
            cursor.execute("DELETE FROM subjects WHERE id=?", (s_id,))
            conn.commit()
            conn.close()
            
            self.load_subjects()
            self.load_daily_tasks()
            self.update_progress()

    def clear_inputs(self):
        self.subject_var.set("")
        self.deadline_var.set("")
        self.hours_var.set("")
        self.priority_var.set("Medium")

    def on_subject_select(self, event):
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            values = item['values']
            self.subject_var.set(values[1])
            self.deadline_var.set(values[2])
            self.priority_var.set(values[3])
            
            # extract est_hours from progress string (e.g. "0.0/30.0h")
            prog_str = values[4]
            est_hours = prog_str.split('/')[1].replace('h', '')
            self.hours_var.set(est_hours)

    def generate_plan(self):
        try:
            available_hours = float(self.daily_hours_var.get())
        except ValueError:
            messagebox.showerror("Error", "Available daily hours must be a number.")
            return
            
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Get incomplete subjects
        cursor.execute("SELECT id, name, priority, est_hours, completed_hours FROM subjects WHERE completed_hours < est_hours")
        subjects = cursor.fetchall()
        
        if not subjects:
            messagebox.showinfo("Info", "No pending subjects to study!")
            conn.close()
            return
            
        # Priority Weighting for Time Distribution
        weights = {"High": 3, "Medium": 2, "Low": 1}
        total_weight = sum(weights[s[2]] for s in subjects)
        
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Clear today's existing incomplete tasks to regenerate
        cursor.execute("DELETE FROM daily_tasks WHERE date=? AND is_completed=0", (today_str,))
        
        for s in subjects:
            s_id = s[0]
            priority = s[2]
            
            # Distribution logic based on weight
            weight = weights[priority]
            allocated_hours = (weight / total_weight) * available_hours
            
            # Ensure we don't allocate more than remaining hours
            remaining_req = s[3] - s[4]
            allocated_hours = min(allocated_hours, remaining_req)
            
            if allocated_hours > 0.1: # Minimum sensible time unit
                cursor.execute('''
                    INSERT INTO daily_tasks (subject_id, date, planned_hours, is_completed)
                    VALUES (?, ?, ?, 0)
                ''', (s_id, today_str, round(allocated_hours, 1)))
                
        conn.commit()
        conn.close()
        
        self.load_daily_tasks()
        messagebox.showinfo("Success", f"Study plan generated successfully for today ({available_hours} hours distributed).")

    def mark_complete(self):
        selected = self.task_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Select a task to mark as complete.")
            return
            
        item = self.task_tree.item(selected[0])
        t_id = item['values'][0]
        status = item['values'][3]
        
        if status == "Done":
            return
            
        planned_hours = float(item['values'][2].replace('h', ''))
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Update task status
        cursor.execute("UPDATE daily_tasks SET is_completed=1 WHERE id=?", (t_id,))
        
        # Add completed hours to subject
        cursor.execute('''
            UPDATE subjects 
            SET completed_hours = completed_hours + ? 
            WHERE id = (SELECT subject_id FROM daily_tasks WHERE id=?)
        ''', (planned_hours, t_id))
        
        conn.commit()
        conn.close()
        
        self.load_daily_tasks()
        self.load_subjects()
        self.update_progress()
        self.warning_label.config(text="Great job completing a task!", fg="#2a9d8f")

if __name__ == "__main__":
    root = tk.Tk()
    app = StudyPlannerApp(root)
    root.mainloop()
