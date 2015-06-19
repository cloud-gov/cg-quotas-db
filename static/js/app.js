var Backbone = require('backbone');

var Router = require('./app/router');

var QuotaCollection = require('./app/models/QuotaCollection');

window.app = window.app || {};

var quotas = new QuotaCollection();
var router = new Router({ collection: quotas });

app.viewCache = {};
app.collection = quotas;
app.router = router;

Backbone.history.start();
