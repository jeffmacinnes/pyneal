
console.log(location.port)

// --------- READ INCOMING SOCKET MESSAGES ----
var socket = io('http://127.0.0.1:' + location.port);
socket.on('connect', function() {
    // we emit a connected message to let know the client that we are connected.
    //socket.emit('client_connected', {data: 'New client!'});
    console.log("browser connected")
});


// handle messages about configuration settings
socket.on('configSettings', function(msg){
    console.log(msg)
    console.log(msg.nTimepts)
});

// handle incoming messages about current volNum
socket.on('volNum', function(msg) {
    console.log(msg)
});


// handle incoming messages about current motion params
socket.on('motion', function(msg) {
    console.log(msg)
});
