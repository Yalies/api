let popup;

function showPopup(icon, title, paragraphs, buttons) {
    const popup = document.createElement('div');
    popup.className = 'popup';
    const content = document.createElement('div');
    content.className = 'content';
    const header = document.createElement('h1');
    header.innerHTML = '<i class="fa fa-' + icon + '"></i> ' + title;
    content.appendChild(header);
    for (const paragraph of paragraphs) {
        let p = document.createElement('p');
        p.innerHTML = paragraph;
        content.appendChild(p);
    }
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'buttons';
    buttonContainer.style.textAlign = 'right';
    for(const button of buttons) {
        const b = document.createElement('button');
        b.textContent = button.text;
        b.onclick = button.onclick;
        buttonContainer.appendChild(b);
    }
    content.appendChild(buttonContainer);
    popup.appendChild(content);
    document.body.appendChild(popup);

    return popup;
}

function closePopup(popup) {
    popup.parentElement.removeChild(popup);
}

// if (!localStorage.popupShown) {
//     let paragraphs = [
//         'All data used on Yalies is already publicly accessible on the <a href="https://students.yale.edu/facebook">Yale Face Book</a> and the <a href="https://directory.yale.edu">Yale Directory</a>. Certain information provided by Yale is understandably disconcerting to some students, including street addresses, room numbers, and occasionally phone numbers.',
//         'Yalies censors such information, however, we can\'t do anything about what\'s on Yale\'s official sources. Though Yale ought to ultimately make this sensitive data hidden by default, for now we encourage you to visit the <a href="https://students.yale.edu/facebook/PreferencesPage">Yale Face Book preferences page</a> and remove any information that makes you uncomfortable. Further documentation on how to remove your data from Yale\'s sources can be found <a href="/hide_me">here</a>.',
//     ];
//     showPopup('flag', 'Note', paragraphs, 'Dismiss warning');
//     localStorage.popupShown = true;
// }


if (!localStorage.popupShownV2discovery) {
    const paragraphs = [
        'Experience a fresh look for Yalies.',
        'We\'ve been working hard on an all-new Yalies, and we\'re excited to share a public preview with you.',
        '<img src="/static/images/yalies-next.png" alt="Yalies Next">',
    ];
    const buttons = [
        {
            text: 'Stay here',
            onclick: function() {
                closePopup(popup);
            },
        },
        {
            text: 'Check it out',
            onclick: function() {
                window.location.href = 'https://next.yalies.io';
            },
        },
    ]
    popup = showPopup('space-shuttle', 'Yalies Next', paragraphs, buttons);
    localStorage.popupShownV2discovery = true;
}
