const readout_key = document.getElementById('readout_key'),
      get_key = document.getElementById('get_key'),
      keys_list = document.getElementById('keys_list');


get_key.onclick = function(e) {
    fetch('/keys', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
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


fetch('/keys', {
    method: 'GET',
})
    .then(response => response.json())
    .then(json => {
        for (let key of json) {
            let tr = document.createElement('tr');
            for (let property of ['key', 'description']) {
                let td = document.createElement('td');
                td.textContent = key[property];
                tr.appendChild(td);
            }
            let td = document.createElement('td');
            let button = document.createElement('button');
            button.className = 'delete';

            button.onclick = function() {
                delete_key(key.id);
            };
        }
    });
