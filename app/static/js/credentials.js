const readout_token = document.getElementById("readout_token"),
      copy_token = document.getElementById("copy_token"),
      reset_token = document.getElementById("reset_token");


copy_token.onclick = function(e) {
    readout_token.select();
    document.execCommand('copy');
}

reset_token.onclick = function(e) {
    var req = new XMLHttpRequest();
    req.open("POST", "/credentials");
    req.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    req.send();
    req.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            var response = JSON.parse(this.responseText);
            readout_token.value = response.token;
        }
    };
};

readout_token.onfocus = function(e) {
    this.select();
}
