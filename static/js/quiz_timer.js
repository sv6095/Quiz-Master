// Quiz timer functionality
function initializeQuizTimer(quizId, quizDurationMinutes, submitUrl) {
    // Check if there's a saved time in session storage
    let remainingSeconds;
    const savedTime = sessionStorage.getItem('quiz_' + quizId + '_remaining_time');
    
    if (savedTime) {
        remainingSeconds = parseInt(savedTime);
    } else {
        // Convert minutes to seconds
        remainingSeconds = quizDurationMinutes * 60;
    }
    
    const timerElement = document.getElementById('timer');
    const remainingTimeInput = document.getElementById('remaining_time_input');
    const quizForm = document.getElementById('quizForm');
    
    // Set initial value for the hidden input
    if (remainingTimeInput) {
        remainingTimeInput.value = remainingSeconds;
    }
    
    function updateTimer() {
        const minutes = Math.floor(remainingSeconds / 60);
        const seconds = remainingSeconds % 60;
        
        // Format the time display
        if (timerElement) {
            timerElement.textContent = minutes + ':' + (seconds < 10 ? '0' : '') + seconds;
        }
        
        // Update the hidden input with current remaining time
        if (remainingTimeInput) {
            remainingTimeInput.value = remainingSeconds;
        }
        
        // Save current time to session storage
        sessionStorage.setItem('quiz_' + quizId + '_remaining_time', remainingSeconds);
        
        // Change color when time is running low
        if (remainingSeconds <= 60 && timerElement) {
            timerElement.parentElement.classList.remove('alert-info');
            timerElement.parentElement.classList.add('alert-danger');
        }
        
        if (remainingSeconds <= 0) {
            // Time's up, submit the quiz
            clearInterval(timerInterval);
            alert('Time is up! Your quiz will be submitted.');
            
            // Create a hidden form to submit the quiz
            const submitForm = document.createElement('form');
            submitForm.method = 'POST';
            submitForm.action = submitUrl;
            
            // Copy all form values from the quiz form if it exists
            if (quizForm) {
                const formData = new FormData(quizForm);
                for (const [name, value] of formData.entries()) {
                    const input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = name;
                    input.value = value;
                    submitForm.appendChild(input);
                }
            }
            
            // Add action input
            const actionInput = document.createElement('input');
            actionInput.type = 'hidden';
            actionInput.name = 'action';
            actionInput.value = 'submit';
            submitForm.appendChild(actionInput);
            
            // Submit the form
            document.body.appendChild(submitForm);
            submitForm.submit();
        } else {
            remainingSeconds--;
        }
    }
    
    // Update timer immediately and then every second
    updateTimer();
    const timerInterval = setInterval(updateTimer, 1000);
    
    // Update hidden input before form submission
    if (quizForm) {
        quizForm.addEventListener('submit', function() {
            if (remainingTimeInput) {
                remainingTimeInput.value = remainingSeconds;
            }
        });
    }
    
    // Save timer state every 5 seconds
    setInterval(function() {
        sessionStorage.setItem('quiz_' + quizId + '_remaining_time', remainingSeconds);
    }, 5000);
    
    return {
        getRemainingTime: function() {
            return remainingSeconds;
        },
        stopTimer: function() {
            clearInterval(timerInterval);
        }
    };
} 