document.addEventListener('DOMContentLoaded', () => {
    console.log("ready");
    setInterval(() => {
        fetch('/status')
        .then(res => res.json())
        .then(json => {
            for (var key in json) {
                document.getElementById(`status${key}`).style.backgroundColor = json[key] ? 'red' : 'lime'; 
            }
        });
    }, 1500);
})