$('button[type="submit"]').removeAttr("data-bs-dismiss")
// PROJECT FORMS

$('#deleteProjectForm').on('submit', function (e) {
    e.preventDefault()
    let $form = $(this);

    $.ajax({
        type: 'POST',
        url: location.origin + location.pathname + `post/delete/`,
        data: $form.serialize(),
        success: function () {
            window.location.href = window.origin + '/project/';
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
        }
    });
});


$('#leaveProjectForm').on('submit', function (e) {
    e.preventDefault()
    let $form = $(this);

    $.ajax({
        type: 'POST',
        url: location.origin + location.pathname + `post/leave/`,
        data: $form.serialize(),
        success: function () {
            window.location.href = window.origin + '/project/';
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
        }
    });
});

// TENEMENT FORMS

$('#addTenementForm').on('submit', function (e) {
    e.preventDefault();
    let $form = $(this);
    let $submitBtn = $form.find('[type="submit"]');
    let submitHtml = $submitBtn.html();
    
    $.ajax({
        type: 'POST',
        url: location.origin + location.pathname + `post/tenement/add/`,
        data: $form.serialize(),
        beforeSend: function (){
            $form.clearFormErrors();
            $submitBtn.addSpinner();
            // const overlay = document.createElement('div');
            // overlay.classList.add('overlay');
            // document.body.appendChild(overlay);
        },
        success: function (data) {
            window.location.href = data['url'];
            location.reload();
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
        },
        complete: function () {
            $submitBtn.removeSpinner(submitHtml);
            // const overlay = document.querySelector('.overlay');
            // document.body.removeChild(overlay); 
        }
    });
});


$('#deleteTenementForm').on('submit', function (e) {
    e.preventDefault();
    let $form = $(this);
    let tenementData = $('#tenement-table').DataTable().row($form.attr('row-index')).data();

    $.ajax({
        type: 'POST',
        url: location.origin + tenementData['permit']['slug'] + `post/relinquish/`,
        data: $form.serialize(),
        success: function () {
            window.location.reload();
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
        }
    });
});


// TASK FORMS

$('#createTaskForm').on('submit', function (e) {
    e.preventDefault();

    let $form = $(this);
    let $table = $('#task-table');
    let $modal = $form.closest('.modal');

    let formData = new FormData(this);

    $.ajax({
        type: 'POST',
        url: location.origin + location.pathname + `post/task/add/`,
        data: formData,
        contentType: false,
        processData: false,

        success: function (response) {
            $table.DataTable().row.add(response.data).draw();
            $modal.modal('hide');
            $form.resetForm();
            location.reload()
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
        }
    });
});

$('#deleteTaskForm').on('submit', function (e) {
    e.preventDefault();
    let $form = $(this);
    let $table = $('#task-table');
    let $modal = $form.closest('.modal');
    let tableRow = $table.DataTable().row($form.attr('row-index'))

    let formData = new FormData($form[0]);
    formData.set('task', tableRow.data()['id']);

    $.ajax({
        type: 'POST',
        url: location.origin + location.pathname + `post/task/delete/`,
        data: formData,
        processData: false,
        contentType: false,
        success: function () {
            tableRow.remove().draw();
            $modal.modal('hide');
            $form.resetForm();
            location.reload()
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
        }
    });
});


// MEMBER FORMS

$('#inviteUserForm').on('submit', function (e) {
    e.preventDefault()
    let $form = $(this);
    let $table = $('#member-table');
    let $modal = $form.closest('.modal');
    let $submitBtn = $form.find('[type="submit"]');
    let submitHtml = $submitBtn.html();


    $.ajax({
        type: 'POST',
        url: location.origin + location.pathname + `post/member/invite/`,
        data: $form.serialize(),
        beforeSend: function (){
            $submitBtn.addSpinner();
            const overlay = document.createElement('div');
            overlay.classList.add('overlay');
            document.body.appendChild(overlay);

        },
        success: function (response) {
            $table.DataTable().row.add(response.data).draw();
            $modal.modal('hide');
            $form.resetForm();
            location.reload();
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
           // location.reload();
        },
        complete: function () {
            $submitBtn.removeSpinner(submitHtml);
            const overlay = document.querySelector('.overlay');
            document.body.removeChild(overlay);

           // location.reload();
        }
    });
});


$('#modifyMemberForm').on('submit', function (e) {
    e.preventDefault();
    let $form = $(this);
    let $table = $('#member-table');
    let $modal = $form.closest('.modal');
    let tableRow = $table.DataTable().row($form.attr('row-index'));

    $.ajax({
        type: 'POST',
        url: location.origin + location.pathname + `post/member/modify/`,
        data: $form.serialize(),
        success: function () {
            $modal.modal('hide');
            $form.resetForm();
            location.reload()
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
        }
    });
});


$('#deleteMemberForm').on('submit', function (e) {
    e.preventDefault()
    let $form = $(this);
    let $table = $('#member-table');
    let $modal = $form.closest('.modal');
    let tableRow = $table.DataTable().row($form.attr('row-index'));

    let formData = new FormData($form[0]);
    formData.set('email', tableRow.data()['email']);

    $.ajax({
        type: 'POST',
        url: location.origin + location.pathname + `post/member/delete/`,
        data: formData,
        processData: false,
        contentType: false,
        success: function () {
            tableRow.remove().draw();
            $modal.modal('hide');
            $form.resetForm();
            location.reload()
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
        }
    });
});

// DATASET/MODEL FORMS

$('#addDatasetForm, #addModelForm').on('submit', function (e) {
    e.preventDefault();

    let $form = $(this);
    let $modal = $form.closest('.modal');
    let $submitBtn = $form.find('[type="submit"]');
    let submitHtml = $submitBtn.html();

    let $table = '';
    let url = location.origin + location.pathname;

    switch ($form.attr('id')) {
        case 'addDatasetForm':
            $table = $('#dataset-table');
            url += 'post/dataset/add/';
            break;
        case 'addModelForm':
            $table = $('#model-table');
            url += 'post/model/add/';
            break;
        default:
            return false;
    }

    let formData = new FormData(this);

    $.ajax({
        type: 'POST',
        url: url,
        data: formData,
        contentType: false,
        processData: false,

        beforeSend: function (){
            $submitBtn.addSpinner();
        },
        success: function (response) {

            response.data.forEach(function(file) {
                $table.DataTable().row.add(file);
            })

            $table.DataTable().draw()

            $modal.modal('hide');
            $form.resetForm();
            location.reload();
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
           // location.reload();
        },
        complete: function () {
            $submitBtn.removeSpinner(submitHtml);
           // location.reload();
        }
    });
});

$('#deleteDatasetForm, #deleteModelForm').on('submit', function (e) {
    e.preventDefault()
    let $form = $(this);
    let $modal = $form.closest('.modal');

    let $table = '';
    let url = location.origin + location.pathname;

    switch ($form.attr('id')) {
        case 'deleteDatasetForm':
            $table = $('#dataset-table');
            url += 'post/dataset/delete/';
            break;
        case 'deleteModelForm':
            $table = $('#model-table');
            url += 'post/model/delete/';
            break;
        default:
            return false;
    }

    let $tableRow = $table.DataTable().row($form.attr('row-index'));

    let formData = new FormData(this);
    formData.set('uuid', $tableRow.data()['uuid']);

    $.ajax({
        type: 'POST',
        url: url,
        data: formData,
        processData: false,
        contentType: false,
        success: function () {
            $tableRow.remove().draw();
            $modal.modal('hide');
            $form.resetForm();
            location.reload()
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
        }
    });
});