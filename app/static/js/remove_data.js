const slides = [
    "slide_introduction",
    "slide_face_book_1",
    "slide_face_book_2",
    "slide_yalies",
    "slide_success",
];

const dataFields = [
    "image",
    "email",
    "room",
    "phone",
    "address",
    "major",
    "birthday",
];

const slideElems = slides.map(id => document.getElementById(id));
let currentSlideIndex = 0;

const save = document.getElementById("save");

const showNextSlide = () => showSlide(currentSlideIndex + 1);

function showSlide(slideIndex) {
    slideElems[currentSlideIndex].style.display = "none";
    slideElems[slideIndex].style.display = "block";
    currentSlideIndex = slideIndex;
}

showSlide(0);

Array.from(document.getElementsByClassName("next_slide_button")).forEach(
    button => button.onclick = showNextSlide
);

function showError(errorText) {
    save.textContent = errorText;
    save.classList.add("fail");
    setTimeout(function() {
        save.textContent = "Save";
        save.className = "";
    }, 1500);
}

async function submitRemoveData() {
    const values = {};
    for(const field of dataFields) {
        values[field] = document.getElementById(`${field}_yes`).checked;
    }

    let result;
    try {
        result = await fetch("/removeme", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(values),
        });
    } catch (error) {
        console.error(error);
        showError("Failed to save.");
        return;
    }

    if(!result.ok) {
        console.error(result);
        showError("Failed to save.");
        return;
    }
    
    showNextSlide();
}
