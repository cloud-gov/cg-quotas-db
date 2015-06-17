var Backbone = require('backbone');
var $ = require('jquery');
var _ = require('underscore');

var Quota = require('./QuotaModel');

var QuotaCollection = Backbone.Collection.extend({
  url: '/api/quotas',
  model: Quota,
  initialize: function initialize () {
    return this.fetch();
  },
  parse: function parse (response) {
    return response.Quotas;
  }
});

module.exports = QuotaCollection;
