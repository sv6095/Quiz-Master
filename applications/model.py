from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# User Model 
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    qualification = db.Column(db.String(100), nullable=True)
    dob = db.Column(db.Date, nullable=True)
    role = db.Column(db.String(20), nullable=False)  

# Subject Model
class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    chapters = db.relationship("Chapter", backref="subject", cascade="all, delete-orphan")

# Chapter Model
class Chapter(db.Model):
    __tablename__ = 'chapters'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    questions = db.relationship("Question", backref="chapter", cascade="all, delete-orphan")
    quizzes = db.relationship("Quiz", backref="chapter", cascade="all, delete-orphan")


# Quiz Model
class Quiz(db.Model):
    __tablename__ = 'quizzes'
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)
    date_of_quiz = db.Column(db.Date, nullable=False)
    time_duration = db.Column(db.String(5), nullable=False)  
    title = db.Column(db.String(100), nullable=False)
    questions = db.relationship("Question", backref="quiz", cascade="all, delete-orphan")  

# Question Model
class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=True)  
    question_statement = db.Column(db.String(500), nullable=False)
    option1 = db.Column(db.String(100), nullable=False)
    option2 = db.Column(db.String(100), nullable=False)
    option3 = db.Column(db.String(100), nullable=False)
    option4 = db.Column(db.String(100), nullable=False)
    correct_option = db.Column(db.Integer, nullable=False)  

# Scores Model
class Score(db.Model):
    __tablename__ = 'scores'
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    time_stamp_of_attempt = db.Column(db.DateTime, nullable=False)
    total_scored = db.Column(db.Integer, nullable=False)
    quiz = db.relationship("Quiz", backref="scores")
    user = db.relationship("User", backref="scores")
