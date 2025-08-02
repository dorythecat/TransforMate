function setCookie(cname, cvalue, exmins) {
    const d = new Date();
    d.setTime(d.getTime() + (exmins * 60 * 1000));
    let expires = "expires="+d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

function getCookie(cname) {
    let name = cname + "=";
    let ca = document.cookie.split(';');
    for(let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') c = c.substring(1);
        if (c.indexOf(name) === 0) return c.substring(name.length, c.length);
    }
    return "";
}

function checkCookie() {
    let user = getCookie("username");
    if (user !== "") alert("Welcome again " + user);
    else {
        user = prompt("Please enter your name:", "");
        if (user !== "" && user != null) setCookie("username", user, 365);
    }
}

const login_form = document.getElementById("login_form");
const output = document.getElementById("output_message");

login_form.onsubmit = function(e) {
    e.preventDefault();
    const request = new XMLHttpRequest();
    request.open("POST", "http://localhost:8000/token", false);
    request.setRequestHeader("Accept", "application/json; odata=verbose");
    let form = new FormData(login_form);
    request.send(form);
    setCookie("token", JSON.parse(request.responseText)['access_token'], 30);
}