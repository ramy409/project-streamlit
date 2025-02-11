import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

class HomeworkSystem:
    def __init__(self):
        st.set_page_config(page_title="Homework Evaluation System")
        if 'logged_in' not in st.session_state:
            st.session_state.logged_in = False
        if 'user_type' not in st.session_state:
            st.session_state.user_type = None
        if 'username' not in st.session_state:
            st.session_state.username = None
            
        self.main()

    def main(self):
        if not st.session_state.logged_in:
            self.login_page()
        else:
            if st.session_state.user_type == 'Admin':
                self.admin_page()
            elif st.session_state.user_type == 'Teacher':
                self.teacher_page()
            elif st.session_state.user_type == 'Student':
                self.student_page()

    def login_page(self):
        st.title("Login")
        with st.form(key='login_form'):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            user_type = st.selectbox("User Type", ["Admin", "Teacher", "Student"])
            submit = st.form_submit_button("Login")

            if submit:
                conn = sqlite3.connect('HomeworkEvaluationSystem.db')
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM User 
                    WHERE username=? AND password=? AND role=?
                """, (username, password, user_type))
                user = cursor.fetchone()
                conn.close()

                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_type = user_type
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Invalid credentials")

    def admin_page(self):
        st.title(f"Welcome Admin: {st.session_state.username}")
        
        option = st.selectbox("Select Action", [
            "Add Teacher", "Add Student", "Add Subject", 
            "Delete Account", "Delete Subject"
        ])

        if option == "Add Teacher":
            with st.form(key='add_teacher_form'):
                name = st.text_input("Teacher Name")
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                
                conn = sqlite3.connect('HomeworkEvaluationSystem.db')
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM subjects")
                subjects = cursor.fetchall()
                conn.close()
                
                selected_subjects = st.multiselect(
                    "Select Subjects", 
                    [subject[1] for subject in subjects]
                )
                
                if st.form_submit_button("Add Teacher"):
                    conn = sqlite3.connect('HomeworkEvaluationSystem.db')
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO User (username, password, user_type)
                        VALUES (?, ?, 'Teacher', ?)
                    """, (username, password, name))
                    
                    teacher_id = cursor.lastrowid
                    
                    # Add teacher-subject relationships
                    for subject_name in selected_subjects:
                        cursor.execute("SELECT id FROM subjects WHERE name=?", (subject_name,))
                        subject_id = cursor.fetchone()[0]
                        cursor.execute("""
                            INSERT INTO user_subjects (user_id, subject_id)
                            VALUES (?, ?)
                        """, (teacher_id, subject_id))
                    
                    conn.commit()
                    conn.close()
                    st.success("Teacher added successfully!")

        elif option == "Add Student":
            with st.form(key='add_student_form'):
                name = st.text_input("Student Name")
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                
                conn = sqlite3.connect('HomeworkEvaluationSystem.db')
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM subjects")
                subjects = cursor.fetchall()
                conn.close()
                
                selected_subjects = st.multiselect(
                    "Select Subjects", 
                    [subject[1] for subject in subjects]
                )
                
                if st.form_submit_button("Add Student"):
                    try:
                        conn = sqlite3.connect('HomeworkEvaluationSystem.db', timeout=30)
                        cursor = conn.cursor()
                        
                        # First verify all subjects exist before making any changes
                        for subject_name in selected_subjects:
                            cursor.execute("SELECT name FROM subjects WHERE code=?", (subject_name,))
                            if cursor.fetchone() is None:
                                st.error(f"Error: Subject '{subject_name}' does not exist in the system")
                                return
                        
                        # If all subjects exist, proceed with adding the student
                        cursor.execute("""
                            INSERT INTO User (username, password, user_type)
                            VALUES (?, ?, 'Student', ?)
                        """, (username, password, name))
                        
                        student_id = cursor.lastrowid
                        
                        # Add student-subject relationships
                        for subject_name in selected_subjects:
                            cursor.execute("SELECT name FROM subjects WHERE code=?", (subject_name,))
                            subject_id = cursor.fetchone()[0]
                            cursor.execute("""
                                INSERT INTO user_subjects (user_id, subject_id)
                                VALUES (?, ?)
                            """, (student_id, subject_id))
                        
                        conn.commit()
                        st.success("Student added successfully!")
                    except sqlite3.OperationalError as e:
                        st.error("Database error: Please try again in a moment")
                        raise e
                    finally:
                        conn.close()

        elif option == "Add Subject":
            with st.form(key='add_subject_form'):
                name = st.text_input("Subject Name")
                code = st.text_input("Subject Code")
                
                if st.form_submit_button("Add Subject"):
                    conn = sqlite3.connect('HomeworkEvaluationSystem.db')
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO subjects (name, code)
                        VALUES (?, ?)
                    """, (name, code))
                    conn.commit()
                    conn.close()
                    st.success("Subject added successfully!")

        elif option == "Delete Account":
            account_type = st.radio("Select account type to delete", ["Student", "Teacher"])
            
            conn = sqlite3.connect('HomeworkEvaluationSystem.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, name FROM User
                WHERE user_type=?
            """, (account_type,))
            accounts = cursor.fetchall()
            conn.close()
            
            if accounts:
                account_to_delete = st.selectbox(
                    f"Select {account_type} to delete",
                    [f"{acc[2]} ({acc[1]})" for acc in accounts]
                )
                
                if st.button("Delete Account"):
                    account_id = accounts[[f"{acc[2]} ({acc[1]})" for acc in accounts].index(account_to_delete)][0]
                    conn = sqlite3.connect('HomeworkEvaluationSystem.db')
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM User WHERE id=?", (account_id,))
                    conn.commit()
                    conn.close()
                    st.success("Account deleted successfully!")
            else:
                st.warning(f"No {account_type}s found")

        elif option == "Delete Subject":
            conn = sqlite3.connect('HomeworkEvaluationSystem.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM subjects")
            subjects = cursor.fetchall()
            conn.close()
            
            if subjects:
                subject_to_delete = st.selectbox(
                    "Select subject to delete",
                    [subject[1] for subject in subjects]
                )
                
                if st.button("Delete Subject"):
                    conn = sqlite3.connect('HomeworkEvaluationSystem.db')
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM subjects WHERE name=?", (subject_to_delete,))
                    conn.commit()
                    conn.close()
                    st.success("Subject deleted successfully!")
            else:
                st.warning("No subjects found")

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user_type = None
            st.session_state.username = None
            st.rerun()

    def teacher_page(self):
        st.title(f"Welcome Teacher: {st.session_state.username}")
        
        conn = sqlite3.connect('HomeworkEvaluationSystem.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.name 
            FROM subjects s
            JOIN user_subjects us ON s.id = us.subject_id
            JOIN User u ON us.user_id = u.id
            WHERE u.username = ?
        """, (st.session_state.username,))
        subjects = cursor.fetchall()
        conn.close()

        if subjects:
            selected_subject = st.selectbox("Select Subject", [s[0] for s in subjects])
            action = st.radio("Select Action", ["Add Assignment", "Grade Assignment"])

            if action == "Add Assignment":
                with st.form(key='add_assignment_form'):
                    question_number = st.number_input("Question Number", min_value=1, step=1)
                    question_text = st.text_area("Question")
                    send_to = st.radio("Send to", ["Single Student", "All Students"])
                    
                    if send_to == "Single Student":
                        conn = sqlite3.connect('HomeworkEvaluationSystem.db')
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT DISTINCT u.id, u.name 
                            FROM User u
                            JOIN user_subjects us ON u.id = us.user_id
                            JOIN subjects s ON us.subject_id = s.id
                            WHERE u.user_type = 'Student' 
                            AND s.name = ?
                        """, (selected_subject,))
                        students = cursor.fetchall()
                        conn.close()
                        
                        selected_student = st.selectbox(
                            "Select Student",
                            [student[1] for student in students]
                        )
                    
                    if st.form_submit_button("Add Assignment"):
                        conn = sqlite3.connect('HomeworkEvaluationSystem.db')
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO assignments (subject_id, question_number, question_text)
                            SELECT id, ?, ? FROM subjects WHERE name = ?
                        """, (question_number, question_text, selected_subject))
                        
                        assignment_id = cursor.lastrowid
                        
                        if send_to == "Single Student":
                            student_id = students[[s[1] for s in students].index(selected_student)][0]
                            cursor.execute("""
                                INSERT INTO AssignmentStudent (student_id, assignment_id)
                                VALUES (?, ?)
                            """, (student_id, assignment_id))
                        else:
                            cursor.execute("""
                                INSERT INTO AssignmentStudent (student_id, assignment_id)
                                SELECT DISTINCT u.id, ?
                                FROM User u
                                JOIN user_subjects us ON u.id = us.user_id
                                JOIN subjects s ON us.subject_id = s.id
                                WHERE u.user_type = 'Student'
                                AND s.name = ?
                            """, (assignment_id, selected_subject))
                        
                        conn.commit()
                        conn.close()
                        st.success("Assignment added successfully!")

            elif action == "Grade Assignment":
                conn = sqlite3.connect('HomeworkEvaluationSystem.db')
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT u.name, sa.id, a.question_number, sa.answer
                    FROM AssignmentStudent sa
                    JOIN assignments a ON sa.assignment_id = a.id
                    JOIN subjects s ON a.subject_id = s.id
                    JOIN User u ON sa.student_id = u.id
                    WHERE s.name = ? AND sa.grade IS NULL
                """, (selected_subject,))
                pending_assignments = cursor.fetchall()
                conn.close()

                if pending_assignments:
                    selected_assignment = st.selectbox(
                        "Select Assignment to Grade",
                        [f"Student: {a[0]} - Question: {a[2]}" for a in pending_assignments]
                    )
                    
                    assignment_index = [f"Student: {a[0]} - Question: {a[2]}" for a in pending_assignments].index(selected_assignment)
                    assignment_data = pending_assignments[assignment_index]
                    
                    st.write(f"Answer: {assignment_data[3]}")
                    
                    with st.form(key='grade_assignment_form'):
                        grade = st.selectbox("Grade", [0, 1, 2])
                        feedback = st.text_area("Feedback (optional)")
                        
                        if st.form_submit_button("Submit Grade"):
                            conn = sqlite3.connect('HomeworkEvaluationSystem.db')
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE AssignmentStudent
                                SET grade = ?, feedback = ?
                                WHERE id = ?
                            """, (grade, feedback if feedback else None, assignment_data[1]))
                            conn.commit()
                            conn.close()
                            st.success("Grade submitted successfully!")
                            st.rerun()
                else:
                    st.info("No assignments pending for grading")
        else:
            st.warning("No subjects assigned to you. Please contact admin to assign subjects.")

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user_type = None
            st.session_state.username = None
            st.rerun()

    def student_page(self):
        st.title(f"Welcome Student: {st.session_state.username}")
        
        conn = sqlite3.connect('HomeworkEvaluationSystem.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.name 
            FROM subjects s
            JOIN user_subjects us ON s.id = us.subject_id
            JOIN User u ON us.user_id = u.id
            WHERE u.username = ?
        """, (st.session_state.username,))
        subjects = cursor.fetchall()
        conn.close()

        if subjects:
            selected_subject = st.selectbox("Select Subject", [s[0] for s in subjects])
            action = st.radio("Select Action", ["Do Homework", "View Grades"])

            if action == "Do Homework":
                conn = sqlite3.connect('HomeworkEvaluationSystem.db')
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT a.id, a.question_number, a.question_text
                    FROM assignments a
                    JOIN subjects s ON a.subject_id = s.id
                    JOIN AssignmentStudent sa ON a.id = sa.assignment_id
                    JOIN User u ON sa.student_id = u.id
                    WHERE s.name = ? AND u.username = ? AND sa.answer IS NULL
                """, (selected_subject, st.session_state.username))
                pending_assignments = cursor.fetchall()
                conn.close()

                if pending_assignments:
                    selected_question = st.selectbox(
                        "Select Question",
                        [f"Question {a[1]}" for a in pending_assignments]
                    )
                    
                    question_index = [f"Question {a[1]}" for a in pending_assignments].index(selected_question)
                    question_data = pending_assignments[question_index]
                    
                    st.write(f"Question: {question_data[2]}")
                    
                    with st.form(key='submit_answer_form'):
                        answer = st.text_area("Your Answer")
                        
                        if st.form_submit_button("Submit Answer"):
                            conn = sqlite3.connect('HomeworkEvaluationSystem.db')
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE AssignmentStudent
                                SET answer = ?
                                WHERE assignment_id = ? AND student_id = (
                                    SELECT id FROM User WHERE username = ?
                                )
                            """, (answer, question_data[0], st.session_state.username))
                            conn.commit()
                            conn.close()
                            st.success("Answer submitted successfully!")
                            st.rerun()
                else:
                    st.info("No pending assignments")

            elif action == "View Grades":
                conn = sqlite3.connect('HomeworkEvaluationSystem.db')
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT a.question_number, sa.grade, sa.feedback
                    FROM AssignmentStudent sa
                    JOIN assignments a ON sa.assignment_id = a.id
                    JOIN subjects s ON a.subject_id = s.id
                    JOIN User u ON sa.student_id = u.id
                    WHERE s.name = ? AND u.username = ? AND sa.grade IS NOT NULL
                """, (selected_subject, st.session_state.username))
                graded_assignments = cursor.fetchall()
                conn.close()

                if graded_assignments:
                    for assignment in graded_assignments:
                        st.write(f"Question {assignment[0]}")
                        st.write(f"Grade: {assignment[1]}/2")
                        if assignment[2]:
                            st.write(f"Feedback: {assignment[2]}")
                        else:
                            st.write("No feedback provided")
                        st.write("---")
                else:
                    st.info("No graded assignments yet")
        else:
            st.warning("No subjects assigned to you. Please contact admin to assign subjects.")

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user_type = None
            st.session_state.username = None
            st.rerun()

if __name__ == "__main__":
    app = HomeworkSystem()
