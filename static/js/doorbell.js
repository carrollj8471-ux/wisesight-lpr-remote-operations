const startButton = document.getElementById("startDoorbellStream");
const stopButton = document.getElementById("stopDoorbellStream");
const statusLabel = document.getElementById("streamStatus");
const video = document.getElementById("doorbellVideo");
const logBox = document.getElementById("doorbellLog");

let peerConnection = null;

function setStatus(message) {
    statusLabel.textContent = message;
}

function log(message) {
    const timestamp = new Date().toLocaleTimeString();
    logBox.textContent = `[${timestamp}] ${message}\n${logBox.textContent}`;
}

function waitForIceGatheringComplete(pc) {
    if (pc.iceGatheringState === "complete") {
        return Promise.resolve();
    }

    return new Promise((resolve) => {
        function checkState() {
            if (pc.iceGatheringState === "complete") {
                pc.removeEventListener("icegatheringstatechange", checkState);
                resolve();
            }
        }

        pc.addEventListener("icegatheringstatechange", checkState);
        setTimeout(resolve, 3000);
    });
}

async function startStream() {
    stopStream();
    setStatus("Connecting");
    startButton.disabled = true;

    try {
        peerConnection = new RTCPeerConnection({
            bundlePolicy: "max-bundle",
            rtcpMuxPolicy: "require",
        });

        peerConnection.addTransceiver("audio", { direction: "recvonly" });
        peerConnection.addTransceiver("video", { direction: "recvonly" });
        peerConnection.createDataChannel("data");

        peerConnection.addEventListener("track", (event) => {
            video.srcObject = event.streams[0];
            video.play().catch(() => {});
            setStatus("Live");
            log("Live stream connected.");
        });

        peerConnection.addEventListener("connectionstatechange", () => {
            log(`Connection state: ${peerConnection.connectionState}`);
            if (peerConnection.connectionState === "failed") {
                setStatus("Connection failed");
            }
        });

        const offer = await peerConnection.createOffer();
        await peerConnection.setLocalDescription(offer);
        await waitForIceGatheringComplete(peerConnection);

        const response = await fetch("/api/doorbell/webrtc", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                offerSdp: peerConnection.localDescription.sdp,
            }),
        });

        const payload = await response.json();
        if (!response.ok) {
            throw new Error(payload.error || "Google SDM stream request failed.");
        }

        await peerConnection.setRemoteDescription({
            type: "answer",
            sdp: payload.answerSdp,
        });

        if (payload.expiresAt) {
            log(`Stream expires at ${payload.expiresAt}.`);
        }
    } catch (error) {
        setStatus("Error");
        log(error.message);
        stopStream();
    } finally {
        startButton.disabled = false;
    }
}

function stopStream() {
    if (peerConnection) {
        peerConnection.close();
        peerConnection = null;
    }

    if (video.srcObject) {
        video.srcObject.getTracks().forEach((track) => track.stop());
        video.srcObject = null;
    }

    setStatus("Stopped");
}

startButton.addEventListener("click", startStream);
stopButton.addEventListener("click", stopStream);
window.addEventListener("beforeunload", stopStream);
