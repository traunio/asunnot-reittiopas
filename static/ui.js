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
	 $.post("/data", {
	     asunto: $("#asunto").val(),
	     poi: $("#poi").val(),
	     combo: $("#combobox").val()       
	 }, function(data) {
	     $("#loading").hide();
	     if (data.error) {
		 $("#myChart").hide();
		 alert(data.error);
	     } 
	     else {		       		   
		 $("#myChart").show();

		 $("#route").html(data.route);
		 
		 myChart.data.datasets = data.datasets;
		 myChart.data.labels = data.labels;
		 myChart.update();
	     }    
	 });
     });
 });

