let chart;

async function loadResultsData() {
    try {
        const response = await fetch('/results_data');
        const data = await response.json();
        
        if (data.error) {
            console.error(data.error);
            return;
        }
        
        document.getElementById('username').textContent = data.username;
        document.getElementById('total-questions').textContent = data.total_questions;
        document.getElementById('correct-answers').textContent = data.correct_answers;
        document.getElementById('accuracy').textContent = `${data.accuracy.toFixed(2)}%`;
        document.getElementById('percentile').textContent = `${(100 - data.percentile).toFixed(2)}%`;
        document.getElementById('average-questions-per-day').textContent = data.average_questions_per_day.toFixed(2);

        updateWeeklyQuestionsChart(data.weekly_questions);
        updateComparisonScoresChart(data.accuracy_data, data.average_accuracy_global);

        const circle = document.querySelector('.circle svg circle:nth-child(2)');
        const circleText = document.querySelector('.circle-text');
        const radius = circle.r.baseVal.value;
        const circumference = 2 * Math.PI * radius;
        const offset = circumference - (data.accuracy / 100) * circumference;
        circle.style.strokeDashoffset = offset;
        circleText.textContent = `정답률 ${data.accuracy.toFixed(2)}%`;

    } catch (error) {
        console.error('Error loading results data:', error);
    }
}

function updateWeeklyQuestionsChart(weeklyQuestions) {
    const ctx = document.getElementById('weekly-questions-chart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['월', '화', '수', '목', '금', '토', '일'],
            datasets: [{
                label: '주간 문제 풀이',
                data: weeklyQuestions,
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
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
}

function updateComparisonScoresChart(accuracyData, averageAccuracyGlobal) {
    const ctx = document.getElementById('comparison-scores-chart').getContext('2d');
    if (chart) {
        chart.data.labels = accuracyData.map((_, index) => index + 1);
        chart.data.datasets[0].data = accuracyData;
        chart.options.plugins.annotation.annotations.line1.yMin = averageAccuracyGlobal;
        chart.options.plugins.annotation.annotations.line1.yMax = averageAccuracyGlobal;
        chart.update();
    } else {
        chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: accuracyData.map((_, index) => index + 1),
                datasets: [{
                    label: '정답률',
                    data: accuracyData,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    fill: false
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                },
                plugins: {
                    annotation: {
                        annotations: {
                            line1: {
                                type: 'line',
                                yMin: averageAccuracyGlobal,
                                yMax: averageAccuracyGlobal,
                                borderColor: 'red',
                                borderWidth: 2,
                                label: {
                                    content: '나이대 평균 점수',
                                    enabled: true,
                                    position: 'center'
                                }
                            }
                        }
                    }
                }
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', loadResultsData);
