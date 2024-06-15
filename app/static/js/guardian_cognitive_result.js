document.addEventListener('DOMContentLoaded', function() {
    fetch('/results_data')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error(data.error);
                return;
            }

            // Update the summary section
            document.getElementById('total-questions').textContent = data.total_questions;
            document.getElementById('correct-answers').textContent = data.correct_answers;
            document.getElementById('accuracy').textContent = data.accuracy + '%';
            document.getElementById('percentile').textContent = data.percentile;
            document.getElementById('average-questions-per-day').textContent = data.average_questions_per_day;

            // Update charts
            const weeklyQuestionsChartCtx = document.getElementById('weekly-questions-chart').getContext('2d');
            const comparisonScoresChartCtx = document.getElementById('comparison-scores-chart').getContext('2d');

            new Chart(weeklyQuestionsChartCtx, {
                type: 'bar',
                data: {
                    labels: ['월', '화', '수', '목', '금', '토', '일'],
                    datasets: [{
                        label: '풀린 문제 수',
                        data: data.weekly_questions,
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });

            new Chart(comparisonScoresChartCtx, {
                type: 'line',
                data: {
                    labels: data.weekly_questions.map((_, i) => `Day ${i + 1}`),
                    datasets: [{
                        label: '정답률',
                        data: data.accuracy_data,
                        fill: false,
                        borderColor: 'rgba(75, 192, 192, 1)',
                        tension: 0.1
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        })
        .catch(error => console.error('Error fetching results data:', error));
});
