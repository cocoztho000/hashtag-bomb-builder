var ctx = document.getElementById("myChart").getContext('2d');
var myChart = new Chart(ctx, {
  type: 'pie',
  options:{
    legend:{
      display:false
    }
  },
  data: {
    labels: ["#dunk", "#espn", "#goat", "#jamesharden", "#kg", "#kobe", "#kobebryant", "#lakers", "#lebron", "#mj", "#mvp", "#nbafinals", "#nbatv", "#nike", "#roty", "#sports", "#stephcurry", "#thunder", "#wolves", "#timberwolves", "#cavs", "#kd", "#kyrieirving", "#lebronjames", "#nba", "#minnesota"],
    datasets: [{
      backgroundColor: [
        "#2ecc71",
        "#3498db",
        "#95a5a6",
        "#9b59b6",
        "#f1c40f",
        "#e74c3c",
        "#34495e",
        "#2ecc71",
        "#3498db",
        "#95a5a6",
        "#9b59b6",
        "#f1c40f",
        "#e74c3c",
        "#34495e",
        "#2ecc71",
        "#3498db",
        "#95a5a6",
        "#9b59b6",
        "#f1c40f",
        "#e74c3c",
        "#34495e",
        "#2ecc71",
        "#3498db",
        "#95a5a6",
        "#9b59b6",
        "#f1c40f",
        "#e74c3c",
        "#34495e",
        "#2ecc71",
        "#3498db",
        "#95a5a6",
        "#9b59b6",
        "#f1c40f",
        "#e74c3c",
        "#34495e",
        "#2ecc71",
        "#3498db",
        "#95a5a6",
        "#9b59b6",
        "#f1c40f",
        "#e74c3c",
        "#34495e",
        "#2ecc71",
        "#3498db",
        "#95a5a6",
        "#9b59b6",
        "#f1c40f",
        "#e74c3c",
        "#34495e",
        "#2ecc71",
        "#3498db",
        "#95a5a6",
        "#9b59b6",
        "#f1c40f",
        "#e74c3c",
        "#34495e"
      ],
      data: [7685, 7685, 7685, 7685, 7685, 7685, 7685, 7685, 7685, 7685, 7685, 7685, 7685, 7685, 7685, 7685, 7685, 7685, 7685, 7693, 9034, 9034, 9034, 9034, 9042, 9454]
    }]
  }
});

document.getElementById('js-legend').innerHTML = myChart.generateLegend();