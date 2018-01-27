
var port = '5558'
console.log('test')
console.log(location.port)

// --------- READ INCOMING SOCKET MESSAGES ----
var socket = io('http://127.0.0.1:' + location.port);
socket.on('connect', function() {
    // we emit a connected message to let know the client that we are connected.
    //socket.emit('client_connected', {data: 'New client!'});
    console.log("browser connected")
});

socket.on('volNum', function(msg) {
    console.log(msg)
});


// ---------- PAGE FUNCTIONS -----------

// circleRadius = 8
// circleGrid_w = 50
// circleGrid_h = 10
// cellSize = 20;
//
// var svg = d3.select('#sliceArea').append('svg')
//     .attr('width', 1200)
//     .attr('height', 500);
//
// circles = svg.selectAll('circle')
//     .data(slices)
//     .enter()
//     .append('circle')
//         .attr('cx', function(d,i){
//             x = (parseInt(i/circleGrid_h)+1) * cellSize;
//             return x
//         })
//         .attr('cy', function(d,i){
//             y = ((i % circleGrid_h) * cellSize) + cellSize;
//             return y
//         })
//         .attr('r', circleRadius)
//         .style('fill', function(d){
//             var c;
//             if (d == 0){
//                 c = 'gainsboro'
//             } else {
//                 c = 'darkred'
//             }
//             return c
//         });
//
//
// function updateCircles(){
//     circles.data(slices)
//         .style('fill', function(d){
//         var c;
//         if (d == 0){
//             c = 'gainsboro'
//         } else {
//             c = 'darkred'
//         }
//         return c
//     });
// }
