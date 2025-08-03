// Cookie utilities
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

if (window.location.href.includes("token")) {
    // Discord tokens last 7 days, more or less
    setCookie("token", window.location.href.split("=")[1], 7 * 24 * 60);
    window.location.href = "index.html";
}

const login = document.getElementById("login");
const logout = document.getElementById("logout");

if (getCookie("token") !== "") {
    login.style.display = "none";
    logout.style.display = "block";
}

login.onclick = function (e) {
    // Link to Discord OAuth
    window.location.href = "https://discord.com/oauth2/authorize?client_id=1274436972621987881&response_type=code&redirect_uri=http%3A%2F%2F127.0.0.1%3A8000%2Flogin%3Fredirect_url%3Dhttp%253A%252F%252Flocalhost%253A63342%252FTransforMate%252Fweb%252Findex.html&scope=identify+guilds";
}

logout.onclick = function (e) {
    setCookie("token", null, -1);
    window.location.href = "index.html";
}