console.log("Content script is running on this page.");

let spinnerStyle = document.createElement('style');
spinnerStyle.type = 'text/css';
spinnerStyle.innerHTML = '@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }';
document.getElementsByTagName('head')[0].appendChild(spinnerStyle);

function showSpinner() {
    let overlay = document.createElement('div');
    overlay.id = 'spinnerOverlay';
    overlay.style.position = 'fixed';
    overlay.style.left = '0';
    overlay.style.top = '0';
    overlay.style.width = '100%';
    overlay.style.height = '100%';
    overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.6)';
    overlay.style.zIndex = '10000';
    overlay.style.display = 'flex';
    overlay.style.justifyContent = 'center';
    overlay.style.alignItems = 'center';

    let spinner = document.createElement('div');
    spinner.id = 'loadingSpinner';
    spinner.style.border = '5px solid transparent';
    spinner.style.borderTopColor = 'blue';
    spinner.style.borderRadius = '50%';
    spinner.style.width = '50px';
    spinner.style.height = '50px';
    spinner.style.animation = 'spin 1s linear infinite';

    overlay.appendChild(spinner);
    document.body.appendChild(overlay);
}

function removeSpinner() {
    let overlay = document.getElementById('spinnerOverlay');
    if (overlay) {
        document.body.removeChild(overlay);
    }
}

let clipboardTooltip = document.createElement('span');
clipboardTooltip.innerHTML = "Ready To Paste";
clipboardTooltip.style.position = "absolute";
clipboardTooltip.style.fontSize = "16px";
clipboardTooltip.style.zIndex = "9999";
clipboardTooltip.style.backgroundColor = "white";
clipboardTooltip.style.border = "1px solid black";
clipboardTooltip.style.padding = "5px";
clipboardTooltip.style.display = "none";
document.body.appendChild(clipboardTooltip);

function copyTextToClipboard(text) {
    let currentScrollPos = window.pageYOffset;

    var textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = 'fixed';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    document.execCommand('copy');
    document.body.removeChild(textArea);
    window.scrollTo(0, currentScrollPos);
    removeSpinner();
}

function showTooltip(event) {
    clipboardTooltip.style.left = event.clientX + window.scrollX + 'px';
    clipboardTooltip.style.top = event.clientY + window.scrollY + 'px';
    clipboardTooltip.style.display = 'inline';
    setTimeout(() => {
        clipboardTooltip.style.display = 'none';
    }, 3000);
}

chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
    if (request.type === 'showSpinner') {
        showSpinner();
    } else if (request.type === 'copyToClipboard') {
        copyTextToClipboard(request.text);
        document.addEventListener('mousemove', function onMouseMove(event) {
            showTooltip(event);
            document.removeEventListener('mousemove', onMouseMove);
        });
    }
});

function addAutoFillButton() {
    const button = document.createElement('button');
    button.id = 'autoFillAIButton';
    button.style.backgroundImage = `url('${chrome.runtime.getURL('images/icon256.png')}')`;
    button.style.backgroundSize = 'contain';
    button.style.width = '50px';
    button.style.height = '50px';
    button.style.position = 'fixed';
    button.style.bottom = '20px';
    button.style.right = '20px';
    button.style.zIndex = '1000';
    button.style.border = 'none';
    button.style.cursor = 'pointer';

    button.addEventListener('click', () => {
        console.log('Auto-Fill AI Button Clicked');
        let questions = extractQuestions();

        if (questions.length === 0) {
            console.log('No questions found on the page.');
            return;
        }

        chrome.storage.local.get(['pin', 'job_description'], function(result) {
            const storedPin = result.pin;
            const storedJobDescription = result.job_description || '';

            if (!storedPin || !storedJobDescription) {
                console.log('Pin or job description not found in local storage.');
                return;
            }

            fetch('http://127.0.0.1:5000/api/autoapply', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    questions: questions,
                    pin: storedPin,
                    job_description: storedJobDescription
                }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Error from server:', data.error);
                } else {
                    const aggregatedAnswers = aggregateMultiLineAnswers(data.answers);
                    Object.keys(aggregatedAnswers).forEach(id => {
                        assignAnswerToInput(id, aggregatedAnswers[id]);
                    });
                }
            })
            .catch(error => {
                console.error('Error fetching from server:', error);
            });
        });
    });

    document.body.appendChild(button);
}

function extractQuestions() {
    let questions = [];
    let questionIndex = 0;

    document.querySelectorAll('input, textarea, select').forEach(input => {
        if (input.type !== 'hidden') {
            let questionText = findAdjacentTextElement(input)?.innerText.trim();
            if (!questionText) {
                questionText = input.placeholder.trim();
            }
            if (questionText) {
                let questionId = input.id || `auto-gen-id-${questionIndex++}`;
                input.setAttribute('data-question-id', questionId);
                questions.push({ id: questionId, question: questionText });
            }
        }
    });

    return questions;
}

function findAdjacentTextElement(input) {
    let sibling = input.previousElementSibling;
    while (sibling) {
        if (sibling.nodeType === Node.TEXT_NODE || sibling.matches('p, span, div, label')) {
            return sibling;
        }
        sibling = sibling.previousElementSibling;
    }
    return null;
}

function assignAnswerToInput(identifier, answer) {
    const inputField = document.querySelector(`[data-question-id="${identifier}"]`);
    if (inputField) {
        // Directly use 'answer' as it is already processed in 'aggregateMultiLineAnswers'
        if (inputField.tagName.toLowerCase() === 'textarea') {
            answer = answer.replace(/\\n/g, '\n');
        }
        inputField.value = answer.trim();
    }
}



function aggregateMultiLineAnswers(answers) {
    const aggregatedAnswers = {};
    let currentId = '';

    answers.forEach(answer => {
        if (answer.includes(':')) {
            const [id, text] = answer.split(': ', 2);
            currentId = id;
            aggregatedAnswers[currentId] = text || '';
        } else {
            // Append to the current multi-line answer
            aggregatedAnswers[currentId] += '\n' + answer;
        }
    });

    return aggregatedAnswers;
}




addAutoFillButton();
