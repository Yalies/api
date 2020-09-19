let face_book_cookie = document.getElementById('face_book_cookie'),
    people_search_session_cookie = document.getElementById('people_search_session_cookie'),
    csrf_token = document.getElementById('csrf_token')
    submit = document.getElementById('submit');

onchange = function() {
    submit.disabled = Boolean(face_book_cookie.textContent) &&
                      Boolean(people_search_session_cookie.textContent) &&
                      Boolean(csrf_token.textContent);
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
