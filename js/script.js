const baseURL = "https://data.etabus.gov.hk/";
const defaultStops = [
    // school
    {
        'id': '937C2A421F2E7D11',
        'description': 'Caldecott Road',
        'bound': 'Kowloon'
    },
    {
        'id': '24D77D8722934A82',
        'description': 'Caldecott Road',
        'bound': 'Sha Tin'
    },
    // 81 to school, Kowloon bound
    {
        'id': '',
        'description': 'Mei Tao House',
        'bound': 'Kowloon'
    },
    {
        'id': '',
        'description': 'Chik Fai Street',
        'bound': 'Kowloon'
    },
    {
        'id': '',
        'description': 'Mei Lam Estate',
        'bound': 'Kowloon'
    },
    {
        'id': '',
        'description': 'Chung Ling Road',
        'bound': 'Kowloon'
    },
    {
        'id': '',
        'description': 'Sha Tin Heights Road',
        'bound': 'Kowloon'
    },
    // 72 to school, Kowloon bound
    {
        'id': '',
        'description': 'Royal Park Hotel',
        'bound': 'Kowloon'
    },
    {
        'id': '',
        'description': 'Sha Tin Town Centre',
        'bound': 'Kowloon'
    },
    // 81 to school, Sha Tin bound
    {
        'id': '',
        'description': 'Prince Edward Station',
        'bound': 'Sha Tin'
    },
    {
        'id': '',
        'description': '',
        'bound': 'Sha Tin'
    },
    // 81 
    {
        'id': '11B2034DDF30617A',
        'description': 'Hung Hom Cross Harbour Tunnel Toll Plaza',
        'bound': '[DEBUG] Kowloon'
    },
    {
        'id': '4D3CBBDB95447F2E',
        'description': 'Hung Hom Cross Harbour Tunnel Toll Plaza',
        'bound': '[DEBUG] Hong Kong'
    }
]

function htmlToElements(html) {
    var template = document.createElement('template');
    template.innerHTML = html;
    return template.content.childNodes;
}

function convertDateToUTC(date) { 
    return new Date(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate(), date.getUTCHours(), date.getUTCMinutes(), date.getUTCSeconds()); 
}

class Eta {
    constructor() {}
    setGeneratedTime(t) {
        this.generated = new Date(t)
    }
    fromStopEta(o) {
        let route = new Route();
        route.fromStopEta(o);
        this.route = route;
        this.eta = new Date(o['eta']);
        this.eta_sequence = o['eta_seq'];
        this.remark_en = o['rmk_en'];
        this.remark_tc = o['rmk_tc'];
        this.lastUpdated = new Date(o['data_timestamp']);
        this.delta = convertDateToUTC(new Date(this.eta - new Date()));
        this.valid = this.eta > new Date();
    }
}

class Route {
    constructor() {}
    fromStopEta(o) {
        this.destination_en = o['dest_en'];
        this.destination_tc = o['dest_tc'];
        this.direction = o['dir'];
        this.route = o['route'];
        this.route_sequence = o['seq'];
    }
}

class Stop {
    constructor(stopId) {
        this.stopId = stopId;
        this.etas = [];
    }

    // gets eta of all routes passing through that stop
    async getEta() {
        let response = await fetch(baseURL+'v1/transport/kmb/stop-eta/'+this.stopId);
        this.response = await response.json()
        return this;
    }

    processEta() {
        for (const data of this.response.data) {
            let eta = new Eta()
            eta.setGeneratedTime(this.response.generated_timestamp)
            eta.fromStopEta(data)
            this.etas.push(eta)
        }
        this.etas.sort((a, b) => a.eta - b.eta)
        return this;
    }

    updateInfo(tblNum) {
        let html = '';
        for (const data of this.etas) {
            if (data.valid) {
                let colour = data.remark_en == '' ? 'table-success' : 'table-secondary'
                html += `<tr class="${colour}">
                    <td>${data.route.route}</td>
                    <td>${data.route.destination_en}</td>
                    <td>${strftime('%H:%M:%S', data.eta)}</td>
                    <td>${strftime('%H:%M:%S', data.delta)}</td>
                    <td>${data.remark_en}</td>
                </tr>`;
            }
        }
        $(`#table${tblNum}`).html(html);
        $(`#generated${tblNum}`).html(strftime('%H:%M:%S', new Date(this.response.generated_timestamp)))
    }
}

// main code
let stopNum1 = 0;
let stopNum2 = 1;

setInterval(function() {
    let stop1 = new Stop(defaultStops[stopNum1].id);
    stop1.getEta()
    .then(() => stop1.processEta())
    .then(() => stop1.updateInfo(1))
    .then(() => {
        // update title and subtitle
        $(`#destination1`).html(defaultStops[stopNum1].description);
        $(`#bound1`).html(defaultStops[stopNum1].bound);
    });

    let stop2 = new Stop(defaultStops[stopNum2].id);
    stop2.getEta()
    .then(() => stop2.processEta())
    .then(() => stop2.updateInfo(2))
    .then(() => {
        // update title and subtitle
        $(`#destination2`).html(defaultStops[stopNum2].description);
        $(`#bound2`).html(defaultStops[stopNum2].bound);
    });
}, 1000);