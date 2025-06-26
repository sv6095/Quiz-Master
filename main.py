import matplotlib
from sqlalchemy import func
matplotlib.use('Agg') 
from flask import Flask, flash, render_template, session, request, redirect, url_for
import matplotlib.pyplot as plt
from applications.database import db
from applications.config import Config
from applications.model import *  
import io
import base64
from datetime import datetime
import os

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        db.create_all()
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin',email='admin@quizmaster.com',password='admin',full_name='Administrator',role='Admin')

            db.session.add(admin)
            db.session.commit()

    return app

app = create_app()

@app.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user and user.role == 'Admin':  # Ensure user is not None
            return redirect(url_for('admin_dashboard'))
        elif user:
            return redirect(url_for('user_dashboard'))
    return render_template('index.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    # Get search query parameter if any
    search_query = request.args.get('query', '')
    
    if search_query:
        # Filter subjects, chapters, and quizzes based on search query
        subjects = Subject.query.filter(Subject.name.ilike(f'%{search_query}%')).all()
        chapters = Chapter.query.filter(Chapter.name.ilike(f'%{search_query}%')).all()
        quizzes = Quiz.query.filter(Quiz.title.ilike(f'%{search_query}%')).all()
    else:
        # Default behavior without search
        subjects = Subject.query.all()
        chapters = Chapter.query.all()
        quizzes = Quiz.query.all()
    
    # Count questions for each quiz
    questions_count = {}
    for quiz in quizzes:
        questions_count[quiz.id] = Question.query.filter_by(chapter_id=quiz.chapter_id).count()
    
    # Pass all necessary data to template including search query
    return render_template('admin_dashboard.html',subjects=subjects,chapters=chapters,quizzes=quizzes,questions_count=questions_count,search_query=search_query)

@app.route('/admin/quiz_management')
def quiz_management():
    search_query = request.args.get('query', '')
    
    if search_query:
        quizzes = Quiz.query.filter(Quiz.title.ilike(f'%{search_query}%')).all()
        questions = Question.query.filter(Question.question_statement.ilike(f'%{search_query}%')).all()
    else:
        quizzes = Quiz.query.all()
        questions = Question.query.all()
    
    chapters = Chapter.query.all()
    subjects = Subject.query.all()
    
    return render_template('quiz_management.html',quizzes=quizzes, questions=questions,chapters=chapters,subjects=subjects, search_query=search_query)

@app.route('/admin/summary')
def summary():
    """Admin summary displaying visualized quiz statistics."""
    subjects = Subject.query.all()
    quizzes = Quiz.query.all()
    scores = Score.query.all()
    

    subject_names = [subject.name for subject in subjects]
    quiz_counts = []
    for subject in subjects:
        chapter_ids = [chapter.id for chapter in subject.chapters]
        count = Quiz.query.filter(Quiz.chapter_id.in_(chapter_ids)).count() if chapter_ids else 0
        quiz_counts.append(count)

    # Generate bar chart
    bar_chart_img = io.BytesIO()
    fig, ax = plt.subplots()
    ax.bar(subject_names, quiz_counts, color='skyblue')
    ax.set_title('Quizzes per Subject')
    ax.set_xlabel('Subjects')
    ax.set_ylabel('Number of Quizzes')
    plt.savefig(bar_chart_img, format='png')
    bar_chart_img.seek(0)
    bar_chart_base64 = base64.b64encode(bar_chart_img.getvalue()).decode()

    # Initialize quiz_avg_scores to avoid UnboundLocalError
    quiz_avg_scores = {}
    pie_chart_base64 = None
    if scores:
        quiz_attempts = {}
        
        for score in scores:
            if score.quiz_id not in quiz_avg_scores:
                quiz_avg_scores[score.quiz_id] = score.total_scored
                quiz_attempts[score.quiz_id] = 1
            else:
                quiz_avg_scores[score.quiz_id] += score.total_scored
                quiz_attempts[score.quiz_id] += 1
        
        # Calculate averages
        for quiz_id in quiz_avg_scores:
            quiz_avg_scores[quiz_id] /= quiz_attempts[quiz_id]
        pie_data = []
        pie_labels = []
        
        for quiz in quizzes:
            if quiz.id in quiz_avg_scores:
                pie_data.append(quiz_avg_scores[quiz.id])
                pie_labels.append(quiz.title)
        
        if pie_data:  
            pie_chart_img = io.BytesIO()
            fig, ax = plt.subplots()
            ax.pie(pie_data, labels=pie_labels, autopct='%1.1f%%')
            ax.set_title('Quiz Score Distribution')
            plt.savefig(pie_chart_img, format='png')
            pie_chart_img.seek(0)
            pie_chart_base64 = base64.b64encode(pie_chart_img.getvalue()).decode()
    subject_attempts = []
    subject_scores = []
    
    for subject in subjects:
        chapter_ids = [chapter.id for chapter in subject.chapters]
        quiz_ids = [quiz.id for quiz in Quiz.query.filter(Quiz.chapter_id.in_(chapter_ids)).all()] if chapter_ids else []
        
        # Count attempts for this subject
        attempts = Score.query.filter(Score.quiz_id.in_(quiz_ids)).count() if quiz_ids else 0
        subject_attempts.append(attempts)
        
        # Calculate average score for this subject
        if attempts > 0:
            total = sum(score.total_scored for score in Score.query.filter(Score.quiz_id.in_(quiz_ids)).all())
            subject_scores.append(total / attempts)
        else:
            subject_scores.append(None)
    
    # Get recent scores for activity table
    recent_scores = Score.query.order_by(Score.time_stamp_of_attempt.desc()).limit(10).all()
    top_quizzes = []
    quiz_avg_scores_list = []
    
    if quiz_avg_scores:
        sorted_quiz_ids = sorted(quiz_avg_scores.keys(), key=lambda x: quiz_avg_scores[x], reverse=True)[:5]
        top_quizzes = [Quiz.query.get(quiz_id) for quiz_id in sorted_quiz_ids]
        quiz_avg_scores_list = [quiz_avg_scores[quiz.id] for quiz in top_quizzes]

    return render_template('summary.html', 
                          bar_chart=bar_chart_base64, pie_chart=pie_chart_base64,subjects=subjects,subject_attempts=subject_attempts,subject_scores=subject_scores,recent_scores=recent_scores,top_quizzes=top_quizzes,quiz_avg_scores=quiz_avg_scores_list)

@app.route('/admin/add_subject', methods=['POST'])
def add_subject():
    """Handles adding a new subject."""
    name = request.form.get('name')
    description = request.form.get('description')

    if name and description:
        subject = Subject(name=name, description=description)
        db.session.add(subject)
        db.session.commit()
        flash("Subject added successfully!", "success")
    else:
        flash("All fields are required!", "danger")

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_chapter', methods=['POST'])
def add_chapter():
    name = request.form.get('name')
    description = request.form.get('description')
    subject_id = request.form.get('subject_id')

    if name and description and subject_id:
        chapter = Chapter(name=name, description=description, subject_id=subject_id)
        db.session.add(chapter)
        db.session.commit()
        flash("Chapter added successfully!", "success")
    else:
        flash("All fields are required!", "danger")

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit_subject/<int:subject_id>', methods=['POST'])
def edit_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    
    subject.name = request.form.get('name')
    subject.description = request.form.get('description')

    db.session.commit()
    flash("Subject updated successfully!", "success")

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_subject/<int:subject_id>', methods=['POST'])
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)

    db.session.delete(subject)
    db.session.commit()
    flash("Subject deleted successfully!", "success")

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit_chapter/<int:chapter_id>', methods=['POST'])
def edit_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    
    chapter.name = request.form.get('name')
    chapter.description = request.form.get('description')
    chapter.subject_id = request.form.get('subject_id')

    db.session.commit()
    flash("Chapter updated successfully!", "success")

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_chapter/<int:chapter_id>', methods=['POST'])
def delete_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)

    db.session.delete(chapter)
    db.session.commit()
    flash("Chapter deleted successfully!", "success")

    return redirect(url_for('admin_dashboard'))

@app.route('/add_question', methods=['POST'])
def add_question():
    chapter_id = request.form.get('chapter_id')
    question_statement = request.form.get('question_statement')
    option1 = request.form.get('option1')
    option2 = request.form.get('option2')
    option3 = request.form.get('option3')
    option4 = request.form.get('option4')
    correct_option = int(request.form.get('correct_option'))

    new_question = Question(
        chapter_id=chapter_id, 
        question_statement=question_statement,
        option1=option1,
        option2=option2,
        option3=option3,
        option4=option4,
        correct_option=correct_option
    )
    db.session.add(new_question)
    db.session.commit()
    flash('Question added successfully!', 'success')
    return redirect(url_for('quiz_management'))


@app.route('/edit_question/<int:question_id>', methods=['POST'])
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)
    question.chapter_id = request.form.get('chapter_id')  # Link question to chapter
    question.question_statement = request.form.get('question_statement')
    question.option1 = request.form.get('option1')
    question.option2 = request.form.get('option2')
    question.option3 = request.form.get('option3')
    question.option4 = request.form.get('option4')
    question.correct_option = int(request.form.get('correct_option'))

    db.session.commit()
    flash('Question updated successfully!', 'success')
    return redirect(url_for('quiz_management'))


@app.route('/admin/add_quiz', methods=['POST'])
def add_quiz():
    title = request.form.get('title')
    chapter_id = request.form.get('chapter_id')  # Get chapter_id from form
    date_of_quiz = datetime.strptime(request.form.get('date_of_quiz'), '%Y-%m-%d').date()
    time_duration = request.form.get('time_duration')
    
    quiz = Quiz(title=title, chapter_id=chapter_id, date_of_quiz=date_of_quiz, time_duration=time_duration)
    db.session.add(quiz)
    db.session.commit()
    flash("Quiz added successfully!", "success")
    return redirect(url_for('quiz_management'))

@app.route('/admin/delete_quiz/<int:quiz_id>', methods=['POST'])
def delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    db.session.delete(quiz)
    db.session.commit()
    flash("Quiz deleted successfully!", "success")
    return redirect(url_for('quiz_management'))

@app.route('/admin/edit_quiz/<int:quiz_id>', methods=['POST'])
def edit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    quiz.title = request.form.get('title')
    quiz.date_of_quiz = datetime.strptime(request.form.get('date_of_quiz'), '%Y-%m-%d').date()
    quiz.time_duration = request.form.get('time_duration')
    quiz.chapter_id = request.form.get('chapter_id')
    db.session.commit()
    flash("Quiz updated successfully!", "success")
    return redirect(url_for('quiz_management'))

@app.route('/admin/delete_question/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    db.session.delete(question)
    db.session.commit()
    flash("Question deleted successfully!", "success")
    return redirect(url_for('quiz_management'))

@app.route('/user/dashboard')
def user_dashboard():
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to access your dashboard", "warning")
        return redirect(url_for('login'))
    
    # Get search query parameter
    search_query = request.args.get('query', '')
    
    user = User.query.get(user_id)
    if not user:
        flash("User not found. Please log in again.", "danger")
        return redirect(url_for('login'))
    
    today = datetime.now().date()
    
    # Apply search filter if query exists
    if search_query:
        upcoming_quizzes = Quiz.query.join(Chapter).join(Subject).filter(
            Quiz.date_of_quiz >= today,
            db.or_(
                Quiz.title.ilike(f'%{search_query}%'),
                Chapter.name.ilike(f'%{search_query}%'),
                Subject.name.ilike(f'%{search_query}%')
            )
        ).all()
    else:
        upcoming_quizzes = Quiz.query.filter(Quiz.date_of_quiz >= today).all()
    
    # Count questions for each quiz
    questions_count = {}
    for quiz in upcoming_quizzes:
        questions_count[quiz.id] = Question.query.filter_by(chapter_id=quiz.chapter_id).count()
    
    # Filter out attempted quizzes
    attempted_quiz_ids = [score.quiz_id for score in Score.query.filter_by(user_id=user_id).all()]
    if attempted_quiz_ids:
        upcoming_quizzes = [quiz for quiz in upcoming_quizzes if quiz.id not in attempted_quiz_ids]
    
    recent_scores = Score.query.filter_by(user_id=user_id).order_by(Score.time_stamp_of_attempt.desc()).limit(5).all()
    for score in recent_scores:
        quiz = Quiz.query.get(score.quiz_id)
        score.quiz_title = quiz.title if quiz and hasattr(quiz, 'title') else "Unknown"
    
    return render_template('user_dashboard.html',upcoming_quizzes=upcoming_quizzes,recent_scores=recent_scores, questions_count=questions_count,search_query=search_query)

@app.route('/user/scores')
def scores():
    user_id = session.get('user_id')
    scores = Score.query.filter_by(user_id=user_id).all()
    return render_template('scores.html', quiz_scores=scores)

@app.route('/user/summary')
def user_summary():
    user_id = session.get('user_id')
    subjects = Subject.query.all()
    user_scores = Score.query.filter_by(user_id=user_id).all()
    
    # Get subject information
    subject_names = [subject.name for subject in subjects]
    quiz_counts = []
    for subject in subjects:
        chapter_ids = [chapter.id for chapter in subject.chapters]
        count = Quiz.query.filter(Quiz.chapter_id.in_(chapter_ids)).count()
        quiz_counts.append(count)
    bar_chart_img = io.BytesIO()
    fig, ax = plt.subplots()
    ax.bar(subject_names, quiz_counts, color='skyblue')
    ax.set_title('Quizzes per Subject')
    ax.set_xlabel('Subjects')
    ax.set_ylabel('Number of Quizzes')
    plt.savefig(bar_chart_img, format='png')
    bar_chart_img.seek(0)
    bar_chart_base64 = base64.b64encode(bar_chart_img.getvalue()).decode()
    pie_chart_base64 = None
    if user_scores:
        # Get only the quizzes that the user has attempted
        attempted_quiz_ids = [score.quiz_id for score in user_scores]
        attempted_quizzes = Quiz.query.filter(Quiz.id.in_(attempted_quiz_ids)).all()
        
        # Create a dictionary to match quiz_id to score
        score_dict = {score.quiz_id: score.total_scored for score in user_scores}
        
        # Create lists that match in length
        pie_data = []
        pie_labels = []
        
        for quiz in attempted_quizzes:
            pie_data.append(score_dict[quiz.id])
            pie_labels.append(quiz.title)
        
        pie_chart_img = io.BytesIO()
        fig, ax = plt.subplots()
        ax.pie(pie_data, labels=pie_labels, autopct='%1.1f%%')
        ax.set_title('Quiz Score Distribution')
        plt.savefig(pie_chart_img, format='png')
        pie_chart_img.seek(0)
        pie_chart_base64 = base64.b64encode(pie_chart_img.getvalue()).decode()
    subject_attempts = []
    subject_scores = []
    for subject in subjects:
        chapter_ids = [chapter.id for chapter in subject.chapters]
        quizzes_in_subject = Quiz.query.filter(Quiz.chapter_id.in_(chapter_ids)).all()
        quiz_ids_in_subject = [quiz.id for quiz in quizzes_in_subject]
        attempts = Score.query.filter(
            Score.quiz_id.in_(quiz_ids_in_subject),
            Score.user_id == user_id
        ).count()
        
        subject_attempts.append(attempts)
        
        if attempts > 0:
            avg_score = db.session.query(db.func.avg(Score.total_scored)).filter(
                Score.quiz_id.in_(quiz_ids_in_subject),
                Score.user_id == user_id
            ).scalar() or 0
            subject_scores.append(avg_score)
        else:
            subject_scores.append(None)

    return render_template(
        'user_summary.html', 
        bar_chart=bar_chart_base64, 
        pie_chart=pie_chart_base64,
        subjects=subjects,
        quiz_counts=quiz_counts,
        subject_attempts=subject_attempts,
        subject_scores=subject_scores
    )

@app.route('/user/start_quiz/<int:quiz_id>')
def start_quiz(quiz_id):
    user_id = session.get('user_id')
    if not user_id:
        flash("Please login to take quizzes", "danger")
        return redirect(url_for('login'))
        
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(chapter_id=quiz.chapter_id).all()  # Use chapter_id
    
    if not questions:
        flash("This quiz's chapter has no questions.", "warning")
        return redirect(url_for('user_dashboard'))
    
    # Initialize or reset quiz session data
    if 'quiz_answers' not in session:
        session['quiz_answers'] = {}
    
    # Clear any previous answers for this quiz
    session['quiz_answers'][str(quiz_id)] = {}
    
    # Clear any previous timer data for this quiz
    if 'quiz_times' not in session:
        session['quiz_times'] = {}
    session['quiz_times'][str(quiz_id)] = None
    
    session.modified = True
    
    return redirect(url_for('take_quiz', quiz_id=quiz_id))

@app.route('/user/take_quiz/<int:quiz_id>', methods=['GET', 'POST'])
def take_quiz(quiz_id):
    user_id = session.get('user_id')
    if not user_id:
        flash("Please login to take quizzes", "danger")
        return redirect(url_for('login'))
        
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(chapter_id=quiz.chapter_id).all()  # Use chapter_id
    
    if not questions:
        flash("This quiz's chapter has no questions.", "warning")
        return redirect(url_for('user_dashboard'))
    
    # Default to first question
    current_question_index = 0
    selected_option = None
    
    # Get index from form if it's a POST request
    if request.method == 'POST':
        current_question_index = int(request.form.get('current_index', 0))
        action = request.form.get('action')
        question_id = request.form.get('question_id')
        
        # Save the current answer
        if question_id:
            selected_option = request.form.get(f'answer_{question_id}')
            
            # Store answers in session
            if 'quiz_answers' not in session:
                session['quiz_answers'] = {}
            
            if str(quiz_id) not in session['quiz_answers']:
                session['quiz_answers'][str(quiz_id)] = {}
            
            if selected_option:
                session['quiz_answers'][str(quiz_id)][question_id] = selected_option
                session.modified = True
        
        # Save remaining time if provided
        remaining_time = request.form.get('remaining_time')
        if remaining_time:
            if 'quiz_times' not in session:
                session['quiz_times'] = {}
            session['quiz_times'][str(quiz_id)] = remaining_time
            session.modified = True
        
        # Handle navigation
        if action == 'previous' and current_question_index > 0:
            current_question_index -= 1
        elif action == 'next' and current_question_index < len(questions) - 1:
            current_question_index += 1
    
    # Make sure we have a valid index
    if current_question_index >= len(questions):
        current_question_index = 0
    
    current_question = questions[current_question_index]
    total_questions = len(questions)

    if 'quiz_answers' in session and str(quiz_id) in session['quiz_answers'] and str(current_question.id) in session['quiz_answers'][str(quiz_id)]:
        selected_option = int(session['quiz_answers'][str(quiz_id)][str(current_question.id)])
    
    # Convert time duration from "MM:SS" format to minutes
    time_parts = quiz.time_duration.split(':')
    quiz_duration_minutes = int(time_parts[0])
    if len(time_parts) > 1:
        quiz_duration_minutes += int(time_parts[1]) / 60
    
    return render_template('take_quiz.html', 
                          quiz=quiz,
                          current_question=current_question,
                          current_question_index=current_question_index,
                          total_questions=total_questions,
                          selected_option=selected_option,
                          quiz_duration_minutes=quiz_duration_minutes)
                          
@app.route('/user/submit_quiz/<int:quiz_id>', methods=['POST'])
def submit_quiz(quiz_id):
    user_id = session.get('user_id')
    if not user_id:
        flash("Please login to submit quizzes", "danger")
        return redirect(url_for('login'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(chapter_id=quiz.chapter_id).all()  
    
    # Get answers from session
    answers = {}
    if 'quiz_answers' in session and str(quiz_id) in session['quiz_answers']:
        answers = session['quiz_answers'][str(quiz_id)]
    
    total_score = 0
    total_questions = len(questions)
    if total_questions > 0: 
        for question in questions:
            if str(question.id) in answers and int(answers[str(question.id)]) == question.correct_option:
                total_score += 1
        percentage_score = (total_score / total_questions) * 100
    else:
        percentage_score = 0
    
    try:
        score = Score(
            quiz_id=quiz_id,
            user_id=user_id,
            time_stamp_of_attempt=datetime.now(),
            total_scored=percentage_score
        )
        db.session.add(score)
        db.session.commit()
        
        # Clear the quiz answers from session
        if 'quiz_answers' in session and str(quiz_id) in session['quiz_answers']:
            del session['quiz_answers'][str(quiz_id)]
            session.modified = True
        
        # Clear the quiz time from session
        if 'quiz_times' in session and str(quiz_id) in session['quiz_times']:
            del session['quiz_times'][str(quiz_id)]
            session.modified = True
        
        flash(f"Quiz submitted! Your score: {percentage_score:.2f}%", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error saving quiz results: {str(e)}", "danger")
    
    return redirect(url_for('user_dashboard'))

@app.route('/search')
def search():
    query = request.args.get('q', '')
    user_type = request.args.get('user_type', '')
    
    if user_type == 'admin':
        return redirect(url_for('admin_dashboard', query=query))
    elif user_type == 'quiz_management':
        return redirect(url_for('quiz_management', query=query))
    else:
        return redirect(url_for('user_dashboard', query=query))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['user_id'] = user.id
            session['role'] = user.role
            if user.role == 'Admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash("Invalid credentials!", "danger")
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        qualification = request.form.get('qualification')
        dob = request.form.get('dob')
        user = User(
            username=username,
            email=username,  
            password=password,
            full_name=full_name,
            qualification=qualification,
            dob=datetime.strptime(dob, '%Y-%m-%d'),
            role='User'
        )
        db.session.add(user)
        db.session.commit()
        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
