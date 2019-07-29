let fields = "image-fields";

function update_type() {
    let dropdown = document.forms["form"]["type-dropdown"];
    let panes = document.getElementsByClassName("media-fields");

    fields = "file-fields";
    if (dropdown.options[dropdown.selectedIndex].value === "Image")
        fields = "image-fields";

    for (let i = 0; i < panes.length; i++)
        panes[i].style.setProperty("display", panes[i].id === fields ? "" : "none");
}

function onVerify() {
    let file = "";
    switch (fields) {
        case "file-fields":
            file = document.forms["form"]["file"].value;
            break;
        case "image-fields":
            if (document.forms["form"]["image-vertical"].value === "" && document.forms["form"]["image-horizontal"].value === "") {
                alert("Please select a horizontal and or vertical image.");
                return false;
            } else if ((document.forms["form"]["image-vertical"].value === "" || document.forms["form"]["image-horizontal"].value === "") && !confirm("Are you sure you only want to upload a " + (document.forms["form"]["image-horizontal"].value === "" ? "vertical" : "horizontal") + " version of the image? Displays of the other orientation won't be able to show the image.")) {
                return false;
            }
            file = document.forms["form"]["image-horizontal"].value === "" ? document.forms["form"]["image-vertical"].value : document.forms["form"]["image-horizontal"].value;
            break
    }

    let startIndex = (file.indexOf('\\') >= 0 ? file.lastIndexOf('\\') : file.lastIndexOf('/'));
    let name = file.substring(startIndex);
    if (name.indexOf('\\') === 0 || name.indexOf('/') === 0)
        name = name.substring(1);
    sendForm("/upload-media/" + document.forms["form"]["media-name"].value + name.substr(name.length - 4, 4));

    return false;
}