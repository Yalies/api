///////////////////
// Page elements //
///////////////////
let p = {
    checkboxes: document.querySelectorAll('input[type="checkbox"]'),
    allCheckboxes: document.querySelectorAll('input[type="checkbox"][name$="-all"]'),
    query: document.getElementById('query'),
    submit: document.getElementById('submit'),
    filters: document.getElementsByClassName('filter'),
    clearFilters: document.getElementById('clear_filters'),
    list: document.getElementById('list'),
    loading: document.getElementById('loading'),
    empty: document.getElementById('empty'),
};

//////////////
// Controls //
//////////////
query.onkeyup = function(e) {
    if (e.keyCode === 13) {
        e.preventDefault();
        p.submit.click();
    }
};

function collapseAllFilters() {
    for (let filter of p.filters) {
        filter.classList.add('collapsed');
    }
}

function resetFilters() {
    for (let filter of p.filters) {
        filter.classList.add('collapsed');
        filter.classList.remove('active');
    }
    for (let checkbox of p.checkboxes) {
        checkbox.checked = false;
    }
    for (let checkbox of p.allCheckboxes) {
        checkbox.checked = true;
    }
}
resetFilters();

p.clearFilters.onclick = function() {
    resetFilters();
    runSearch();
}

function isFilter(element) {
    return element.tagName === 'DIV' && element.classList.contains('filter');
}

function isPronunciation(element) {
    return element.tagName === 'SPAN' && element.classList.contains('pronunciation');
}

onclick = function(e) {
    let filter = null;
    if (isFilter(e.target)) {
        filter = e.target;
    } else if (e.target.tagName === 'H4' && isFilter(e.target.parentElement)) {
        filter = e.target.parentElement;
    } else if (e.target.tagName === 'I' && isFilter(e.target.parentElement.parentElement)) {
        filter = e.target.parentElement.parentElement;
    }
    if (filter) {
        filter.classList.toggle('collapsed');
    }

    let pronunciation = null;
    if (isPronunciation(e.target)) {
        pronunciation = e.target;
    } else if (e.target.tagName === 'I' && isPronunciation(e.target.parentElement)) {
        pronunciation = e.target.parentElement;
    }
    if (pronunciation) {
        // Play audio
        pronunciation.classList.add('playing');
        let audio = pronunciation.getElementsByTagName('audio')[0];
        audio.onended = function() {
            pronunciation.classList.remove('playing');
        }
        console.log(audio);
        audio.play();
    }
};

onchange = function(e) {
    let input = e.target;
    if (input.type === 'checkbox') {
        let checked = input.checked;
        let otherCheckboxes = Array.from(input.parentElement.parentElement.getElementsByTagName('input'));
        let allCheckbox = otherCheckboxes.shift();
        let filter = input.parentElement.parentElement;
        if (input == allCheckbox) {
            filter.classList.toggle('active', !checked);
            for (let checkbox of otherCheckboxes) {
                checkbox.checked = !checked;
            }
        } else {
            if (checked) {
                filter.classList.add('active');
                allCheckbox.checked = false;
            } else {
                let anyChecked = false;
                for (let checkbox of otherCheckboxes) {
                    if (checkbox.checked) {
                        anyChecked = true;
                        break;
                    }
                }
                filter.classList.toggle('active', anyChecked);
                allCheckbox.checked = !anyChecked;
            }
        }
        runSearch();
    }
};


///////////////////
// List building //
///////////////////
let criteria = {
    'filters': {
        'school_code': ['YC'],
    },
};
let pagesLoaded = 0;
let pagesFinished = false;

function runSearch() {
    let filters = {
        'school_code': ['YC'],
    };
    for (let filter of p.filters) {
        let category = filter.id;
        let otherCheckboxes = Array.from(filter.getElementsByTagName('input'));
        let allCheckbox = otherCheckboxes.shift();
        if (!allCheckbox.checked) {
            filters[category] = [];
            for (let checkbox of otherCheckboxes) {
                if (checkbox.checked) {
                    if (category === 'leave' || category === 'eli_whitney') {
                        filters[category].push(checkbox.name === 'Yes');
                    } else if (category === 'year' || category === 'floor' || category === 'room') {
                        filters[category].push(checkbox.name ? parseInt(checkbox.name) : null);
                    } else {
                        filters[category].push(checkbox.name);
                    }
                }
            }
        }
    }
    criteria = {};
    query = p.query.value.trim();
    if (query)
        criteria['query'] = query;
    criteria['filters'] = filters;
    p.list.innerHTML = '';
    pagesLoaded = 0;
    pagesFinished = false;
    loadNextPage();
}

p.submit.onclick = function() {
    collapseAllFilters();
    runSearch();
};

function addRow(container, property, title, icon, person, url, showTitle) {
    let value = person[property];
    if (value) {
        let row = document.createElement('div');
        row.title = title;
        row.classList.add('row');
        row.classList.add(property);
        let i = document.createElement('i');
        i.className = 'fa fa-' + icon;
        row.appendChild(i);
        let readout = document.createElement('p');
        readout.classList.add('value');
        readout.classList.add(property);
        if (typeof(value) === 'string' && value.includes('\n')) {
            let lines = value.split('\n');
            //readout.appendChild(document.createTextNode(lines.shift()));
            //for (let line of lines) {
            //    readout.appendChild(document.createElement('br'));
            //    readout.appendChild(document.createTextNode(line));
            //}
            readout.textContent = lines[lines.length - 1];
        } else if (url) {
            let a = document.createElement('a');
            a.href = url;
            if (showTitle) {
                a.textContent = title;
            } else {
                a.textContent = value;
            }
            readout.appendChild(a);
        } else {
            readout.textContent = value;
        }
        row.appendChild(readout);

        container.appendChild(row);
    }
}

function createPronunciationButton(person) {
    let button = document.createElement('span');
    button.className = 'pronunciation';
    if (person.phonetic_name) {
        button.title = person.phonetic_name;
    }
    let icon = document.createElement('i');
    icon.className = 'fa fa-volume-up';

    let audio = document.createElement('audio');
    let source = document.createElement('source');
    source.src = person.name_recording;
    // All pronunciations appear to be mp3 files
    source.type = 'audio/mpeg';
    audio.appendChild(source);

    icon.appendChild(audio);
    button.appendChild(icon);
    return button;
}

function loadNextPage() {
    if (!pagesFinished) {
        p.empty.style.display = 'none';
        p.loading.style.display = 'block';
        criteria['page'] = ++pagesLoaded;
        console.log('Loading page', pagesLoaded);
        fetch('/api/people', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(criteria),
        })
            .then(response => response.json())
            .then(people => {
                pagesFinished = (people.length < 20);
                if (pagesLoaded == 1 && !people.length) {
                    p.empty.style.display = 'block';
                }
                for (let person of people) {
                    let personContainer = document.createElement('div');
                    personContainer.className = 'person';

                    let image = document.createElement('div');
                    image.className = 'image';
                    if (person.image) {
                        image.style.backgroundImage = 'url(' + person.image + ')';
                    }
                    personContainer.appendChild(image);
                    let name = document.createElement('h3');
                    name.className = 'name';
                    let fullName = person.last_name + ', ' + person.first_name;
                    if (person.profile) {
                        let a = document.createElement('a');
                        a.href = person.profile;
                        a.textContent = fullName;
                        name.appendChild(a);
                    } else {
                        name.textContent = fullName;
                    }
                    if (person.name_recording) {
                        name.textContent += ' ';
                        name.appendChild(createPronunciationButton(person));
                    }
                    personContainer.appendChild(name);

                    if (person.netid || person.upi) {
                        let pills = document.createElement('div');
                        pills.className = 'pills';
                        if (person.netid) {
                            let pill = document.createElement('div');
                            pill.className = 'pill';
                            pill.textContent = 'NetID ' + person.netid;
                            pills.appendChild(pill);
                        }
                        if (person.upi) {
                            let pill = document.createElement('div');
                            pill.className = 'pill';
                            pill.textContent = 'UPI ' + person.upi;
                            pills.appendChild(pill);
                        }
                        personContainer.appendChild(pills);
                    }
                    addRow(personContainer, 'title', 'Title', 'tags', person);
                    addRow(personContainer, 'year', 'Graduation Year', 'calendar', person);
                    if (person.leave) {
                        let row = document.createElement('div');
                        row.classList.add('row');
                        row.classList.add('leave');
                        let i = document.createElement('i');
                        i.className = 'fa fa-' + 'hourglass';
                        row.appendChild(i);
                        let readout = document.createElement('p');
                        readout.classList.add('value');
                        readout.classList.add('leave');
                        readout.textContent = 'Took Leave';
                        row.appendChild(readout);

                        personContainer.appendChild(row);
                    }
                    if (person.eli_whitney) {
                        let row = document.createElement('div');
                        row.classList.add('row');
                        row.classList.add('eli-whitney');
                        let i = document.createElement('i');
                        i.className = 'fa fa-' + 'history';
                        row.appendChild(i);
                        let readout = document.createElement('p');
                        readout.classList.add('value');
                        readout.classList.add('eli-whitney');
                        readout.textContent = 'Eli Whitney Program';
                        row.appendChild(readout);

                        personContainer.appendChild(row);
                    }
                    addRow(personContainer, 'college', 'Residential College', 'graduation-cap', person);
                    addRow(personContainer, 'email', 'Email', 'envelope', person, person.email ? 'mailto:' + person.email : null, false);
                    //addRow(personContainer, 'residence', 'Residence', 'building', person);
                    addRow(personContainer, 'major', 'Major', 'book', person);
                    if (person.school_code !== 'YC') {
                        addRow(personContainer, 'phone', 'Phone Number', 'phone', person, person.phone ? 'tel:' + person.phone : null, false);
                    }
                    addRow(personContainer, 'birthday', 'Birthday', 'birthday-cake', person);
                    addRow(personContainer, 'access_code', 'Swipe Access Code', 'key', person);
                    addRow(personContainer, 'address', 'Address', 'home', person);
                    addRow(personContainer, 'website', 'Website', 'globe', person, person.website, true);
                    //addRow(personContainer, 'education', 'Education', 'university', person);

                    p.list.appendChild(personContainer);
                }
                p.loading.style.display = 'none';
            });
    }
}

loadNextPage();

window.onscroll = function(e) {
    if (2 * window.innerHeight + window.scrollY >= document.body.offsetHeight) {
        loadNextPage();
        // Temporarily set so that we won't load tons of pages at once
        pagesFinished = true;
    }
}
