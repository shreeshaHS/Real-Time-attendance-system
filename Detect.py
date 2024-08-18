import cv2
import sqlite3
import time
import csv
import os
import tkinter as tk
from tkinter import simpledialog
from datetime import datetime

# Function to connect to the database and retrieve student information
def get_student_info(student_id):
    try:
        conn = sqlite3.connect('instance/database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, regno FROM student WHERE id = ?", (student_id,))
        student_info = cursor.fetchone()
        conn.close()
        return student_info
    except sqlite3.DatabaseError as e:
        print(f"Error: {e}")
        return None

def log_attendance(student_id, subject_name):
    try:
        conn = sqlite3.connect('instance/database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO attendance (student_id, timestamp, subject) VALUES (?, ?, ?)", 
                       (student_id, datetime.utcnow(), subject_name))
        conn.commit()
        conn.close()
    except sqlite3.DatabaseError as e:
        print(f"Error: {e}")

def save_to_csv(timestamp, student_id, name, regno, subject_name):
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, student_id, name, regno, subject_name])

# Initialize CSV file
csv_file = 'detected_faces.csv'

# Create a new CSV file if it doesn't exist
if not os.path.isfile(csv_file):
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Timestamp', 'Student ID', 'Name', 'Reg No', 'Subject'])

# Load pre-trained face detection and recognition models
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('recognizer/Trainingdata.yml')  # Load the trained recognizer model

# Initialize video capture
cap = cv2.VideoCapture(0)

# Dictionary to store the display time and info for each detected face
display_info = {}

# Set to track recorded student IDs
recorded_ids = set()

# Load recorded IDs from the existing CSV file
if os.path.isfile(csv_file):
    with open(csv_file, mode='r', newline='') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row
        for row in reader:
            recorded_ids.add(row[1])  # Assuming student ID is in the second column

# Create Tkinter window for subject input
root = tk.Tk()
root.withdraw()  # Hide the root window

# Prompt user for subject name
subject_name = simpledialog.askstring("Input", "Enter the subject name:", parent=root)

if subject_name:
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

        current_time = time.time()

        for (x, y, w, h) in faces:
            # Predict the face using the recognizer
            id_, confidence = recognizer.predict(gray[y:y+h, x:x+w])

            # If confidence is less than 100, a match is found
            if confidence < 100:
                student_info = get_student_info(id_)
                if student_info:
                    student_id, name, regno = student_info
                    # Check if the student ID has already been recorded
                    if student_id not in recorded_ids:
                        # Log attendance in the database
                        log_attendance(student_id, subject_name)
                        # Save student info to CSV
                        save_to_csv(datetime.utcnow(), student_id, name, regno, subject_name)
                        recorded_ids.add(student_id)
                    # Update display info
                    display_info[student_id] = (name, regno, subject_name, current_time + 5)
            else:
                # If confidence is high, mark as Unknown
                display_info[id_] = ('Unknown', '', '', current_time + 5)

            # Draw rectangle around the face
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

        # Display the name and registration number for each detected face for 5 seconds
        for id_, (name, regno, subject, display_until) in list(display_info.items()):
            if current_time < display_until:
                text = f'Name: {name}, Reg No: {regno}, Subject: {subject}' if regno else 'Unknown'
                # Find a face rectangle to use for positioning the text
                for (x, y, w, h) in faces:
                    cv2.putText(frame, text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0) if regno else (0, 0, 255), 2)
            else:
                del display_info[id_]

        cv2.imshow('Face Recognition', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
else:
    print("No subject name entered. Exiting.")
