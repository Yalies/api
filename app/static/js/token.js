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
            readout_token.value = json.token;
            readout_token.select();
            document.execCommand('copy');
            get_token.textContent = 'Copied!';
            setTimeout(function() {
                get_token.textContent = 'Get token';
            }, 1500);
        });
};

readout_token.onfocus = function(e) {
    this.select();
}
