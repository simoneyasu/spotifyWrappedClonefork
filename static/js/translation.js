/**
 * Sets the selected language in local storage and translates the page.
 *
 * @param {string} language - The target language code (e.g., "en" for English, "fr" for French).
 */
function setLanguage(language) {
  localStorage.setItem('selectedLanguage', language);
  translatePage(language);
}

/**
 * Event listener for the DOMContentLoaded event.
 * Initializes the page translation process by checking the stored language in local storage.
 */
document.addEventListener("DOMContentLoaded", function() {
  let selectedLanguage = localStorage.getItem('selectedLanguage') || 'en';
  console.log("Page loaded. Current language from localStorage:", selectedLanguage);

  if (selectedLanguage !== 'en') {
    translatePage(selectedLanguage);
  }
});

/**
 * Translates the text content of specified elements on the page to the target language.
 *
 * @async
 * @param {string} targetLanguage - The target language code (e.g., "en", "fr", "es").
 */
async function translatePage(targetLanguage) {
  console.log(`Translating page to: ${targetLanguage}`);

  const elementsToTranslate = Array.from(document.querySelectorAll('#content h1, #content h2, #content h3, #content h4, #content h5, #content p, #content button, #content a, #content label'))
                                    .filter(el => !el.closest('[data-no-translate]'));

  const textArray = elementsToTranslate.map(element => {
    // Save original text if not already saved
    if (!element.getAttribute('data-original-text')) {
      element.setAttribute('data-original-text', element.innerText);
    }
    return element.innerText;
  });

  const csrftoken = getCookie('csrftoken');

  try {
    const response = await fetch('/translation/translate/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken
      },
      body: JSON.stringify({ text: textArray, target: targetLanguage })
    });

    const data = await response.json();

    if (data.translatedTexts) {
      elementsToTranslate.forEach((element, index) => {
        // Apply translated text while keeping links intact
        element.innerText = data.translatedTexts[index];
      });
    } else {
      console.error("Translation error:", data.error);
      restoreOriginalText(elementsToTranslate);
    }
  } catch (error) {
    console.error("Translation failed:", error);
    restoreOriginalText(elementsToTranslate);
  }
}

/**
 * Restores the original text content of elements if the translation fails.
 *
 * @param {HTMLElement[]} elements - The list of elements whose text needs to be restored.
 */
function restoreOriginalText(elements) {
  elements.forEach((element) => {
    const originalText = element.getAttribute('data-original-text');
    if (originalText) {
      element.innerText = originalText;
    }
  });
}

/**
 * Retrieves the value of a specific cookie by name.
 *
 * @param {string} name - The name of the cookie to retrieve.
 * @returns {string|null} The value of the cookie if found, otherwise `null`.
 */
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
