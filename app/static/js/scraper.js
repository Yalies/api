let inputs = document.getElementsByTagName('textarea'),
    cacheCheckboxes = document.getElementsByClassName('cache'),
    submit = document.getElementById('submit');

function setSubmitEnabled() {
    let completed = true;
    for (let input of inputs) {
        if (!Boolean(input.value.trim())) {
            completed = false;
            break;
        }
    }
    submit.disabled = !completed;
}

function saveInputsToURL() {
    const params = new URLSearchParams();
    for (let input of inputs) {
        params.append(input.name, encodeURIComponent(input.value));
    }
    this.history.pushState({}, '', '?' + params.toString());
}

function loadInputsFromURL() {
    const params = new URLSearchParams(window.location.search);
    console.log(inputs.length)
    for (let input of inputs) {
        input.value = decodeURIComponent(params.get(input.name));
    }

}

document.oninput = function() {
    setSubmitEnabled();
    saveInputsToURL();
}

window.onload = function() {
    loadInputsFromURL();
    setSubmitEnabled();
}

submit.onclick = function() {
    console.log('Trying to start scraper.');
    let payload = {};
    for (let input of inputs) {
        payload[input.name] = input.value.trim();
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
