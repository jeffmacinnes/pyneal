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
                    .attrs({'width':'95%', 'height': '100%'})

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
        .attr('width', ((volIdx+1)/numTimepts)*100 + '%')
}
