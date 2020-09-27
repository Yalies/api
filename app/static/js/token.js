const readout_token = document.getElementById('readout_token'),
      get_token = document.getElementById('get_token');


get_token.onclick = function(e) {
    fetch('/token', {
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
