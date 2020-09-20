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

function addRow(container, slug, name, student) {
    if (student[slug]) {
        let row = document.createElement('div');
        let key = document.createElement('h4');
        key.className = 'key';
        key.textContent = name;
        row.appendChild(key);
        let value = document.createElement('p');
        value.classList.add('value');
        value.classList.add(slug);
        value.textContent = student[slug];
        row.appendChild(value);
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
                let name = document.createElement('h3');
                name.className = 'name';
                name.textContent = student.surname + ', ' + student.forename;
                studentContainer.appendChild(name);
                addRow(studentContainer, 'netid', 'NetID', student);
                addRow(studentContainer, 'year', 'Year', student);
                addRow(studentContainer, 'college', 'College', student);
                addRow(studentContainer, 'email', 'email', student);
                addRow(studentContainer, 'residence', 'Residence', student);
                addRow(studentContainer, 'birthday', 'Birthday', student);
                addRow(studentContainer, 'major', 'Major', student);
                addRow(studentContainer, 'address', 'Address', student);
                addRow(studentContainer, 'phone', 'Phone', student);
                addRow(studentContainer, 'leave', 'On Leave', student);
                addRow(studentContainer, 'access_code', 'Access Code', student);

                output.appendChild(studentContainer);
            }
        });
}
