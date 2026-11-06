#!/bin/bash

show_menu() {
    clear
    echo "1. Elementary Data Items"
    echo "2. Conditional Branches & Loops"
    echo "3. Functions"
    echo "4. Classes & Objects"
    echo "5. Inheritance"
    echo "6. Polymorphism"
    echo "7. NumPy"
    echo "8. Pandas"
    echo "9. Matplotlib"
    echo "10. Web Page Using Forms"
    echo "R. Create requirements.txt"
    echo "0. Exit"
}

while true
do
    show_menu
    read -rp "Select [0-10/R]: " choice

    case "$choice" in
        1)
            cat > prg1.py <<'PY'
name = "Joseph"
age = 30
is_student = False
fruits = ["apple", "banana", "cherry"]
scores = [98, 85, 77, 92]
person = {"name": "Shree", "age": 25, "is_student": True}
point_2d = (3, 5)
coordinates_3d = (1, 2, 4)

print(name, age, is_student)
print(fruits)
print(scores)
print(person)
print(point_2d)
print(coordinates_3d)
PY
            echo "Saved: ./prg1.py"
            ;;

        2)
            cat > prg2.py <<'PY'
import math

def roots(a, b, c):
    d = b * b - 4 * a * c
    if d > 0:
        print((-b + math.sqrt(d)) / (2 * a))
        print((-b - math.sqrt(d)) / (2 * a))
    elif d == 0:
        print(-b / (2 * a))
    else:
        print("No real roots")

n = int(input("Number of equations: "))
for i in range(n):
    a = float(input("a: "))
    b = float(input("b: "))
    c = float(input("c: "))
    roots(a, b, c)
PY
            echo "Saved: ./prg2.py"
            ;;

        3)
            cat > prg3.py <<'PY'
def factorial(n):
    r = 1
    for i in range(1, n + 1):
        r *= i
    return r

def npr(n, r):
    return factorial(n) // factorial(n - r)

def ncr(n, r):
    return factorial(n) // (factorial(r) * factorial(n - r))

n = int(input("n: "))
r = int(input("r: "))

if r <= n:
    print("nPr =", npr(n, r))
    print("nCr =", ncr(n, r))
else:
    print("r must be <= n")
PY
            echo "Saved: ./prg3.py"
            ;;

        4)
            cat > prg4.py <<'PY'
class Complex:
    def __init__(self, real, imag):
        self.real = real
        self.imag = imag

    def show(self):
        print(f"{self.real} {'+' if self.imag >= 0 else '-'} {abs(self.imag)}i")

    def __add__(self, other):
        return Complex(self.real + other.real, self.imag + other.imag)

    def __sub__(self, other):
        return Complex(self.real - other.real, self.imag - other.imag)

c1 = Complex(2, 5)
c2 = Complex(int(input("Real: ")), int(input("Imaginary: ")))

c1.show()
c2.show()
(c1 + c2).show()
(c1 - c2).show()
PY
            echo "Saved: ./prg4.py"
            ;;

        5)
            cat > prg5.py <<'PY'
class Employee:
    def __init__(self, name):
        self.name = name

class Employee1(Employee):
    def display(self):
        return self.name + " works at TCS!"

class Employee2(Employee):
    def display(self):
        return self.name + " works at Wipro!"

print(Employee1("Shree").display())
print(Employee2("Rao").display())
PY
            echo "Saved: ./prg5.py"
            ;;

        6)
            cat > prg6.py <<'PY'
class Animal:
    def __init__(self, name):
        self.name = name

class Dog(Animal):
    def speak(self):
        return self.name + " says woof!"

class Cat(Animal):
    def speak(self):
        return self.name + " says meow!"

class Duck(Animal):
    def speak(self):
        return self.name + " says quack!"

animals = [Dog("Buddy"), Cat("Whiskers"), Duck("Daffy")]

for animal in animals:
    print(animal.speak())
PY
            echo "Saved: ./prg6.py"
            ;;

        7)
            cat > prg7.py <<'PY'
import numpy as np

data = np.random.randint(1, 100, 20)
x = data[data > 50]

print(data)
print(x)
print(np.mean(x))
print(np.std(x))
print(np.min(x))
print(np.max(x))
print(np.sum(x))
PY
            echo "Saved: ./prg7.py"
            ;;

        8)
            cat > prg8.py <<'PY'
import pandas as pd

data = {
    "Name": ["Kaviya", "Hari", "Suresh", "Vasanth", "Sivasri", "Madhan", "Suji"],
    "Total": [477, 378, 413, 375, 366, 400, 180],
    "Result": ["Pass", "Pass", "Pass", "Pass", "Pass", "Pass", "Fail"]
}

df = pd.DataFrame(data)
print(df)
PY
            echo "Saved: ./prg8.py"
            ;;

        9)
            cat > prg9.py <<'PY'
import matplotlib.pyplot as plt

x = [1, 2, 3, 4, 5]
y = [10, 15, 13, 18, 20]

plt.plot(x, y, marker="o", linestyle="--")
plt.xlabel("X-axis")
plt.ylabel("Y-axis")
plt.title("Sample Line Plot")
plt.grid()
plt.show()
PY
            echo "Saved: ./prg9.py"
            ;;

        10)
            cat > prg10.py <<'PY'
from flask import Flask, request, render_template_string

app = Flask(__name__)

html = """
<h1>Welcome to the Interactive Web Page</h1>
<form method="POST">
<input type="text" name="username" required>
<input type="submit" value="Submit">
</form>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        return "Hello, " + request.form["username"]
    return render_template_string(html)

if __name__ == "__main__":
    app.run(debug=True)
PY
            echo "Saved: ./prg10.py"
            ;;

        [rR])
            cat > requirements.txt <<'REQ'
numpy
pandas
matplotlib
flask
REQ
            echo "Saved: ./requirements.txt"
            ;;

        0)
            exit 0
            ;;

        *)
            echo "Invalid option."
            ;;
    esac

    echo
    read -rp "Press Enter to continue..."
done
