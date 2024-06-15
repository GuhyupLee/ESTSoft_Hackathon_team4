let mediaRecorder;
let chunks = [];

async function startQuestion() {
    const response = await fetch('/start');
    const data = await response.json();
    const questionText = data.question;
    document.getElementById('question-bubble').textContent = questionText;
    document.getElementById('question-bubble').classList.remove('hidden');

    const audioResponse = await fetch('/audio');
    const audioBlob = await audioResponse.blob();
    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);
    audio.play();
}

async function toggleRecording() {
    const recordButton = document.getElementById('record-button');
    if (!recordButton.classList.contains('recording')) {
        await startRecording();
        recordButton.textContent = '버튼 눌러서 대답 끝내기';
        recordButton.classList.add('recording');
    } else {
        stopRecording();
        recordButton.textContent = '버튼 누르고 대답하기';
        recordButton.classList.remove('recording');
    }
}

async function startRecording() {
    try {
        chunks = [];
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const options = {
            mimeType: 'audio/webm'
        };
        mediaRecorder = new MediaRecorder(stream, options);
        mediaRecorder.start();
        mediaRecorder.ondataavailable = (e) => {
            chunks.push(e.data);
        };
        mediaRecorder.onstop = async (e) => {
            const recordingBlob = new Blob(chunks, { type: "audio/mpeg" });
            const formData = new FormData();
            formData.append("file", recordingBlob, "input.mp3");
            const response = await fetch("/answer", {
                method: "POST",
                body: formData,
            });
            const data = await response.json();
            document.getElementById('user-response').textContent = data.user_answer;
            document.getElementById('user-response').classList.remove('hidden');
            document.getElementById('result').textContent = data.result;
            document.getElementById('result').classList.remove('hidden');

            // Fetch the answer audio
            const responseAudioBlob = await fetch('/answer_audio').then(res => res.blob());
            const audioUrl = URL.createObjectURL(responseAudioBlob);
            const audio = new Audio(audioUrl);
            audio.play();
        };
    } catch (error) {
        console.error('Error accessing media devices.', error);
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
    }
}

async function sendAnswer() {
    const recordingBlob = new Blob(chunks, { type: 'audio/mpeg' });
    const formData = new FormData();
    formData.append('file', recordingBlob, 'input.mp3');
    const response = await fetch('/answer', { method: 'POST', body: formData });
    const data = await response.json();
    document.getElementById('user-response').textContent = data.user_answer;
    document.getElementById('user-response').classList.remove('hidden');
    document.getElementById('result').textContent = data.result;
    document.getElementById('result').classList.remove('hidden');
}
