// print nulls as empty strings
function pr(str) {
    if (!str || 0 === str.length){
        return ""
    } else {
        return str
    }
};

// json2html transformations definitions
var transformMain = {
    "<>":"tr",
    "html":[
        {"<>": "td", "html": "${nazwa}"},
        {"<>": "td", "html": "${regon}"},
        {"<>": "td", "html": "${adres}"},
        {"<>": "td", "html": "${skrytka}"},
        {"<>": "td", "html": "<button type=\"button\" class=\"btn btn-outline-secondary\" data-toggle=\"modal\" data-target=\"#allAddressesModal\" data-addressid=\"${id}\" data-tooltip=\"tooltip\" data-placement=\"right\" title=\"Pokaż wszystkie\">&middot;&middot;&middot;</button>"}
    ]
};

var transformURIs = {
    "<>": "div",
    "id": "modalBody",
    "html": "${skrytki}\n"
};

// helper function to call search api and update site with results
function getAddresses (query, czy_urzad = false, limit = 100) {
    $("#annotation").html("");

    var cu = $('input[name=options1]:checked', '#searchOptions').val();
    if (cu == 1) {
        czy_urzad = true;
    } else if (cu == 0) {
        czy_urzad = false;
    }

    limit = $('input[name=options2]:checked', '#searchOptions').val();

    $.get({ url: "search", data: {query: query, czy_urzad: czy_urzad, limit: limit} })
        .done(function(response){

            $("#t").empty().json2html(response, transformMain);

            if (response.length == 0){
                $("#annotation").html("<div class=\"alert alert-warning\" role=\"alert\">Nie znaleziono wyników dla tego zapytania.</div>");
            }
        })
        .fail(function(){
            alert("Coś poszło nie tak przy wyszukiwaniu. Spróbuj ponownie lub zmień wyszukiwany tekst.");
        });
};

// listeners
$('#formId').submit(function() {
    var str = $("#inlineFormInput").val();
    if (str != "") { getAddresses(str); }
    return false;
});

var timeoutId = 0;
var timeoutValueInMs = 200;
$('#formId').keypress(function () {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(function () {
        var str = $("#inlineFormInput").val();
        if (str != "") { getAddresses(str); }
    }, timeoutValueInMs);
});

$("#allAddressesModal").on("show.bs.modal", function (event) {
    var button = $(event.relatedTarget) // Button that triggered the modal
    var addressid = button.data("addressid") // Extract info from data-* attributes

    $.get({ url: "get_uris/" + encodeURIComponent(addressid) })
    .done(function(response){
        $("#modalBody").empty().json2html(response, transformURIs);
    })
    .fail(function(){
        alert("Nie udało się załadować pełnej listy skrytek dla podanego podmiotu. Spróbuj ponownie lub skontaktuj się z administratorem.");
    });
});

// activate bootstrap tooltips on elements that have them
$('body').tooltip({
    selector: '[data-tooltip=tooltip]'
});