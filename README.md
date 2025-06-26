# Quiz Master

A modern, responsive web-based quiz management system built with Flask that allows administrators to create subjects, chapters, quizzes, and questions, while users can take quizzes and view their performance.



## Features

- **User Authentication**: Login and registration system with role-based access (Admin/User)
- **Admin Dashboard**: Manage subjects, chapters, quizzes, and questions
- **Quiz Management**: Create, edit, and delete quizzes and questions
- **Data Visualization**: View quiz statistics and performance metrics
- **User Dashboard**: Take quizzes and track performance
- **Search Functionality**: Search for subjects, chapters, quizzes, and questions
- **Timer Functionality**: Timed quizzes with automatic submission when time expires
- **Question Navigation**: Easy navigation between questions during quiz attempts
- **Progress Tracking**: Track user performance across different subjects
- **Responsive Design**: Modern UI that works on desktop and mobile devices

## Tech Stack

- **Backend**: Flask, SQLAlchemy
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Database**: SQLite
- **Data Visualization**: Matplotlib
- **Data Processing**: Pandas, NumPy
- **Icons**: Font Awesome
- **Fonts**: Google Fonts (Poppins)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/quiz-master.git
   cd quiz-master
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv env
   # On Windows
   env\Scripts\activate
   # On macOS/Linux
   source env/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the application:
   ```
   python main.py
   ```

5. Access the application at `http://localhost:5000`

## Default Admin Credentials

- **Username**: admin
- **Password**: admin
- **Email**: admin@quizmaster.com

## Project Structure

- `main.py`: Main application file with Flask routes
- `applications/`: Package containing application modules
  - `config.py`: Application configuration
  - `database.py`: Database setup
  - `model.py`: SQLAlchemy models
- `templates/`: HTML templates for the application views
- `static/`: Static assets
  - `css/`: CSS stylesheets
  - `js/`: JavaScript files
- `instance/`: Contains the SQLite database

## Key Features in Detail

### Timer Functionality
The application includes a timer feature for quizzes that:
- Displays remaining time during quiz attempts
- Persists time between page reloads
- Automatically submits when time expires
- Changes color when time is running low

### Responsive Design
- Modern UI with custom styling
- Works on mobile, tablet, and desktop devices
- Smooth animations and transitions
- Consistent color scheme and typography

### User Experience
- Intuitive navigation with clear icons
- Visual feedback for selected quiz options
- Question navigator for easy movement between questions
- Progress tracking and performance visualization

## Screenshots



### Admin Dashboard
![Admin Dashboard](https://via.placeholder.com/400x200?text=Admin+Dashboard)

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
