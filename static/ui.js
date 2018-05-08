 $("#myChart").hide();
 $("#loading").hide();
 $(document).ready(function() {

     var ctx = document.getElementById("myChart");
     var myChart = new Chart(ctx, {
	 type: 'bar',
	 data: {},
	 options: {
	     scales: {
		 xAxes: [{
		     stacked: true,
		     scaleLabel: {
			 display: true,
			 labelString: 'Time of day'}
		 }],
		 yAxes: [{
		     stacked: true,
		     ticks: { beginAtZero:true   },
		     scaleLabel: {
			 display: true,
			 labelString: 'Number of departures per hour' }
		 }]
	     }
	 }
     });

     $("#button").click(function (){
	 $("#loading").show();
	 emptyList("fromList");
	 emptyList("toList");
	 displayInfo("");
	 $.post("/data", {
	     asunto: $("#asunto").val(),
	     poi: $("#poi").val(),
	     combo: $("#combobox").val()       
	 }, function(data) {
	     $("#loading").hide();
	     $("#myChart").hide();
	     $("route").hide();
	     
	     if (data.asuntos) {
		 addToList("fromList", data.asuntos);
	     }
	     if (data.pois) {
		 addToList("toList", data.pois);
	     }
	     if (data.noasunto) {
		 displayInfo(data.noasunto);
	     }
	     if (data.nopois) {
		 displayInfo(data.nopois);
	     }
	     if (data.error) {
		 displayInfo(data.error);
	     }
	     if (data.datasets && data.labels) {
		 $("#myChart").show();
		 $("#route").html(data.route);
		 
		 myChart.data.datasets = data.datasets;
		 myChart.data.labels = data.labels;
		 myChart.update();
	     }    
	 });
     });
 });

function displayInfo(text) {
    var puff = document.getElementById("infotxt");
    puff.innerHTML = "<p>" + text + "</p>";
}

function changeAddress(id, text) {
    var puff;

    if (id == "fromList") {
	puff = document.getElementById("asunto");
    } else {
	puff = document.getElementById("poi");

    }
    puff.value = text;
}
    


function addToList(id, elements) {
    var l = elements.length;
    var list = document.getElementById(id);
    for (var i=0; i < l; i++) {
	var entry = document.createElement('li');
	entry.appendChild(document.createTextNode(elements[i]));
	const ids = id.toString();
	const ellu = elements[i].toString();
	entry.addEventListener("click", function () {changeAddress(ids, ellu);}, true);
	list.appendChild(entry);
    }
}

function emptyList(id) {
    var del = document.getElementById(id);
    del.innerHTML = "";
}



