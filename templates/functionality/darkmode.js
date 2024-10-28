{% load static %}

document.getElementById('dark-mode-toggle').addEventListener('click', () => {
    const isDarkMode = document.body.classList.toggle('bg-dark');
    document.body.classList.toggle('text-white');
    document.body.classList.toggle('bg-light');
    document.body.classList.toggle('text-dark');
    document.cookie = `darkmode=${isDarkMode}; path=/;`;
});
