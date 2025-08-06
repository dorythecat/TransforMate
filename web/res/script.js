// Global variables
TM_API = "http://api.transformate.live";

// General utility
const strJSON = (integer) => {
    return JSON.parse(integer.replace(/("[^"]*"\s*:\s*)(\d{16,})/g, '$1"$2"'));
}

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

function decode_tsf(tsf) {
    tsf = tsf.split(";");

    if (tsf[0] !== "15" || tsf.length !== 23) return;

    const getArray = (index) => {
        if (tsf[index] === "0") return [];
        return tsf[index + 1].split(",").map(p => {
            const [content, value] = p.split("|");
            return {content, value};
        });
    }

    return {
        into: tsf[1],
        image_url: tsf[2],
        big: tsf[3] === "1",
        small: tsf[4] === "1",
        hush: tsf[5] === "1",
        backwards: tsf[6] === "1",
        stutter: parseInt(tsf[7]),
        proxy_prefix: tsf[8],
        proxy_suffix: tsf[9],
        bio: tsf[10],
        prefixes: getArray(11),
        suffixes: getArray(13),
        sprinkles: getArray(15),
        muffles: getArray(17),
        alt_muffles: getArray(19),
        censors: getArray(21)
    }
}

// Token handling
if (window.location.href.includes("token")) {
    setCookie("token", window.location.href.split("=")[1], 7 * 24 * 60); // 7 days
    window.location.href = "index.html";
}

const login = document.getElementById("login");
const logout = document.getElementById("logout");

if (getCookie("token") !== "") {
    login.classList.add("hidden");
    logout.classList.remove("hidden")
}

login.onclick = function (e) {
    window.location.href = "https://discord.com/oauth2/authorize?client_id=1274436972621987881&response_type=code&redirect_uri=http%3A%2F%2F127.0.0.1%3A8000%2Flogin%3Fredirect_url%3Dhttp%253A%252F%252Flocalhost%253A63342%252FTransforMate%252Fweb%252Findex.html&scope=identify+guilds";
}

logout.onclick = async function (e) {
    try {
        const response = await fetch(`${TM_API}/logout`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getCookie('token')}`
            }
        });
    } catch (error) {
        console.error('Error during logout:', error);
    }
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
        tf_file_container: document.getElementById("tf_file_container"),
        tf_data_form: document.getElementById("tf_data_form"),
        big: document.getElementById("big"),
        small: document.getElementById("small"),
        hush: document.getElementById("hush"),
        backwards: document.getElementById("backwards"),
        bio: document.getElementById("bio")
    };

    if (getCookie("token") !== "") {
        const response = fetch(`${TM_API}/users/me/discord`, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${getCookie("token")}`
            }
        }).catch(e => console.error(e)).then(r => r.text()).then(r => strJSON(r));

        response.then(r => {
            elements.new_tf_name.value = r.username;
            elements.new_tf_img.value = `https://cdn.discordapp.com/avatars/${r.id}/${r.avatar}.png`;
        })
    }

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

    const updateList = (ID) => {
        const { list, container } = listConfigs[ID];
        container.innerHTML = list
            .map((item, index) => `
                <li class="item">
                    <span>${item.content} (${item.value}${ID === 'censor' ? "" : "%"})</span>
                    <button type="button" onclick="removeFunction(${index}, '${ID}')">Remove</button>
                </li>`)
            .join('');
    };

    window.removeFunction = (index, ID) => {
        listConfigs[ID].list.splice(index, 1);
        updateList(ID);
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

                updateList(ID);

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
        elements.tf_data_form.style.display = "inline";
        elements.new_tf_submit.style.display = "none";
        elements.tf_file_container.style.display = "none";
    };

    let loaded_servers = [];
    document.getElementById("submit_tf_btn").onclick = async () => {
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

        // Select and copy the output when the associated button is pressed
        document.getElementById("copy_tf_output").onclick = () => {
            new_tf_output.select();
            new_tf_output.setSelectionRange(0, 99999); // Mobile compatibility
            navigator.clipboard.writeText(new_tf_output.value).then(
                r => alert("Copied to clipboard!"),
                r => alert("Failed to copy to clipboard!")
            );
        }

        // Download the TSF-compliant file when the associated button is pressed
        document.getElementById("download_tf_output").onclick = () => {
            const element = document.createElement('a');
            element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(tsf_data));
            element.setAttribute('download', `${elements.new_tf_name.value}.tsf`);
            element.click();
            element.remove();
        }

        const loading_container = document.getElementById("loading_container");

        // Check if the user is logged in, if they are, allow them to select what server to apply the transformation to,
        // and wait before loading the rest of the elements down here
        if (getCookie("token") && loaded_servers.length === 0) {
            // Make the throbber visible
            loading_container.style.display = "block";

            const response = fetch(`${TM_API}/users/me/discord/servers`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${getCookie('token')}`
                }
            }).catch(e => console.error(e)).then(r => r.text()).then(r => strJSON(r));

            await response.then(servers => {
                loaded_servers = servers;
                const serverSelect = document.getElementById("tf_output_server");
                for (const server of loaded_servers) {
                    const option = document.createElement("option");
                    option.value = server['id'];
                    option.textContent = server['name'];
                    serverSelect.appendChild(option);
                }

                const button = document.getElementById("apply_tf_output");
                button.onclick = async () => {
                    const server = serverSelect.value;
                    if (server === "") return;
                    const response = fetch(`${TM_API}/users/me/tsf/${server}`, {
                        method: 'PUT',
                        headers: {
                            'Authorization': `Bearer ${getCookie('token')}`,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(tsf_data)
                    }).catch(e => console.error(e)).then(r => r.json());

                    await response.then(r => {
                        alert("Transformation applied successfully!");
                        window.location.href = "tsf_editor.html";
                    });
                }

                serverSelect.classList.remove("hidden");
                button.classList.remove("hidden");
            });

            loading_container.style.display = "none";
            document.getElementById("tf_submit_output").style.display = "block";
        }
        loading_container.style.display = "none";
        document.getElementById("tf_submit_output").style.display = "block";
    };

    const inputElement = document.getElementById("tf_file_input");
    inputElement.addEventListener("change", handleFiles, false);
    function handleFiles() {
        const fileList = this.files;
        const file = fileList[0];
        const reader = new FileReader();
        reader.readAsText(file);
        // The file contains a TSF string to decode
        reader.onload = function (e) {
            const data = decode_tsf(e.target.result);
            if (!data) return;

            elements.new_tf_name.value = data.into;
            elements.new_tf_img.value = data.image_url;
            elements.big.checked = data.big;
            elements.small.checked = data.small;
            elements.hush.checked = data.hush;
            elements.backwards.checked = data.backwards;
            elements.bio.value = data.bio;

            document.getElementById("stutter").value = data.stutter;
            document.getElementById("stutter_value").value = data.stutter;

            // We need to pair them since they have different names.
            const pairs = {
                'prefix': 'prefixes',
                'suffix': 'suffixes',
                'sprinkle': 'sprinkles',
                'muffle': 'muffles',
                'alt_muffle': 'alt_muffles',
                'censor': 'censors'
            }

            for (const [key, value] of Object.entries(pairs)) {
                const list = listConfigs[key].list;
                const dataList = data[value];
                for (const [index, item] of dataList.entries()) {
                    list[index] = {
                        content: item.content,
                        value: item.value
                    }
                }
                updateList(key);
            }

            elements.tf_data_form.style.display = "inline";
            elements.new_tf_submit.style.display = "none";
            elements.tf_file_container.style.display = "none";
        }
    }
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

// Add click event listener to the theme toggle button
const themeToggle = document.getElementById('theme_toggle');
themeToggle.addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data_theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
});

function toggleMenu() {
    const x = document.getElementsByClassName("topnav")[0];
    if (x.className === "topnav") x.className += " responsive";
    else x.className = "topnav";
}