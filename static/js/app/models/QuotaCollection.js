var Backbone = require('backbone');
var $ = require('jquery');
var _ = require('underscore');

var QuotaModel = require('./QuotaModel');

var QuotaCollection = Backbone.Collection.extend({
  url: '/api/quotas',
  model: QuotaModel,
  initialize: function initialize () {
    this.fetch();
  },
  search: function search (id) {
    var model = this.get(id);
    if (model) {
      return $.Deferred().resolveWith(this, model);
    }
    else {
      model = new QuotaModel({ guid: id });
      return model.fetch();
    }
  },
  parse: function parse (response) {
    return response.Quotas;
  }
});

module.exports = QuotaCollection;
