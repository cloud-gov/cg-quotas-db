var Backbone = require('backbone');
var $ = require('jquery');

var QuotaCollection = require('./models/QuotaCollection');
var ListView = require('./views/ListView');
var DetailView = require('./views/DetailView');

var mainView = $('main').append('div').addClass('app');

var Router = Backbone.Router.extend({
  routes: {
    '': 'listQuotas',
    'quota/:guid': 'showQuota'
  },
  initialize: function initialize () {
    console.log('up!');
    this.lastView = {};
    this.quotas = new QuotaCollection();
  },
  listQuotas: function listQuotas () {
    this.listView = new ListView({ collection: this.quotas });
    mainView.html(this.listView.$el);
  },
  showQuota: function showQuota (guid) {
    console.log('what!', guid);

    function renderDetailView (collection) {
      console.log('collection', collection);
      var quota = collection.findWhere({ guid: guid });
      detailView = new DetailView({ model: quota });
      mainView.html(detailView.$el);

      return this
    }

    if (this.quotas.length < 1) {
      this.quotas.fetch().then(function(newObjects) {
        console.log('this.quotas', this.quotas);
        renderDetailView(this.quotas);
      });
    }
    else {
      console.log('y');
      renderDetailView(this.quotas);
    }
  }
});



module.exports = Router;
