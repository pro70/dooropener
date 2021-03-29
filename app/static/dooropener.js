
function loadData(element, url) {
    const xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            element.value = this.responseText;
        }
    };
    xhttp.open("GET", url, true);
    xhttp.send();
}

function saveData(id, url) {
    const xhttp = new XMLHttpRequest();
    http.setRequestHeader('Content-type', 'text/plain');
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            console.log("update successful", url, value);
        }
    };
    xhttp.open('POST', url, true);
    xhttp.send(document.getElementById(id).value);
}

function loadAll(id, classes) {
    for(var c in classes) {
        const data = document.querySelector(`#${id} .${c} td .data`)
        const url = 'api/status/' + id + '_' + c + classes[c];
        loadData(data, url);
    }
}

function loadAllRelais(id) {
    const classes = {
        'on': '_url',
        'off': '_url',
        'time': '',
    };
    
    loadAll(id, classes);
}

function loadAllLifeCheck(id) {
    const classes = {
        'url': '',
        'time': '',
    };
    
    loadAll(id, classes);
}

function loadAllBell(id) {
    const classes = {
        'time': '',
    };
    
    loadAll(id, classes);
}

window.onload = function() {
    loadAllRelais('r1');
    loadAllRelais('r2');
    loadAllLifeCheck('online');
    loadAllBell('bell');
}
