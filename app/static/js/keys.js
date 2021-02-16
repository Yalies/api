const description_key = document.getElementById('description_key'),
      readout_key = document.getElementById('readout_key'),
      get_key = document.getElementById('get_key'),
      keys_table = document.getElementById('keys_table');
      keys_list = document.getElementById('keys_list');


function submission_ready() {
    return Boolean(description_key.value);
}

description_key.onchange = function() {
    get_key.disabled = !submission_ready();
}

get_key.onclick = function(e) {
    fetch('/keys', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            description: description_key.value,
        })
    })
        .then(response => response.json())
        .then(json => {
            readout_key.value = json.key;
            readout_key.select();
            document.execCommand('copy');
            get_key.textContent = 'Copied!';
            setTimeout(function() {
                get_key.textContent = 'Get key';
            }, 1500);
        });
};

readout_key.onfocus = function(e) {
    this.select();
}

function delete_key(id) {

}

function load_keys() {
    fetch('/keys', {
        method: 'GET',
    })
        .then(response => response.json())
        .then(json => {
            keys_list.innerHTML = '';
            for (let key of json) {
                let tr = document.createElement('tr');
                for (let property of ['key', 'description']) {
                    let td = document.createElement('td');
                    td.textContent = key[property];
                    tr.appendChild(td);
                }
                // Create delete button
                let td = document.createElement('td');
                let button = document.createElement('button');
                button.className = 'delete';
                let icon = document.createElement('i');
                icon.className = 'fa fa-trash';
                button.appendChild(icon);
                button.appendChild(document.createTextNode('Delete'));
                button.onclick = function() {
                    delete_key(key.id);
                };
                td.appendChild(button);
                tr.appendChild(td);

                keys_list.appendChild(tr);
            }
        });
}

load_keys();
