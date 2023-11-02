let state = 0;
const wtBaseURL = "http://localhost:8111";
const wtStatePath = "/state";
let theButton = document.getElementById("go-next-btn");
let instructions = document.getElementById("instruction-text");
let errorMessage = document.getElementById("error-text");

let wtReachable = false;
let inSession = false;

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function buttonClick() {
    switch (state) {
        case 0:
            checkWtConnection();
            break;

        case 1:
            theButton.onclick = setStopFlag;
            await doSession();
            break;
            
        default:
            

    }
}

function setStopFlag() {
    inSession = false;
}

function stopSession() {

}

async function doSession() {
    let r = new XMLHttpRequest();
    r.open("POST", "/api/start", true);

    r.onload = function() {
        if (r.status !== 200) {
            console.error("Session start FAIL! Code " + r.status);
            inSession = false;
        }
    };

    r.send();
    
    instructions.innerHTML = "Collecting your in-game telemetry... Press 'Stop' to end the collection session.";
    theButton.innerHTML = "Stop";
    inSession = true;

    while (inSession) {
        let r1 = new XMLHttpRequest();
        r1.open("GET", wtBaseURL + wtStatePath, true);

        r1.onload = function () {
            if (r1.status === 200) {
                let data = JSON.parse(r1.responseText);

                let r2 = new XMLHttpRequest();
                r2.open("POST", "/api/data", true);
                r2.setRequestHeader("Content-Type", "application/json");

                r2.onload = function() {
                    if (r2.status !== 200) {
                        console.warn("HTTP error encountered during data forwarding: code " + r2.status);
                    }
                };

                r2.onerror = function() {
                    console.error("Data forwarding XHR failed: " + r2.status);
                };

                r2.send(JSON.stringify(data));
                
            } else {
                console.warn("HTTP error encountered during data fetching: code " + r1.status);
            }
        };

        r1.onerror = function() {
            console.error("Data fetching XHR failed: " + r1.status);
        };

        r1.send();
        await sleep(50);
    }
    stopSession();
}

function checkWtConnection() {
    errorMessage.hidden = true;
    instructions.hidden = false;
    theButton.innerHTML = "Start";
    theButton.disabled = true;
    instructions.innerHTML = "Checking connection...";
    let r = new XMLHttpRequest();

    r.onload = function () {
        instructions.innerHTML = "War Thunder is running and reachable!<br>Click the 'Start' button when you're ready to begin data logging.";
        state++;
        theButton.disabled = false;
    }

    r.onerror = function (e) {
        console.log(e);
        theButton.innerHTML = "Retry";
        instructions.hidden = true;
        errorMessage.innerHTML = "A connection could not be established to your game's live map endpoint.<br>Please make sure War Thunder is running and try again.";
        errorMessage.hidden = false;
        theButton.disabled = false;
    }

    r.open("GET", wtBaseURL + wtStatePath);
    r.send();
}

