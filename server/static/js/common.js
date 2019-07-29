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