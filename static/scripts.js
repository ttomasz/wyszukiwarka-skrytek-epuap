function pr(str) {
    if (!str || 0 === str.length){
        return ""
    } else {
        return str
    }
};

var transform = {
    "<>":"tr",
    "html":[
        {"<>": "td", "html": "${nazwa}"},
        {"<>": "td", "html": "${regon}"},
        {"<>": "td", "html": "${adres}"},
        {"<>": "td", "html": "${skrytka}"}
    ]
};

function getAddresses (param) {
    $("#annotation").html("");

    $.get({ url: "search/"+encodeURIComponent(param) })
        .done(function(response){

            $("#t").empty().json2html(response, transform);

            if (response.length == 0){
                $("#annotation").html("<div class=\"alert alert-warning\" role=\"alert\">Nie znaleziono wyników dla tego zapytania.</div>");
            }
        })
        .fail(function(){
            alert("Coś poszło nie tak przy wyszukiwaniu. Spróbuj ponownie lub zmień wyszukiwany tekst.");
        });
};

$('#formId').submit(function() {
    var str = $("#inlineFormInput").val();
    if (str != "") { getAddresses(str); }
    return false;
});