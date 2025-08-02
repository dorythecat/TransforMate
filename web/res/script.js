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
        request.setRequestHeader("accept", "application/json");
        let form = new FormData(login_form);
        request.send(form);
        if (request.status === 200) {
            setCookie("token", JSON.parse(request.responseText)['access_token'], 30);
            window.location.href = "index.html";
        } else if (request.status === 403) output.textContent = "Incorrect username or password!";
        else output.textContent = "Unknown error!";
    }
}

if (window.location.href.split("/").at(-1) === "account.html") {
    const username = document.getElementById("username");
    const email = document.getElementById("email");
    const linked_id = document.getElementById("linked_id");

    const request = new XMLHttpRequest();
    request.open("GET", "http://localhost:8000/users/me", false);
    request.setRequestHeader("accept", "application/json");
    request.setRequestHeader("Authorization", `Bearer ${getCookie("token")}`);
    request.send();
    response = JSON.parse(request.responseText);

    username.innerHTML += response['username'];
    email.innerHTML += response['email'];
    linked_id.innerHTML += response['linked_id'];
}

const login = document.getElementById("login");
const account = document.getElementById("account");
const logout = document.getElementById("logout");

if (getCookie("token") !== "") {
    login.style.display = "none";
    account.style.display = "block";
    logout.style.display = "block";
}

logout.onclick = function (e) {
    setCookie("token", null, -1);
    window.location.reload();
}