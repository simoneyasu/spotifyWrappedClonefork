/**
 * Sets the selected language in local storage and translates the page.
 *
 * @param {string} language - The target language code (e.g., "en" for English, "fr" for French).
 */
function setLanguage(language) {
  localStorage.setItem('selectedLanguage', language);
  translatePage(language);
  location.reload();
}

/**
 * Event listener for the DOMContentLoaded event.
 * Initializes the page translation process by checking the stored language in local storage.
 */
document.addEventListener("DOMContentLoaded", function () {
  const selectedLanguage = localStorage.getItem('selectedLanguage') || 'en';
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

  // Select text nodes of elements to translate
  const elementsToTranslate = Array.from(document.querySelectorAll('*'))
    .filter(el => !el.closest('[data-no-translate]') && el.childNodes.length > 0)
    .flatMap(el =>
      Array.from(el.childNodes).filter(node =>
        node.nodeType === Node.TEXT_NODE && node.nodeValue.trim()
      )
    );

  if (elementsToTranslate.length === 0) {
    console.warn("No text nodes found for translation.");
    return;
  }

  const textArray = elementsToTranslate.map(node => node.nodeValue);
  console.log("Texts to translate:", textArray);

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

    if (data.translatedTexts && data.translatedTexts.length === elementsToTranslate.length) {
      elementsToTranslate.forEach((node, index) => {
        node.nodeValue = data.translatedTexts[index];
      });
    } else {
      console.error("Translation mismatch or error:", data.error || "Unknown error");
    }
  } catch (error) {
    console.error("Translation failed:", error);
  }
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

/**
 * MutationObserver for dynamically added or updated elements.
 */
const observer = new MutationObserver(() => {
  const selectedLanguage = localStorage.getItem('selectedLanguage') || 'en';
  if (selectedLanguage !== 'en') translatePage(selectedLanguage);
});

observer.observe(document.body, { childList: true, subtree: true });

/**
 * Handles elements that are dynamically added or modified, ensuring they are translated.
 */
document.addEventListener('DOMNodeInserted', function () {
  const selectedLanguage = localStorage.getItem('selectedLanguage') || 'en';
  if (selectedLanguage !== 'en') translatePage(selectedLanguage);
});
