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
        .then(emails => {
            console.log(emails);
            output.value = emails.join(', ');
            output.style.display = 'block';
            output.select();
            document.execCommand('copy');
            submit.textContent = 'Copied ' + emails.length + ' emails to clipboard!';
            if (emails.length > MAX_EMAILS_PER_DAY) {
                warning.textContent = 'Warning: Gmail will only allow sending emails to a maximum of ' + MAX_EMAILS_PER_DAY + ' recipients per day. Consider sending your email in batches to smaller groups.';
            }
            setTimeout(function() {
                submit.textContent = 'Generate email list';
            }, 1500);
        });
}
