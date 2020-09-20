let body = document.body,
    checkboxes = document.querySelectorAll('input[type="checkbox"]'),
    allCheckboxes = document.querySelectorAll('input[type="checkbox"][name$="-all"]'),
    output = document.getElementById('output');

for (let checkbox of checkboxes) {
    checkbox.checked = false;
}
for (let checkbox of allCheckboxes) {
    checkbox.checked = true;
}

onchange = function(e) {
    let input = e.target;
    if (input.type === 'checkbox') {
        let checked = input.checked;
        let otherCheckboxes = Array.from(input.parentElement.parentElement.getElementsByTagName('input'));
        let allCheckbox = otherCheckboxes.shift();
        if (input == allCheckbox) {
            for (let checkbox of otherCheckboxes) {
                checkbox.checked = !checked;
            }
        } else {
            if (checked) {
                allCheckbox.checked = false;
            } else {
                let anyChecked = false;
                for (let checkbox of otherCheckboxes) {
                    anyChecked = anyChecked || checkbox.checked;
                }
                allCheckbox.checked = !anyChecked;
            }
        }
    }
};

let submit = document.getElementById('submit'),
    sections = document.getElementsByTagName('section'),
    warning = document.getElementById('warning');

function addRow(container, slug, icon, student) {
    if (student[slug]) {
        let row = document.createElement('div');
        let i = document.createElement('i');
        i.className = 'fa fa-' + icon;
        row.appendChild(i);
        let value = document.createElement('p');
        value.classList.add('value');
        value.classList.add(slug);
        value.textContent = student[slug];
        row.appendChild(value);

        container.appendChild(row);
    }
}

submit.onclick = function() {
    let filters = {};
    for (let section of sections) {
        let category = section.id;
        let otherCheckboxes = Array.from(section.getElementsByTagName('input'));
        let allCheckbox = otherCheckboxes.shift();
        if (!allCheckbox.checked) {
            filters[category] = []
            for (let checkbox of otherCheckboxes) {
                if (checkbox.checked) {
                    if (category === 'leave') {
                        filters[category].push(checkbox.name === 'Yes');
                    } else {
                        filters[category].push(checkbox.name);
                    }
                }
            }
        }
    }
    console.log(filters);
    fetch('/api/students', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'filters': filters,
        }),
    })
        .then(response => response.json())
        .then(students => {
            console.log(students);
            for (let student of students) {
                let studentContainer = document.createElement('div');
                studentContainer.className = 'student';

                let img = document.createElement('img');
                img.className = 'image';
                if (student.image_id) {
                    img.src = 'https://students.yale.edu/facebook/Photo?id=' + student.image_id;
                } else {
                    img.src = '/static/images/user.png';
                }
                studentContainer.appendChild(img);
                let name = document.createElement('h3');
                name.className = 'name';
                name.textContent = student.surname + ', ' + student.forename;
                if (student.netid) {
                    let netid = document.createElement('span');
                    netid.className = 'netid';
                    netid.textContent = '[' + student.netid + ']';
                    name.appendChild(netid);
                }
                studentContainer.appendChild(name);
                addRow(studentContainer, 'year', 'graduation-cap', student);
                addRow(studentContainer, 'leave', 'hourglass', student);
                addRow(studentContainer, 'college', 'school', student);
                addRow(studentContainer, 'email', 'envelope', student);
                addRow(studentContainer, 'residence', 'building', student);
                addRow(studentContainer, 'birthday', 'birthday-cake', student);
                addRow(studentContainer, 'major', 'book-open', student);
                addRow(studentContainer, 'address', 'home', student);
                addRow(studentContainer, 'phone', 'phone', student);
                addRow(studentContainer, 'access_code', 'key', student);

                output.appendChild(studentContainer);
            }
        });
}

onclick = function(e) {
    console.log(e.target);
    let section = null;
    if (e.target.tagName == 'SECTION') section = e.target;
    if (e.target.tagName == 'H4' && e.target.parentElement.tagName == 'SECTION') section = e.target.parentElement;

    if (section) {
        section.classList.toggle('collapsed');
    }
}
