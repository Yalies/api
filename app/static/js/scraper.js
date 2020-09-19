let inputs = document.getElementsByTagName('textarea'),
    submit = document.getElementById('submit');

onchange = function() {
    let completed = true;
    for (let input of inputs) {
        completed = completed && Boolean(input.textContent);
    }
    submit.disabled = !completed;
}

submit.onclick = function() {
    console.log('Trying to start scraper.');
    let payload = {
        'face_book_cookie': face_book_cookie.value,
        'people_search_session_cookie': people_search_session_cookie.value,
        'csrf_token': csrf_token.value,
    };
    fetch('/scraper', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload),
    }).then(response => {
        if (response.ok) {
            submit.textContent = 'Scraper started!';
            submit.classList.add('success');
        } else {
            submit.textContent = 'Scraper run failed.';
            submit.classList.add('fail');
        }
        setTimeout(function() {
            submit.textContent = 'Run Scraper';
            submit.className = '';
        }, 1500);
    });
}
