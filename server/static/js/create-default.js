let fields = "file-fields";

function updateType() {
    let dropdown = document.forms['form']["type"];
    let panes = document.getElementsByClassName("media-fields");

    document.getElementById("image-preview").style.display = "none";
    switch (dropdown.options[dropdown.selectedIndex].value) {
        case "Image":
            document.getElementById("image-preview").style.display = "";
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
    let image = document.forms["form"]["media-names"].options[document.forms["form"]["media-names"].selectedIndex].label;
    let splot = image.split(".");
    if (splot[1] === "png" || splot[1] === "jpg" || splot[1] === "jpeg") {
        document.getElementById("image-preview-vertical").src = "/media/" + splot[0] + "_vertical." + splot[1];
        document.getElementById("image-preview-horizontal").src = "/media/" + splot[0] + "_horizontal." + splot[1];
    } else {
        document.getElementById("image-preview-vertical").src = "";
        document.getElementById("image-preview-horizontal").src = "";
    }
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