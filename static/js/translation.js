function setLanguage(language) {
  localStorage.setItem('selectedLanguage', language);
  translatePage(language);
}

document.addEventListener("DOMContentLoaded", function() {
  let selectedLanguage = localStorage.getItem('selectedLanguage') || 'en';
  console.log("Page loaded. Current language from localStorage:", selectedLanguage);

  if (selectedLanguage !== 'en') {
    translatePage(selectedLanguage);
  }
});

async function translatePage(targetLanguage) {
  console.log(`Translating page to: ${targetLanguage}`);
  const elementsToTranslate = document.querySelectorAll('#content h2, #content p, #content button, #content a, #content label');

  const textArray = Array.from(elementsToTranslate).map(element => {
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
        // For <a> tags, only change the inner text, keep href
        if (element.tagName === 'A') {
          element.innerText = data.translatedTexts[index];
        } else {
          element.innerText = data.translatedTexts[index];
        }
      });
    } else {
      console.error("Translation error:", data.error);
      // Restore original text if translation fails
      elementsToTranslate.forEach((element) => {
        element.innerText = element.getAttribute('data-original-text');
      });
    }
  } catch (error) {
    console.error("Translation failed:", error);
    // Restore original text on network or translation error
    elementsToTranslate.forEach((element) => {
      element.innerText = element.getAttribute('data-original-text');
    });
  }
}

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
