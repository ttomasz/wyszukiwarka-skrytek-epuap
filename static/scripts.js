function pr(str) {
    if (!str || 0 === str.length){
        return ""
    } else {
        return str
    }
};

function getAddresses (param) {
    var xmlhttp, myObj, x, txt = "";
    xmlhttp = new XMLHttpRequest();
    xmlhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            myObj = JSON.parse(this.responseText);
            for (x in myObj) {
                txt += "<tr>";
                txt += "<td>" + pr(myObj[x].nazwa) + "</td>";
                txt += "<td>" + pr(myObj[x].regon) + "</td>";
                txt += "<td>" + myObj[x].adres + "</td>";
                txt += "<td>" + myObj[x].skrytka + "</td>";
                txt += "</tr>";
            }
            document.getElementById("t").innerHTML = txt;
        }
    }
    xmlhttp.open("GET", "search/"+param, true)
    xmlhttp.send()
};
