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
        });
};

readout_token.onfocus = function(e) {
    this.select();
}
