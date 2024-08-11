export const KMS = {
    socket: {},
    connectedUsers: [],
    /**
     * Handles incoming websocket messages.
     * @param data JSON Data
     */
    receive(data) { /* Re-define this elsewhere. */
    },
    /**
     * Sends the users mouse position via the websocket.
     * @param event
     */
    sendMousePosition(event) {
    }
}

/**
 * Generates an HTML element specific to a user connected to the current page.
 * @param user
 * @returns {string}
 */
const userToStr = (user) => `<b data-user="${user.email}">${user.name}</b>`

/**
 * Accumulator for generating a string of connected users as an array
 * @returns {string}
 */
const currentUsersToStr = () =>
    Object.entries(KMS.connectedUsers).reduce((acc, [_, user]) => {
        return acc + userToStr(user);
    }, '')

function SetupKMSWebsocket() {
    const url = new URL(window.location.href);
    url.protocol = 'wss:';
    url.pathname = '/ws' + url.pathname;

    KMS.socket = new WebSocket(url);

    KMS.socket.onopen = () => { /* Runs when socket is opened successfully */
    }

    KMS.socket.onclose = (e) => {
        // Should the connection close, every 10 seconds try and reconnect to notification socket
        setTimeout(SetupKMSWebsocket, 10000);
    }

    /**
     * Handles incoming websocket messages. Redirects non-default messages to KMS.receive()
     * @param e
     */
    KMS.socket.onmessage = (e) => {
        const data = JSON.parse(e.data);


        if (data.event === 'current_users') {
            KMS.connectedUsers = data['users'];

            $('#online-users').html(currentUsersToStr());

        } else if (data.event === 'user_connected') {
            KMS.connectedUsers.push(data.user);

            $('#online-users').append(userToStr(data.user))

        } else if (data.event === 'user_disconnected') {
            let removeIndex = KMS.connectedUsers.findIndex((item) => item.email === data.user.email);

            if (removeIndex !== -1) {
                KMS.connectedUsers.splice(removeIndex, 1);

                $('#online-users').find(`[data-user="${data.user.email}"]`).remove();
            }
        } else if (data.event === 'field_content') {
            // TODO: Make sure this can handle all element types
            let element = document.getElementById(data.element);

            element.innerHTML = data.content;

        } else if (data.event === 'model_content') {
            /* TODO:
                - Figure out how to add data to the table without having to reload the ajax (which calling draw() does)
                - Update other elements with the "data.instance" stuff
             */

            $(`table[data-model="${data.model}"]`).DataTable().ajax.reload();

            // $(`table[data-model="${data.model}"]`).DataTable().row.add(data.instance).draw();


        } else {
            // If it wasn't a default message, check in user defined events.
            KMS.receive(data);
        }
    }

    KMS.sendMousePosition = function (event) {
        if (KMS.socket.readyState === WebSocket.OPEN) {
            KMS.socket.send(JSON.stringify({
                    action: 'mouse_position',
                    x: event.clientX,
                    y: event.clientY,
                })
            );
        }
    }
}

function dataURItoBlob(dataURI) {
    var byteString = atob(dataURI.split(',')[1]);
    var mimeString = dataURI.split(',')[0].split(':')[1].split(';')[0];
    var ab = new ArrayBuffer(byteString.length);
    var ia = new Uint8Array(ab);
    for (var i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i);
    }
    return new Blob([ab], {type: mimeString});
}
function file_picker_callback(cb, value, meta) {
    var input = document.createElement('input');
    input.setAttribute('type', 'file');
    input.setAttribute('accept', 'image/*');

    /*
      Note: In modern browsers input[type="file"] is functional without
      even adding it to the DOM, but that might not be the case in some older
      or quirky browsers like IE, so you might want to add it to the DOM
      just in case, and visually hide it. And do not forget do remove it
      once you do not need it anymore.
    */

    input.onchange = function () {
        var file = this.files[0];

        var reader = new FileReader();
        reader.onload = function () {
            /*
              Note: Now we need to register the blob in TinyMCEs image blob
              registry. In the next release this part hopefully won't be
              necessary, as we are looking to handle it internally.
            */
            var id = 'blobid' + (new Date()).getTime();
            var blobCache = tinymce.activeEditor.editorUpload.blobCache;


            var base64 = reader.result.split(',')[1];
            var blobInfo = blobCache.create(id, file, base64);
            blobCache.add(blobInfo);

            /* call the callback and populate the Title field with the file name */
            cb(blobInfo.blobUri(), {title: file.name});
        };
        reader.readAsDataURL(file);
    };

    input.click();
}
async function save_onsavecallback() {
    let form = tinymce.activeEditor.formElement;
    let formData = new FormData(form);
    let content = tinymce.activeEditor.getContent()
    const imgRegex = /<img.*?>/g
    const imgElements = content.match(imgRegex)
    if (imgElements) {
        for (let [index, element] of imgElements.entries()) {
            const srcRegex = /src="(.*?)"/g
            let srcURI, imgType
            try {
                srcURI = element.match(srcRegex)[0].replace('src="', "").replace('"', "")
                console.log(srcURI)
                imgType = srcURI.match(/data:(.*?);/g)[0].replace("data:", "").replace(";", "")
            }catch (error){
                console.log(error)
                continue
            }
            if (imgType == "image/svg+xml"){
                formData.append(`##Image_${index}##`, dataURItoBlob(srcURI))
                content = content.replace(srcURI, `##Image_${index}##`)
                continue
            }

            console.log(imgType)
            const canvas = document.createElement('canvas')
            var img = new Image();
            img.src = srcURI
            img.onload = async () => {
                if (img.width / img.height > 1280 / 720) {
                    if (img.width > 1280) {
                        img.height = 1280 / img.width * img.height
                        img.width = 1280
                    }
                } else {
                    if (img.height > 720) {
                        img.width = 720 / img.height * img.width
                        img.height = 720
                    }
                }
                canvas.width = img.width
                canvas.height = img.height
                canvas.getContext('2d').drawImage(img, 0, 0, img.width, img.height)
                formData.append(`##Image_${index}##`, dataURItoBlob(canvas.toDataURL(imgType, 0.92)))
                console.log(`##Image_${index}##`)
            }
            await img.decode();
            content = content.replace(srcURI, `##Image_${index}##`)
        }
    }

    formData.append('id', form.id)
    formData.append('content', content);
    for (var pair of formData.entries()) {
        console.log(pair[0] + ", " + pair[1]);
    }
    $.ajax({
        type: "POST",
        url: form['action'],
        data: formData,
        processData: false,
        contentType: false,
        success: function (response) {
        },
        error: function (xhr, status, error) {
        }
    });
}

function initTinyMceInput() {
    tinymce.init({
        selector: 'textarea[data-tinymce-i]',
        branding: false,
        menubar: false,
        image_title: true,
        automatic_uploads: true,
        file_picker_types: 'image',
        file_picker_callback: file_picker_callback,
        plugins: 'save lists codesample autolink table image',
        toolbar: 'save | undo redo | formatselect | bold italic underline | forecolor | alignleft aligncenter ' +
            'alignright alignjustify | bullist numlist outdent indent | table | image ',
        setup: function (editor) {
            editor.on('init', function () {
                // Remove the path item from the status bar
                editor.editorContainer.querySelector('.tox-statusbar__path').style.display = 'none';
            });
            // Listen for changes to the content of the editor
            editor.on('NodeChange', function (e) {
                if (e && e.element && e.element.tagName === "IMG") {
                    // If the element before the image is not a break, add one
                    if (e.element.previousSibling && e.element.previousSibling.tagName !== "BR") {
                        let br = document.createElement('br');
                        e.element.parentNode.insertBefore(br, e.element);
                    }
                    
                    // If the element after the image is not a break, add one
                    if (e.element.nextSibling && e.element.nextSibling.tagName !== "BR") {
                        let br = document.createElement('br');
                        e.element.parentNode.insertBefore(br, e.element.nextSibling);
                    }
                }
            });
        },
        save_onsavecallback: save_onsavecallback
    });
}

/**
 * Returns the ajax object required for the KMS datatables.
 * @param path
 * @returns {{dataFilter: (function(*): string), data: (function(*): {pageLength: *, page}), url: string, dataSrc: string}}
 */

export var companyFilter = null
export function changeCompanyFilter(value){companyFilter = value;}
export function getDataTableAjax(path) {
    return {
        url: location.origin + location.pathname + path,
        dataSrc: function(json){
            return json.data
        },
        data: function(data) {

            return {
                companyFilter: companyFilter,
                page: (data.start / data.length) + 1 || 1,  // Adjust page number calculation
                pageLength: data.length || 1,
            };
        },
        dataFilter: function (data) {
            // Process the response data before DataTables
            let json = $.parseJSON(data);
            json.recordsFiltered = json.recordsFiltered || 0;
            json.recordsTotal = json.recordsTotal || 0;

            return JSON.stringify(json);
        }
    }
}

function initTinyMceForm() {
    tinymce.init({
        selector: 'textarea[data-tinymce-f]',
        branding: false,
        menubar: false,
        file_picker_types: 'image',
        file_picker_callback: file_picker_callback,
        plugins: 'lists codesample autolink table image',
        toolbar: 'undo redo | formatselect | bold italic underline | forecolor | alignleft aligncenter ' +
            'alignright alignjustify | bullist numlist outdent indent | table | image',
        setup: function (editor) {
            editor.on('init', function () {
                // Remove the path item from the status bar
                editor.editorContainer.querySelector('.tox-statusbar__path').style.display = 'none';
            });
            editor.on('change', function (e) {
                // This will populate the textarea so the form can actually be submitted as form data
                editor.save();
            });
        }
    });
}
function initTinyMceRead() {
    tinymce.init({
        selector: 'textarea[data-tinymce-r]',

        branding: false,
        menubar: false,
        toolbar: false,
        noneditable_class: 'mceNonEditable',
        setup: function (editor) {
            editor.on('init', function () {
                // Remove the path item from the status bar
                editor.editorContainer.querySelector('.tox-statusbar__path').style.display = 'none';
            });
            editor.on('change', function (e) {
                // This will populate the textarea so the form can actually be submitted as form data
                editor.save();
            });
        },
    });
}

// Comment needs Tinymce premium
// function initTinyMceCommentView() {
//     tinymce.init({
//         selector: 'textarea[data-tinymce-c]',
//         branding: false,
//         menubar: false,
//         plugins: 'lists codesample autolink table tinycomments',
//         toolbar: 'addcomment showcomments',
//         setup: function (editor) {
//             editor.on('init', function () {
//                 // Remove the path item from the status bar
//                 editor.editorContainer.querySelector('.tox-statusbar__path').style.display = 'none';
//             });
//             editor.on('change', function (e) {
//                 // This will populate the textarea so the form can actually be submitted as form data
//                 editor.save();
//             });
//         },
//     });
// }
SetupKMSWebsocket();
initTinyMceInput();
initTinyMceForm();
initTinyMceRead();
// initTinyMceCommentView();

$(document).on('focusin', function(e) {
    if ($(e.target).closest(".mce-window").length) {
      e.stopImmediatePropagation();
    }
  });


$(document).ready(function () {

    // TARGET FORMS

    $('#addEditTargetForm').on('submit', function (e) {
        e.preventDefault();
        let $form = $(this);
        let $table = $('#target-table');
        let tableRow = $table.DataTable().row($form.attr('row-index'));
        let url = $('#id_target_id').val() ? location.origin + location.pathname + `post/target/edit/` + tableRow.data()['name'] : location.origin + location.pathname + `post/target/add/`;
        let $modal = $form.closest('.modal');
        let $submitBtn = $form.find('[type="submit"]');
        let submitHtml = $submitBtn.html();

        $.ajax({
            type: 'POST',
            url: url,
            data: $form.serialize(),
            beforeSend: function () {
                $submitBtn.addSpinner();
                const overlay = document.createElement('div');
                overlay.classList.add('overlay');
                document.body.appendChild(overlay);
            },
            success: function (response) {
                var coordinates = response.data.location.split(" ")
                
                response.data.location = "[ " + coordinates[0] + ", " + coordinates[1] + " ]"
                if ($('#id_target_id').val()) {
                    $table.DataTable().row($form.attr('row-index')).data(response.data).draw();
                }
                else {
                    $table.DataTable().row.add(response.data).draw();
                }

                $modal.modal('hide');
                $form.resetForm();

                $('#project_map_box').load(location.origin + location.pathname + `get/project_map/`);

            },
            error: function (response) {
                console.log("Broke?")
                if (response['responseJSON']) {
                    $form.displayFormErrors(response['responseJSON']);
                }
                else {
                    $form.displayFormErrors({ '__all__': ['Target with this Project and Name already exists.'] });
                }

            },
            complete: function () {
                $submitBtn.removeSpinner(submitHtml);
                const overlay = document.querySelector('.overlay');
                document.body.removeChild(overlay);
                // location.reload();
            }
        });
    });

    $('#addEditTargetModal').on("hidden.bs.modal", function () {
        $('#addEditTargetForm').resetForm();
    });

    $(document).on('click', 'button[data-action="delete"]', function () {
        let $btn = $(this);
        var row = $btn.closest('tr');
        console.log(row[0])

        $.ajaxSetup({
            beforeSend: function (xhr, settings) {
                function getCookie(name) {
                    var cookieValue = null;
                    if (document.cookie && document.cookie != '') {
                        var cookies = document.cookie.split(';');
                        for (var i = 0; i < cookies.length; i++) {
                            var cookie = jQuery.trim(cookies[i]);
                            // Does this cookie string begin with the name we want?
                            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                                break;
                            }
                        }
                    }
                    return cookieValue;
                }

                if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                    // Only send the token to relative URLs i.e. locally.
                    xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                }
            }
        });

        $.ajax({
            type: "DELETE",
            url: `form/${$btn.attr("data-form")}/${row[0].id}`,
            success: function (response) {
                var table = $(`table[data-model="${$btn.attr('data-form')}"]`).DataTable();
                table.row("#" + row[0].id).remove().draw();
            },
            error: function (xhr, status, error) {
            }
        });


        deleteReport(reportData, "work_report")

        $("#deleteWorkReportModal").modal('hide')
        
    });

    $('#deleteStatusReportForm').on('submit', function (e) {
        e.preventDefault()
        let $form = $(this);
        let reportData = $('#statusReportsTable').DataTable().row($form.attr('row-index')).data();

        deleteReport(reportData, "status_report")
        $("#deleteStatusReportModal").modal('hide')

        
    });

    $('#deleteHistoricalReportForm').on('submit', function (e) {
        e.preventDefault()
        let $form = $(this);
        let reportData = $('#previousReportsTable').DataTable().row($form.attr('row-index')).data();

        deleteReport(reportData, "historical_report")

        $("#deleteHistoricalReportModal").modal('hide')

        
    });
    

    $('.accordion-collapse').on('show.bs.collapse', function () {
        console.log("OK")
        $(this).find('table.dataTable').each(function () {
            $(this).DataTable().columns.adjust().draw();
        });
    });

    $(document).on('click', 'button[data-action="modify"]', function () {
        let $btn = $(this);

        let formName = $btn.data('form');
        let instanceId = $btn.data('id');
        let $container = null;

        if (formName == "work_report") {
            $container = $("#workReportModal");
        } else if (formName == "status_report") {
            $container = $("#statusReportModal");
        } else if (formName == "historical_report") {
            $container = $("#historicalReportModal");
        }

        const mceFields = ["id_distribution_status", "id_personnel_at_site", "id_distribution",
            "id_summary", "id_summary_historical", "id_health_safety_status", "id_enviro_status", "id_community_status", "id_operational_summary"]
        const htmlFields = ["id_name", "id_author", "id_manager", "id_report_id", "id_company", "id_tenure_number", "id_date_published"]
        const radioFields = ["was_community_interaction", "was_reportable_enviro_incident", "was_reportable_hns_incident", "is_noted_in_lms"]

        if (instanceId.length !== 0) {
            $.ajax({
                type: "GET",
                url: `form/${formName}/${instanceId}`,
                success: function (response) {

                    $container.modal('show')
                    $container.find("#id_instance_id").val(instanceId)

                    const html = new DOMParser().parseFromString(response.html, "text/html");

                    const jqueryHTML = $('<output>').append($.parseHTML(response.html))

                    $container.find('.selectpicker').selectpicker('val', jqueryHTML.find("#id_prospect_tags").val());

                    mceFields.forEach((field) => {
                        try {
                            tinyMCE.get(field).setContent(html.getElementById(field).value);
                        } catch (ex) {
                        }
                    })

                    htmlFields.forEach((field) => {
                        try {
                            $container.find("#" + field).val(html.getElementById(field).value)
                        } catch (ex) {
                        }
                    })

                    radioFields.forEach((field) => {
                        try {
                            $container.find(`input:radio[id=id_${field}_${jqueryHTML.find(`input[name=${field}]:checked`).val()}]`).prop('checked', true)
                        } catch (ex) {

                        }
                    })

                    try {
                        $container.find("#id_type_of_work").val(html.getElementById("id_type_of_work").value).change()
                    } catch (ex) {
                    }


                },
                error: function (xhr, status, error) {
                    console.log(error);
                }
            });

        }
    }).on('submit', '.modal-dialog form[action][method]', async function (e) {
        e.preventDefault();
        tinymce.triggerSave();

        if (this.getAttribute('id') === "addEditTargetForm") return

        let $form = $(this);
        let formData = new FormData(this);
        let empty = false;
        let firstFieldImageNums = 0
        async function replaceImage(content, indexStart){
            const imgRegex = /<img.*?>/g
            const imgElements = content.match(imgRegex)
            firstFieldImageNums = firstFieldImageNums + imgElements.length
            if (imgElements) {
                for (let [index, element] of imgElements.entries()) {
                    const srcRegex = /src="(.*?)"/g
                    let srcURI, imgType
                    try {
                        srcURI = element.match(srcRegex)[0].replace('src="', "").replace('"', "")
                        imgType = srcURI.match(/data:(.*?);/g)[0].replace("data:", "").replace(";", "")
                    }catch (error){
                        console.log(error)
                        continue
                    }
                    if (imgType == "image/svg+xml"){
                        formData.append(`##Image_${indexStart + index}##`, dataURItoBlob(srcURI))
                        content = content.replace(srcURI, `##Image_${indexStart + index}##`)
                        continue
                    }

                    const canvas = document.createElement('canvas')
                    var img = new Image();
                    img.src = srcURI
                    img.onload = async () => {
                        if (img.width / img.height > 1280 / 720) {
                            if (img.width > 1280) {
                                img.height = 1280 / img.width * img.height
                                img.width = 1280
                            }
                        } else {
                            if (img.height > 720) {
                                img.width = 720 / img.height * img.width
                                img.height = 720
                            }
                        }
                        canvas.width = img.width
                        canvas.height = img.height
                        canvas.getContext('2d').drawImage(img, 0, 0, img.width, img.height)
                        formData.append(`##Image_${indexStart + index}##`, dataURItoBlob(canvas.toDataURL(imgType, 0.92)))

                    }
                    await img.decode();
                    content = content.replace(srcURI, `##Image_${indexStart + index}##`)
                }
            }
            return content
            }


        for (var pair of formData.entries()) {
            try {
                formData.set(pair[0], await replaceImage(pair[1], firstFieldImageNums))
                if (pair[0] == "distribution") {
                    $(tinymce.get("id_" + pair[0] + "_status").getContainer()).css("border", '1px solid #eee');
                }
                if (pair[0] == "summary") {
                    $(tinymce.get("id_" + pair[0] + "_historical").getContainer()).css("border", '1px solid #eee');
                }
                $(tinymce.get("id_" + pair[0]).getContainer()).css("border", '1px solid #eee')
            console.log(pair[1])
            } catch (ex) {
            }

            if (pair[0] == "instance_id" || pair[0] == "form_templates")
                continue

            if (pair[1] == "") {
                if (pair[0] == "distribution") {
                    $(tinymce.get("id_" + pair[0] + "_status").getContainer()).css("border", '1px solid #ff0000');
                }
                if (pair[0] == "summary") {
                    $(tinymce.get("id_" + pair[0] + "_historical").getContainer()).css("border", '1px solid #ff0000');
                }
                $(tinymce.get("id_" + pair[0]).getContainer()).css("border", '1px solid #ff0000');
                empty = true;
            }
        }

        if (empty) {
            alert("All fields must be filled");
            return false;
        }

        let $submitBtn = $form.find('[type="submit"]');
        let originalHTML = $submitBtn.addSpinner();

        $.ajax({
            type: $form.attr('method'),
            url: location.origin + location.pathname + $form.attr('action'),
            data: formData,
            processData: false, // Prevent jQuery from processing the data
            contentType: false, // Set content type to false for FormData
            beforeSend: function () {
                $form.clearFormErrors();

            },
            success: function (response) {
                $form.closest('.modal').modal('hide');
                $form.trigger('reset');
            },
            error: function (xhr, status, error) {
                console.log('ERROR', xhr, status, error);
            },
            complete: function () {
                $submitBtn.removeSpinner(originalHTML);
            }
        });

        return false;
    });
    
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
    


    $('#kmsForms').on('click', 'button[data-import]', function () {
        let $btn = $(this);
        let $select = $btn.siblings('select[name="form_templates"]');
        let $container = $(this).closest('.modal-body');

        let formName = $btn.data('import');
        let selectVal = $select.val();

        const mceFields = ["id_distribution_status", "id_personnel_at_site", "id_distribution",
            "id_summary", "id_summary_historical", "id_health_safety_status", "id_enviro_status", "id_community_status", "id_operational_summary"]
        const htmlFields = ["id_name", "id_author", "id_manager", "id_report_id", "id_company", "id_tenure_number", "id_date_published"]
        const radioFields = ["was_community_interaction", "was_reportable_enviro_incident", "was_reportable_hns_incident", "is_noted_in_lms"]

        if (selectVal.length !== 0) {

            $.ajax({
                type: "GET",
                url: `form/${formName}/${selectVal}`,
                success: function (response) {
                    const html = new DOMParser().parseFromString(response.html, "text/html");

                    const jqueryHTML = $('<output>').append($.parseHTML(response.html))

                    $container.find('.selectpicker').selectpicker('val', jqueryHTML.find("#id_prospect_tags").val());
                    mceFields.forEach((field) => {
                        try {
                            tinyMCE.get(field).setContent(html.getElementById(field).value);
                        } catch (ex) {
                        }
                    })

                    htmlFields.forEach((field) => {
                        try {
                            $container.find("#" + field).val(html.getElementById(field).value)
                        } catch (ex) {
                        }
                    })

                    try {
                        $container.find("#id_type_of_work").val(html.getElementById("id_type_of_work").value).change()
                    } catch (ex) {
                    }

                    radioFields.forEach((field) => {
                        try {
                            $container.find(`input:radio[id=id_${field}_${jqueryHTML.find(`input[name=${field}]:checked`).val()}]`).prop('checked', true)
                        } catch (ex) {

                        }
                    })

                },
                error: function (xhr, status, error) {
                    console.log(error);
                }
            });

        }
    }).on('submit', '.modal-dialog form[action][method]', async function (e) {
        e.preventDefault();
        tinymce.triggerSave();
        // TODO: this is where we'll need to catch the html and maybe do something with the image tags
        // sample image html:
        //<p><img title="Screenshot 2023-07-14 112840.png" src="blob:https://www.tiny.cloud/67e0a8bd-0e71-4471-8b78-08b5a9ddf1a6" alt="thtrhrt" width="137" height="159" /></p>
        // https://www.tiny.cloud/docs/plugins/opensource/image/

        let $form = $(this);
        let formData = new FormData(this);
        let empty = false;

        async function replaceImage(content){
            const imgRegex = /<img.*?>/g
            const imgElements = content.match(imgRegex)
            if (imgElements) {
                for (let [index, element] of imgElements.entries()) {
                    const srcRegex = /src="(.*?)"/g
                    let srcURI, imgType
                    try {
                        srcURI = element.match(srcRegex)[0].replace('src="', "").replace('"', "")
                        imgType = srcURI.match(/data:(.*?);/g)[0].replace("data:", "").replace(";", "")
                    }catch (error){
                        console.log(error)
                        continue
                    }
                    if (imgType == "image/svg+xml"){
                        formData.append(`##Image_${index}##`, dataURItoBlob(srcURI))
                        content = content.replace(srcURI, `##Image_${index}##`)
                        continue
                    }

                    const canvas = document.createElement('canvas')
                    var img = new Image();
                    img.src = srcURI
                    img.onload = async () => {
                        if (img.width / img.height > 1280 / 720) {
                            if (img.width > 1280) {
                                img.height = 1280 / img.width * img.height
                                img.width = 1280
                            }
                        } else {
                            if (img.height > 720) {
                                img.width = 720 / img.height * img.width
                                img.height = 720
                            }
                        }
                        canvas.width = img.width
                        canvas.height = img.height
                        canvas.getContext('2d').drawImage(img, 0, 0, img.width, img.height)
                        formData.append(`##Image_${index}##`, dataURItoBlob(canvas.toDataURL(imgType, 0.92)))

                    }
                    await img.decode();
                    content = content.replace(srcURI, `##Image_${index}##`)
                }
            }

            return content
        }

        for (var pair of formData.entries()) {
            try {
                if (pair[0] == "distribution") {
                    formData.set(pair[0], await replaceImage(pair[1]))
                    $(tinymce.get("id_" + pair[0] + "_status").getContainer()).css("border", '1px solid #eee');
                }
                if (pair[0] == "summary") {
                    formData.set(pair[0], await replaceImage(pair[1]))
                    $(tinymce.get("id_" + pair[0] + "_historical").getContainer()).css("border", '1px solid #eee');
                }
                $(tinymce.get("id_" + pair[0]).getContainer()).css("border", '1px solid #eee')
            console.log(pair[1])
            } catch (ex) {
            }

            if (pair[0] == "instance_id" || pair[0] == "form_templates")
                continue

            if (pair[1] == "") {
                if (pair[0] == "distribution") {
                    $(tinymce.get("id_" + pair[0] + "_status").getContainer()).css("border", '1px solid #ff0000');
                }
                if (pair[0] == "summary") {
                    $(tinymce.get("id_" + pair[0] + "_historical").getContainer()).css("border", '1px solid #ff0000');
                }

                $(tinymce.get("id_" + pair[0]).getContainer()).css("border", '1px solid #ff0000');
                empty = true;
            }
        }

        if (empty) {
            alert("All fields must be filled");
            return false;
        }

        window.location.reload()

        return false;
    });

    $(".form-open").on('click', () => {
        $(".instance_id_val").val(-1)
    })
});