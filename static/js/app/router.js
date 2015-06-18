var Backbone = require('backbone');
var $ = require('jquery');

var ListView = require('./views/ListView');

var mainView = $('main').append('div').addClass('app');

var Router = Backbone.Router.extend({
  routes: {
    '': 'listQuotas',
    'quota/:guid': 'showQuota'
  },
  initialize: function initialize (opts) {
    this.quotas = opts.collection;
  },
  listQuotas: function listQuotas () {
    listView = app.viewCache['listView'] || new ListView({ collection: this.quotas });
    app.viewCache['listView'] = listView;
    mainView.html(listView.$el);
  }
});



module.exports = Router;
