function showPopup() {
    let popup = document.createElement('div');
    popup.id = 'popup';
    popup.innerHTML = `
        <div class="content">
            <h1>Warning</h1>
            <p>All data used on Yalies is publicly accessible on the <a href="https://students.yale.edu/facebook">Yale Face Book</a> and the <a href="https://directory.yale.edu">Yale Directory</a>. Certain information provided by Yale is understandably disconcerting to some students, including street addresses and even phone numbers.</p>
            <p>Yalies censors such sensitive information, however, we can't do anything about what's on Yale's official sources. We encourage students to visit the <a href="https://students.yale.edu/facebook/PreferencesPage">Face Book preferences page</a> and remove information that makes them uncomfortable. Extended documentation on how to remove your data from Yale's sources has been compiled <a href="/hide_me">here</a>.</p>
            <button id="close_popup">Dismiss warning</button>
        </div>
    `;
    document.body.appendChild(popup);
}

showPopup();
