const readout_token = document.getElementById("readout_token"),
      copy_token = document.getElementById("copy_token"),
      reset_token = document.getElementById("reset_token");


copy_token.onclick = function(e) {
    readout_token.select();
    document.execCommand('copy');
}

reset_token.onclick = function(e) {
    fetch('/credentials', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'filters': filters,
        }),
    })
        .then(response => response.json())
        .then(json => {
            readout_token.value = json.token;
        });
};

readout_token.onfocus = function(e) {
    this.select();
}
