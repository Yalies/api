let p = {
    checkboxes: document.querySelectorAll('input[type="checkbox"]'),
    allCheckboxes: document.querySelectorAll('input[type="checkbox"][name$="-all"]'),
    query: document.getElementById('query'),
    submit: document.getElementById('submit'),
    filters: document.getElementsByClassName('filter'),
    clearFilters: document.getElementById('clear_filters'),
    output: document.getElementById('output'),
    loading: document.getElementById('loading'),
    empty: document.getElementById('empty'),
};

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
}

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
    }
};

query.onkeyup = function(e) {
    if (e.keyCode === 13) {
        e.preventDefault();
        p.submit.click();
    }
};

let criteria = {};
let pagesLoaded = 0;
let pagesFinished = false;

function loadNextPage() {
    if (!pagesFinished) {
        p.empty.style.display = 'none';
        p.loading.style.display = 'block';
        criteria['page'] = ++pagesLoaded;
        console.log('Loading page', pagesLoaded);
        fetch('/api/students', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(criteria),
        })
            .then(response => response.json())
            .then(students => {
                console.log(students);
                pagesFinished = (students.length < 20);
                if (pagesLoaded == 1 && !students.length) {
                    p.empty.style.display = 'block';
                }
                for (let student of students) {
                    let studentContainer = document.createElement('div');
                    studentContainer.className = 'student';

                    let img = document.createElement('img');
                    img.className = 'image';
                    if (student.image) {
                        img.src = student.image;
                    } else {
                        img.src = '/static/images/user.png';
                    }
                    studentContainer.appendChild(img);
                    let name = document.createElement('h3');
                    name.className = 'name';
                    name.textContent = student.last_name + ', ' + student.first_name;
                    studentContainer.appendChild(name);

                    if (student.netid || student.upi) {
                        let pills = document.createElement('div');
                        pills.className = 'pills';
                        if (student.netid) {
                            let pill = document.createElement('div');
                            pill.className = 'pill';
                            pill.textContent = 'NetID ' + student.netid;
                            pills.appendChild(pill);
                        }
                        if (student.upi) {
                            let pill = document.createElement('div');
                            pill.className = 'pill';
                            pill.textContent = 'UPI ' + student.upi;
                            pills.appendChild(pill);
                        }
                        studentContainer.appendChild(pills);
                    }
                    addRow(studentContainer, 'year', 'calendar', student);
                    if (student.leave) {
                        let row = document.createElement('div');
                        row.classList.add('row');
                        row.classList.add('leave');
                        let i = document.createElement('i');
                        i.className = 'fa fa-' + 'hourglass';
                        row.appendChild(i);
                        let readout = document.createElement('p');
                        readout.classList.add('value');
                        readout.classList.add('leave');
                        readout.textContent = 'On Leave';
                        row.appendChild(readout);

                        studentContainer.appendChild(row);
                    }
                    if (student.eli_whitney) {
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

                        studentContainer.appendChild(row);
                    }
                    addRow(studentContainer, 'college', 'graduation-cap', student);
                    addRow(studentContainer, 'email', 'envelope', student, 'mailto');
                    addRow(studentContainer, 'residence', 'building', student);
                    addRow(studentContainer, 'major', 'book', student);
                    addRow(studentContainer, 'phone', 'phone', student, 'tel');
                    addRow(studentContainer, 'birthday', 'birthday-cake', student);
                    addRow(studentContainer, 'access_code', 'key', student);
                    addRow(studentContainer, 'address', 'home', student);

                    p.output.appendChild(studentContainer);
                }
                p.loading.style.display = 'none';
            });
    }
}

loadNextPage();

function addRow(container, property, icon, student, protocol) {
    let value = student[property];
    if (value) {
        let row = document.createElement('div');
        row.classList.add('row');
        row.classList.add(property);
        let i = document.createElement('i');
        i.className = 'fa fa-' + icon;
        row.appendChild(i);
        let readout = document.createElement('p');
        readout.classList.add('value');
        readout.classList.add(property);
        if (typeof(value) == 'string' && value.includes('\n')) {
            let lines = value.split('\n');
            readout.appendChild(document.createTextNode(lines.shift()));
            for (let line of lines) {
                readout.appendChild(document.createElement('br'));
                readout.appendChild(document.createTextNode(line));
            }
        } else if (protocol) {
            let a = document.createElement('a');
            a.href = protocol + ':' + value;
            a.textContent = value;
            readout.appendChild(a);
        } else {
            readout.textContent = value;
        }
        row.appendChild(readout);

        container.appendChild(row);
    }
}

function collapseAllFilters() {
    for (let filter of p.filters) {
        filter.classList.add('collapsed');
    }
}

p.submit.onclick = function() {
    collapseAllFilters();
    let filters = {};
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
                    } else if (category == 'year') {
                        filters[category].push(checkbox.name ? parseInt(checkbox.name) : null);
                    } else {
                        filters[category].push(checkbox.name);
                    }
                }
            }
        }
    }
    criteria = {
        'query': query.value,
        'filters': filters,
    };
    output.innerHTML = '';
    pagesLoaded = 0;
    pagesFinished = false;
    loadNextPage();
};

onclick = function(e) {
    let filter = null;
    if (e.target.tagName == 'DIV' && e.target.classList.contains('filter')) {
        filter = e.target;
    } else if (e.target.tagName == 'H4' &&
               e.target.parentElement.tagName == 'DIV' && e.target.parentElement.classList.contains('filter')) {
        filter = e.target.parentElement;
    }

    if (filter) {
        filter.classList.toggle('collapsed');
    }
};



window.onscroll = function(e) {
    if (2 * window.innerHeight + window.scrollY >= document.body.offsetHeight) {
        loadNextPage();
        // Temporarily set so that we won't load tons of pages at once
        pagesFinished = true;
    }
}
