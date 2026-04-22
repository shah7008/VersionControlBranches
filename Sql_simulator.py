import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import csv
import os

class SQLSimulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SQL Query Simulator")
        self.root.geometry("850x650")
        self.root.minsize(600, 400)
        
        self.db_name = "simulator.db"
        self.history = []
        
        self.apply_styles()
        self.setup_database()
        self.create_ui()

    def apply_styles(self):
        self.root.configure(bg="#2b2d42")
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except:
            pass
        
        style.configure("TFrame", background="#2b2d42")
        style.configure("TLabelframe", background="#2b2d42", foreground="#8d99ae", font=("Segoe UI", 12, "bold"), borderwidth=2)
        style.configure("TLabelframe.Label", background="#2b2d42", foreground="#8d99ae")
        style.configure("Treeview", background="#edf2f4", foreground="#2b2d42", fieldbackground="#edf2f4", borderwidth=0, font=("Consolas", 10))
        style.configure("Treeview.Heading", background="#8d99ae", foreground="#2b2d42", font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[('selected', '#ef233c')], foreground=[('selected', 'white')])
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=5)
        
    def setup_database(self):
        """Creates the database and predefined tables if they do not exist."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Create students table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    marks INTEGER
                )
            ''')
            
            # Create courses table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS courses (
                    id INTEGER PRIMARY KEY,
                    course_name TEXT NOT NULL
                )
            ''')
            
            # Create employees table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY,
                    salary REAL
                )
            ''')
            
            # Insert sample data if tables are empty
            cursor.execute("SELECT COUNT(*) FROM students")
            if cursor.fetchone()[0] == 0:
                cursor.executemany("INSERT INTO students (name, marks) VALUES (?, ?)", 
                                   [('Alice', 85), ('Bob', 92), ('Charlie', 78), ('David', 95)])
                
            cursor.execute("SELECT COUNT(*) FROM courses")
            if cursor.fetchone()[0] == 0:
                cursor.executemany("INSERT INTO courses (course_name) VALUES (?)", 
                                   [('Database Systems',), ('Data Structures',), ('Operating Systems',)])
                
            cursor.execute("SELECT COUNT(*) FROM employees")
            if cursor.fetchone()[0] == 0:
                cursor.executemany("INSERT INTO employees (salary) VALUES (?)", 
                                   [(50000.0,), (65000.0,), (80000.0,)])
                
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to initialize database:\n{e}")

    def create_ui(self):
        # --- Top Frame: Query Editor ---
        editor_frame = ttk.LabelFrame(self.root, text="Query Editor", padding=10)
        editor_frame.pack(fill=tk.BOTH, expand=False, padx=15, pady=10)
        
        self.query_text = tk.Text(editor_frame, height=5, font=("Consolas", 12), bg="#1e1e2e", fg="#cdd6f4", insertbackground="white", relief=tk.FLAT, bd=0)
        self.query_text.pack(fill=tk.BOTH, expand=True)
        
        # --- Middle Frame: Controls ---
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=15, pady=5)
        
        run_btn = tk.Button(control_frame, text="▶ Run Query", command=self.run_query, bg="#ef233c", fg="white", font=("Segoe UI", 11, "bold"), relief=tk.FLAT, padx=10, pady=5, cursor="hand2")
        run_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        clear_btn = tk.Button(control_frame, text="Clear", command=self.clear_ui, bg="#8d99ae", fg="white", font=("Segoe UI", 11, "bold"), relief=tk.FLAT, padx=10, pady=5, cursor="hand2")
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        history_btn = tk.Button(control_frame, text="📜 History", command=self.show_history, bg="#8d99ae", fg="white", font=("Segoe UI", 11, "bold"), relief=tk.FLAT, padx=10, pady=5, cursor="hand2")
        history_btn.pack(side=tk.LEFT, padx=5)
        
        export_btn = tk.Button(control_frame, text="💾 Export CSV", command=self.export_csv, bg="#8d99ae", fg="white", font=("Segoe UI", 11, "bold"), relief=tk.FLAT, padx=10, pady=5, cursor="hand2")
        export_btn.pack(side=tk.LEFT, padx=5)
        
        help_btn = tk.Button(control_frame, text="❓ Help / Practice", command=self.show_help, bg="#8d99ae", fg="white", font=("Segoe UI", 11, "bold"), relief=tk.FLAT, padx=10, pady=5, cursor="hand2")
        help_btn.pack(side=tk.RIGHT, padx=5)
        
        # --- Bottom Frame: Results ---
        result_frame = ttk.LabelFrame(self.root, text="Query Results", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Treeview with Scrollbars
        tree_scroll_y = ttk.Scrollbar(result_frame)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        tree_scroll_x = ttk.Scrollbar(result_frame, orient='horizontal')
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.tree = ttk.Treeview(result_frame, yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)
        
        # --- Status Bar / Error Display ---
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_label = tk.Label(self.root, textvariable=self.status_var, bg="#2b2d42", fg="#8d99ae", font=("Segoe UI", 10), anchor=tk.W, padx=15)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 5))

    def run_query(self):
        query = self.query_text.get("1.0", tk.END).strip()
        if not query:
            self.show_error("Query is empty!")
            return
            
        self.history.append(query)
        
        # Clear existing tree data
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = []
        
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(query)
            
            # Check if it's a SELECT query (returns rows)
            if query.upper().startswith("SELECT") or query.upper().startswith("PRAGMA"):
                rows = cursor.fetchall()
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    
                    self.tree["columns"] = columns
                    self.tree["show"] = "headings"
                    
                    for col in columns:
                        self.tree.heading(col, text=col)
                        self.tree.column(col, width=100)
                        
                    for row in rows:
                        self.tree.insert("", tk.END, values=row)
                        
                    self.show_success(f"Query executed successfully. Returned {len(rows)} row(s).")
                else:
                    self.show_success("Query executed successfully, but returned no data.")
            else:
                conn.commit()
                self.show_success(f"Query executed successfully. {cursor.rowcount} row(s) affected.")
                
            conn.close()
            
        except sqlite3.Error as e:
            self.show_error(f"SQL Error: {e}")
        except Exception as e:
            self.show_error(f"Error: {e}")

    def clear_ui(self):
        self.query_text.delete("1.0", tk.END)
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = []
        self.show_success("Ready")

    def export_csv(self):
        if not self.tree.get_children():
            messagebox.showinfo("Export", "No results to export.")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            title="Save Results as CSV"
        )
        
        if file_path:
            try:
                with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    
                    # Write headers
                    headers = self.tree["columns"]
                    writer.writerow(headers)
                    
                    # Write rows
                    for item_id in self.tree.get_children():
                        row_data = self.tree.item(item_id)["values"]
                        writer.writerow(row_data)
                        
                messagebox.showinfo("Success", f"Data exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save CSV:\n{e}")

    def show_history(self):
        history_window = tk.Toplevel(self.root)
        history_window.title("Query History")
        history_window.geometry("400x300")
        
        listbox = tk.Listbox(history_window, font=("Consolas", 10))
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for q in self.history:
            listbox.insert(tk.END, q)
            
        def load_selected(event):
            selection = listbox.curselection()
            if selection:
                query = listbox.get(selection[0])
                self.query_text.delete("1.0", tk.END)
                self.query_text.insert("1.0", query)
                history_window.destroy()
                
        listbox.bind("<Double-Button-1>", load_selected)
        
        tk.Label(history_window, text="Double-click a query to load it.", fg="gray").pack()

    def show_help(self):
        help_window = tk.Toplevel(self.root)
        help_window.title("SQL Help & Practice")
        help_window.geometry("500x400")
        
        text_widget = tk.Text(help_window, wrap=tk.WORD, font=("Arial", 11), padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        help_content = """=== SQL Commands Cheat Sheet ===

1. SELECT
Used to fetch data from a database.
Example: SELECT * FROM students;
Example: SELECT name, marks FROM students WHERE marks > 80;

2. INSERT
Used to insert new rows.
Example: INSERT INTO courses (course_name) VALUES ('Python Basics');

3. UPDATE
Used to modify existing data.
Example: UPDATE employees SET salary = 90000 WHERE id = 1;

4. DELETE
Used to remove rows.
Example: DELETE FROM students WHERE marks < 50;

=== Available Tables ===
- students (id, name, marks)
- courses (id, course_name)
- employees (id, salary)

=== Practice Questions ===
Q1: Find all students who scored more than 90.
Q2: Add a new course 'Machine Learning'.
Q3: Increase the salary of all employees by 5000.
Q4: List all courses.

* Tip: Check for typos in table/column names if you get errors!"""
        
        text_widget.insert("1.0", help_content)
        text_widget.config(state=tk.DISABLED) # Make read-only

    def show_error(self, message):
        self.status_var.set(message)
        self.status_label.config(fg="#ef233c", font=("Segoe UI", 10, "bold"))
        
    def show_success(self, message):
        self.status_var.set(message)
        self.status_label.config(fg="#4CAF50", font=("Segoe UI", 10, "bold"))


if __name__ == "__main__":
    root = tk.Tk()
    app = SQLSimulatorApp(root)
    root.mainloop()
