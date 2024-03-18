const FIELDS = [
    'socials_instagram',
    'socials_snapchat',
    'privacy_hide_image',
    'privacy_hide_email',
    'privacy_hide_room',
    'privacy_hide_phone',
    'privacy_hide_address',
    'privacy_hide_major',
    'privacy_hide_birthday'
];

const submit = document.getElementById('submit');
submit.onclick = async (e) => {
    const data = {};
    for(const field of FIELDS) {
        const elem = document.getElementById(field);
        if(elem.type === 'checkbox') data[field] = elem.checked;
        else if(elem.type === 'text') data[field] = elem.value;
    }
    let response;
    try {
        response = await fetch('/edit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
    } catch(e) {
        console.error(e);
    }
    if(response.status === 200) {
        window.location.reload();
    } else {
        console.error(response);
    }
}
