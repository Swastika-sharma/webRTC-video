// Config variables: change them to point to your own servers
const SIGNALING_SERVER_URL = "https://sparteek65.online:9999";
// WebRTC config: you don't have to change this for the example to work
// If you are testing on localhost, you can just use PC_CONFIG = {}
const PC_CONFIG = {
  iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
};

// Signaling methods
let socket = io(SIGNALING_SERVER_URL, { autoConnect: false });

socket.on("data", (data) => {
  console.log("Data received: ", data);
  handleSignalingData(data);
});

socket.on("ready", () => {
  console.log("Ready");
  socket.emit("join", roomName);
  // Connection with signaling server is ready, and so is local stream
  createPeerConnection();
  sendOffer();
});

let sendData = (data) => {
  socket.emit("data", { room: roomName, data: data });
};

// WebRTC methods
let pc;
let dataChannel;
let receivedChunks = [];
let receivedSize = 0;
let expectedFileSize = 0;
let filename = "";
let localStream;
let remoteStreamElement = document.querySelector("#remoteStream");
let localStreamElement = document.querySelector("#localStream");
let roomName = "class"; // document.querySelector("#room");
let fileSelector = document.getElementById("fileInput");
fileSelector.disabled = true;

let getLocalStream = () => {
  navigator.mediaDevices
    .getUserMedia({ audio: true, video: true })
    .then((stream) => {
      console.log("Stream found");
      localStream = stream;
      // Disable the microphone by default
      stream.getAudioTracks()[0].enabled = false;
      localStreamElement.srcObject = localStream;
      // Connect after making sure that local stream is availble
      socket.connect();
    })
    .catch((error) => {
      console.error("Stream not found: ", error);
    });
};

let createPeerConnection = () => {
  try {
    pc = new RTCPeerConnection(PC_CONFIG);
    pc.onicecandidate = onIceCandidate;
    pc.ontrack = onTrack;
    pc.addStream(localStream);
    dataChannel = pc.createDataChannel("fileTransferChannel");
    handleDataChannel();
    console.log("PeerConnection created");
  } catch (error) {
    console.error("PeerConnection failed: ", error);
  }
};

let handleDataChannel = () => {
  dataChannel.onopen = () => {
    console.log("Data channel is open and ready to be used.");
  };

  dataChannel.onclose = () => {
    console.log("Data channel is closed.");
  };

  dataChannel.onerror = (error) => {
    console.log("Data channel error:", error);
  };

  dataChannel.onmessage = (event) => {
    console.log("Data channel message received:", event.data);
    // Handle incoming file data here
  };

  dataChannel.addEventListener("open", (event) => {
    fileSelector.disabled = false;
  });

  // Disable input when closed
  dataChannel.addEventListener("close", (event) => {
    fileSelector.disabled = true;
  });

  pc.ondatachannel = (event) => {
    const receiveChannel = event.channel;
    receiveChannel.onopen = () => {
      console.log("Receive channel is open and ready to be used.");
    };

    receiveChannel.onclose = () => {
      console.log("Receive channel is closed.");
    };

    receiveChannel.onerror = (error) => {
      console.log("Receive channel error:", error);
    };

    receiveChannel.onmessage = (event) => {
      console.log("Receive channel message received:", event.data);
      if (expectedFileSize === 0) {
        expectedFileSize = event.data;
        console.log("recieved expected file size : ", expectedFileSize);
        var downloadLink = document.createElement("a");
        downloadLink.id = `${expectedFileSize}`;
        downloadLink.style.backgroundColor = "#638f9b";
        downloadLink.style.margin = "10px";
        downloadLink.style.color = "white";
        downloadLink.style.padding = "10px";

        document.getElementById("download").appendChild(downloadLink);
        return;
      }
      if (filename === "") {
        filename = event.data;
        console.log("recieved expected file size : ", expectedFileSize);
        return;
      }
      downloadLink = document.getElementById(`${expectedFileSize}`);
      receivedChunks.push(event.data);
      receivedSize += event.data.byteLength;
      console.log("recieved file size currently downloaded : ", receivedSize);
      downloadLink.style.width = `${receivedSize / expectedFileSize}%`;
      // Check if the received size matches the expected file size
      if (`${receivedSize}` === `${expectedFileSize}`) {
        console.log("download complete ");
        const receivedBlob = new Blob(receivedChunks);

        // Set the ID of the paragraph
        downloadLink.href = URL.createObjectURL(receivedBlob);
        downloadLink.download = filename;
        downloadLink.style.display = "block";
        downloadLink.textContent = filename;
        filename = "";
        receivedSize = 0;
        expectedFileSize = 0;
        receivedChunks = [];
        downloadLink.style.width = `100%`;
      }
      // Handle incoming file data here
    };
  };
};

let sendOffer = () => {
  console.log("Send offer");
  pc.createOffer().then(setAndSendLocalDescription, (error) => {
    console.error("Send offer failed: ", error);
  });
};

let sendAnswer = () => {
  console.log("Send answer");
  pc.createAnswer().then(setAndSendLocalDescription, (error) => {
    console.error("Send answer failed: ", error);
  });
};

let setAndSendLocalDescription = (sessionDescription) => {
  pc.setLocalDescription(sessionDescription);
  console.log("Local description set");
  sendData(sessionDescription);
};

let onIceCandidate = (event) => {
  if (event.candidate) {
    console.log("ICE candidate");
    sendData({
      type: "candidate",
      candidate: event.candidate,
    });
  }
};

let onTrack = (event) => {
  console.log("Add track");
  remoteStreamElement.srcObject = event.streams[0];
};

let iceCandidates = [];

// Function to handle adding ICE candidates after setting the remote description
const addIceCandidates = () => {
  iceCandidates.forEach((candidate) => {
    pc.addIceCandidate(new RTCIceCandidate(candidate))
      .then(() => {
        console.log("ICE candidate added successfully.");
      })
      .catch((error) => {
        console.error("Error adding ICE candidate:", error);
      });
  });
  // Clear the iceCandidates array after adding all candidates
  iceCandidates = [];
};

let handleSignalingData = (data) => {
  try {
    switch (data.data.type) {
      case "offer":
        createPeerConnection();
        pc.setRemoteDescription(new RTCSessionDescription(data.data));
        sendAnswer();
        break;
      case "answer":
        // Define a function to handle setting remote description
        const setRemoteDescriptionStable = () => {
          if (pc.signalingState === "stable") {
            pc.setRemoteDescription(new RTCSessionDescription(message.data))
              .then(() => {
                // Remote description successfully set
                console.log("Remote description set successfully.");
                // Add ICE candidates after setting remote description
                addIceCandidates();
              })
              .catch((error) => {
                // Handle any errors that occur during setting the remote description
                console.error("Error setting remote description:", error);
              });
          } else {
            // Wait and try again when signaling state becomes stable
            setTimeout(setRemoteDescriptionStable, 100); // Adjust the timeout value if needed
          }
        };

        // Call setRemoteDescriptionStable when receiving an "answer" message
        setRemoteDescriptionStable();
        break;

      case "candidate":
        // If remote description is already set, add ICE candidate immediately
        if (pc.remoteDescription) {
          pc.addIceCandidate(new RTCIceCandidate(message.data.candidate))
            .then(() => {
              console.log("ICE candidate added successfully.");
            })
            .catch((error) => {
              console.error("Error adding ICE candidate:", error);
            });
        } else {
          // If remote description is not set, queue ICE candidate to be added later
          iceCandidates.push(message.data.candidate);
        }
        break;

      // Handle other message types if needed
      // case ...

      default:
        // Handle unsupported message types or other cases
        break;
    }
  } catch (error) {
    console.log("Unknow data type recieved: ", error);
  }
};

let toggleMic = () => {
  let track = localStream.getAudioTracks()[0];
  track.enabled = !track.enabled;
  let micClass = track.enabled ? "unmuted" : "muted";
  document.getElementById("toggleMic").className = micClass;
  document.getElementById("toggleMic").style.backgroundColor = track.enabled
    ? "white"
    : "tomato";
};

function sendFile(expectedFileSize, file) {
  const chunkSize = 16 * 1024; // 16 KB chunks
  let offset = 0;

  const reader = new FileReader();

  reader.onload = () => {
    const arrayBuffer = reader.result;
    sendChunk(arrayBuffer);
  };

  reader.onerror = (error) => {
    console.error("Error reading file:", error);
  };

  function sendChunk(arrayBuffer) {
    while (offset < arrayBuffer.byteLength) {
      if (dataChannel.bufferedAmount > dataChannel.bufferedAmountLowThreshold) {
        console.log("Data channel buffer is full, waiting...");
        dataChannel.onbufferedamountlow = () => {
          dataChannel.onbufferedamountlow = null;
          sendChunk(arrayBuffer);
        };
        return;
      }
      const chunk = arrayBuffer.slice(offset, offset + chunkSize);
      dataChannel.send(chunk);
      offset += chunkSize;
      console.log(`Sent chunk: ${offset} / ${arrayBuffer.byteLength}`);
      increaseProgress(expectedFileSize, offset / file.size);
    }
    console.log("sending complete ");
    increaseProgress(expectedFileSize, 100);
  }

  reader.readAsArrayBuffer(file);
}

// Usage example with an input element
document.getElementById("send").addEventListener("click", (event) => {
  const file = fileSelector.files[0];
  if (file) {
    expectedFileSize = file.size;
    filename = file.name;
    dataChannel.send(expectedFileSize);
    dataChannel.send(filename);
    appendSending("sending", filename, expectedFileSize);
    sendFile(expectedFileSize, file);
  }
});

let appendSending = (parent, text, id) => {
  // Create a new paragraph element
  var paragraph = document.createElement("p");

  // Set the ID of the paragraph
  paragraph.id = `${id}`;

  // Set the text content of the paragraph
  paragraph.textContent = `sending ... ${text}`;
  paragraph.style.backgroundColor = "#8b83d0";
  paragraph.style.padding = "10px";
  paragraph.style.color = "white";

  // Set the width of the paragraph using inline styles

  // Append the paragraph to the document body or any other element you want
  document.getElementById(parent).appendChild(paragraph);
};

let increaseProgress = (id, percentage) => {
  document.getElementById(id).style.width = `${percentage}%`;
};

// Start connection
getLocalStream();
