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

if (window.location.href.split("/").at(-1) === "login.html") {
    const login_form = document.getElementById("login_form");
    const output = document.getElementById("output_message");

    login_form.onsubmit = function (e) {
        e.preventDefault();
        const request = new XMLHttpRequest();
        request.open("POST", "http://localhost:8000/login", false);
        request.setRequestHeader("Accept", "application/json; odata=verbose");
        let form = new FormData(login_form);
        request.send(form);
        if (request.status === 200) {
            setCookie("token", JSON.parse(request.responseText)['access_token'], 30);
            window.location.href = "index.html";
        } else if (request.status === 403) output.textContent = "Incorrect username or password!";
        else output.textContent = "Unknown error!";
    }
}

const login = document.getElementById("login");
const logout = document.getElementById("logout");

if (getCookie("token") !== "") {
    login.style.display = "none";
    logout.style.display = "block";
}

logout.onclick = function (e) {
    setCookie("token", null, -1);
    window.location.reload();
}