// import getCookie from 'js/cookies.js';
var NUMBER_OF_DOTS_IN_COPY_SECTION = 5;
var NUMBER_OF_DOTS_IN_COPY_SECTION_COOKIE =
  "NUMBER_OF_DOTS_IN_COPY_SECTION_COOKIE";
var TAG_COOKIE_STR = "tags_disabled";
var TAG_SEARCHED_STR = "tags_searched";

var dataSet = [];
var hiddenDataSet = [];

function getDataset(tag, onLoadCallback) {
  if (dataSet.length == 0 && hiddenDataSet.length == 0) {
    console.log("Making request");
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "http://api.hashtagbombbuilder.com/v1/tag/" + tag, true);
    xhr.send();

    xhr.addEventListener(
      "readystatechange",
      function(e) {
        try {
          if (xhr.status != 200) {
            showError(
              "There was a problem loading the data. Please reload the page and try again."
            );
            return;
          }
          if (xhr.readyState == 4) {
            var tagResponse = JSON.parse(xhr.responseText);
            var backgrounds = randomColor({
              count: Object.keys(tagResponse).length,
              luminosity: "light"
            });
            var index = 0;
            for (var key in tagResponse) {
              // check if the property/key is defined in the object itself, not in parent
              if (tagResponse.hasOwnProperty(key)) {
                dataSet.push({
                  label: key,
                  backgroundColor: backgrounds[index],
                  data: [parseInt(tagResponse[key], 10)]
                });
                console.log(key, tagResponse[key]);
                index++;
              }
            }
            showChartContainer();
            hideLoadingBar();
            hideInfoContainer();

            console.log(dataSet);
            onLoadCallback(dataSet);
          }
        } catch (err) {
          console.log("Error loading data" + err);
          showError("There was a problem loading data. Please try again.");
        }
      },
      false
    );
  } else {
    console.log(dataSet);
    onLoadCallback(dataSet);
  }
}

function getDatasetPie(tags, pieChartCallback) {
  getDataset(tags, function(tempDataset) {
    var returnData = {
      labels: [],
      datasets: [
        {
          backgroundColor: [],
          data: []
        }
      ]
    };

    tempDataset.forEach(function(tempData) {
      returnData["labels"].push(tempData["label"]);
      returnData["datasets"][0]["backgroundColor"].push(
        tempData["backgroundColor"]
      );
      returnData["datasets"][0]["data"].push(tempData["data"]);
    });
    pieChartCallback(returnData);
  });
}

function getDatasetTags(tags, onLoadCallback) {
  getDataset(tags, function(tempDataset) {
    var returnData = {};
    var previouslyHiddenTags = getCookie(TAG_COOKIE_STR);

    tempDataset.forEach(function(tempData) {
      // TODO(tom):find a way to save this in a cookie
      // Mark the tag as hidden if its in the hidden tag cookie
      returnData[tempData["label"]] = false; //previouslyHiddenTags.includes(tempData["label"]);
    });
    onLoadCallback(returnData);
  });
}

function shuffle(arra1) {
  var ctr = arra1.length,
    temp,
    index;

  // While there are elements in the array
  while (ctr > 0) {
    // Pick a random index
    index = Math.floor(Math.random() * ctr);
    // Decrease ctr by 1
    ctr--;
    // And swap the last element with it
    temp = arra1[ctr];
    arra1[ctr] = arra1[index];
    arra1[index] = temp;
  }
  return arra1;
}

var allTags = {};

function generateDots() {
  var dotStr = ".<br/>";
  var dotCookieCountStr = getCookie(NUMBER_OF_DOTS_IN_COPY_SECTION_COOKIE);

  if (dotCookieCountStr !== undefined && dotCookieCountStr != "") {
    dotCookieCountStr = parseInt(dotCookieCountStr, 10);
  }

  return dotStr.repeat(dotCookieCountStr);
}

function getTagSting() {
  var tagText = '<div style="line-height: 1;">' + generateDots() + "</div>";
  var tempTag = "";
  var tagArray = [];

  // Loop through all hashtags
  for (var key in allTags) {
    tempTag = key;
    if (allTags[key]) {
      continue;
    }
    if (!tempTag.includes("#")) {
      tempTag = "#" + tempTag;
    }

    tagArray.push(tempTag);
  }
  // Randomize order
  if (tagArray.length > 0) {
    tagArray = shuffle(tagArray);
  }
  for (var i = 0; i < tagArray.length; i++) {
    tagText = tagText.concat(" " + tagArray[i]);
  }
  return tagText;
}

function updateTagBlock() {
  tagText = getTagSting();
  document.getElementById("tags").innerHTML = tagText;

  // When tag block changes reset copy button
  resetCopyButton();
}

var allSiteCharts = [];
var BarCharCtx = document.getElementById("barChart").getContext("2d");
var PiChartCtx = document.getElementById("myChart").getContext("2d");
// Override the click handler
var defaultLegendClickHandler = Chart.defaults.global.legend.onClick;
var weightChartOptions = {
  plugins: {
    datalabels: {
      formatter: function(value, context) {
        return context.chart.data.labels[context.dataIndex];
      },
      allowOverlap: false,
      align: "end",
      offset: 20,
      anchor: "center",
      rotation: 90
    }
  },
  responsive: true,
  legendCallback: function(chart) {
    console.log(chart.data);
    console.log("cocozzello");
    var legendHtml = [];
    legendHtml.push('<ul id="horizontal-list">');
    for (var i = 0; i < chart.data.datasets[0].data.length; i++) {
      var tempBkndClr = myBar.data.datasets[0].backgroundColor[i];
      legendHtml.push('<li id="' + i + '" class="legend-item">');
      legendHtml.push(
        '    <div class="legend-div" onclick="newLegendClickHandler(event, ' +
          "'" +
          i +
          "'" +
          ')">'
      );
      legendHtml.push(
        '        <span class="legend_span chart-legend-color" style="background-color:' +
          tempBkndClr +
          '"></span>'
      );
      if (chart.data.labels[i]) {
        legendHtml.push(
          "        " +
            chart.data.labels[i] +
            ": " +
            chart.data.datasets[0].data[i] +
            "</div></li>"
        );
      } else {
        legendHtml.push("    </div>");
        legendHtml.push("</li>");
      }
    }
    legendHtml.push("</ul>");
    return legendHtml.join("");
  },
  legend: {
    display: false
  },
  scales: {
    xAxes: [
      {
        display: false //this will remove all the x-axis grid lines
      }
    ],
    yAxes: [
      {
        ticks: {
          beginAtZero: true
        }
      }
    ]
  }
  // scales: {
  //     yAxes: [{
  //         ticks: {
  //             beginAtZero: true
  //         }
  //     }]
  // }
};

// Show/hide chart by click legend
updateDataset = function(e, datasetIndex) {
  var index = datasetIndex;
  var ci = e.view.weightChart;
  var meta = ci.getDatasetMeta(index);

  // See controller.isDatasetVisible comment
  meta.hidden = meta.hidden === null ? !ci.data.datasets[index].hidden : null;

  // We hid a dataset ... rerender the chart
  ci.update();
};

myBar = new Chart(BarCharCtx, {
  type: "bar",
  data: null,
  labels: null,
  options: weightChartOptions
});
allSiteCharts.push(myBar);
var pieChart = new Chart(PiChartCtx, {
  type: "pie",
  options: {
    plugins: {
      labels: {
        // render 'label', 'value', 'percentage', 'image' or custom function, default is 'percentage'
        render: "label",
        overlap: false
      },
      datalabels: {
        formatter: function(value, context) {
          return "";
        }
      }
      // TODO(tom): Un comment when datalabels supports overlap detection. Its a PR right now
      // datalabels: {
      //     formatter: function(value, context) {
      //         return context.chart.data.labels[context.dataIndex];
      //     },
      //     allowOverlap: false,
      //     align: "end",
      //     offset: 20,
      //     anchor: "center",
      // },
    },
    legend: {
      display: false
    }
  },
  data: {
    labels: null,
    datasets: null
  }
});
allSiteCharts.push(pieChart);

function loadBarChart(tags) {
  getDatasetPie(tags, function(barData) {
    var barChartData = {
      labels: barData["labels"],
      datasets: barData["datasets"]
    };
    console.log("bitches");
    console.log(myBar);

    myBar.data = barChartData;
    myBar.update();
  });
}
function loadTagCopy(tags) {
  getDatasetTags(tags, function(tempTags) {
    allTags = tempTags;
    updateTagBlock();
  });
}

function loadCharts(tags) {
  loadBarChart(tags);

  getDatasetPie(tags, function(pieCharData) {
    var pieChartData = {
      labels: pieCharData["labels"],
      datasets: pieCharData["datasets"]
    };
    console.log("more bitches");
    console.log(pieChart);
    pieChart.data = pieChartData;

    // Allow For chart to be modified
    pieChart.update();
  });
  loadTagCopy(tags);

  generateLegend();
}

function generateLegend() {
  console.log("Generating Legend");
  var legend = document.getElementById("legendContainer");
  legend.innerHTML = myBar.generateLegend();
}

function getCharts() {
  return allSiteCharts;
}

function resetCopyButton() {
  var copyButton = document.getElementById("copyCodeBlock");
  copyButton.innerHTML = "copy";
}

function showLoadingBar() {
  $(".bar").css("visibility", "visible");
  setInfoText("Gathering your tags");
  hideHelpContainer();
}
function setInfoText(text) {
  document.getElementById("infoTextLine1").innerHTML = text;
  $("#infoTextLine2").css("display", "none");
}
function hideInfoContainer() {
  $("#infoContainer").css("display", "none");
}
function showInfoContainer() {
  $("#infoContainer").css("display", "inline");
}
function hideHelpContainer() {
  $("#helpContainer").css("display", "none");
}
function hideLoadingBar() {
  $(".bar").css("visibility", "hidden");
}
function showChartContainer() {
  $("#chartContainer").css("visibility", "visible");
  $("#legendContainer").css("visibility", "visible");
}
function hideChartContainer() {
  $("#chartContainer").css("visibility", "hidden");
  $("#legendContainer").css("visibility", "hidden");
}

function showError(errorStr) {
  hideLoadingBar();
  hideHelpContainer();
  hideChartContainer();
  showInfoContainer();
  setInfoText(errorStr);
}

function newLegendClickHandler(e, legendItemIndex) {
  console.log("INDEX: " + legendItemIndex);
  var parent = e.target;
  // If user click on an inside element of the div use the parent to put the strike through
  if ($(parent).attr("class") == "legend_span") {
    parent = $(parent).parent();
  }

  var line_through = $(parent).css("text-decoration");
  // Toggle line-through
  if (!line_through.includes("line-through")) {
    $(parent).css("text-decoration", "line-through");
  } else {
    $(parent).css("text-decoration", "none");
  }

  var index = legendItemIndex;

  var tagName = "";
  var tagHidden = false;

  // Loop through all charts and upate them when legend is clicked
  getCharts().forEach(function(siteChart) {
    if (siteChart != null) {
      console.log(pieChart.data.labels);
      var tagName = pieChart.data.labels[legendItemIndex];
      console.log("CLICK LEGEND" + tagName);
      // POP TAG OUT OF dataSet
      if (siteChart.config.type === "bar") {
        var found = false;
        var item;

        // Delete the item from the graph
        for (var i = 0; i < dataSet.length; i++) {
          item = dataSet[i];

          console.log(item);
          if (item.label == tagName) {
            found = true;
            // Pop item and put it in hiddenDataSet
            hiddenDataSet.push(dataSet.splice(i, 1)[0]);
            break;
          }
        }

        // Add the item back to the graph
        if (!found) {
          for (var i = 0; i < hiddenDataSet.length; i++) {
            item = hiddenDataSet[i];
            if (item.label == tagName) {
              // Pop item and put it in dataSet
              dataSet.push(hiddenDataSet.splice(i, 1)[0]);
              break;
            }
          }
        }
        // Update the bar char with the new data. We can't call myBar.Update()
        // since we are hacking the bar chart library to hold 1 dataset but allow
        // us to modify the data in a legend
        loadBarChart("");
      }
      if (siteChart.config.type === "pie") {
        var hideData = !siteChart.legend.legendItems[index].hidden;
        tagHidden = hideData;

        console.log("pie chart");
        siteChart.getDatasetMeta(0).data[index].hidden = hideData;
      }
      console.log(siteChart);
      siteChart.update();
    }
  });
  if (tagName != "") {
    allTags[tagName] = tagHidden;
  }
  loadTagCopy();
}

function searchContainerBadCaracter(tempSearchText) {
  badChars = ["!", "$", "%", "^", "&", "*", "+", "."];
  for (badChar of badChars) {
    if (tempSearchText.indexOf(badChar) > -1) {
      return (
        "Hashtags can't contain these special characters: '" +
        badChars.join("', '") +
        "'"
      );
    }
  }

  if (tempSearchText.match(/^\d/)) {
    return "Hashtags can't start with a number!";
  }
  return "";
}

function setSearchButtonBackgroundRandom() {
  var searchBackgroundColor = randomColor({ count: 1, luminosity: "light" });
  $("#search_submit").css("background-color", "" + "#A513B6");
  $("#search_submit").css("border-color", "" + "#A513B6");
  $("#search_submit").css("color", "" + "white");
}

function copyTags() {
  var holdtext = document.getElementById("tags");
  var copyButton = document.getElementById("copyCodeBlock");

  const selection = window.getSelection();
  const range = document.createRange();
  range.selectNodeContents(holdtext);
  selection.removeAllRanges();
  selection.addRange(range);

  document.execCommand("copy");
  copyButton.innerHTML = "copied";
}

// function onWidthChange(){
//     if ($('#div-id')[0].scrollWidth >  $('#div-id').innerWidth()) {
//         //Text has over-flown
//     }
// }

// Trigger when screen size changes
var width = $(window).width();
$(window).on("resize", function() {
  if ($(this).width() != width) {
    width = $(this).width();
    console.log(width);
    // onWidthChange();
  }
});

//setSearchButtonBackgroundRandom();
$("#copyCodeBlock").click(function() {
  copyTags();
});
$("#tags").click(function() {
  copyTags();
});

$("#leftSide").click(function(){
  window.open(window.location.pathname.split('?')[0],"_self");
})

// TODO(tom): Enable this
// $("#search_values").autocomplete({
//     source: ["Apple", "Boy", "Cat"],
//     minLength: 0,
// }).focus(function () {
//     $(this).autocomplete("search");
// });

$("#search_submit").click(function() {
  var tags = $("#search_values").val();
  if (tags == "") {
    return;
  }
  errorStr = searchContainerBadCaracter(tags);
  if (errorStr.length > 0) {
    showError(errorStr);
    return;
  }

  newTags = "";
  for (var i = 0; i < tags.length; i++) {
    if (tags.charAt(i) == "#") {
      continue;
    }
    if (tags.charAt(i) == " " || tags.charAt(i) == ",") {
      showError("Sorry currently we only support ONE tag at a time");
      return;
    }
    newTags += tags.charAt(i);
  }
  // Update URL incase the user hits the refresh button it brings them back to the page they were on
  window.history.pushState('page2', 'Tag Bomb - ' + tags, '?q=' + tags);
  document.getElementById("search_values").blur();
  showLoadingBar();
  // Reset Dataset when new value is submited
  dataSet = [];
  hiddenDataSet = [];
  getDataset(newTags, function(data) {
    loadCharts(newTags);
    // NOTE(tom): disabling tag generator since it looks like i am hacking the user.
    // startCharacterGenerator();
    flashClickLegendWarning();
  });
});

$("#contactForm").submit(function() {
  return false;
});

function setCookie(name, value) {
  document.cookie = name + "=" + (value || "");
}

function getCookie(name) {
  var nameEQ = name + "=";
  var ca = document.cookie.split(";");
  for (var i = 0; i < ca.length; i++) {
    var c = ca[i];
    while (c.charAt(0) == " ") c = c.substring(1, c.length);
    if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length, c.length);
  }
  return "";
}

function pluralizeString(integerToCheck, stringToPluralize){
  if (integerToCheck == 1){
    return stringToPluralize;
  }
  return (stringToPluralize + "s");
}

// Range Slider
var rangeSlider = function() {
  var value = $(".range-slider__value");
  var sliderJS = document.getElementById('range_slider');
 
  // Get the number of dots
  var numDots = getCookie(NUMBER_OF_DOTS_IN_COPY_SECTION_COOKIE);
  if (numDots === null || numDots === "" || numDots === undefined) {
    console.log(`Number of dots is: ${numDots}. Defaulting to "3"`);
    numDots = "3";
  }

  // Set inital value of dot slider
  value.html(numDots + pluralizeString(numDots, " Dot"));

  // On ever slide of the slider update cookie, tag block and slider output string
  sliderJS.addEventListener('input', function(){
    setCookie(NUMBER_OF_DOTS_IN_COPY_SECTION_COOKIE, this.value.toString());
    updateTagBlock()
    value.html(this.value + pluralizeString(this.value, " Dot"));
  });
};
rangeSlider();

// ----------------------------------------------------------------
// Click Legend Warning
function flashClickLegendWarning(){
  fadeOpposite(8, "#legendNotification")
}

var isFaddedIn=true
function fadeOpposite(count, element){
  if (count <= 0){
    return
  }

  if (isFaddedIn) {
    isFaddedIn=false
    $(element).fadeOut("slow", "swing", function(){
      fadeOpposite(--count, element)
    });
  } else {
    isFaddedIn=true
    $(element).fadeIn("slow", "swing", function(){
      fadeOpposite(--count, element)
    });
  }
  return
}
// ----------------------------------------------------------------

// ----------------------------------------------------------------
// Process Query URL Arg - On the first time the page loads check the query url arg and load data
var getUrlParameter = function getUrlParameter(sParam) {
  var sPageURL = window.location.search.substring(1),
      sURLVariables = sPageURL.split('&'),
      sParameterName,
      i;

  for (i = 0; i < sURLVariables.length; i++) {
      sParameterName = sURLVariables[i].split('=');

      if (sParameterName[0] === sParam) {
          return sParameterName[1] === undefined ? true : decodeURIComponent(sParameterName[1]);
      }
  }
};

function processUrlArgs(){
  var query = getUrlParameter('q');
  console.log("URL ARG: "+ query);
  if (query !== undefined && query != ""){
    $("#search_values").val(query);
    $("#search_submit").click();
  }
}

processUrlArgs();


// ----------------------------------------------------------------


// // Random character generator
// var randomChars = [
//   "!",
//   "@",
//   "#",
//   "$",
//   "%",
//   "^",
//   "&",
//   "*",
//   "(",
//   ")",
//   "_",
//   "+",
//   "<",
//   ">",
//   "?",
//   "/"
// ];

// function randomCharacterString(lengthInt) {
//   var randomCharStr = "";
//   for (i = 0; i < lengthInt; i++) {
//     var x = Math.floor(Math.random() * randomChars.length);
//     randomCharStr += randomChars[x];
//   }
//   return randomCharStr;
// }

// var wordInterval;
// var finalStr = "Click the Legend to hide tags";
// var index = 1;

// function startCharacterGenerator() {
//   wordInterval = setInterval(myTimer, 100);
// }

// function myTimer() {
//   if (index > finalStr.length) {
//     // Stop character generator
//     clearInterval(wordInterval);
//     return;
//   }
//   var realWord = finalStr.slice(0, index);
//   var randomWord = randomCharacterString(finalStr.length - index);

//   document.getElementById("legendNotification").innerHTML =
//     realWord + randomWord;
//   index++;
// }
// // ----------------------------------------------------------------
