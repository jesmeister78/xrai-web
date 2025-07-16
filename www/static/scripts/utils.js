function getFormJSON(formId) {
	const form = document.querySelector(`form#${formId}`);

	if (!form) {
		console.error("No form element found with ID:", formId);
		return {};
	}
	const formData = new FormData(form);
	return Object.fromEntries(formData.entries());
}

function getChangedValues(original, updated) {
	const changes = {};

	for (const key in updated) {
		if (updated.hasOwnProperty(key)) {
			if (original[key] !== updated[key]) {
				changes[key] = updated[key];
			}
		}
	}

	return changes;
}
