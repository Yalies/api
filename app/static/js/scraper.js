let inputs = document.getElementsByTagName('textarea'),
    cacheCheckboxes = document.getElementsByClassName('cache'),
    submit = document.getElementById('submit');

oninput = function() {
    let completed = true;
    for (let input of inputs) {
        if (!Boolean(input.value)) {
            completed = false;
            break;
        }
    }
    submit.disabled = !completed;
}

submit.onclick = function() {
    console.log('Trying to start scraper.');
    let payload = {};
    for (let input of inputs) {
        payload[input.name] = input.value;
    }
    let caches = {};
    for (let cacheCheckbox of cacheCheckboxes) {
        caches[cacheCheckbox.name] = cacheCheckbox.checked;
    }
    payload.caches = caches;
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
