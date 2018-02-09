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
    console.log(msg.nTimepts)
});

// handle incoming messages about current volNum
socket.on('volNum', function(msg) {
    currentVol = msg
    console.log(currentVol)
    updateProgressBar(currentVol)
});


// handle incoming messages about current motion params
socket.on('motion', function(msg) {
    console.log(msg)
});



// Progress Area functions
var progressBar = d3.select('#progressDiv')
                    .append('svg')
                    .attrs({'width':'90%', 'height': 200})

progressBar.append('rect')
    .attrs({x: 10, y:10, width:'100%', height:20, fill:'white'});
progressBar.append('rect')
    .attrs({id: 'progressBarRect', x: 10, y:10, width:'0%', height:20, fill:'#A44754'});

function updateProgressBar(volIdx) {
    d3.select('#progressBarRect')
        .transition()
        .attr('width', volIdx+1/numTimepts*100 + '%')
}
