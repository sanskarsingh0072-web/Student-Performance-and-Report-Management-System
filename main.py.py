# -----------------------------------------------------------------------
# Tkinter Dashboard for Student Report Card Analysis System 
# Uses MySQL backend and existing analytics (radar/progress/remarks)
# -----------------------------------------------------------------------

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkinter.scrolledtext import ScrolledText
import mysql.connector
import matplotlib.pyplot as plt
import numpy as np

# --------------------------- DB CONNECTION -----------------------------
con = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Mahi@2007",#<-----Change if needed-------->
    database="student_analysis"
)
cursor = con.cursor()

# --------------------------- ANALYSIS HELPERS ----------------
def analyze_subject_strength(subjects, values):
    if not subjects or not values:
        return None, None, []
    max_marks = max(values)
    min_marks = min(values)
    strongest = subjects[values.index(max_marks)]
    weakest = subjects[values.index(min_marks)]
    threshold = 40
    below_threshold = [subjects[i] for i, v in enumerate(values) if v < threshold]
    return strongest, weakest, below_threshold

def auto_generate_remarks(percentage, weakest_subject, below_threshold_list=None):
    if percentage is None:
        return "N/A", "No data to generate remarks."

    if percentage >= 91:
        grade = "A1"
    elif percentage >= 81:
        grade = "A2"
    elif percentage >= 71:
        grade = "B1"
    elif percentage >= 61:
        grade = "B2"
    elif percentage >= 51:
        grade = "C1"
    elif percentage >= 41:
        grade = "C2"
    elif percentage >= 33:
        grade = "D"
    else:
        grade = "E"

    if percentage >= 90:
        remark = "Outstanding performance. Keep up the excellent work!"
    elif percentage >= 75:
        remark = "Very good performance. You can aim even higher."
    elif percentage >= 60:
        remark = "Good work. Maintain consistency and keep improving."
    elif percentage >= 50:
        remark = "Satisfactory. Focus more on weak areas for better results."
    elif percentage >= 40:
        remark = "Needs improvement. More practice required."
    else:
        remark = "Poor performance. Get help and focus on fundamentals."

    if weakest_subject:
        remark += f" Special attention needed in {weakest_subject}."

    if below_threshold_list:
        remark += " Also, work on: " + ", ".join(below_threshold_list)

    return grade, remark

# --------------------------- CHARTS ----------------
def radar_chart(name, labels, values, exam_name):
    if not labels or not values:
        messagebox.showinfo("No Data", "No subject data to draw radar chart.")
        return
    values2 = values + [values[0]]
    angles = np.linspace(0, 2 * np.pi, len(values2))
    plt.figure(figsize=(7, 6))
    ax = plt.subplot(111, polar=True)
    ax.plot(angles, values2, marker='o')
    ax.fill(angles, values2, alpha=0.3)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    plt.title(f"{name} - Performance Radar ({exam_name})")
    plt.show()

def progress_line(roll):
    cursor.execute("""
        SELECT exam_types.exam_name, AVG(marks.marks)
        FROM marks
        JOIN exam_types ON marks.exam_id = exam_types.exam_id
        WHERE roll=%s
        GROUP BY marks.exam_id
        ORDER BY marks.exam_id
    """, (roll,))
    rows = cursor.fetchall()
    if not rows:
        messagebox.showinfo("No Data", "No exam history to show progress.")
        return

    exams = [row[0] for row in rows]
    avg_marks = [round(row[1], 2) for row in rows]

    plt.figure(figsize=(7, 5))
    plt.plot(exams, avg_marks, marker='o')
    plt.title(f"Progress Over Time (Roll {roll})")
    plt.xlabel("Exams")
    plt.ylabel("Average Marks")
    plt.grid(True)
    plt.show()

# --------------------------- RANK UPDATE  --------------------
def update_rank(exam_id):
    cursor.execute("""
        SELECT roll, AVG(marks) AS percentage
        FROM marks
        WHERE exam_id=%s
        GROUP BY roll
        ORDER BY percentage DESC
    """, (exam_id,))
    data = cursor.fetchall()

    rank = 1
    for row in data:
        roll = row[0]
        cursor.execute("""
            UPDATE marks SET student_rank=%s
            WHERE roll=%s AND exam_id=%s
        """, (rank, roll, exam_id))
        rank += 1

    con.commit()

# --------------------------- REPORT CARD ------------------------------
def generate_report_card_gui():
    roll = simpledialog.askinteger("Report Card", "Enter Roll Number:", parent=root)
    if roll is None:
        return

    exam_id = simpledialog.askinteger("Report Card", "Enter Exam ID:", parent=root)
    if exam_id is None:
        return

    cursor.execute("SELECT name, class FROM students WHERE roll=%s", (roll,))
    stu = cursor.fetchone()
    if not stu:
        messagebox.showerror("Error", "Student not found.")
        return

    cursor.execute("SELECT exam_name FROM exam_types WHERE exam_id=%s", (exam_id,))
    exam_name = cursor.fetchone()[0]

    cursor.execute("""
        SELECT subjects.subject_name, marks.marks
        FROM marks
        JOIN subjects ON subjects.subject_id = marks.subject_id
        WHERE marks.roll=%s AND marks.exam_id=%s
    """, (roll, exam_id))
    data = cursor.fetchall()

    subjects = []
    values = []
    total = 0
    for s, m in data:
        subjects.append(s)
        values.append(m)
        total += m

    percentage = round(total / len(values), 2)

    cursor.execute("""
        SELECT student_rank FROM marks 
        WHERE roll=%s AND exam_id=%s LIMIT 1
    """, (roll, exam_id))
    rank = cursor.fetchone()[0]

    strongest, weakest, below = analyze_subject_strength(subjects, values)
    grade, remarks = auto_generate_remarks(percentage, weakest, below)

    messagebox.showinfo(
        "Report Card",
        f"Name: {stu[0]}\nClass: {stu[1]}\nExam: {exam_name}\n"
        f"Percentage: {percentage}\nRank: {rank}\nGrade: {grade}\n\nRemarks:\n{remarks}"
    )
# --------------------------- GUI Work ------------------------------
def add_student_gui():
    win = tk.Toplevel(root)
    win.title("Add Student")
    win.geometry("350x230")
    ttk.Label(win, text="Roll Number:").pack(pady=(10,0))
    roll_e = ttk.Entry(win); roll_e.pack()
    ttk.Label(win, text="Name:").pack(pady=(8,0))
    name_e = ttk.Entry(win); name_e.pack()
    ttk.Label(win, text="Gender:").pack(pady=(8,0))
    gender_e = ttk.Entry(win); gender_e.pack()
    ttk.Label(win, text="Class (e.g., 12-A):").pack(pady=(8,0))
    class_e = ttk.Entry(win); class_e.pack()

    def submit():
        try:
            roll = int(roll_e.get())
        except ValueError:
            messagebox.showerror("Invalid", "Roll must be numeric.")
            return
        name = name_e.get().strip()
        gender = gender_e.get().strip()
        cls = class_e.get().strip()
        if not name or not cls:
            messagebox.showerror("Invalid", "Name and Class required.")
            return
        try:
            cursor.execute("INSERT INTO students VALUES (%s,%s,%s,%s)", (roll, name, gender, cls))
            con.commit()
            messagebox.showinfo("Success", "Student added.")
            win.destroy()
        except mysql.connector.IntegrityError:
            messagebox.showerror("Error", "Student with this roll already exists.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    ttk.Button(win, text="Add Student", command=submit).pack(pady=12)

def add_subject_gui():
    subj = simpledialog.askstring("Add Subject", "Enter subject name:", parent=root)
    if not subj:
        return
    try:
        cursor.execute("INSERT INTO subjects (subject_name) VALUES (%s)", (subj.strip(),))
        con.commit()
        messagebox.showinfo("Success", "Subject added.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def remove_subject_gui():
    cursor.execute("SELECT subject_id, subject_name FROM subjects")
    subs = cursor.fetchall()
    if not subs:
        messagebox.showinfo("Info", "No subjects to remove.")
        return
    # Simple selection dialog: show list and ask for ID
    s_list = "\n".join([f"{s[0]} -> {s[1]}" for s in subs])
    sid = simpledialog.askinteger("Remove Subject", f"Available Subjects:\n{s_list}\n\nEnter subject ID to delete:", parent=root)
    if sid is None:
        return
    try:
        cursor.execute("DELETE FROM subjects WHERE subject_id=%s", (sid,))
        con.commit()
        messagebox.showinfo("Success", "Subject removed.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def add_exam_gui():
    exam = simpledialog.askstring("Add Exam Type", "Enter exam name:", parent=root)
    if not exam:
        return
    try:
        cursor.execute("INSERT INTO exam_types (exam_name) VALUES (%s)", (exam.strip(),))
        con.commit()
        messagebox.showinfo("Success", "Exam type added.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def add_marks_gui():
    # popup to get roll and exam
    try:
        roll = simpledialog.askinteger("Add Marks", "Enter Roll Number:", parent=root)
    except Exception:
        return
    if roll is None:
        return
    cursor.execute("SELECT * FROM students WHERE roll=%s", (roll,))
    if cursor.fetchone() is None:
        messagebox.showerror("Error", "Student not found.")
        return

    cursor.execute("SELECT exam_id, exam_name FROM exam_types")
    exams = cursor.fetchall()
    if not exams:
        messagebox.showerror("Error", "No exam types found. Add exam first.")
        return
    # show exams
    ex_list = "\n".join([f"{e[0]} -> {e[1]}" for e in exams])
    exam_id = simpledialog.askinteger("Add Marks", f"Available Exams:\n{ex_list}\n\nEnter Exam ID:", parent=root)
    if exam_id is None:
        return

    cursor.execute("SELECT subject_id, subject_name FROM subjects")
    subjects = cursor.fetchall()
    if not subjects:
        messagebox.showerror("Error", "No subjects found. Add subjects first.")
        return

    # create a marks entry window with entry for each subject
    win = tk.Toplevel(root)
    win.title(f"Enter Marks - Roll {roll} - Exam {exam_id}")
    entries = []
    for sid, sname in subjects:
        frm = ttk.Frame(win)
        frm.pack(fill="x", padx=10, pady=4)
        ttk.Label(frm, text=sname + ":", width=20).pack(side="left")
        e = ttk.Entry(frm, width=10); e.pack(side="left")
        entries.append((sid, sname, e))

    def submit_marks():
        try:
            for sid, sname, ent in entries:
                val = ent.get().strip()
                if val == "":
                    messagebox.showerror("Error", f"Enter marks for {sname}")
                    return
                m = int(val)
                if m < 0 or m > 100:
                    messagebox.showerror("Error", f"Marks for {sname} must be 0-100")
                    return
                cursor.execute("""
                    INSERT INTO marks (roll, exam_id, subject_id, marks)
                    VALUES (%s,%s,%s,%s)
                """, (roll, exam_id, sid, m))
            con.commit()
            update_rank(exam_id)
            messagebox.showinfo("Success", "Marks added.")
            win.destroy()
        except ValueError:
            messagebox.showerror("Error", "Marks must be numeric.")
            con.rollback()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            con.rollback()

    ttk.Button(win, text="Submit Marks", command=submit_marks).pack(pady=10)

def generate_report_card_gui():
    # Get roll & exam via dialogs
    try:
        roll = simpledialog.askinteger("Report Card", "Enter Roll Number:", parent=root)
    except Exception:
        return
    if roll is None:
        return
    try:
        exam_id = simpledialog.askinteger("Report Card", "Enter Exam ID:", parent=root)
    except Exception:
        return
    if exam_id is None:
        return

    cursor.execute("SELECT name, class FROM students WHERE roll=%s", (roll,))
    stu = cursor.fetchone()
    if not stu:
        messagebox.showerror("Error", "Student not found.")
        return

    cursor.execute("SELECT exam_name FROM exam_types WHERE exam_id=%s", (exam_id,))
    exam_row = cursor.fetchone()
    if not exam_row:
        messagebox.showerror("Error", "Exam not found.")
        return
    exam_name = exam_row[0]

    cursor.execute("""
        SELECT subjects.subject_name, marks.marks
        FROM marks
        JOIN subjects ON subjects.subject_id = marks.subject_id
        WHERE marks.roll=%s AND marks.exam_id=%s
    """, (roll, exam_id))
    data = cursor.fetchall()
    if not data:
        messagebox.showinfo("No Data", "No marks found for this student/exam.")
        return

    subjects = []
    values = []
    total = 0
    for sub_name, mark in data:
        subjects.append(sub_name)
        values.append(mark if mark is not None else 0)
        total += (mark if mark is not None else 0)
    percentage = round(total / len(values), 2) if values else 0.0

    cursor.execute("""SELECT student_rank FROM marks WHERE roll=%s AND exam_id=%s LIMIT 1""", (roll, exam_id))
    rank_row = cursor.fetchone()
    rank = rank_row[0] if rank_row else "N/A"

    # Analyze
    strongest, weakest, below_threshold = analyze_subject_strength(subjects, values)
    grade_remark = auto_generate_remarks(percentage, weakest, below_threshold)
    if isinstance(grade_remark, tuple):
        grade, remarks = grade_remark
    else:
        grade = "N/A"
        remarks = grade_remark

    # Compose report text
    report_text = []
    report_text.append("============ REPORT CARD ============")
    report_text.append(f"Name: {stu[0]}")
    report_text.append(f"Class: {stu[1]}")
    report_text.append(f"Exam: {exam_name}")
    report_text.append("------------------------------------")
    for s, v in zip(subjects, values):
        report_text.append(f"{s}: {v}")
    report_text.append("------------------------------------")
    report_text.append(f"Total: {total}")
    report_text.append(f"Percentage: {percentage}")
    report_text.append(f"Rank: {rank}")
    report_text.append(f"Grade: {grade}")
    report_text.append(f"Strongest Subject: {strongest}")
    report_text.append(f"Weakest Subject: {weakest}")
    if below_threshold:
        report_text.append("Subjects below threshold: " + ", ".join(below_threshold))
    report_text.append("Remarks: " + str(remarks))
    report_text.append("====================================")

    # Show report in a new window 
    rpt_win = tk.Toplevel(root)
    rpt_win.title(f"Report Card - Roll {roll}")
    rpt_win.geometry("480x520")
    st = ScrolledText(rpt_win, wrap="word", font=("Consolas", 11))
    st.pack(expand=True, fill="both", padx=10, pady=10)
    st.insert("1.0", "\n".join(report_text))
    st.config(state="disabled")

    # Buttons to show charts (radar/progress)
    btn_frame = ttk.Frame(rpt_win)
    btn_frame.pack(pady=8)
    ttk.Button(btn_frame, text="Show Radar Chart",
               command=lambda: radar_chart(stu[0], subjects, values, exam_name)).grid(row=0, column=0, padx=8)
    ttk.Button(btn_frame, text="Show Progress Graph",
               command=lambda: progress_line(roll)).grid(row=0, column=1, padx=8)


# --------------------------- DASHBOARD UI ------------------------------
root = tk.Tk()
root.title("Student Performance Dashboard")
root.geometry("720x420")
root.resizable(False, False)
root.configure(bg="#F7FAFF")

# Title
title = ttk.Label(root, text="STUDENT PERFORMANCE DASHBOARD", font=("Arial", 18, "bold"))
title.pack(pady=(18, 6))

# Stats frame (fetch counts)
def fetch_counts():
    try:
        cursor.execute("SELECT COUNT(*) FROM students")
        total_students = cursor.fetchone()[0]
    except Exception:
        total_students = "N/A"
    try:
        cursor.execute("SELECT COUNT(*) FROM subjects")
        total_subjects = cursor.fetchone()[0]
    except Exception:
        total_subjects = "N/A"
    try:
        cursor.execute("SELECT COUNT(*) FROM exam_types")
        total_exams = cursor.fetchone()[0]
    except Exception:
        total_exams = "N/A"
    return total_students, total_subjects, total_exams

tot_stu, tot_sub, tot_ex = fetch_counts()
stats_frame = ttk.Frame(root)
stats_frame.pack(pady=8)

ttk.Label(stats_frame, text=f"Total Students: {tot_stu}", font=("Arial", 12)).grid(row=0, column=0, padx=20)
ttk.Label(stats_frame, text=f"Total Subjects: {tot_sub}", font=("Arial", 12)).grid(row=0, column=1, padx=20)
ttk.Label(stats_frame, text=f"Total Exams: {tot_ex}", font=("Arial", 12)).grid(row=0, column=2, padx=20)

# Buttons grid
btn_frame = ttk.Frame(root)
btn_frame.pack(pady=20)

ttk.Button(btn_frame, text="Add Student", width=22, command=add_student_gui).grid(row=0, column=0, padx=10, pady=10)
ttk.Button(btn_frame, text="Add Subject", width=22, command=add_subject_gui).grid(row=0, column=1, padx=10, pady=10)
ttk.Button(btn_frame, text="Remove Subject", width=22, command=remove_subject_gui).grid(row=0, column=2, padx=10, pady=10)

ttk.Button(btn_frame, text="Add Exam Type", width=22, command=add_exam_gui).grid(row=1, column=0, padx=10, pady=10)
ttk.Button(btn_frame, text="Add Marks", width=22, command=add_marks_gui).grid(row=1, column=1, padx=10, pady=10)
ttk.Button(btn_frame, text="Generate Report Card", width=22, command=generate_report_card_gui).grid(row=1, column=2, padx=10, pady=10)

ttk.Button(root, text="Refresh Counts", command=lambda: refresh_counts()).pack(pady=(0,6))
ttk.Button(root, text="Exit", command=root.destroy).pack()

def refresh_counts():
    s, sub, ex = fetch_counts()
    for widget in stats_frame.winfo_children():
        widget.destroy()
    ttk.Label(stats_frame, text=f"Total Students: {s}", font=("Arial", 12)).grid(row=0, column=0, padx=20)
    ttk.Label(stats_frame, text=f"Total Subjects: {sub}", font=("Arial", 12)).grid(row=0, column=1, padx=20)
    ttk.Label(stats_frame, text=f"Total Exams: {ex}", font=("Arial", 12)).grid(row=0, column=2, padx=20)

# Start the app
root.mainloop()
