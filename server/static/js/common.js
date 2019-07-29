function hamburger() {
    document.getElementById("burger").classList.toggle('is-active');
    document.getElementById("navbar").classList.toggle('is-active');
}

function sendForm(url) {
    let request = new XMLHttpRequest();
    request.open('POST', url, true);
    request.onload = function() {
        alert(request.responseText);
        document.forms["form"].reset();
    };
    request.onerror = function() {
        alert(request.errorEmitted);
    };
    console.log(document.forms["form"]);
    let form = new FormData(document.forms['form']);
    request.send(form);
}