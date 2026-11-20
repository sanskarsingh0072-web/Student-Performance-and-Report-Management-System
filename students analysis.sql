CREATE DATABASE student_analysis;
USE student_analysis;

-- STUDENTS TABLE
CREATE TABLE students (
    roll INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50),
    gender VARCHAR(10),
    class VARCHAR(10)
);

-- SUBJECTS TABLE 
CREATE TABLE subjects (
    subject_id INT PRIMARY KEY AUTO_INCREMENT,
    subject_name VARCHAR(50)
);

-- EXAMS TABLE
CREATE TABLE exam_types (
    exam_id INT PRIMARY KEY AUTO_INCREMENT,
    exam_name VARCHAR(50)
);

-- MARKS TABLE
CREATE TABLE marks (
    mark_id INT PRIMARY KEY AUTO_INCREMENT,
    roll INT,
    exam_id INT,
    subject_id INT,
    marks INT,
    student_rank INT,
    FOREIGN KEY (roll) REFERENCES students(roll),
    FOREIGN KEY (exam_id) REFERENCES exam_types(exam_id),
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);
