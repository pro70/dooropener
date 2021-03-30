
// Load data functions

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

// Save data functions

function saveData(id, c, url) {
    const element = document.querySelector(`#${id} .${c} td .data`)
    const data = element.value

    const xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            console.log("update successful", url, data);
            loadData(element, url);
        }
    };
    xhttp.open('POST', url, true);
    xhttp.setRequestHeader('Content-type', 'text/plain');
    xhttp.send(data);
}

// Setup page

function initSaveButtons(id, classes) {
    for(var c in classes) {
        const button = document.querySelector(`#${id} .${c} td .save`)
        const url = 'api/status/' + id + '_' + c + classes[c];
        const button_class = c;
        button.onclick = () => saveData(id, button_class, url)
        console.log('init button with url', button, url)
    }
}

function initAllButtonsRelais(id) {
    const classes = {
        'on': '_url',
        'off': '_url',
        'time': '',
    };
    
    initSaveButtons(id, classes);
}

function initAllButtonsLifeCheck(id) {
    const classes = {
        'url': '',
        'time': '',
    };
    
    initSaveButtons(id, classes);
}

function initAllButtonsBell(id) {
    const classes = {
        'time': '',
    };
    
    initSaveButtons(id, classes);
}


window.onload = function() {
    loadAllRelais('r1');
    loadAllRelais('r2');
    loadAllLifeCheck('online');
    loadAllBell('bell');
    loadAllRelais('ba');

    initAllButtonsRelais('r1');
    initAllButtonsRelais('r2');
    initAllButtonsLifeCheck('online');
    initAllButtonsBell('bell');
    initAllButtonsRelais('ba');
}
