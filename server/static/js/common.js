function hamburger() {
    document.getElementById("burger").classList.toggle('is-active');
    document.getElementById("navbar").classList.toggle('is-active');
}

function load() {
    let request = new XMLHttpRequest();
    request.open('GET', '/auth', true);
    request.onload = function() {
        if (request.responseText !== "admin")
            document.getElementById("admin-nav").style.display = "none";
    };
    request.send();
}

function sendForm(url, form='form') {
    let request = new XMLHttpRequest();
    request.open('POST', url, true);
    request.onload = function() {
        alert(request.responseText);
        document.forms[form].reset();
    };
    request.onerror = function() {
        alert(request.errorEmitted);
    };
    let data = new FormData(document.forms[form]);
    request.send(data);
}