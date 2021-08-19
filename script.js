const r = s=>atob(s).replace(/[a-z]/ig,c=>String.fromCharCode((c=c.charCodeAt())+((c&95)>77?-13:13)));
const azureKey = r("czRxM3IyMXE0c3AxNDk1NG4xcTU5MzBxNHFxcjM4MDk=");
const hkmsKey = r("NTg0bzJzbjY4NnMxNG9uMjgzODc0MzE4bzNvOHE2bzA=");

var satelliteURL = "https://landsd.azure-api.net/dev/ags/map/imagery/HK80";
var streetURL = "https://api.hkmapservice.gov.hk/ags/map/basemap/HK80";
// var mapEngLBUrl ="https://landsd.azure-api.net/dev/ags/map/label-en/HK80";

var groundURL = "https://landsd.azure-api.net/dev/ags/image/hkterrain/HK80";
var infra3Durl = "https://landsd.azure-api.net/dev/ags/i3s/3dsd/infrastructure/HK80";
var building3Durl = "https://landsd.azure-api.net/dev/ags/i3s/3dsd/building/HK80";

var kowloonEastHQmesh = "https://landsd.azure-api.net/dev/ags/i3s/meshmodel/kowlooneast/HK80";

const copyToClipboard = str => {
    const el = document.createElement('textarea');
    el.value = str;
    document.body.appendChild(el);
    el.select();
    document.execCommand('copy');
    document.body.removeChild(el);
};
var cb = document.getElementById("clipboardBtn");
cb.disabled = true;

var bldb = document.getElementById("buildingsBtn");
var infb = document.getElementById("infrastructuresBtn");
var terb = document.getElementById("terrainBtn");
var mapb = document.getElementById("mapBtn");

require([
    "esri/Map",
    "esri/views/SceneView",
    "esri/layers/SceneLayer",
    "esri/Basemap",
    "esri/Ground",
    "esri/webscene/Lighting",
    "esri/layers/TileLayer",
    "esri/layers/ElevationLayer",
    "esri/layers/SceneLayer",
    "esri/layers/IntegratedMeshLayer",
    "esri/core/urlUtils",
    "esri/views/MapView",
    "esri/config",
    "esri/layers/FeatureLayer",
    "esri/Graphic",
    "esri/geometry/SpatialReference",
    "esri/geometry/Point",
    "esri/widgets/BasemapToggle",
    "esri/widgets/Compass",
    "esri/widgets/DirectLineMeasurement3D",
    "esri/widgets/AreaMeasurement3D",
    "esri/geometry/projection",
    "esri/core/promiseUtils",
    "dojo/domReady!"
], function(Map, SceneView, SceneLayer, Basemap, Ground, Lighting,
    TileLayer, ElevationLayer, SceneLayer, IntegratedMeshLayer, 
    urlUtils, MapView, esriConfig, FeatureLayer, Graphic,
    SpatialReference, Point, 
    BasemapToggle, Compass, DirectLineMeasurement3D, AreaMeasurement3D,
    projection, promiseUtils) {
    
    esriConfig.request.trustedServers.push("https://landsd.azure-api.net");
    esriConfig.request.interceptors.push({
        before: function(params) {
            if (params.url.indexOf("landsd.azure-api.net")>=0) {
                if (params.requestOptions.query) {
                    params.requestOptions.query.key = azureKey
                } else {
                    params.requestOptions.query = {key: azureKey}
                }
            }
            if (params.url.indexOf("api.hkmapservice.gov.hk")>=0) {
                if (params.requestOptions.query) {
                    params.requestOptions.query.key = hkmsKey
                } else {
                    params.requestOptions.query = {key: hkmsKey}
                }
            }
            if (params.url.indexOf("api.hkmapservice.gov.hk/ags/map/layer/ib1000/buildings/building/0") >=0 )
                params.url = params.url.replace('building/0','building');
        },
        after: function(response) {
            if (!response.ssl) {
                response.ssl = true;
            }
        }
    });
    urlUtils.removeQueryParameters = function(a,c) {return a;}
    projection.load()
    const wgs84sr = new SpatialReference({
        wkid: 4326
    });

    var satelliteMap = new Basemap({
        baseLayers: [
            new TileLayer({
                url: satelliteURL
            }),
        ],
        title: "Satellite Map"
    });
    var streetMap = new Basemap({
        baseLayers: [
            new TileLayer({
                url: streetURL
            })
        ],
        title: "Street Map"
    })
    var groundLayer = new ElevationLayer({
        url: groundURL
    }) // needed for querying ground level height on click.
    var ground = new Ground({
        layers: [groundLayer]
    });
    // var meshModel = new IntegratedMeshLayer({
    //     url: kowloonEastHQmesh+"/layers/0"
    // });

    var buildings = new SceneLayer({
        url: `${building3Durl}/layers/0`,
        popupEnabled: false,
        outFields: ["*"]
    });
    var infrastructures = new SceneLayer({
        url: `${infra3Durl}/layers/0`,
        popupEnabled: false,
        outFields: ["*"]
    });
    
    
    var map = new Map({
        basemap: satelliteMap,
        ground: ground
    });
    map.add(buildings);
    map.add(infrastructures);
    // map.add(meshModel);
    
    var scene = new SceneView({   
        container: "scene-area",
        map: map,
        camera: {
            position: {
                x: 836467.5,
                y: 817872.7,
                z: 25000,
                spatialReference: { wkid: 2326 }
            },
            tilt: 0,
            heading: 0
        },
        environment: {
            starsEnabled: true,
            atmosphereEnabled: false, // performance
        }
    });

    var highlight;
    scene.on("click",function(event){
        // add red dot
        let pt = new Graphic({
            geometry: {
                type: 'point',
                x: event.mapPoint.x,
                y: event.mapPoint.y,
                z: event.mapPoint.z,
                spatialReference: {
                    wkid: 2326
                }
            },
            symbol: {
                type: "simple-marker",
                color: "red",
                size: "8px",
            },
        });
        scene.graphics.removeAll();
        scene.graphics.add(pt);

        let lastHit = null;
        scene.hitTest(event, {exclude:[scene.graphics]}).then(function(hitTestResult){
            if(hitTestResult.results.length > 0){
                lastHit = hitTestResult.results[0];
                // highlight selected building
                scene.whenLayerView(lastHit.graphic.layer).then(function(layerView){
                    if(highlight)
                        highlight.remove();
                    highlight = layerView.highlight(lastHit.graphic);
                });
                // query selected building
                if(lastHit && lastHit.graphic.attributes && lastHit.graphic.attributes.Name){
                    var geonum = lastHit.graphic.attributes.Name.substring(1, 10);
                    var building = new FeatureLayer({
                        url: "https://api.hkmapservice.gov.hk/ags/map/layer/ib1000/buildings/building",
                        outFields:["*"],
                        popupTemplate: {
                            title: "{englishbuildingname}, {chinesebuildingname}",
                            content: "Base Level: {baselevel}m ({baseleveldatasource})<br />\
                                        Roof Level: {rooflevel}m ({roofleveldatasource})<br />\
                                        CSUID: {buildingcsuid}"
                        },
                    });
                    var query = building.createQuery();
                    query.where = `buildingcsuid like '%${geonum}%'`
                    building.queryFeatures(query).then(function(response){
                        if(response.features.length > 0) {
                            for (const field of building.fields) {
                                switch (field['name']) {
                                    case 'baseleveldatasource':
                                        for (const feature of response.features) {
                                            for (const blm of field['domain']['codedValues']) {
                                                if (blm['code'] === feature['attributes']['baseleveldatasource']) {
                                                    feature['attributes']['baseleveldatasource'] = blm['code'];
                                                    break;
                                                }
                                            }
                                            feature['attributes']['baselevel'] = parseFloat(feature['attributes']['baselevel']).toFixed(1)
                                        }
                                    case 'roofleveldatasource':
                                        // rlds_dict = field['domain']['codedValues']
                                        for (const feature of response.features) {
                                            for (const rlm of field['domain']['codedValues']) {
                                                if (rlm['code'] === feature['attributes']['roofleveldatasource']) {
                                                    feature['attributes']['roofleveldatasource'] = rlm['code'];
                                                    break;
                                                }
                                            }
                                            feature['attributes']['rooflevel'] = parseFloat(feature['attributes']['rooflevel']).toFixed(1)
                                        }
                                }
                            }
                            for (const feature of response.features) {
                                if (feature['attributes']['englishbuildingname'] === null) {
                                    feature['attributes']['englishbuildingname'] = '<i>Unknown</i>'
                                }
                                if (feature['attributes']['chinesebuildingname'] === null) {
                                    feature['attributes']['chinesebuildingname'] = '<i>不明</i>'
                                }
                            }
                            scene.popup.open({
                                features : response.features
                            })
                        }
                    });
                }
            }
        });
        //
        cb.innerHTML = "Loading...";
        cb.className = "btn btn-disabled";
        let queryGroundHeight = groundLayer.queryElevation(event.mapPoint)
        promiseUtils.eachAlways([queryGroundHeight]).then(function(results) {
            const hk80 = new Point({
                x: event.mapPoint.x,
                y: event.mapPoint.y,
                spatialReference: {
                    wkid: 2326
                }
            });
            const wgs84 = projection.project(hk80, wgs84sr);
            document.getElementById("hk80coords").innerHTML = `N${parseFloat(hk80.y).toFixed(2)}, E${parseFloat(hk80.x).toFixed(2)}`;
            document.getElementById("wgs84coords").innerHTML = `${parseFloat(wgs84.y).toFixed(7)}, ${parseFloat(wgs84.x).toFixed(7)}`;
            document.getElementById("wgs84coords").setAttribute("data-command", `/tpll ${wgs84.y} ${wgs84.x}`)
            document.getElementById("elevation").innerHTML = `${parseFloat(results[0].value.geometry.z).toFixed(2)} m`
            document.getElementById("height").innerHTML = `${parseFloat(event.mapPoint.z).toFixed(2)} m <span class="dim">(${parseFloat(event.mapPoint.z - results[0].value.geometry.z).toFixed(2)} m above terrain)</span>`
            cb.disabled = false;
            if (event.button === 1) {
                copyTPLL();
            } else {
                cb.innerHTML = "Copy command";
                cb.className = "btn btn-enabled";
            }
        })
    });

    scene.when(function() {
        var mapt = new BasemapToggle({
            view: scene,
            nextBasemap: streetMap,
            visibleElements: {
                title: true
            }
        })
        // from https://developers.arcgis.com/javascript/latest/sample-code/widgets-measurement-3d/
        var activeWidget = null;
        scene.ui.add("topbar", "top-right")
        scene.ui.add("bottomRightBar", "bottom-right")
        scene.ui.add("bottomLeftBar", "bottom-left")

        var copyTPLL = () => {
            if (cb.disabled === false) {
                cb.disabled = true;
                copyToClipboard(document.getElementById("wgs84coords").getAttribute("data-command"));
                cb.innerHTML = "Copied to clipboard";
                cb.className = "btn btn-active bold";
                setTimeout(function() {
                    cb.innerHTML = "Copy command";
                    cb.className = "btn btn-enabled";
                    cb.disabled = false;
                }, 1000)
            }
        }
        cb.addEventListener("click", copyTPLL);
        
        bldb.addEventListener("click", function(e) {
            if (bldb.getAttribute("data-status") === "off") {
                buildings.visible = true;
                bldb.className = "btn btn-pad btn-enabled";
                bldb.innerHTML = "On";
                bldb.setAttribute("data-status", "on");
            } else {
                buildings.visible = false;
                bldb.className = "btn btn-pad btn-disabled";
                bldb.innerHTML = "Off";
                bldb.setAttribute("data-status", "off");
            }
        });
        infb.addEventListener("click", function(e) {
            if (infb.getAttribute("data-status") === "off") {
                infrastructures.visible = true;
                infb.className = "btn btn-pad btn-enabled";
                infb.innerHTML = "On";
                infb.setAttribute("data-status", "on");
            } else {
                infrastructures.visible = false;
                infb.className = "btn btn-pad btn-disabled";
                infb.innerHTML = "Off";
                infb.setAttribute("data-status", "off");
            }
        });
        terb.addEventListener("click", function(e) {
            if (terb.getAttribute("data-status") === "off") {
                map.ground.layers.forEach(function(layer) {
                    layer.visible = true;
                })
                terb.className = "btn btn-pad btn-enabled";
                terb.innerHTML = "On";
                terb.setAttribute("data-status", "on");
            } else {
                map.ground.layers.forEach(function(layer) {
                    layer.visible = false;
                })
                terb.className = "btn btn-pad btn-disabled";
                terb.innerHTML = "Off";
                terb.setAttribute("data-status", "off");
            }
        });
        mapb.addEventListener("click", function(e) {
            if (mapb.getAttribute("data-status") === "satellite") {
                mapt.toggle()
                mapb.className = "btn btn-pad btn-active";
                mapb.innerHTML = "Street";
                mapb.setAttribute("data-status", "street");
            } else {
                mapt.toggle()
                mapb.className = "btn btn-pad btn-enabled";
                mapb.innerHTML = "Satellite";
                mapb.setAttribute("data-status", "satellite");
            }
        });

        document.getElementById("distanceButton").addEventListener("click", function() {
            setActiveWidget(null);
            if (!this.classList.contains("active")) {
                setActiveWidget("distance");
            } else {
                setActiveButton(null);
            }
        });

        document.getElementById("areaButton").addEventListener("click", function() {
            setActiveWidget(null);
            if (!this.classList.contains("active")) {
                setActiveWidget("area");
            } else {
                setActiveButton(null);
            }
        });

        function setActiveWidget(type) {
            switch (type) {
                case "distance":
                activeWidget = new DirectLineMeasurement3D({
                    view: scene
                });

                activeWidget.viewModel.newMeasurement();

                scene.ui.add(activeWidget, "top-right");
                setActiveButton(document.getElementById("distanceButton"));
                break;
                case "area":
                activeWidget = new AreaMeasurement3D({
                    view: scene
                });

                activeWidget.viewModel.newMeasurement();

                scene.ui.add(activeWidget, "top-right");
                setActiveButton(document.getElementById("areaButton"));
                break;
                case null:
                if (activeWidget) {
                    scene.ui.remove(activeWidget);
                    activeWidget.destroy();
                    activeWidget = null;
                }
                break;
            }
        }

        function setActiveButton(selectedButton) {
            scene.focus();
            var elements = document.getElementsByClassName("active");
            for (var i = 0; i < elements.length; i++) {
                elements[i].classList.remove("active");
            }
            if (selectedButton) {
                selectedButton.classList.add("active");
            }
        }
    })
});