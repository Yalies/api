const description_key = document.getElementById('description_key'),
      get_key = document.getElementById('get_key'),
      keys_table = document.getElementById('keys_table');
      keys_list = document.getElementById('keys_list');


function submission_ready() {
    return Boolean(description_key.value);
}
function refresh_button() {
    get_key.disabled = !submission_ready();
}

description_key.oninput = refresh_button;

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
        .then(key => {
            description_key.value = '';
            refresh_button();
            insert_key(key);
            keys_table.style.display = 'block';
            let key_readout = keys_list.querySelector('tr:first-child td:first-child input');
            key_readout.select();
            document.execCommand('copy');
            get_key.textContent = 'Copied!';
            setTimeout(function() {
                get_key.textContent = 'Create key';
            }, 1500);
        });
};

function delete_key(id) {
    fetch('/keys/' + id, {
        method: 'DELETE',
    })
        .then(response => response.json())
        .then(json => {
            load_keys();
        });
}

function create_td(content) {
    let td = document.createElement('td');
    td.textContent = content;
    return td;
}

function create_time_td(timestamp) {
    if (!timestamp) {
        return create_td('Never');
    }
    let date = new Date(timestamp);
    return create_td(date.toLocaleDateString() + ' ' + date.toLocaleTimeString());
}

function insert_key(key) {
    let tr = document.createElement('tr');

    let td_token = document.createElement('td');
    let input = document.createElement('input');
    input.type = 'text';
    input.value = key.token;
    input.readonly = true;
    input.onclick = function(e) {
        this.select();
    };
    td_token.appendChild(input);
    tr.appendChild(td_token);

    tr.appendChild(create_td(key.description));
    tr.appendChild(create_time_td(key.created_at));
    tr.appendChild(create_time_td(key.last_used));
    tr.appendChild(create_td(key.uses));

    // Create delete button
    let td_delete = document.createElement('td');
    let button = document.createElement('button');
    button.className = 'fail';
    let icon = document.createElement('i');
    icon.className = 'fa fa-trash';
    button.appendChild(icon);
    button.onclick = function() {
        delete_key(key.id);
    };
    td_delete.appendChild(button);
    tr.appendChild(td_delete);

    keys_list.appendChild(tr);

    return input;
}

function load_keys() {
    fetch('/keys', {
        method: 'GET',
    })
        .then(response => response.json())
        .then(keys => {
            keys_list.innerHTML = '';
            for (let key of keys) {
                insert_key(key);
            }
            keys_table.style.display = Boolean(keys.length) ? 'block' : 'none';
        });
}

load_keys();
