#!/bin/bash

DIR="dbms_programs"
mkdir -p "$DIR"

show_menu() {
    clear
    echo "1. SQL Basics"
    echo "2. DML"
    echo "3. SQL Operators & Functions"
    echo "4. Joins & Subqueries"
    echo "5. Views"
    echo "6. PL/SQL & Cursors"
    echo "0. Exit"
}

while true
do
    show_menu
    read -rp "Select [0-6]: " choice

    case "$choice" in

        1)
            cat > "$DIR/prg1.sql" <<'SQL'
CREATE DATABASE CollegeDB;
USE CollegeDB;

CREATE TABLE Student (
    id INT PRIMARY KEY,
    name VARCHAR(50),
    age INT,
    department VARCHAR(30)
);

DESC Student;
ALTER TABLE Student ADD phone VARCHAR(15);
ALTER TABLE Student MODIFY name VARCHAR(100);
RENAME TABLE Student TO Student_Details;
RENAME TABLE Student_Details TO Student;
SQL
            echo "Saved: $DIR/prg1.sql"
            ;;

        2)
            cat > "$DIR/prg2.sql" <<'SQL'
USE CollegeDB;

CREATE TABLE Student (
    id INT PRIMARY KEY,
    name VARCHAR(50),
    age INT,
    department VARCHAR(30)
);

INSERT INTO Student VALUES
(101, 'Arun', 20, 'CSE'),
(102, 'Priya', 21, 'BCA'),
(103, 'Rahul', 19, 'IT');

SELECT * FROM Student;

UPDATE Student SET age = 21 WHERE id = 101;

DELETE FROM Student WHERE id = 103;

SELECT * FROM Student;
SQL
            echo "Saved: $DIR/prg2.sql"
            ;;

        3)
            cat > "$DIR/prg3.sql" <<'SQL'
USE CollegeDB;

CREATE TABLE Marks (
    id INT,
    name VARCHAR(50),
    mark1 INT,
    mark2 INT,
    mark3 INT
);

INSERT INTO Marks VALUES
(101, 'Arun', 80, 75, 90),
(102, 'Priya', 85, 88, 92),
(103, 'Rahul', 70, 65, 78);

SELECT * FROM Marks;

SELECT name, mark1 + mark2 + mark3 AS Total FROM Marks;

SELECT name, (mark1 + mark2 + mark3) / 3 AS Average FROM Marks;

SELECT COUNT(*) FROM Marks;
SELECT SUM(mark1) FROM Marks;
SELECT AVG(mark1) FROM Marks;
SELECT MAX(mark1) FROM Marks;
SELECT MIN(mark1) FROM Marks;

SELECT UPPER(name) FROM Marks;
SELECT LOWER(name) FROM Marks;
SELECT LENGTH(name) FROM Marks;
SQL
            echo "Saved: $DIR/prg3.sql"
            ;;

        4)
            cat > "$DIR/prg4.sql" <<'SQL'
USE CollegeDB;

CREATE TABLE Department (
    dept_id INT PRIMARY KEY,
    dept_name VARCHAR(30)
);

CREATE TABLE Employee (
    emp_id INT PRIMARY KEY,
    emp_name VARCHAR(50),
    salary INT,
    dept_id INT
);

INSERT INTO Department VALUES
(1, 'CSE'),
(2, 'ECE'),
(3, 'IT');

INSERT INTO Employee VALUES
(101, 'Arun', 50000, 1),
(102, 'Priya', 45000, 1),
(103, 'Rahul', 40000, 2),
(104, 'Divya', 55000, 3);

SELECT e.emp_name, d.dept_name
FROM Employee e
INNER JOIN Department d ON e.dept_id = d.dept_id;

SELECT d.dept_name, e.emp_name
FROM Department d
LEFT JOIN Employee e ON d.dept_id = e.dept_id;

SELECT d.dept_name, e.emp_name
FROM Department d
RIGHT JOIN Employee e ON d.dept_id = e.dept_id;

SELECT emp_name, salary
FROM Employee
WHERE salary = (SELECT MAX(salary) FROM Employee);
SQL
            echo "Saved: $DIR/prg4.sql"
            ;;

        5)
            cat > "$DIR/prg5.sql" <<'SQL'
USE CollegeDB;

CREATE VIEW Employee_View AS
SELECT emp_id, emp_name, salary
FROM Employee;

SELECT * FROM Employee_View;

CREATE VIEW High_Salary AS
SELECT emp_id, emp_name, salary
FROM Employee
WHERE salary > 40000;

SELECT * FROM High_Salary;

SHOW CREATE VIEW Employee_View;

DROP VIEW Employee_View;
SQL
            echo "Saved: $DIR/prg5.sql"
            ;;

        6)
            cat > "$DIR/prg6.sql" <<'SQL'
USE CollegeDB;

CREATE TABLE Employee_PL (
    emp_id INT PRIMARY KEY,
    emp_name VARCHAR(50),
    salary INT,
    department VARCHAR(30)
);

INSERT INTO Employee_PL VALUES
(101, 'Arun', 50000, 'CSE'),
(102, 'Priya', 45000, 'ECE'),
(103, 'Rahul', 40000, 'IT'),
(104, 'Divya', 55000, 'CSE');

DELIMITER //

CREATE PROCEDURE CheckSalary(IN s INT)
BEGIN
    IF s >= 50000 THEN
        SELECT 'High Salary';
    ELSE
        SELECT 'Normal Salary';
    END IF;
END //

DELIMITER ;

CALL CheckSalary(55000);

DELIMITER //

CREATE PROCEDURE PrintNumbers()
BEGIN
    DECLARE n INT DEFAULT 1;

    WHILE n <= 5 DO
        SELECT n;
        SET n = n + 1;
    END WHILE;
END //

DELIMITER ;

CALL PrintNumbers();

DELIMITER //

CREATE PROCEDURE DisplayEmployees()
BEGIN
    DECLARE done INT DEFAULT 0;
    DECLARE id INT;
    DECLARE name VARCHAR(50);

    DECLARE cur CURSOR FOR
        SELECT emp_id, emp_name FROM Employee_PL;

    DECLARE CONTINUE HANDLER FOR NOT FOUND
        SET done = 1;

    OPEN cur;

    read_loop: LOOP
        FETCH cur INTO id, name;

        IF done = 1 THEN
            LEAVE read_loop;
        END IF;

        SELECT id, name;
    END LOOP;

    CLOSE cur;
END //

DELIMITER ;

CALL DisplayEmployees();
SQL
            echo "Saved: $DIR/prg6.sql"
            ;;

        0)
            echo "Bye!"
            exit 0
            ;;

        *)
            echo "Invalid option."
            ;;

    esac

    echo
    read -rp "Press Enter to continue..."
done
