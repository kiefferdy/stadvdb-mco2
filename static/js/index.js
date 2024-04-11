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

function editAppointment(apptid) {
    fetch(`/appointments/get/${apptid}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.log('Error:', data.error);
            } else {
                const form = document.getElementById('editAppointmentForm');
                form.action = `/appointments/update/${data.apptid}`;

                // Pre-fill fields with existing data
                form.elements['doctor'].value = data.doctorid || '';
                form.elements['patient'].value = data.pxid || '';
                form.elements['clinic'].value = data.clinicid || '';
                form.elements['start_time'].value = data.StartTime ? data.StartTime.slice(0, 16) : '';
                form.elements['end_time'].value = data.EndTime ? data.EndTime.slice(0, 16) : '';
                form.elements['type'].value = data.type || '';
                form.elements['status'].value = data.status || '';
                form.elements['virtual'].checked = data.Virtual === 'True' || data.Virtual === true;

                // Show the modal
                $('#editAppointmentModal').modal('show');
            }
        })
        .catch(error => {
            console.log('Error:', error);
        });
}