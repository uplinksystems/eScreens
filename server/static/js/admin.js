function onVerifyUpdate() {
    if (document.forms["form-update"]["updateFile"].value === "") {
        alert("Please select a python program.");
        return false;
    }
    if (!confirm("Are you sure you want to update with this file? This will overwrite the program on all displays."))
        return false;
    sendForm("/update", form='form-update');

    return false;
}

function onVerifyAddDisplay() {
    if (document.forms["form-add-display"]["screen-name"].value === "") {
        alert("Please specify a screen name.");
        return false;
    }

    if (!confirm("Are you sure you want to create a display with this name? If a screen of this name already exists, it will completely overwrite it."))
        return false;

    sendForm("/create-screen", form='form-add-display');

    return false;
}