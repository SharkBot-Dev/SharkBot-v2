var express = require("express");
var app = express();

const api = require("./api/api")

var server = app.listen(3320, function(){
    console.log("JS-Server is listening to PORT:" + server.address().port);
});

app.use('/api', api);