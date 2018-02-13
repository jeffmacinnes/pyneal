// Config vars
var numTimepts = 1;     // tmp value for total number of timePts
var currentVol = 0;
var motion = [];        // empty array to hold motion objects

// --------- READ INCOMING SOCKET MESSAGES ----
var socket = io('http://127.0.0.1:' + location.port);
socket.on('connect', function() {
    // we emit a connected message to let know the server that we are connected.
    socket.emit('client_connected', {data: 'New client!'});
    console.log("sent request for data")
});


// handle when server sends all existing data
socket.on('existingData', function(msg){
    console.log('received all existing data:');
    console.log(msg);

    // set the number of timepts
    numTimepts = msg.numTimepts;

    // set up motion
    motion = msg.motion;

    // update all plots
    drawAll();
})


// handle messages about configuration settings
socket.on('configSettings', function(msg){
    // get total timePts
    console.log(msg)
    numTimepts = msg.numTimepts;
    drawAll();

});


// handle incoming messages about current volIdx
socket.on('volIdx', function(msg) {
    currentVol = msg
    updateCurrentVol(currentVol)
    updateProgressBar(currentVol)
});


// handle incoming messages about current motion params
socket.on('motion', function(msg) {
    // 'msg' will be JSON object with vals for volIdx, and any other motion
    // parameters you want. Add it to the 'motion' array, then update plot
    motion.push(msg);
    //drawMotionPlot();
    updateMotionPlot();
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
var motionScale_x, motionAxis_x;
var motionScale_y, motionAxis_y;
var motionPlotWidth, motionPlotHeight;
var rms_abs_line, rms_rel_line;

function drawMotionPlot() {
    var motionPlotDiv = d3.select('#motionPlotDiv');
    motionPlotDiv.html("")      // clear the existing contents

    var margin = {top: 10, right:10, bottom: 30, left:40};

    // get the current dimensions of the div
    var divBBox = motionPlotDiv.node().getBoundingClientRect();
    var divWidth = divBBox.width;
    var divHeight = divBBox.height;
    motionPlotWidth = divWidth - margin.left - margin.right;
    motionPlotHeight = divHeight - margin.top - margin.bottom;

    // size the svg for the plot
    var motionPlotSVG = motionPlotDiv.append('svg')
                        .attrs({'id': 'motionPlotSVG', 'width':divWidth, 'height':divHeight})
                        .append('g')
                            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    //figure out max motion param to scale plots
    var rms_abs_min = d3.min(motion, function(d){ return d.rms_abs})
    var rms_rel_min = d3.min(motion, function(d){ return d.rms_rel})
    var rms_abs_max = d3.max(motion, function(d){ return d.rms_abs})
    var rms_rel_max = d3.max(motion, function(d){ return d.rms_rel})
    var upper_yLim = 1.2* d3.max([rms_abs_max, rms_rel_max]);
    var lower_yLim = 1.2* d3.min([rms_abs_min, rms_rel_min]);
    var y_range = upper_yLim - lower_yLim

    // Set up the scales and axes
    motionScale_x = d3.scaleLinear()
                    .domain([0,numTimepts])
                    .range([0,motionPlotWidth]);
    motionAxis_x = d3.axisBottom()
                    .scale(motionScale_x)

    motionScale_y = d3.scaleLinear()
                    .domain([lower_yLim, upper_yLim])
                    .range([motionPlotHeight, 0])
    motionAxis_y = d3.axisLeft()
                    .scale(motionScale_y)
                    .ticks(5);

    // define the lines
    rms_abs_line = d3.line()
            .x(function(d){ return motionScale_x(d.volIdx+1)})
            .y(function(d){ return motionScale_y(d.rms_abs)});

    motionPlotSVG.append('path')
        .datum(motion)
        .attr('id', 'rmsABS_line')
        .attr('d', rms_abs_line);

    // call the axes to draw it to the div
    motionPlotSVG.append('g')
        .attr("id", "motionPlot_xAxis")
        .attr("transform", "translate(0," + (upper_yLim/y_range)*motionPlotHeight + ")")
        .call(motionAxis_x);

    motionPlotSVG.append('g')
        .attr("id", "motionPlot_yAxis")
        .call(motionAxis_y);
    motionPlotSVG.append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", 0 - margin.left)
        .attr("x",0 - (motionPlotHeight / 2))
        .attr("dy", "1em")
        .style("text-anchor", "middle")
        .style("font-size", 12)
        .text("displacement (mm)");
}

function updateMotionPlot(){
    // rescale the y-axis if needed
    var rms_abs_min = d3.min(motion, function(d){ return d.rms_abs})
    var rms_rel_min = d3.min(motion, function(d){ return d.rms_rel})
    var rms_abs_max = d3.max(motion, function(d){ return d.rms_abs})
    var rms_rel_max = d3.max(motion, function(d){ return d.rms_rel})
    var upper_yLim = 1.2* d3.max([rms_abs_max, rms_rel_max]);
    var lower_yLim = 1.2* d3.min([rms_abs_min, rms_rel_min]);
    var y_range = upper_yLim - lower_yLim

    motionScale_y.domain([lower_yLim, upper_yLim])

    d3.select("#motionPlot_xAxis")
        .attr("transform", "translate(0," + (upper_yLim/y_range)*motionPlotHeight + ")")
        .call(motionAxis_x);
    d3.select("#motionPlot_yAxis")
            .call(motionAxis_y);

    // update motion plot with new current motion data
    d3.select('#rmsABS_line')
        .datum(motion)
        .attr('d', rms_abs_line);
}

// Timing Area behavior ---------------------------------------------


// draw all elements upon load
drawAll()
function drawAll(){
    console.log('resized')
    drawMotionPlot()
    // drawtimingPlot(numTimepts);
}

// Redraw based on the new size whenever the browser window is resized.
window.addEventListener("resize", function(){
    drawAll();
});
