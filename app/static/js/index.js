///////////////////
// Page elements //
///////////////////
let p = {
	checkboxes: document.querySelectorAll('input[type="checkbox"]'),
	allCheckboxes: document.querySelectorAll(
		'input[type="checkbox"][name$="-all"]'
	),
	query: document.getElementById("query"),
	submit: document.getElementById("submit"),
	filters: document.getElementsByClassName("filter"),
	clearFilters: document.getElementById("clear_filters"),
	list: document.getElementById("list"),
	loading: document.getElementById("loading"),
	empty: document.getElementById("empty"),
	scrollTop: document.getElementById("scroll_top"),
};

//////////////
// Controls //
//////////////
query.onkeyup = function (e) {
	if (e.keyCode === 13) {
		e.preventDefault();
		p.submit.click();
	}
};

function collapseAllFilters() {
	for (let filter of p.filters) {
		filter.classList.add("collapsed");
	}
}

function resetFilters() {
	for (let filter of p.filters) {
		filter.classList.add("collapsed");
		filter.classList.remove("active");
	}
	for (let checkbox of p.checkboxes) {
		checkbox.checked = false;
	}
	for (let checkbox of p.allCheckboxes) {
		checkbox.checked = true;
	}
}
resetFilters();

// ... (other controls)
const schoolFilter = document.getElementById("school"),
	schoolAllCheckbox = document.querySelector('input[name="school-all"]'),
	schoolYCCheckbox = document.querySelector('input[name="Yale College"]');
schoolFilter.classList.add("active");
schoolAllCheckbox.checked = false;
schoolYCCheckbox.checked = true;

p.clearFilters.onclick = function () {
	resetFilters();
	runSearch();
};

function isFilter(element) {
	return element.tagName === "DIV" && element.classList.contains("filter");
}

function isPronunciation(element) {
	return (
		element.tagName === "SPAN" && element.classList.contains("pronunciation")
	);
}

onclick = function (e) {
	let filter = null;
	if (isFilter(e.target)) {
		filter = e.target;
	} else if (e.target.tagName === "H4" && isFilter(e.target.parentElement)) {
		filter = e.target.parentElement;
	} else if (
		e.target.tagName === "I" &&
		isFilter(e.target.parentElement.parentElement)
	) {
		filter = e.target.parentElement.parentElement;
	}
	if (filter) {
		filter.classList.toggle("collapsed");
	}

	let pronunciation = null;
	if (isPronunciation(e.target)) {
		pronunciation = e.target;
	} else if (
		e.target.tagName === "I" &&
		isPronunciation(e.target.parentElement)
	) {
		pronunciation = e.target.parentElement;
	}

	if (pronunciation) {
		// Play audio

		let audio = pronunciation.getElementsByTagName("audio")[0];
		if (!isPlaying(audio)) {
			pronunciation.classList.add("playing");
			audio.onended = function () {
				pronunciation.classList.remove("playing");
			};
			audio.play();
		} else {
			pronunciation.classList.remove("playing");
			audio.pause();
			audio.currentTime = 0;
		}
	}
};

function isPlaying(audio) {
	return !audio.paused;
}

onchange = function (e) {
	let input = e.target;
	if (input.type === "checkbox") {
		let checked = input.checked;
		let otherCheckboxes = Array.from(
			input.parentElement.parentElement.getElementsByTagName("input")
		);
		let allCheckbox = otherCheckboxes.shift();
		let filter = input.parentElement.parentElement;
		if (input == allCheckbox) {
			filter.classList.toggle("active", !checked);
			for (let checkbox of otherCheckboxes) {
				checkbox.checked = !checked;
			}
		} else {
			if (checked) {
				filter.classList.add("active");
				allCheckbox.checked = false;
			} else {
				let anyChecked = false;
				for (let checkbox of otherCheckboxes) {
					if (checkbox.checked) {
						anyChecked = true;
						break;
					}
				}
				filter.classList.toggle("active", anyChecked);
				allCheckbox.checked = !anyChecked;
			}
		}
		runSearch();
	}
};

p.scrollTop.onclick = function () {
	window.scrollTo({
		top: 0,
		behavior: "smooth",
	});
};

///////////////////
// List building //
///////////////////
let criteria = {
	filters: {},
};
let pagesLoaded = 0;
let pagesFinished = false;

function runSearch() {
	let filters = {};
	for (let filter of p.filters) {
		let category = filter.id;
		let otherCheckboxes = Array.from(filter.getElementsByTagName("input"));
		let allCheckbox = otherCheckboxes.shift();
		if (!allCheckbox.checked) {
			filters[category] = [];
			for (let checkbox of otherCheckboxes) {
				if (checkbox.checked) {
					if (category === "leave") {
						if (checkbox.name === "True") {
							filters[category].push(true);
						} else if (checkbox.name === "False") {
							filters[category].push(false);
						} else {
							filters[category].push(checkbox.name || null);
						}
					} else if (
						["year", "birth_month", "birth_day", "floor", "room"].includes(
							category
						)
					) {
						filters[category].push(
							checkbox.name ? parseInt(checkbox.name) : null
						);
					} else {
						filters[category].push(checkbox.name);
					}
				}
			}
		}
	}
	criteria = {};
	query = p.query.value.trim();
	if (query) criteria["query"] = query;
	criteria["filters"] = filters;
	p.list.innerHTML = "";
	pagesLoaded = 0;
	pagesFinished = false;
	loadNextPage();
}

p.submit.onclick = function () {
	collapseAllFilters();
	runSearch();
};

/**
 * Adds a metadata pill to a container if the provided person's property has a value.
 * @param {HTMLElement} pillContainer - The container to which the pill will be added.
 * @param {string} property - The property name of the person.
 * @param {string} title - The title to be displayed in the pill.
 * @param {string} icon - The icon class for the pill.
 * @param {object} person - The person object containing the property.
 */
function addPill(pillContainer, property, title, icon, person) {
	// Get the value of the specified property from the person object
	let value = person[property];

	// Check if the value exists
	if (value) {
		// Create a new div element for the pill
		let pill = document.createElement("div");
		pill.className = "pill_metadata";

		// Create an icon element
		let iconElement = document.createElement("i");
		iconElement.className = "fa fa-" + icon;
		pill.appendChild(iconElement);

		// Create a span element for the text content
		let textSpan = document.createElement("span");
		textSpan.style.paddingLeft = "2px";

		// Set the text content of the span element based on the value type
		if (typeof value === "string" && value.includes("\n")) {
			// If the value is a string with line breaks, only display the last line
			let lines = value.split("\n");
			textSpan.textContent += lines[lines.length - 1];
		} else {
			// Otherwise, display the full value
			textSpan.textContent += " " + value;
		}
		pill.appendChild(textSpan);

		// Append the pill to the container
		pillContainer.appendChild(pill);
	}
}

/**
 * Adds a row of information to the container if the provided person's property has a value.
 * @param {HTMLElement} container - The container to which the row will be added.
 * @param {string} property - The property name of the person.
 * @param {string} title - The title of the row (optional).
 * @param {string} icon - The icon class for the row.
 * @param {object} person - The person object containing the property.
 * @param {string} url - URL (optional) for creating a link within the row's content.
 * @param {boolean} showTitle - Indicates whether to display the title in the link (if 'url' is provided).
 * @param {boolean} checkLeave - Indicates whether to check 'leave' and 'visitor' properties.
 */
function addRow(
	container,
	property,
	title,
	icon,
	person,
	url,
	showTitle,
	checkLeave
) {
	let value = person[property];

	// Check if the value exists
	if (value) {
		// Create a new div element for the row
		let row = document.createElement("div");

		// Set title attribute if provided
		if (title) {
			row.title = title;
		}

		// Add classes for styling
		row.classList.add("row");
		row.classList.add(property);

		// Create an icon element
		let iconElement = document.createElement("i");
		iconElement.style.paddingRight = "3px";
		iconElement.className = "fa fa-" + icon;
		row.appendChild(iconElement);

		// Create a paragraph element for the content
		let contentParagraph = document.createElement("p");
		contentParagraph.classList.add("value");
		contentParagraph.classList.add(property);

		// Handle different value types and conditions
		if (typeof value === "string" && value.includes("\n")) {
			let lines = value.split("\n");
			contentParagraph.textContent = lines[lines.length - 1];
		} else if (url) {
			let link = document.createElement("a");
			link.href = url;
			link.textContent = showTitle ? title : value;
			contentParagraph.appendChild(link);
		} else {
			// Handle special cases like 'leave' and 'visitor'
			if (property === "leave") {
				contentParagraph.textContent = "Took Leave";
			} else if (property === "visitor") {
				contentParagraph.textContent = "Visiting International Program";
			} else {
				contentParagraph.textContent = value;
			}
		}

		// Check if 'checkLeave' is true
		if (checkLeave) {
			let leaveValue = person["leave"];
			let leavespan = document.createElement("span");
			if (leaveValue) {
				leavespan.classList.add("leave");
				leavespan.textContent = " (Took Leave)";
			} else {
				let visitValue = person["visitor"];
				if (visitValue) {
					leavespan.classList.add("visitor");
					leavespan.textContent = " (Visiting Student)";
				}
			}
			contentParagraph.appendChild(leavespan);
		}

		// Apply different styling based on content length
		if (
			contentParagraph.textContent.length > 20 &&
			contentParagraph.textContent.length < 25
		) {
			contentParagraph.classList.add("long_value");
		} else if (contentParagraph.textContent.length >= 25) {
			contentParagraph.classList.add("longer_value");
		}

		// Append the content paragraph to the row
		row.appendChild(contentParagraph);

		// Append the row to the container
		container.appendChild(row);
	}
}

function createPronunciationButton(person) {
	let button = document.createElement("span");
	button.className = "pronunciation";
	if (person.phonetic_name) {
		button.title = person.phonetic_name;
	}
	let icon = document.createElement("i");
	icon.className = "fa fa-volume-up";

	let audio = document.createElement("audio");
	let source = document.createElement("source");
	source.src = person.name_recording;
	// All pronunciations appear to be mp3 files
	source.type = "audio/mpeg";
	audio.appendChild(source);

	icon.appendChild(audio);
	button.appendChild(icon);
	return button;
}

/**
 * Loads the next page of people's information if available.
 */
function loadNextPage() {
	// Check if there are more pages to load
	if (!pagesFinished) {
		// Hide the 'empty' element and show the 'loading' element
		p.empty.style.display = "none";
		p.loading.style.display = "block";

		// Update the page criteria with the next page number
		criteria["page"] = ++pagesLoaded;
		console.log("Loading page", pagesLoaded);

		// Fetch the data from the server
		fetch("/api/people", {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify(criteria),
		})
			.then((response) => response.json())
			.then((people) => {
				// Update the flag for finished pages based on the number of fetched people
				pagesFinished = people.length < 20;

				// Display the 'empty' element if it's the first page and no people are fetched
				if (pagesLoaded === 1 && !people.length) {
					p.empty.style.display = "block";
				}

				// Loop through the fetched people and create elements for each
				for (let person of people) {
					// Create a container for the person's information
					let personContainer = document.createElement("div");
					personContainer.className = "person";

					// Create a wrapper for the header
					let headerWrapper = document.createElement("div");
					headerWrapper.className = "header_wrap";

					// Create an element for the person's image (if available)
					let image = document.createElement("div");
					image.className = "image";
					if (person.image) {
						image.style.backgroundImage = "url(" + person.image + ")";
					}
					headerWrapper.appendChild(image);

					// Create a wrapper for the person's name
					let nameWrapper = document.createElement("div");
					nameWrapper.className = "name_wrap";

					// Create an element for the person's name
					let name = document.createElement("h3");
					name.className = "name";
					name.style.marginTop = "0px";

					// Build the full name
					let fullName = person.last_name + ", " + person.first_name;

					// Add a class for long names
					if (fullName.length > 20) {
						name.classList.add("long_name");
					}

					// Create a link if the person's profile URL is available
					if (person.profile) {
						let a = document.createElement("a");
						a.href = person.profile;
						a.textContent = fullName;
						name.appendChild(a);
					} else {
						name.textContent = fullName;
					}

					// Add pronunciation button if available
					if (person.name_recording) {
						name.textContent += " ";
						name.appendChild(createPronunciationButton(person));
					}
					nameWrapper.appendChild(name);

					// Add rows for different information categories
					addRow(
						nameWrapper,
						"email",
						"Email",
						"envelope",
						person,
						person.email ? "mailto:" + person.email : null,
						false
					);
					if (person.college_code) {
						let row = document.createElement("div");
						row.title = "Residential College";
						row.classList.add("row");
						row.classList.add("college");
						let img = document.createElement("img");
						img.src = "/static/images/shields/" + person.college_code + ".png";
						row.appendChild(img);
						let readout = document.createElement("p");
						readout.textContent = person.college;
						readout.classList.add("value");
						readout.classList.add("college");
						row.appendChild(readout);
						nameWrapper.appendChild(row);
					}
					if (person.school && !person.college_code) {
						addRow(nameWrapper, "school", "School", "university", person);
					}
					addRow(
						nameWrapper,
						"year",
						"Graduation Year",
						"graduation-cap",
						person,
						null,
						true,
						true
					);
					// Don't show student Phone#
					if (person.school_code !== "YC") {
						addRow(
							nameWrapper,
							"phone",
							"Phone Number",
							"phone",
							person,
							person.phone ? "tel:" + person.phone : null,
							false
						);
					}
					addRow(
						nameWrapper,
						"website",
						"Website",
						"globe",
						person,
						person.website,
						false,
						true
					);

					// Append the name wrapper to the header wrapper
					headerWrapper.appendChild(nameWrapper);

					// Append the header wrapper to the person container
					personContainer.appendChild(headerWrapper);

					// Create a container for the metadata pills
					let pills = document.createElement("div");
					pills.className = "pills";

					// Add NETid pills
					if (person.netid || person.upi) {
						if (person.netid) {
							let pill = document.createElement("div");
							pill.className = "pill";
							pill.textContent = "NetID " + person.netid;
							pills.appendChild(pill);
						}
						if (person.upi) {
							let pill = document.createElement("div");
							pill.className = "pill";
							pill.textContent = "UPI " + person.upi;
							pills.appendChild(pill);
						}
					}

					// Add metadata pills
					addPill(pills, "pronouns", "Pronouns", "comments", person);
					addPill(pills, "title", "Title", "tags", person);
					addPill(pills, "major", "Major", "book", person);
					addPill(pills, "birthday", "Birthday", "birthday-cake", person);
					addPill(pills, "address", "Address", "home", person);

					// Append the pills container to the person container
					personContainer.appendChild(pills);

					// Append the person container to the main list
					p.list.appendChild(personContainer);
				}

				// Hide the 'loading' element once the data is fetched and processed
				p.loading.style.display = "none";
			});
	}
}

runSearch();

window.onscroll = function (e) {
	if (2 * window.innerHeight + window.scrollY >= document.body.offsetHeight) {
		loadNextPage();
		// Temporarily set so that we won't load tons of pages at once
		pagesFinished = true;
	}

	p.scrollTop.classList.toggle(
		"shown",
		window.scrollY > 2 * window.innerHeight
	);
};

document.addEventListener("DOMContentLoaded", (event) => {
	let filters = document.querySelectorAll("#filters > div");
	filters.forEach((filter, index) => {
		const IMPORTANT_FILTERS = 4; // NUMBER OF DEFAULT FILTERS
		if (index >= IMPORTANT_FILTERS) {
			filter.style.display = "none";
		}
	});

	document
		.getElementById("expand_filters")
		.addEventListener("click", function () {
			filters.forEach((filter) => {
				filter.style.display = "inline-block";
			});
			this.style.display = "none";
		});
});
