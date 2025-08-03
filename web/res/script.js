// Cookie utilities
function setCookie(cname, cvalue, exmins) {
    const d = new Date();
    d.setTime(d.getTime() + (exmins * 60 * 1000));
    let expires = "Expires="+d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";Path=/;Secure;SameSite=Strict;"; // Make cookie secure
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

// TSF utilities
// See https://dorythecat.github.io/TransforMate/commands/transformation/export_tf.html#transformation-string-format
function encode_tsf(into,
                    image_url,
                    big = false,
                    small = false,
                    hush = false,
                    backwards = false,
                    stutter = 0,
                    proxy_prefix = null,
                    proxy_suffix = null,
                    bio = null,
                    prefixes = null,
                    suffixes = null,
                    sprinkles = null,
                    muffles = null,
                    alt_muffles = null,
                    censors = null) {
    data = ["15"]; // We're on TSFv1, so TMUDv15
    data.push(into);
    data.push(image_url);

    data.push(big ? "1" : "0");
    data.push(small ? "1" : "0");
    data.push(hush ? "1" : "0");
    data.push(backwards ? "1" : "0");

    data.push(stutter.toString());
    data.push(proxy_prefix);
    data.push(proxy_suffix);
    data.push(bio);

    data.push(prefixes ? "1" : "0");
    if (prefixes) {
        let prefix_data = []
        for (let prefix in prefixes) prefix_data.push(prefix + "|" + prefixes[prefix]);
        data.push(prefix_data.join(","));
    } else data.push("");
    data.push(suffixes ? "1" : "0");
    if (suffixes) {
        let suffix_data = []
        for (let suffix in suffixes) suffix_data.push(suffix + "|" + suffixes[suffix]);
        data.push(suffix_data.join(","));
    } else data.push("");
    data.push(sprinkles ? "1" : "0");
    if (sprinkles) {
        let sprinkle_data = []
        for (let sprinkle in sprinkles) sprinkle_data.push(sprinkle + "|" + sprinkles[sprinkle]);
        data.push(sprinkle_data.join(","));
    } else data.push("");
    data.push(muffles ? "1" : "0");
    if (muffles) {
        let muffle_data = []
        for (let muffle in muffles) muffle_data.push(muffle + "|" + muffles[muffle]);
        data.push(muffle_data.join(","));
    } else data.push("");
    data.push(alt_muffles ? "1" : "0");
    if (alt_muffles) {
        let alt_muffle_data = []
        for (let alt_muffle in alt_muffles) alt_muffle_data.push(alt_muffle + "|" + alt_muffles[alt_muffle]);
        data.push(alt_muffle_data.join(","));
    } else data.push("");
    data.push(censors ? "1" : "0");
    if (censors) {
        let censor_data = []
        for (let censor in censors) censor_data.push(censor + "|" + censors[censor]);
        data.push(censor_data.join(","));
    } else data.push("");
    return data.join(";");
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

// TSF Editor page
if (window.location.href.includes("tsf_editor.html")) {
    new_tf_name = document.getElementById("new_tf_name");
    new_tf_img = document.getElementById("new_tf_img");
    new_tf_submit = document.getElementById("new_tf_submit");

    new_tf_submit.onclick = function (e) {
        console.log(encode_tsf(new_tf_name.value, new_tf_img.value));
    }
}