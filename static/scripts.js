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
    xmlhttp = new XMLHttpRequest();
    xmlhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {

            $("#t").empty().json2html(this.responseText, transform);

            if (this.responseText === "[]\n"){
                $("#annotation").html("<div class=\"alert alert-warning\" role=\"alert\">Nie znaleziono wyników dla tego zapytania.</div>");
            }
        } else if (this.readyState == 4 && this.status != 200) {
            alert("Coś poszło nie tak przy wyszukiwaniu. Spróbuj ponownie lub zmień wyszukiwany tekst.");
        }
    }
    xmlhttp.open("GET", "search/"+param, true)
    xmlhttp.send()
};

$('#formId').submit(function() {
    var str = $("#inlineFormInput").val();
    if (str != "") { getAddresses(str); }
    return false;
});