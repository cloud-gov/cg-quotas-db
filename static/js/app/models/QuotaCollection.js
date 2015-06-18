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
  getId: function search (id) {
    var model = this.get(id);
    if (model) {
      return $.Deferred().resolveWith(this, model);
    }
    else {
      model = new QuotaModel({ guid: id });
      return model.fetch();
    }
  },
  filterByDates: function filterByDates (sinceDate, untilDate, guid) {
    console.log('filtering by dates');
    console.log('sinceDate', sinceDate);
    console.log('untilDate', untilDate);
    console.log('guid', guid);
    if (sinceDate === undefined && untilDate === undefined && guid === undefined) {
      return this;
    }
    var dates = {
      'since': sinceDate,
      'until': untilDate
    };
    this.trigger('sync');

    return this.fetch({data: dates});
  },
  parse: function parse (response) {
    return response.Quotas;
  }
});

module.exports = QuotaCollection;
