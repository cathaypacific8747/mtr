// initialise map
var inverted = 1
var invertFilter = ['invert:100%','bright:120%','contrast:80%','hue:180deg','saturate:100%'];
var map = L.map('map', {
    scrollWheelZoom: false,
    smoothWheelZoom: true,
    smoothSensitivity: 1.5,
}).setView([22.344484, 114.148469], 11);
map.scrollWheelZoom = true;

let base = L.tileLayer.colorFilter('https://api.hkmapservice.gov.hk/osm/xyz/basemap/WGS84/tile/{z}/{x}/{y}.png?key=454c6d4b534c40fbb29b2a0845e32a55', {
    attribution: "&copy; Map from <a href='https://api.portal.hkmapservice.gov.hk/disclaimer' target='_blank'>Lands Department</a>",
    minZoom: 10,
    maxZoom: 20,
    filter: invertFilter,
}).addTo(map);
let labels = L.tileLayer.colorFilter('https://api.hkmapservice.gov.hk/osm/xyz/label-en/WGS84/tile/{z}/{x}/{y}.png?key=454c6d4b534c40fbb29b2a0845e32a55', {
    attribution: "&copy; Map from <a href='https://api.portal.hkmapservice.gov.hk/disclaimer' target='_blank'>Lands Department</a>",
    minZoom: 10,
    maxZoom: 20,
    filter: invertFilter,
}).addTo(map);
var routeLayer = L.featureGroup().addTo(map)
var etaLayer = L.featureGroup().addTo(map)

// useful functions and variables
var baseURL = 'https://search.kmb.hk/KMBWebSite/Function/FunctionRequest.ashx'
proj4.defs('WGS84', "+title=WGS 84 (long/lat) +proj=longlat +ellps=WGS84 +datum=WGS84 +units=degrees");
proj4.defs('EPSG:2326', '+proj=tmerc +lat_0=22.31213333333334 +lon_0=114.1785555555556 +k=1 +x_0=836694.05 +y_0=819069.8 +ellps=intl +towgs84=-162.619,-276.959,-161.764,0.067753,-2.24365,-1.15883,-1.09425 +units=m +no_defs');

var HK80_to_WGS84 = (x, y) => {
    LonLat = proj4('EPSG:2326', 'WGS84', [x, y])
    return [LonLat[1], LonLat[0]]
};

String.prototype.toProperCase = function () {
    return this.replace(/\w\S*/g, function(txt){return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();});
};

Number.prototype.toRad = function () {
    return this * Math.PI / 180;
}

Number.prototype.toDeg = function () {
    return this * 180 / Math.PI;
}

function getDistance(lat1, lon1, lat2, lon2) {
    // formula from: http://www.movable-type.co.uk/scripts/latlong.html
    const φ1 = lat1.toRad(); // φ, λ in radians
    const φ2 = lat2.toRad();
    const Δφ = (lat2-lat1).toRad();
    const Δλ = (lon2-lon1).toRad();

    const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) + Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ/2) * Math.sin(Δλ/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

    return 6371e3 * c; // in metres
}

function getIntermediate(lat1, lon1, lat2, lon2, distanceTo1) {
    const d = getDistance(lat1, lon1, lat2, lon2)
    const f = distanceTo1 / d //fraction between point 1 and point 2

    const φ1 = lat1.toRad();
    const λ1 = lon1.toRad();
    const φ2 = lat2.toRad();
    const λ2 = lon2.toRad();

    const δ = d / 6371e3 // angular distance
    const A = Math.sin((1-f)*δ) / Math.sin(δ);
    const B = Math.sin(f*δ) / Math.sin(δ);

    const x = A * Math.cos(φ1) * Math.cos(λ1) + B * Math.cos(φ2) * Math.cos(λ2);
    const y = A * Math.cos(φ1) * Math.sin(λ1) + B * Math.cos(φ2) * Math.sin(λ2);
    const z = A * Math.sin(φ1) + B * Math.sin(φ2);

    const φ3 = Math.atan2(z, Math.sqrt(x*x + y*y));
    const λ3 = Math.atan2(y, x);

    return [φ3.toDeg(), λ3.toDeg()]
}

var pad = val => ('00'+val).slice(-2)
var isNumber = n => !isNaN(parseFloat(n)) && !isNaN(n - 0)
// var getTimeDifference = new Promise((resolve, reject) => {
//     $.ajax({
//         'type': 'GET',
//         'url': 'http://worldtimeapi.org/api/timezone/Asia/Hong_Kong',
//         'success': function (e) {
//             resolve(e.unixtime*1000 - new Date().getTime())
//         }
//     })
// })

// getTimeDifference.then((e) => {
//     console.log(e)
// })

function toggleMapInvert() {
    if (inverted) {
        base.updateFilter([])
        labels.updateFilter([])
    } else {
        base.updateFilter(invertFilter)
        labels.updateFilter(invertFilter)
    }
    inverted ^= 1
}

function disableOption(id) {
    $(`#${id}Input`).removeClass('disabled')
    $(`#${id}Input`).children().splice(1).forEach((e) => {
        e.remove();
    });
    $(`#${id}Text`).removeClass('disabled').prop('checked', true).addClass('disabled')
    $(`#${id}Input`).addClass('disabled')
    $(`#${id}Search`).removeClass('btn-primary').addClass('disabled');
}

var deselected_icon = L.divIcon({
    className: 'deselected-icon',
    iconSize: [8, 8],
    iconAnchor: [4, 4]
})
var selected_icon = L.divIcon({
    className: 'selected-icon',
    iconSize: [12, 12],
    iconAnchor: [6, 6]
})

function deselectAllStops() {
    routeLayer.eachLayer(layer => {
        if (layer._icon) {
            layer.setIcon(deselected_icon)
            const oldName = layer._tooltip._content
            layer.unbindTooltip()
            layer.bindTooltip(oldName, {
                permanent: true,
                interactive: true,
                opacity: 1
            })
        }
    })
    for (let entryCount = 0; entryCount < 3; entryCount++) {
        $(`#eta${entryCount}`).html('---')
        $(`#info${entryCount}`).html('---')
        $('#lastUpdated').html('---')
    }
    etaLayer.clearLayers(); 
}

//start

function getBounds() {
    const routeNumber = $('#routeNumberInput').val()
    // if user inputs wrong route preceded by a correct route, remove all bounds information and disable the input (to start over).
    routeLayer.clearLayers()
    disableOption('direction')
    disableOption('stop')
    $.ajax({
        type: 'GET',
        url: baseURL+'?action=getroutebound&route='+routeNumber,
        success: function (e) {
            if (e['data'].length) {
                // for each bound, request the different variants and append them to the bound selection dropdown.
                for (f of e['data']) {
                    const bound = f['BOUND']
                    $.ajax({
                        type: 'GET',
                        url: baseURL+'?action=getSpecialRoute&route='+routeNumber+'&bound='+bound,
                        success: function (g) {
                            for (h of g['data']['routes']) {
                                const specialServiceText = parseInt(h['ServiceType']) == 1 ? '': '*'
                                const displayText = `${specialServiceText}${h['Origin_ENG'].toProperCase()} > ${h['Destination_ENG'].toProperCase()}${h['Desc_ENG'] ? ` - ${h['Desc_ENG']}`: ''}`
                                $('#directionInput').append($(`<option value="success" data-bound="${bound}" data-service="${Number(h['ServiceType'])}">${displayText}</option>`))
                            }
                        }
                    })
                }
                $('#directionInput').removeClass('disabled')
                $('#directionSearch').removeClass('disabled').addClass('btn-primary');
                $('#routeNumberInput').removeClass("is-invalid");
            } else {
                $('#routeNumberInput').addClass('is-invalid');
                halfmoon.initStickyAlert({
                    content: "Route does not exist!",
                    title: "<b>Error</b>",
                    alertType: "alert-secondary",
                    fillType: "filled-dm",
                    timeShown: 2000
                });
            }
        }
    });
}

// search button onClick || input onKeyPress 'return': get the bounds of the specified routeNumber
$('#routeGroup').on('click', (e) => {
    $('#routeNumberInput').removeClass("is-invalid");
    if ($(e.target).is('#routeNumberSearch')) {
        getBounds();
    }
}).on('keypress', (e) => {
    if (e.which == 13) {
        getBounds();
    }
});

function getStops() {
    const selected = $("#directionInput option:selected")
    routeLayer.clearLayers()
    $(`#stopInput`).children().splice(1).forEach((e) => {
        e.remove();
    });
    if (selected.val() == 'success') {
        const routeNumber = $('#routeNumberInput').val()
        const bound = selected.attr('data-bound')
        const serviceType = selected.attr('data-service')
        $.ajax({
            'type': 'GET',
            'url': `${baseURL}?action=getstops&route=${routeNumber}&bound=${bound}&serviceType=${serviceType}`,
            'success': function (f) {
                // add list of stops to entry
                for (g of f['data']['routeStops']) {
                    const coords = HK80_to_WGS84(Number(g['Y']), Number(g['X']))
                    $('#stopInput').append($(`<option value="success" data-bound="${bound}" data-service="${serviceType}" data-stop="${g['BSICode']}" data-seq="${g['Seq']}">${g['Seq']} - ${g['EName'].toProperCase()}</option>`))
                }
                $('#stopInput').removeClass('disabled')
                $('#stopSearch').removeClass('disabled').addClass('btn-primary');

                // show route on map

                JSON5.parse(f['data']['route']['lineGeometry'])['paths'].forEach(path => {
                    let thisPath = []
                    path.forEach(hk80coord => {
                        thisPath.push(HK80_to_WGS84(Number(hk80coord[0]), Number(hk80coord[1])))
                    })
                    let rt = L.polyline(thisPath, {
                        color: 'white',
                        weight: 2,
                        opacity: 0.5,
                        lineJoin: 'round',
                    })
                    routeLayer.addLayer(rt)
                });
                f['data']['routeStops'].forEach(stop => {
                    const coords = HK80_to_WGS84(Number(stop['X']), Number(stop['Y']))
                    const m = L.marker([coords[0], coords[1]], {
                        'icon': deselected_icon,
                        'seq': stop['Seq']
                    })
                    m.on('click', function (e) {
                        $(`#stopInput option[data-seq=${stop['Seq']}]`).attr('selected', 'selected')
                        deselectAllStops()
                        e.target.setIcon(selected_icon)
                        const oldName = e.target._tooltip._content
                        e.target.unbindTooltip()
                        e.target.bindTooltip(oldName, {
                            className: 'selected-tooltip',
                            permanent: true,
                            interactive: true,
                            opacity: 1
                        })
                        getETAfromInputs()
                    }).bindTooltip(`${stop['Seq']} - ${stop['EName'].toProperCase()}`, {
                        permanent: true,
                        interactive: true,
                        opacity: 1
                    })
                    routeLayer.addLayer(m)
                })
                map.flyToBounds(routeLayer.getBounds(), {
                    'duration': 0.5
                })
            }
        });
    } else {
        disableOption('stop')
    }
}

// search button onClick || input onKeyPress 'return': get all stops for that bound.
$('#directionSearch').on('click', () => {
    getStops();
});
$('#directionInput').on('change', (e) => {
    getStops();
});

function getETAfromInputs() {
    const selected = $("#stopInput option:selected")
    if (selected.val() == 'success') {
        const routeNumber = $('#routeNumberInput').val()
        const bound = selected.attr('data-bound')
        const serviceType = selected.attr('data-service')
        const stopId = selected.attr('data-stop')
        const seq = selected.attr('data-seq')
        getETA(routeNumber, bound, serviceType, stopId, seq)
    } else {
        deselectAllStops()
    }
}

function getETA(routeNumber, bound, serviceType, stopId, seq) {
    const time = new Date()
    const t = `${time.getUTCFullYear()}-${pad(time.getUTCMonth()+1)}-${pad(time.getUTCDate())} ${pad(time.getUTCHours())}:${pad(time.getUTCMinutes())}:${pad(time.getUTCSeconds())}.${pad(time.getUTCMilliseconds())}.`
    const sep = `--31${t}13--`
    const token = 'E'+Base64.encode(`${routeNumber}${sep}${bound}${sep}${serviceType}${sep}${stopId.replace(/-/g, '')}${sep}${seq}${sep}${time.getTime()}`)
    etaLayer.clearLayers();
    $.ajax({
        'type': 'POST',
        'url': baseURL + '?action=get_ETA&lang=0',
        'data': {
            'token': token,
            't': t
        },
        'dataType': 'json',
        'success': function (e, status, xhr) {
            const updated = new Date(e.data.updated)
            const generated = new Date(e.data.generated)
            $('#lastUpdated').html(`${pad(updated.getHours())}:${pad(updated.getMinutes())}:${pad(updated.getSeconds())} (${Math.abs(generated-updated)/1000}s delay)`)
            for (let entryCount = 0; entryCount < 3; entryCount++) {
                thisEntry = e.data.response[entryCount]
                if (!thisEntry) { // no entry given (e.g. 2 entries max)
                    $(`#eta${entryCount}`).html('')
                    $(`#info${entryCount}`).html('')
                } else {// there is a bus, eta given or not.
                    let etaString = ''
                    let extraInfo = ''
                    if (thisEntry != null) {
                        if (thisEntry.t[2] == ':') { // show all info accordingly.
                            const parsed = thisEntry.t.split(/ (.+)/)
                            // calculate time exact bus arrival time.
                            let etaSec = thisEntry.t.substring(0,2)*3600 + thisEntry.t.substring(3,5)*60 //- (generated-updated)
                            const trueEtaDisplay = new Date(etaSec*1000).toISOString().substr(11, 8)
                            
                            // calculate time until bus arrives
                            const tNow = new Date()
                            const nowSec = tNow.getHours()*60*60 + tNow.getUTCMinutes()*60 + tNow.getSeconds()
                            etaSec = thisEntry.t.substring(0,2) == 0 && tNow.getHours() == 23 ? etaSec + 86400 : etaSec; // so it could subtract properly for the next day (00:15-23:30 = 24:15-23:30 = 00:45)
                            const isInvalid = nowSec > etaSec
                            const trueDeltaEtaDisplay = isInvalid ? '': `T-${new Date((etaSec - nowSec)*1000).toISOString().substr(14, 5)}`
                            const trueEtaColor = isInvalid ? 'text-danger': 'text-success'

                            etaString = `<span class="${trueEtaColor}">${trueEtaDisplay}</span>\n<span class="font-italic text-muted">${trueDeltaEtaDisplay}</span>`
                            extraInfo = parsed[1] ||= ''
                        } else { // eta time is not empty -> show information
                            etaString = ''
                            extraInfo = thisEntry.t
                        }
                    }
                    const distanceAwayDisplay = !thisEntry || thisEntry.dis === null ? '' : `<span class="text-success">${thisEntry.dis / 1000} km</span>\n` // show 0km also
                    const extraInfoColor = !extraInfo ? '': extraInfo.includes('Scheduled') || extraInfo.includes('Last Bus') ? 'text-warning': 'text-danger' // journey delayed, already departed, eta suspended = show red text
                    $(`#eta${entryCount}`).html(etaString)
                    $(`#info${entryCount}`).html(`${distanceAwayDisplay}<span class="${extraInfoColor}">${extraInfo}</span>`)
                }
            } // update <table>'s eta and other related information

            let fullRt = [] // fullRouteBeforeCandidate 
            if (Number(seq) != 0) { // if the selected stop is not the origin, get a route with coordinates including the preceding stops. 
                routeLayer.eachLayer(stop => {
                    if (stop.options.seq == seq) {
                        // since the location of stops are not directly on the route,
                        // find the closest matching stop.
                        let segmentId = null
                        let shortestDistance = Infinity
                        routeLayer.eachLayer(l => {
                            if (l._latlngs) {
                                let endPoint = l._latlngs[l._latlngs.length-1]
                                let thisDistance = getDistance(stop._latlng.lat, stop._latlng.lng, endPoint.lat, endPoint.lng)
                                if (thisDistance < shortestDistance) {
                                    segmentId = l._leaflet_id
                                    shortestDistance = thisDistance
                                }
                            }
                        })

                        if (shortestDistance < 50) {
                            routeLayer.eachLayer(l => {
                                if (l._latlngs && l._leaflet_id <= segmentId) {
                                    l._latlngs.forEach(e => {
                                        fullRt.push([e.lat, e.lng])
                                    })
                                }
                            })
                        } else {
                            // if the stop is too far from the intended route,
                            // try to intersect the segment with the shortest distance
                            // e.g. 81 Southbound @ Chik Fai Street.
                            routeLayer.eachLayer(l => {
                                if (l._latlngs && l._leaflet_id < segmentId) {
                                    l._latlngs.forEach(e => {
                                        fullRt.push([e.lat, e.lng])
                                    })
                                } else if (l._latlngs && l._leaflet_id == segmentId) {
                                    let closestIndex = null
                                    let smallestDistance = Infinity
                                    for (let index = 0; index < l._latlngs.length; index++) {
                                        let thisStop = l._latlngs[index]
                                        let thisDistance = getDistance(stop._latlng.lat, stop._latlng.lng, thisStop.lat, thisStop.lng)
                                        if (thisDistance < smallestDistance) {
                                            closestIndex = index
                                            smallestDistance = thisDistance
                                        }
                                    }
                                    for (let i = 0; i <= closestIndex; i++) {
                                        fullRt.push([l._latlngs[i].lat, l._latlngs[i].lng])
                                    }
                                }
                            })
                        }
                        fullRt.push([stop._latlng.lat, stop._latlng.lng])
                        fullRt.reverse()
                        // fullRt is now an array of coordinates,
                        // which backtracks from the currentstop and can be used to reverse the location from the distance.
                        L.polyline(fullRt, {
                            color: 'yellow',
                            weight: 2,
                            lineJoin: 'round',
                        }).addTo(etaLayer)
                    }
                })
            } // otherwise buses are at the terminal/travelling inbound.

            // get eta information
            // calculate actual coords for each eta.
            for (let entryCount = 0; entryCount < 3; entryCount++) {
                thisEntry = e.data.response[entryCount]
                if (thisEntry && thisEntry.dis) {
                    let distanceSoFar = 0
                    let estRt = {} // estimatedRouteSegment
                    for (let i = 0; i < fullRt.length; i++) {
                        // assume _ = 100m,
                        // targeted = 1500m
                        // route =    1_________2_____3__________4____...
                        // for each starting lcoation of the route:
                        // - 1>2: 900m (accumulated 900m)
                        // - 2>3: 500m (accumulated 1400m)
                        // - 3>4: 1000m (accumulated 2400m - above 1500m so break out of the loop.)
                        // now we obtain that the route segment to be 3>4, and store that in estRt.
                        toNextDistance = getDistance(fullRt[i][0], fullRt[i][1], fullRt[i+1][0], fullRt[i+1][1])
                        if (distanceSoFar + toNextDistance > thisEntry.dis) {
                            estRt = {
                                'start': fullRt[i],
                                'end': fullRt[i+1]
                            }
                            break;
                        }
                        distanceSoFar += toNextDistance
                    }
                    if (estRt) {
                        // as the bus is between this route segment,
                        // by continuing to backtrack the remaining distance from the start point of the route segment
                        // the exact coords of the bus could be found.
                        predictedLocation = getIntermediate(estRt['start'][0], estRt['start'][1], estRt['end'][0], estRt['end'][1], thisEntry.dis - distanceSoFar)
                        L.marker(predictedLocation).addTo(etaLayer)
                    }
                }
            }
            // calculate velocity
            // show bus location
            console.log(e.data.response)
        }
    })
}

// search button onClick || input onKeyPress 'return': get eta for this stop.
$('#stopInput').on('change', (e) => {
    deselectAllStops();
    getETAfromInputs();
});
$('#stopSearch').on('click', () => {
    getETAfromInputs();
});
$('#map').on('click', (e) => {
    if (e.target.id == 'map') {
        deselectAllStops();
    }
});

// misc: smooth scroll