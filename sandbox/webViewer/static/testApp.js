
// --------- READ INCOMING SOCKET MESSAGES ----
var socket = io.connect('http://' + document.domain + ':' + location.port);
socket.on('connect', function() {
    // we emit a connected message to let know the client that we are connected.
    socket.emit('client_connected', {data: 'New client!'});
    console.log("client connected")
});

var slices = Array.apply(null, new Array(9000)).map(Number.prototype.valueOf, 0);
var circles

socket.on('sliceReceived', function(msg) {
    console.log(msg.sliceNum)
    thisSliceNum = msg.sliceNum
    slices[thisSliceNum] = 1;

    updateCircles()
})


// ---------- PAGE FUNCTIONS -----------

circleRadius = 2
circleGrid_w = 500
circleGrid_h = 18
cellSize = 5;

var svg = d3.select('#sliceArea').append('svg')
    .attr('width', 1200)
    .attr('height', 500);

circles = svg.selectAll('circle')
    .data(slices)
    .enter()
    .append('circle')
        .attr('cx', function(d,i){
            x = (parseInt(i/circleGrid_h)+1) * cellSize;
            return x
        })
        .attr('cy', function(d,i){
            y = ((i % circleGrid_h) * cellSize) + cellSize;
            return y
        })
        .attr('r', circleRadius)
        .style('fill', function(d){
            var c;
            if (d == 0){
                c = 'gainsboro'
            } else {
                c = 'darkred'
            }
            return c
        });


function updateCircles(){
    circles.data(slices)
        .style('fill', function(d){
        var c;
        if (d == 0){
            c = 'gainsboro'
        } else {
            c = 'darkred'
        }
        return c
    });
}
