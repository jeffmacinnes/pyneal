// Config vars
var numTimepts = 1;     // tmp value for total number of timePts
var currentVol = 0;


// --------- READ INCOMING SOCKET MESSAGES ----
var socket = io('http://127.0.0.1:' + location.port);
socket.on('connect', function() {
    // we emit a connected message to let know the server that we are connected.
    //socket.emit('client_connected', {data: 'New client!'});
    console.log("browser connected")
});


// handle messages about configuration settings
socket.on('configSettings', function(msg){
    // get total timePts
    numTimepts = msg.nTimepts;
    setupMotionPlot(numTimepts);
    console.log(msg.nTimepts)
});


// handle incoming messages about current volNum
socket.on('volNum', function(msg) {
    currentVol = msg
    updateCurrentVol(currentVol)
    updateProgressBar(currentVol)
});


// handle incoming messages about current motion params
socket.on('motion', function(msg) {
    console.log(msg)
});



// Progress Area behavior ---------------------------------------------
var progressBar = d3.select('#progressBarDiv')
                    .append('svg')
                    .attrs({'width':'95%', 'height': '100%'});

progressBar.append('rect')
    .attrs({x: 0, y:30,
            width:'100%', height:30,
            fill:'white',
            stroke: 'rgb(100, 100, 100)',
            'stroke-alignment': 'inner'});

progressBar.append('rect')
    .attrs({id: 'progressBarRect', x: 0, y:30,
            width:'0%', height:30,
            fill:'#A44754'});

function updateCurrentVol(volIdx){
    d3.select('#currentVol').html(String(volIdx+1));
}

function updateProgressBar(volIdx) {
    console.log((volIdx+1)/numTimepts*100 + '%')
    d3.select('#progressBarRect')
        .transition()
        .attr('width', ((volIdx+1)/numTimepts)*100 + '%');
}


// Motion Area behavior ---------------------------------------------
function drawMotionPlot(numTimepts) {
    var motionScale_x, motionAxis_x
    var motionScale_y, motionAxis_y

    var motionPlotDiv = d3.select('#motionPlotDiv');
    motionPlotDiv.html("")      // clear the existing contents

    var margin = {top: 10, right:10, bottom: 30, left:15};

    // get the current dimensions of the div
    var divBBox = motionPlotDiv.node().getBoundingClientRect();
    var divWidth = divBBox.width;
    var divHeight = divBBox.height;
    var plotWidth = divWidth - margin.left - margin.right;
    var plotHeight = divHeight - margin.top - margin.bottom;

    // size the svg for the plot
    var motionPlotSVG = motionPlotDiv.append('svg')
                        .attrs({'width':divWidth, 'height':divHeight})
                        .append('g')
                            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    // Set up the scales and axes
    motionScale_x = d3.scaleLinear()
                    .domain([0,numTimepts])
                    .range([0,plotWidth]);
    motionAxis_x = d3.axisBottom()
                    .scale(motionScale_x)
                    .tickSizeOuter(0);

    motionScale_y = d3.scaleLinear()
                    .domain([-3, 3])
                    .range([plotHeight, 0]);
    motionAxis_y = d3.axisLeft()
                    .scale(motionScale_y)
                    .ticks(5);

    // call the axes to draw it to the div
    motionPlotSVG.append('g')
        .attr("transform", "translate(0," + plotHeight/2 + ")")
        .call(motionAxis_x);
    motionPlotSVG.append('g')
        .call(motionAxis_y);
}


// Timing Area behavior ---------------------------------------------
// var timingPlotDiv = d3.select('#timingPlotDiv');
// var timingPlotSVG = timingPlotDiv.append('svg');
// var timingScale_x, timingAxis_x
// var timingScale_y, timingAxis_y
//
// function drawtimingPlot(numTimepts) {
//     // clear current contents
//     timingPlotSVG.html("")
//
//     // get the current dimensions of the div
//     var divBBox= timingPlotDiv.node().getBoundingClientRect();
//     console.log(divBBox)
//     var divWidth = divBBox.width;
//     var divHeight = divBBox.height;
//     var paddingBottom = 15;
//     var paddingLeft = 30;
//     var plotWidth = (.95*divWidth)-paddingLeft;
//     var plotHeight = (.95*divHeight)-paddingBottom;
//
//     // size the svg for the plot
//     console.log(divWidth);
//     timingPlotSVG.attrs({'width':divWidth, 'height':divHeight});
//
//
//     // Set up the scales and axes
//     timingScale_x = d3.scaleLinear()
//                     .domain([0,numTimepts])
//                     .range([0,plotWidth]);
//     timingAxis_x = d3.axisBottom()
//                     .scale(timingScale_x);
//
//     timingScale_y = d3.scaleLinear()
//                     .domain([1.5, 0])
//                     .range([0, plotHeight-paddingBottom]);
//     timingAxis_y = d3.axisLeft()
//                     .scale(timingScale_y)
//                     .ticks(3);
//
//     // call the axes to draw it to the div
//     timingPlotSVG.append('g')
//         .attr("transform", function(){
//             var plotOffsetX = paddingLeft;
//             var plotOffsetY = plotHeight;
//             return "translate(" + plotOffsetX + "," + plotOffsetY + ")";
//         })
//         .call(timingAxis_x);
//     timingPlotSVG.append('g')
//         .attr("transform", function(){
//             var plotOffsetX = paddingLeft;
//             var plotOffsetY = (divHeight-plotHeight)/2;
//             return "translate(" + plotOffsetX + "," + plotOffsetY + ")";
//         })
//         .call(timingAxis_y);
// }


numTimepts = 60;
drawAll()

function drawAll(){
    console.log('resized')
    drawMotionPlot(numTimepts)
    // drawtimingPlot(numTimepts);
}

// Redraw based on the new size whenever the browser window is resized.
window.addEventListener("resize", function(){
    drawAll();
});
