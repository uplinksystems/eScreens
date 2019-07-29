let fields = "file-fields";

function updateType() {
    let dropdown = document.getElementById("type");
    let panes = document.getElementsByClassName("media-fields");

    switch (dropdown.options[dropdown.selectedIndex].value) {
        case "Image":
        case "Video":
        case "Presentation":
            fields = "file-fields";
            break;
        case "Countdown":
            fields = "countdown-fields";
            break;
        case "Twitch":
            fields = "stream-fields";
            break;
    }

    for (let i = 0; i < panes.length; i++)
        panes[i].style.setProperty("display", panes[i].id === fields ? "" : "none");
}

function updatePreview() {

}

function onVerify() {
    switch (fields) {
        case "file-fields":
            if (document.forms["form"]["media-names"].value === "") {
                alert("Please select a media file to display.");
                return false;
            } else if (document.forms["form"]["screens"].value === "") {
                alert("Please select at least one location to display at.");
                return false;
            } else if (document.forms["form"]["start-time"].value === "") {
                alert("Please select a starting time");
                return false;
            }
            break;
        case "countdown-fields":

            break
    }

    sendForm("/create-default");

    return false;
}

function onLoad() {
    $.get(window.location.origin + "/screen", function (data, status) {
        let select = document.forms["form"]['screens'];
        for (let index in data) {
            select.options[select.options.length] = new Option(data[index], index);
        }
    });

    $.get(window.location.origin + "/media", function (data, status) {
        let select = document.forms["form"]['media-names'];
        for (let index in data) {
            select.options[select.options.length] = new Option(data[index], index);
        }
    });
}