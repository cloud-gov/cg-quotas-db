var Backbone = require('backbone');
var $ = require('jquery');

var ListView = require('./views/ListView');
var DetailView = require('./views/DetailView');

var QuotaModel = require('./models/QuotaModel');

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
  },
  showQuota: function showQuota (guid) {
    var quotas = this.quotas;
    var model = quotas.get(guid);
    if (model) {
      var detailView = new DetailView({model: model});
      mainView.html(detailView.$el);
    }
    else {
      var newModel = new QuotaModel({ guid: guid });
      newModel.fetch({
        success: function () {
          console.log('new model', newModel);
          var detailView = new DetailView({model: newModel});
          mainView.html(detailView.$el);
        }
      })
    }
  }
});



module.exports = Router;
