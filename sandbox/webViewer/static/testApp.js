var socket = io.connect('http://' + document.domain + ':' + location.port);
socket.on('connect', function() {
    // we emit a connected message to let know the client that we are connected.
    socket.emit('client_connected', {data: 'New client!'});
    console.log("this works")
});

socket.on('message', function(data) {
    console.log(data);
    update_header(data.newText);
})


function update_header(newHeader){
    $('#topTitle').text(newHeader);
}
