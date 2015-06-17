var Backbone = require('backbone');

var Router = require('./app/router');

var router = new Router();
window.r = router;
Backbone.history.start()
