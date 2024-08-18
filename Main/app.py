import cv2
import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash,get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)

# User table
class User(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    
# Student table
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    department = db.Column(db.String(50))
    name = db.Column(db.String(50))
    regno = db.Column(db.String(50))
    phone = db.Column(db.String(15))
    email = db.Column(db.String(50))
    photo = db.Column(db.String(100))
    semester = db.Column(db.String(10))
    course = db.Column(db.String(20))
    year = db.Column(db.String(10))
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    subject = db.Column(db.String(100))

    student = db.relationship('Student', backref=db.backref('attendances', lazy=True))
def create_db():
    with app.app_context():
        db.create_all()

create_db()
@app.route('/')
def login():
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.form
        user = User.query.filter_by(username=data['new_username']).first()
        
        if user:
            return 'User already exists!'
        new_user = User(username=data['new_username'], password=generate_password_hash(data['new_password']), email=data['email_add'])
        
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('sign-up.html')

@app.route('/login', methods=['POST'])
def login_post():
    if request.method == 'POST':
        data = request.form
        user = User.query.filter_by(username=data['username']).first()
        if not user or not check_password_hash(user.password, data['password']):
            flash('Login failed! Invalid username or password!', 'danger')
            return redirect(url_for('login'))
        
        # Assuming you have a last_login field in the User model
        user.last_login = datetime.utcnow()
        db.session.commit()
        flash('Login successful!', 'success')
        return redirect(url_for('container'))
    flash("login success")
    return render_template('main.html')

@app.route('/forgotpass', methods=['GET', 'POST'])
def forgotpass():
    if request.method == 'POST':
        email = request.form['email']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        user = User.query.filter_by(email=email).first()

        if user:
            if new_password == confirm_password:
                hashed_password = generate_password_hash(new_password)
                user.password = hashed_password
                db.session.commit()
                flash('Your password has been updated!', 'success')
                return redirect(url_for('login'))
            else:
                flash('Passwords do not match!', 'danger')
        else:
            flash('Email not found!', 'danger')

    return render_template('forgotpass.html')


@app.route('/details')
def details():
    users = User.query.all()
    return render_template('detail.html', users=users)

@app.route('/container')
def container():
    return render_template('main.html')


@app.route('/success')
def success():
    students = Student.query.all()
    return render_template('student.html', students=students)

@app.route('/student')
def student_page():
    return render_template('student.html')
@app.route('/save_student', methods=['POST'])
def save_student():
    if request.method == 'POST':
        data = request.form
        existing_student = Student.query.filter(
            Student.name == data['name'],
            Student.regno == data['regno']
        ).first()
        if existing_student:
            return "Student already exists!"

        photo_path = capture_photo(data['name'])

        new_student = Student(
            department=data['department'],
            name=data['name'],
            phone=data['phone'],
            regno=data['regno'],
            email=data['email'],
            semester=data['semester'],
            photo=photo_path,
            course=data['course'],
            year=data['year']
        )
        db.session.add(new_student)
        db.session.commit()
        
        # Fetch all students to display in the student.html template
        students = Student.query.all()
        flash('saved','success')
        return render_template('student.html', students=students)

        

@app.route('/update_student', methods=['POST'])
def update_student():
    if request.method == 'POST':
        data = request.form
        student = Student.query.filter_by(regno=data['regno']).first()
        
        if student:
            student.department = data['department']
            student.name = data['name']
            student.phone = data['phone']
            student.email = data['email']
            student.semester = data['semester']
            student.course = data['course']
            student.year = data['year']
            db.session.commit()
            flash('Student information updated successfully!', 'success')
        else:
            flash('Student not found!', 'danger')
        
        students = Student.query.all()
        return render_template('student.html', students=students)

@app.route('/delete_student', methods=['POST'])
def delete_student():
    regno = request.form.get('regno')
    if regno:
        student = Student.query.filter_by(regno=regno).first()
        if student:
            db.session.delete(student)
            db.session.commit()
            flash('Student information deleted successfully!', 'success')
        else:
            flash('Student not found!', 'danger')
    else:
        flash('No registration number provided!', 'danger')
    
    return redirect(url_for('show_all_students'))


@app.route('/search_student', methods=['GET'])
def search_student():
    regno = request.args.get('search-input')
    if regno:
        student = Student.query.filter_by(regno=regno).first()
        if student:
            return render_template('student.html', students=[student])
    flash('No student found with the provided registration number', 'danger')
    return redirect(url_for('success'))

@app.route('/show_all_students', methods=['GET'])
def show_all_students():
    
    students = Student.query.all()
    return render_template('student.html', students=students)

@app.route('/capture_photo', methods=['GET', 'POST'])
def capture_photo(student_name):
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    output_dir = 'Main/static/captured_images'
    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return "Error: Could not open webcam."

    images_captured = 0
    while images_captured < 70:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            photo_path = os.path.join(output_dir, f'{student_name}_{images_captured}.jpg')
            cv2.imwrite(photo_path, gray[y:y + h, x:x + w])
            images_captured += 1

        cv2.imshow('Capture Faces', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return os.path.join(output_dir, f'{student_name}_0.jpg')



@app.route('/train', methods=['GET','POST'])
def train():
    import subprocess
    # Call the Python script to capture images
    subprocess.call(['python', 'train.py'])
      # Send a JSON response indicating success
    return redirect(url_for('container'))



@app.route('/openfloder', methods=['GET','POST'])
def open():
    import subprocess
    # Call the Python script to capture images
    subprocess.call(['python', 'openfloder.py'])
      # Send a JSON response indicating success
    return redirect(url_for('container'))




@app.route('/detect', methods=['GET','POST'])
def detect():
    import subprocess
    # Call the Python script to capture images
    subprocess.call(['python', 'Detect.py'])
      # Send a JSON response indicating success
    return redirect(url_for('container'))

@app.route('/exit')
def exit_page():
    return render_template('login.html')



@app.route('/attendance')
def attendance():
    attendances = Attendance.query.join(Student).all()
    return render_template('attendance.html', attendances=attendances)


from datetime import date


def is_student_present(student_id, check_date=None):
    if check_date is None:
        check_date = date.today()
    start_of_day = datetime.combine(check_date, datetime.min.time())
    end_of_day = datetime.combine(check_date, datetime.max.time())

    attendance = Attendance.query.filter(
        Attendance.student_id == student_id,
        Attendance.timestamp >= start_of_day,
        Attendance.timestamp <= end_of_day
    ).first()
    
    return attendance is not None

def is_student_present(student_id, check_date=None):
    from datetime import date, datetime

    if check_date is None:
        check_date = date.today()
    
    start_of_day = datetime.combine(check_date, datetime.min.time())
    end_of_day = datetime.combine(check_date, datetime.max.time())

    attendance = Attendance.query.filter(
        Attendance.student_id == student_id,
        Attendance.timestamp >= start_of_day,
        Attendance.timestamp <= end_of_day
    ).first()
    
    return attendance is not None



@app.route('/get_response', methods=['POST'])
def get_response():
    user_message = request.json.get('message')
    response = generate_response(user_message)
    return jsonify({'response': response})

def generate_response(message):
    
    responses = {
        'good morning':'very good morning sir',
        'what is chatbot':'A computer program designed to simulate conversation with human users,esoecially over the internet',
        'hello': 'Hi there! How can I assist you with the application?',
            'how it work': (
            ' Step1: The camera detects and locates the images of a face alone or in a crowd.\n'
            'Step2: Image of the face is captured and analyzed.\n'
            'Step3: Converting image to a dataset.\n'
            'Step4: Finding Match.'
        
    ),
    
    'who is your creator':'Creator wants to be Unknown HA HA....',
    'bye': 'Goodbye! If you have any more questions, feel free to ask.',
    'what is machine learning':'Machine learning is an branch of AI',
    'how are you':'when my software is working than i am Fine and You',
    'fine':'Nice to here'
    }
    return responses.get(message.lower(), 'Sorry, I do not understand your question.')

@app.route('/developer_info')
def developer_info():
    return render_template('devleper.html')

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
