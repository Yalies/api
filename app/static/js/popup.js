function showPopup() {
    let popup = document.createElement('div');
    popup.id = 'popup';
    let content = document.createElement('div');
    content.className = 'content';
    let header = document.createElement('h1');
    content.appendChild(header);
    paragraphs = [
        'All data used on Yalies is publicly accessible on the <a href="https://students.yale.edu/facebook">Yale Face Book</a> and the <a href="https://directory.yale.edu">Yale Directory</a>. Certain information provided by Yale is understandably disconcerting to some students, including street addresses and even phone numbers.',
        'Yalies censors such information, however, we can\'t do anything about what\'s on Yale\'s official sources. We encourage students to visit the <a href="https://students.yale.edu/facebook/PreferencesPage">Face Book preferences page</a> and remove information that makes them uncomfortable. Extensive documentation on how to remove your data from Yale\'s sources has been compiled <a href="/hide_me">here</a>.',
    ];
    for (let paragraph of paragraphs) {
        let p = document.createElement('p');
        p.innerHTML = paragraph;
        content.appendChild(p);
    }
    let closeButton = document.createElement('button');
    button.id = 'close_popup';
    button.textContent = 'Dismiss warning';
    button.onclick = closePopup;
    content.appendChild(button);
    document.body.appendChild(popup);
}

function closePopup() {

}

showPopup();
