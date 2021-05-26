var map = L.map('map').setView([22.355048, 114.106522], 11);
L.tileLayer(
    'http://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    attribution: '&copy; <a href="http://www.esri.com/">Esri</a>, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
    minZoom: 10,
    maxZoom: 18,
}).addTo(map);

String.prototype.toProperCase = function () {
    return this.replace(/\w\S*/g, function(txt){return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();});
};

function HK80_to_WGS84([x, y]) {
    proj4.defs('WGS84', "+title=WGS 84 (long/lat) +proj=longlat +ellps=WGS84 +datum=WGS84 +units=degrees");
    proj4.defs('EPSG:2326', '+proj=tmerc +lat_0=22.31213333333334 +lon_0=114.1785555555556 +k=1 +x_0=836694.05 +y_0=819069.8 +ellps=intl +towgs84=-162.619,-276.959,-161.764,0.067753,-2.24365,-1.15883,-1.09425 +units=m +no_defs');
    return proj4('EPSG:2326','WGS84',[x,y]);
}

var base = 'https://search.kmb.hk/KMBWebSite/Function/FunctionRequest.ashx'

function getBounds() {
    const routeNumber = $('#routeNumberInput').val()
    $('#directionInput').removeClass('disabled')
    $('#directionInput').children().splice(1).forEach((e) => {
        e.remove() // remove all inputs in bounds
    })
    $('#directionText').removeClass('disabled').prop('checked', true).addClass('disabled')
    $('#directionInput').addClass('disabled')
    $.ajax({
        type: 'GET',
        url: base+'?action=getroutebound&route='+routeNumber,
        success: function (e) {
            if (e['data'].length) {
                for (f of e['data']) {
                    const bound = f['BOUND']
                    $.ajax({
                        type: 'GET',
                        url: base+'?action=getSpecialRoute&route='+routeNumber+'&bound='+bound,
                        success: function (g) {
                            for (h of g['data']['routes']) {
                                const displayText = `${h['Origin_ENG'].toProperCase()} > ${h['Destination_ENG'].toProperCase()}${h['Desc_ENG'] ? ` - ${h['Desc_ENG']}`: ''}`
                                $('#directionInput').append($(`<option value="success" data-bound="${bound}" data-service="${Number(h['ServiceType'])}">${displayText}</option>`))
                            }
                        }
                    })
                }
                $('#directionInput').removeClass('disabled')
                $('#directionSearch').removeClass('disabled').addClass('btn-primary');
            } else {
                $('#routeNumberInput').addClass('is-invalid');
                $('#directionInput').addClass('disabled')
                $('#directionSearch').removeClass('btn-primary').addClass('disabled');
                halfmoon.initStickyAlert({
                    content: "Route does not exist!",
                    title: "<b>Error</b>",
                    alertType: "alert-secondary",
                    fillType: "filled-dm",
                    timeShown: 2000
                });
            }
        }
    })
}

$('#routeGroup').on('click', (e) => {
    $('#routeNumberInput').removeClass("is-invalid");
    if ($(e.target).is('#routeNumberSearch')) {
        getBounds()
    }
}).on('keypress', (e) => {
    if (e.which == 13) {
        getBounds();
    }
});

function getStops() {
    const selected = $("#directionInput option:selected")
    if (selected.val() == 'success') {
        const bound = selected.attr('data-bound')
        const serviceType = selected.attr('data-service')
        console.log(bound, serviceType)
    }
}

$('#directionSearch').on('click', () => {
    getStops();
});
$('#directionInput').on('change', (e) => {
    getStops()
});