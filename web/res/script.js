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
    
    // Initialize with required fields
    const data = [
        "15",  // TSFv1/TMUDv15
        into,
        image_url,
        big ? "1" : "0",
        small ? "1" : "0",
        hush ? "1" : "0",
        backwards ? "1" : "0",
        stutter.toString(),
        proxy_prefix ?? "",
        proxy_suffix ?? "",
        bio ?? ""
    ];

    // Helper function to process arrays
    const processArray = (arr) => {
        if (!arr?.length) return ["0", ""];
        return ["1", arr.map(item => `${item.content}|${item.value}`).join(",")];
    };

    // Process all arrays
    const arrays = [prefixes, suffixes, sprinkles, muffles, alt_muffles, censors];
    arrays.forEach(arr => { data.push(...processArray(arr)); });

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
    const new_tf_name = document.getElementById("new_tf_name");
    const new_tf_img = document.getElementById("new_tf_img");
    const new_tf_submit = document.getElementById("new_tf_submit");
    const new_tf_container = document.getElementById("new_tf_container");
    const tf_data_form = document.getElementById("tf_data_form");

    new_tf_submit.onclick = function (e) {
        if (new_tf_name.value === "" || new_tf_img.value === "") {
            alert("Please fill out all required fields!");
            return;
        }
        if (new_tf_name.value.length < 2) {
            alert("Name must be at least 2 characters long!");
            return;
        }
        if (new_tf_img.value.length < 15 || new_tf_img.value.length > 1024 || !new_tf_img.value.startsWith("http")) {
            alert("Image URL must be a valid URL!");
            return;
        }
        new_tf_container.style.width = "100%";
        tf_data_form.style.display = "inline";
    }

    // Form data
    const big = document.getElementById("big");
    const small = document.getElementById("small");
    const hush = document.getElementById("hush");
    const backwards = document.getElementById("backwards");
    const bio = document.getElementById("bio");

    // Set the sliders to sync with their respective values and viceversa
    const sliderPairs = [
        { // Stutter
            slider: document.getElementById("stutter"),
            value: document.getElementById("stutter_value")
        },
        { // Prefix
            slider: document.getElementById('prefix_chance'),
            value: document.getElementById('prefix_chance_value')
        },
        { // Suffix
            slider: document.getElementById('suffix_chance'),
            value: document.getElementById('suffix_chance_value')
        },
        { // Sprinkles
            slider: document.getElementById('sprinkle_chance'),
            value: document.getElementById('sprinkle_chance_value')
        },
        { // Muffles
            slider: document.getElementById('muffle_chance'),
            value: document.getElementById('muffle_chance_value')
        },
        { // Alt Muffles
            slider: document.getElementById('alt_muffle_chance'),
            value: document.getElementById('alt_muffle_chance_value')
        }
    ];

    sliderPairs.forEach(pair => {
        // Sync slider to value input
        pair.slider.addEventListener("input", (event) => {
            pair.value.value = event.target.value;
        });

        // Sync value input to slider
        pair.value.addEventListener("input", (event) => {
            pair.slider.value = event.target.value;
        });
    });

    const listConfigs = {
        'prefixes': {
            list: [],
            container: document.getElementById('prefix-container'),
            contentInput: document.getElementById('prefix-content'),
            chancePair: sliderPairs[1]
        },
        'suffixes': {
            list: [],
            container: document.getElementById('suffix-container'),
            contentInput: document.getElementById('suffix-content'),
            chancePair: sliderPairs[2]
        },
        'sprinkles': {
            list: [],
            container: document.getElementById('sprinkle-container'),
            contentInput: document.getElementById('sprinkle-content'),
            chancePair: sliderPairs[3]
        },
        'muffles': {
            list: [],
            container: document.getElementById('muffle-container'),
            contentInput: document.getElementById('muffle-content'),
            chancePair: sliderPairs[4]
        },
        'alt_muffles': {
            list: [],
            container: document.getElementById('alt-muffle-container'),
            contentInput: document.getElementById('alt-muffle-content'),
            chancePair: sliderPairs[5]
        },
        'censors': {
            list: [],
            container: document.getElementById('censor-container'),
            contentInput: document.getElementById('censor-content'),
            replacementInput: document.getElementById('censor-replacement')
        }
    };

    const listButtons = {
        'prefixes': document.getElementById('add-prefix-btn'),
        'suffixes': document.getElementById('add-suffix-btn'),
        'sprinkles': document.getElementById('add-sprinkle-btn'),
        'muffles': document.getElementById('add-muffle-btn'),
        'alt_muffles': document.getElementById('add-alt-muffle-btn'),
        'censors': document.getElementById('add-censor-btn')
    }

    window.removeFunction = (index, ID) => {
        listConfigs[ID].list.splice(index, 1);
        updateList(ID);
    };

    function updateList(ID, censor = false) {
        const { list, container } = listConfigs[ID];
        container.innerHTML = '';

        list.forEach((item, index) => {
            const li = document.createElement('li');
            li.className = 'item';
            li.innerHTML = `
                <span>${item.content} (${item.value}${censor ? "" : "%"})</span>
                <button type="button" onclick="removeFunction(${index}, '${ID}')">Remove</button>
            `;
            container.appendChild(li);
        });
    }

    for (const [ID, button] of Object.entries(listButtons)) {
        button.addEventListener('click', () => {
            const config = listConfigs[ID];

            let valueInput = ID === 'censors' ? config.replacementInput.value : config.chancePair.slider.value
            if (!config.contentInput.value || !valueInput) return;

            const item = {
                content: config.contentInput.value,
                value: valueInput
            }

            config.list.push(item);
            updateList(ID, ID === 'censors');

            // Reset inputs
            config.contentInput.value = '';
            if (ID === 'censors') config.replacementInput.value = '';
            else {
                config.chancePair.slider.value = 30;
                config.chancePair.value.value = 30;
            }
        });
    }

    // Censor has to be handled separately due to it being a string-string pair
    

    const submit_tf_btn = document.getElementById("submit_tf_btn");

    submit_tf_btn.onclick = function (e) {
        const tsf_data = encode_tsf(
            new_tf_name.value,
            new_tf_img.value,
            big.checked,
            small.checked,
            hush.checked,
            backwards.checked,
            parseInt(document.getElementById("stutter_value").value),
            null,
            null,
            bio.value,
            listConfigs.prefixes.list,
            listConfigs.suffixes.list,
            listConfigs.sprinkles.list,
            listConfigs.muffles.list,
            listConfigs.alt_muffles.list,
            listConfigs.censors.list
        )

        console.log(tsf_data);
    }
}