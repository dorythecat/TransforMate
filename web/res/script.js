// Cookie utilities
const setCookie = (cname, cvalue, exmins) => {
    const expires = new Date(Date.now() + exmins * 60 * 1000).toUTCString();
    document.cookie = `${cname}=${cvalue};Expires=${expires};Path=/;Secure;SameSite=Strict;`;
};

const getCookie = (cname) => {
    const name = `${cname}=`;
    return document.cookie
        .split(';')
        .map(c => c.trim())
        .find(c => c.startsWith(name))
        ?.substring(name.length) || '';
};

// TSF utilities
// See https://dorythecat.github.io/TransforMate/commands/transformation/export_tf.html#transformation-string-format
function encode_tsf(into, image_url, options = {
    big: false,
    small: false,
    hush: false,
    backwards: false,
    stutter: 0,
    proxy_prefix: null,
    proxy_suffix: null,
    bio: null,
    prefixes: [],
    suffixes: [],
    sprinkles: [],
    muffles: [],
    alt_muffles: [],
    censors: []
}) {
    // Helper function to process arrays
    const processArray = (arr) =>
        !arr?.length ? ["0", ""] : ["1", arr.map(({content, value}) => `${content}|${value}`).join(",")];

    // Generate arrays and make it into the proper data to return
    return ["15",
            into,
            image_url,
            Number(options.big),
            Number(options.small),
            Number(options.hush),
            Number(options.backwards),
            options.stutter.toString(),
            options.proxy_prefix ?? "",
            options.proxy_suffix ?? "",
            options.bio ?? "",
            ...processArray(options.prefixes),
            ...processArray(options.suffixes),
            ...processArray(options.sprinkles),
            ...processArray(options.muffles),
            ...processArray(options.alt_muffles),
            ...processArray(options.censors)
    ].join(";");

}

// Token handling
if (window.location.href.includes("token")) {
    setCookie("token", window.location.href.split("=")[1], 7 * 24 * 60); // 7 days
    window.location.href = "index.html";
}

const login = document.getElementById("login");
const logout = document.getElementById("logout");

if (getCookie("token") !== "") {
    login.style.display = "none";
    logout.style.display = "block";
}

login.onclick = function (e) {
    window.location.href = "https://discord.com/oauth2/authorize?client_id=1274436972621987881&response_type=code&redirect_uri=http%3A%2F%2F127.0.0.1%3A8000%2Flogin%3Fredirect_url%3Dhttp%253A%252F%252Flocalhost%253A63342%252FTransforMate%252Fweb%252Findex.html&scope=identify+guilds";
}

logout.onclick = function (e) {
    setCookie("token", null, -1);
    window.location.href = "index.html";
}

// TSF Editor page
if (window.location.href.includes("tsf_editor.html")) {
    const elements = {
        new_tf_name: document.getElementById("new_tf_name"),
        new_tf_img: document.getElementById("new_tf_img"),
        new_tf_submit: document.getElementById("new_tf_submit"),
        new_tf_container: document.getElementById("new_tf_container"),
        tf_data_form: document.getElementById("tf_data_form"),
        big: document.getElementById("big"),
        small: document.getElementById("small"),
        hush: document.getElementById("hush"),
        backwards: document.getElementById("backwards"),
        bio: document.getElementById("bio")
    };

    const sliderPairs = [
        { name: 'stutter', default: 0 },
        { name: 'prefix_chance', default: 30 },
        { name: 'suffix_chance', default: 30 },
        { name: 'sprinkle_chance', default: 30 },
        { name: 'muffle_chance', default: 30 },
        { name: 'alt_muffle_chance', default: 30 }
    ].map(({ name, default: defaultValue }) => ({
        slider: document.getElementById(name),
        value: document.getElementById(`${name}_value`),
        defaultValue
    }));

    const syncSliderPair = (pair) => {
        const syncValues = (event) => {
            pair.slider.value = pair.value.value = event.target.value;
        };
        pair.slider.addEventListener("input", syncValues);
        pair.value.addEventListener("input", syncValues);
    };

    sliderPairs.forEach(syncSliderPair);

    const listConfigs = ['prefix', 'suffix', 'sprinkle', 'muffle', 'alt_muffle', 'censor']
        .reduce((acc, id) => {
            acc[id] = {
                list: [],
                container: document.getElementById(`${id}_container`),
                contentInput: document.getElementById(`${id}_content`),
                ...(id === 'censor'
                    ? { replacementInput: document.getElementById('censor_replacement') }
                    : { chancePair: sliderPairs[sliderPairs.findIndex(p => p.slider.id.includes(id))] })
            };
            return acc;
        }, {});

    window.removeFunction = (index, ID) => {
        listConfigs[ID].list.splice(index, 1);
        updateList(ID);
    };

    const updateList = (ID, isCensor = false) => {
        const { list, container } = listConfigs[ID];
        container.innerHTML = list
            .map((item, index) => `
                <li class="item">
                    <span>${item.content} (${item.value}${isCensor ? "" : "%"})</span>
                    <button type="button" onclick="removeFunction(${index}, '${ID}')">Remove</button>
                </li>`)
            .join('');
    };

    Object.entries(listConfigs).forEach(([ID, config]) => {
        const isCensor = ID === 'censor';
        document.getElementById(`add_${ID}_btn`)
            .addEventListener('click', () => {
                const valueInput = isCensor ? config.replacementInput.value : config.chancePair.slider.value;
                if (!config.contentInput.value || !valueInput) return;

                config.list.push({
                    content: config.contentInput.value,
                    value: valueInput
                });

                updateList(ID, isCensor);

                config.contentInput.value = '';
                if (isCensor) config.replacementInput.value = '';
                else {
                    config.chancePair.slider.value = config.chancePair.defaultValue;
                    config.chancePair.value.value = config.chancePair.defaultValue;
                }
            });
    });

    elements.new_tf_submit.onclick = () => {
        const { new_tf_name, new_tf_img } = elements;
        if (!new_tf_name.value || !new_tf_img.value) {
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
        elements.new_tf_container.style.width = "100%";
        elements.tf_data_form.style.display = "inline";
    };

    document.getElementById("submit_tf_btn").onclick = () => {
        // Generate TSF string with provided data
        const tsf_data = encode_tsf(
            elements.new_tf_name.value,
            elements.new_tf_img.value,
            {
                big: elements.big.checked,
                small: elements.small.checked,
                hush: elements.hush.checked,
                backwards: elements.backwards.checked,
                stutter: parseInt(document.getElementById("stutter_value").value),
                proxy_prefix: null,
                proxy_suffix: null,
                bio: elements.bio.value,
                prefixes: listConfigs.prefix.list,
                suffixes: listConfigs.suffix.list,
                sprinkles: listConfigs.sprinkle.list,
                muffles: listConfigs.muffle.list,
                alt_muffles: listConfigs.alt_muffle.list,
                censors: listConfigs.censor.list
            }
        );

        // Set output text
        const new_tf_output = document.getElementById("new_tf_output");
        new_tf_output.value = tsf_data;

        // Display output and associated label
        document.getElementById("tf_submit_output").style.display = "block";

        // Select and copy the output when the associated button is pressed
        document.getElementById("copy_tf_output").onclick = () => {
            new_tf_output.select();
            new_tf_output.setSelectionRange(0, 99999); // Mobile compatibility
            navigator.clipboard.writeText(new_tf_output.value).then(
                r => alert("Copied to clipboard!"),
                r => alert("Failed to copy to clipboard!")
            );
        }
    };
}

// Theme toggle utility
function setTheme(theme) {
    document.documentElement.setAttribute('data_theme', theme);
    localStorage.setItem('theme', theme);

    // Update the icon
    const themeToggle = document.getElementById('theme_toggle');
    themeToggle.textContent = theme === 'dark' ? 'Light Mode' : 'Dark Mode';
}

// Initialize theme
// Check for saved theme preference or default to dark theme
setTheme(localStorage.getItem('theme') || 'dark');

// Add click event listener to theme toggle button
const themeToggle = document.getElementById('theme_toggle');
themeToggle.addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data_theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
});

function toggleMenu() {
    var x = document.getElementsByClassName("topnav")[0];
    if (x.className === "topnav") {
        x.className += " responsive";
    } else {
        x.className = "topnav";
    }
}