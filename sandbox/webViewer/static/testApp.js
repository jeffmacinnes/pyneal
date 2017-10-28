var socket = io.connect('http://' + document.domain + ':' + location.port);
socket.on('connect', function() {
    // we emit a connected message to let know the client that we are connected.
    socket.emit('client_connected', {data: 'New client!'});
    console.log("this works")
});

socket.on('message', function(msg) {
    console.log(msg);
    update_header(data.newText);
})

socket.on('headerText', function(msg) {
    update_header(msg.value);
})

socket.on('header2Text', function(msg) {
    update_header2(msg.value);
})


function update_header(newHeader){
    $('#topTitle').text(newHeader);
}


function update_header2(newHeader){
    $('#bottomTitle').text(newHeader);
}
