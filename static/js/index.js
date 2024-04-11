document.addEventListener('DOMContentLoaded', () => {
    console.log("DOMContentLoaded");

    // For node activity statuses
    setInterval(() => {
        fetch('/status')
            .then(res => res.json())
            .then(json => {
                for (var key in json) {
                    document.getElementById(`status${key}`).style.backgroundColor = json[key] ? 'red' : 'lime';
                }
            });
    }, 1500);
});