$(document).ready(function () {

    document.querySelectorAll('iframe[type="embed-pdf"]').forEach(iFrame => {
        const observer = new MutationObserver((mutationList) => {
            for (const mutation of mutationList) {
                if (mutation.attributeName === 'src') {
                    const newValue = mutation.target.getAttribute('src');
                    const parentContainer = mutation.target.closest('.embed-pdf-container');
                    const downloadLink = parentContainer.querySelector('a[data-type="embed-pdf-download"]');
                    downloadLink.setAttribute('href', newValue);
                }
            }
        });

        observer.observe(iFrame, {attributes: true});
    });

});