import {KMS} from './KMS.js'

KMS.receive = function (data) {
    console.log("POTATO");
}

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

    const $workReportsTable = $('#workReportsTable').DataTable({
        sort: true,
        pageLength: 50,
        lengthChange: false,
        destroy: true,
        columns: [
            {data: 'name', title: 'Name'},
            {data: 'type', title: 'Type'},
            {data: 'prospect', title: 'Prospect'},
            {data: 'author', title: 'Author'},
            {
                title: 'Link',
                data: null,
                defaultContent: `
                    <button class="btn btn-ofx-fa btn-ofx-fa-blue" data-popout="workReport">
                        <i class="fa-solid fa-arrow-up-right-from-square"></i>
                    </button>`
            }
        ]
    });

    const $statusReportsTable = $('#statusReportsTable').DataTable({
        sort: true,
        pageLength: 50,
        lengthChange: false,
        destroy: true,
        columns: [
            {data: 'name', title: 'Name'},
            {data: 'author', title: 'Author'},
            {data: 'manager', title: 'Manager'},
            {
                title: 'Link',
                data: null,
                render: function (data, type, row) {
                    return `<button class="btn btn-ofx-fa btn-ofx-fa-blue" data-popout="statusReport">
                                <i class="fa-solid fa-arrow-up-right-from-square"></i>
                            </button>`
                }
            }
        ]
    });

    const $mapsTable = $('#mapsTable').DataTable({
        sort: true,
        pageLength: 50,
        lengthChange: false,
        destroy: true,
        columns: [
            {data: 'name', title: 'Latest Map Name'},
            {data: 'author', title: 'Map Author'},
            {
                title: 'Link',
                data: null,
                render: function (data, type, row) {
                    return `<button class="btn btn-ofx-fa btn-ofx-fa-blue" data-popout="map">
                                <i class="fa-solid fa-arrow-up-right-from-square"></i>
                            </button>`
                }
            }
        ]
    });

    const $previousReportsTable = $('#previousExplorationReports').DataTable({
        sort: true,
        pageLength: 50,
        lengthChange: false,
        destroy: true,
        columns: [
            {data: 'company', title: 'Company'},
            {data: 'reportNo', title: 'Report No.'},
            {data: 'prevPermitNo', title: 'Previous Permit No.'},
            {
                title: 'Original Document',
                data: null,
                render: function (data, type, row) {
                    return `<button class="btn btn-ofx-fa btn-ofx-fa-blue" data-popout="previousReport">
                                <i class="fa-solid fa-arrow-up-right-from-square"></i>
                            </button>`
                }
            }
        ]
    });

    $('#fullReportSelectSortBy').on('change', function (e) {
        function reverseChildren(parent) {
            for (var i = 1; i < parent.childNodes.length; i++) {
                parent.insertBefore(parent.childNodes[i], parent.firstChild);
            }
        }

        reverseChildren($('#reportItems')[0])
    });
    const REPORTS_PER_PAGE = 10

    function renderPage(page) {
        $.each($('.reportItem'), function (key, value) {
            $('#reportItems').attr("page", page)
            if ($(value).attr("reportIndex") <= REPORTS_PER_PAGE * page &&
                $(value).attr("reportIndex") > REPORTS_PER_PAGE * (page - 1)) {
                $(value).css("display", "block")
            }
            else{
                $(value).css("display", "none")
            }
        })
    }


    function initReportPagenation() {
        if ($('.reportItem').length > REPORTS_PER_PAGE) {

            let pageButtons = ""
            for (let i = 1; i < Math.round($('.reportItem').length / REPORTS_PER_PAGE) + 1; i++) {
                pageButtons = pageButtons + "<li class=\"page-item\" index=\"" + i + "\">" +
                    "<div class=\"page-link\" >" + i + "</div></li>\n"
            }
            renderPage(1)
            const pagenation = "<div class = \"justify-content-center d-flex mt-4\">\n" +
                "  <ul class=\"pagination\">\n" +
                "    <li class=\"page-item\" index=\"prev\">\n" +
                "      <div class=\"page-link\"  href=\"#\" aria-label=\"Previous\">\n" +
                "        <span aria-hidden=\"true\">&laquo;</span>\n" +
                "        <span class=\"sr-only\">Previous</span>\n" +
                "      </div>\n" +
                "    </li>\n" +
                pageButtons +
                "    <li class=\"page-item\" index=\"next\">\n" +
                "      <div class=\"page-link\"  href=\"#\" aria-label=\"Next\">\n" +
                "        <span aria-hidden=\"true\">&raquo;</span>\n" +
                "        <span class=\"sr-only\">Next</span>\n" +
                "      </div>\n" +
                "    </li>\n" +
                "  </ul>\n" +
                "</div>"
            $('#reportItems').after(pagenation)
        }
    }

    initReportPagenation()
    $(".page-item").on("click", function (e) {
        let page = Number($('#reportItems').attr("page"))

        if ($(this).attr("index") == "prev") {
            if (page >= 2) {
                page = page - 1
            }
        } else if ($(this).attr("index") == "next") {
            if (page < Math.round($('.reportItem').length / REPORTS_PER_PAGE)) {
                page = page + 1
            }
        } else {
            page = $(this).attr("index")
        }
        renderPage(page)

    })


});