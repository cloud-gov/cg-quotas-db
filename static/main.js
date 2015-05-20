(function () {

  'use strict';

  angular.module('QuotaApp', [])

  .controller('QuotaController', ['$scope', '$log', '$http', '$filter',
    function($scope, $log, $http, $filter) {

    $scope.getResults = function() {

        // get the URL from the input
        var url = 'api/quotas/' + $scope.quota;
        var start_date = $scope.start_date;
        var end_date = $scope.end_date;

        // Insert date into url
        if( start_date != undefined  & end_date != undefined ){
            start_date = $filter('date')(start_date, "yyyy-MM-dd");
            end_date = $filter('date')(end_date, "yyyy-MM-dd")
            var url = url + '/' + start_date  + '/' + end_date
        }

        // log url
        $log.log(url)

        // send API request
        $http.get(url)
            .success(function(results) {
                //$log.log(results);
                getData(results)
            })
            .error(function(error) {
                $scope.quota_data = {'error': 'no data'}
        });
    };

    // return updated data
    function getData(data){
        $scope.quota_data = data;
    }


  }

  ]);

}());
