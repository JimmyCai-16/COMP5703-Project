import {KMS, getDataTableAjax, companyFilter, changeCompanyFilter} from './KMS.js'

const hostName = window.location.host;
const hostPath = window.location.pathname
KMS.receive = function (data) {
    console.log("POTATO");
}

function getDataFunction(data) {
    return {
        page: (data.start / data.length) + 1,  // Adjust page number calculation
    };
}

function dataFilterFunction(data) {
    let json = $.parseJSON(data);
    json.recordsFiltered = json.recordsFiltered || 0;  // Handle missing recordsFiltered value
    json.recordsTotal = json.recordsTotal || 0;  // Handle missing recordsTotal value
    return JSON.stringify(json);
}


export const $prospectsTable = $('#prospectsTable').DataTable({
    sort: true,
    destroy: true,
    serverSide: true,
    processing: true,
    pageLength: 10,
    columns: [
        {
            title: 'Prospect',
            data: 'name',
            render: function (data, type, row, meta) {
                let perm = meta.settings.json && meta.settings.json.permission ? meta.settings.json.permission : 0;
                let buttonsHTML = `
                                    ${data}
                                    <a href="./prospect/${row.prospect_id}"><button class="view-projects-btn" data-bs-toggle="tooltip" data-bs-placement="right" title="View Prospect">View</button></a>

                                    `;
                return buttonsHTML
            }

            
        },
        {title: 'Description', data: 'description', bSortable: false},
        {title: 'Location (Lat/Long)', data: 'location', bSortable: false},


    ],
    ajax: getDataTableAjax('model/prospect'),
});




export const $workReportsTable = $('#workReportsTable').DataTable({
    sort: true,
    destroy: true,
    serverSide: true,
    processing: true,
    pageLength: 10,
    rowId: "id",
    columns: [
        {data: 'name', title: 'Name', width: "10%"},
        {
            data: 'type_of_work', title: 'Type', width: "20%",
            render: function (data, type, row) {
                return data.label;
            }
        },
        {
            data: 'prospect_tags', title: 'Prospect', width: "20%",
            render: function (data, type, row) {
                let labelConcat = '';
                for (let i = 0; i < data.length; i++) {
                    labelConcat += data[i].label + ', ';
                }

                // Remove the trailing comma and space
                labelConcat = labelConcat.slice(0, -2);

                // Return the concatenated label values
                return labelConcat;
            }
        },
        {data: 'author', title: 'Author', width: "20%"},
        {
            title: `Actions`,
            data: null,
            render: function (data, type, row, meta) {
                let perm = meta.settings.json && meta.settings.json.permission ? meta.settings.json.permission : 0;
                let src = `get/report/work_report/${row.id}`;
                let buttonsHTML = `<button class="btn btn-ofx-fa btn-ofx-fa-blue" onclick="previewReportPDF('${src}')" data-bs-toggle="modal" data-bs-target="#pdfModal">
                                        <i class="fa-regular fa-file-pdf"></i>
                                   </button>`;
                if (perm >= 8) {
                    buttonsHTML += `<button class="btn btn-ofx-fa btn-ofx-fa-blue" data-id=${row.id} data-form=work_report data-action="modify">
                                      <i class="fa-regular fa-pen-to-square"></i>
                                    </button>`
                }
                if (perm >= 15) {
                    buttonsHTML += `<button data-form=work_report class="btn btn-ofx-fa btn-ofx-fa-red delete-report" data-action="delete">
                                        <i class="fa-regular fa-trash-can"></i>
                                    </button>`
                }
                return buttonsHTML
            }
        }
    ],
    ajax: getDataTableAjax('model/work_report')
});

export const $statusReportsTable = $('#statusReportsTable').DataTable({
    sort: true,
    destroy: true,
    serverSide: true,
    processing: true,
    pageLength: 10,
    rowId: "id",
    columns: [
        {data: 'name', title: 'Name'},
        {data: 'author', title: 'Author'},
        {data: 'manager', title: 'Manager'},
        {
            data: 'prospect_tags', title: 'Prospect',
            render: function (data, type, row) {
                let labelConcat = '';
                for (let i = 0; i < data.length; i++) {
                    labelConcat += data[i].label + ', ';
                }

                // Remove the trailing comma and space
                labelConcat = labelConcat.slice(0, -2);

                // Return the concatenated label values
                return labelConcat;
            }
        },
        {
            title: `Actions`,
            data: null,
            render: function (data, type, row, meta) {
                let perm = meta.settings.json && meta.settings.json.permission ? meta.settings.json.permission : 0;
                let src = `get/report/status_report/${row.id}`;
                let buttonsHTML = `<button class="btn btn-ofx-fa btn-ofx-fa-blue" onclick="previewReportPDF('${src}')" data-bs-toggle="modal" data-bs-target="#pdfModal">
                                        <i class="fa-regular fa-file-pdf"></i>
                                   </button>`;
                if (perm >= 8) {
                    buttonsHTML += `<button class="btn btn-ofx-fa btn-ofx-fa-blue" data-id=${row.id} data-form=status_report data-action="modify">
                                      <i class="fa-regular fa-pen-to-square"></i>
                                    </button>`
                }
                if (perm >= 15) {
                    buttonsHTML += `<button data-form=status_report class="btn btn-ofx-fa btn-ofx-fa-red" data-action="delete">
                                        <i class="fa-regular fa-trash-can"></i>
                                    </button>`
                }
                return buttonsHTML
            }
        }
    ],
    ajax: getDataTableAjax('model/status_report')
});

export const $mapsTable = $('#mapsTable').DataTable({
    sort: true,
    destroy: true,
    serverSide: true,
    processing: true,
    pageLength: 10,
    columns: [
        {data: 'name', title: 'Latest Map Name'},
        {data: 'author', title: 'Author'},
        {
            title: ``,
            data: null,
            render: function (data, type, row, meta) {
                let perm = meta.settings.json && meta.settings.json.permission ? meta.settings.json.permission : 0;
                let buttonsHTML = `<button class="btn btn-ofx-fa btn-ofx-fa-blue" data-action="open">
                                        <i class="fa-regular fa-folder"></i>
                                    </button>`;
                if (perm >= 8) {
                    buttonsHTML += `<button class="btn btn-ofx-fa btn-ofx-fa-gray" data-action="modify">
                                        <i class="fa-regular fa-pen-to-square"></i>
                                    </button>`
                }
                if (perm >= 15) {
                    buttonsHTML += `<button class="btn btn-ofx-fa btn-ofx-fa-red" data-action="delete">
                                        <i class="fa-regular fa-trash-can"></i>
                                    </button>`
                }
                return buttonsHTML
            }
        }
    ],
    ajax: getDataTableAjax('model/maps'),
});

export const $previousReportsTable = $('#previousReportsTable').DataTable({
    sort: true,
    destroy: true,
    serverSide: true,
    processing: true,
    pageLength: 10,
    rowId: "id",
    columns: [
        {data: 'company', title: 'Company'},
        {data: 'report_id', title: 'Report No.'},
        {data: 'date_published', title: 'Date'},
        {
            title: 'Original Document',
            data: null,

            render: function (data, type, row, meta) {
                let perm = meta.settings.json && meta.settings.json.permission ? meta.settings.json.permission : 0;
                let src = `get/report/historical_report/${row.id}`;
                let buttonsHTML = `<button class="btn btn-ofx-fa btn-ofx-fa-blue" onclick="previewReportPDF('${src}')" data-bs-toggle="modal" data-bs-target="#pdfModal">
                                        <i class="fa-regular fa-file-pdf"></i>
                                   </button>`;
                if (perm >= 8) {
                    buttonsHTML += `<button class="btn btn-ofx-fa btn-ofx-fa-blue" data-id=${row.id} data-form=historical_report data-action="modify">
                                      <i class="fa-regular fa-pen-to-square"></i>
                                    </button>`
                }
                if (perm >= 15) {
                    buttonsHTML += `<button data-form=historical_report class="btn btn-ofx-fa btn-ofx-fa-red" data-action="delete">
                                        <i class="fa-regular fa-trash-can"></i>
                                    </button>`
                }
                return buttonsHTML
            }
        }
    ],
    ajax: getDataTableAjax('model/historical_report'),
});
$('#previousReportsTableContainer').hide();
$(".company-folder").click(function () {
    if ($(this).hasClass("company-folder-selected"))
    {
        $('#previousReportsTableContainer').hide();
        $(this).removeClass("company-folder-selected")
    }
    else{
        $('#previousReportsTableContainer').show();
        $(".company-folder").removeClass("company-folder-selected")
        $(this).addClass("company-folder-selected")
        changeCompanyFilter($(this).attr("company"))
        $previousReportsTable.ajax.reload();
    }

});


$(document).ready(function () {

    const $popout = $('#popoutContainer');

    $('table').on('click', 'button[data-popout]', function () {

        let table = $(this).closest('table').DataTable();
        let row = $(this).closest('tr');
        let rowData = table.row(row).data();
        let requestType = $(this).data('popout');

        $popout.addClass('shown');

    });

    $popout.on('click', '#popoutCloseBtn', function () {
        $popout.removeClass('shown');
    });

});