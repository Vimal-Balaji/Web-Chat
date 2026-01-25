<template>
  <div class="video-call">
    <h2>WebRTC Video Call (First 2 users only)</h2>

    <div class="video-container">
      <video ref="localVideo" autoplay playsinline class="video"></video>
      <video ref="remoteVideo" autoplay playsinline class="video"></video>
    </div>

    <div class="controls">
      <button @click="toggleMute">{{ isMuted ? "Unmute Mic" : "Mute Mic" }}</button>
      <button @click="toggleVideo">{{ videoOff ? "Turn Video On" : "Turn Video Off" }}</button>
      <button @click="$router.push('/chat')">Back to Chat</button>
    </div>
  </div>
</template>

<script>
import { io } from "socket.io-client";

export default {
  name: "videoChat",
  data() {
    return {
      userId: localStorage.getItem("userId"),
      otherUserId: this.$route.query.to,
      socket: null,
      pc: null,
      localStream: null,
      isMuted: false,
      videoOff: false
    };
  },
  async mounted() {
    try {
      this.socket = io("http://localhost:8000", { 
        withCredentials: true,
        query: { type: "video" } 
      });

      // Access mic and camera
      this.localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      this.$refs.localVideo.srcObject = this.localStream;

      // Create peer connection
      this.pc = new RTCPeerConnection({
        iceServers: [
          { urls: "stun:stun.l.google.com:19302" },
          {
            urls: "turn:openrelay.metered.ca:80",
            username: "openrelayproject",
            credential: "openrelayproject"
          }
        ]
      });

      // Add local tracks
      this.localStream.getTracks().forEach(track => this.pc.addTrack(track, this.localStream));

      // Remote stream
      this.pc.ontrack = (event) => {
        this.$refs.remoteVideo.srcObject = event.streams[0];
      };

      // ICE candidate
      this.pc.onicecandidate = (event) => {
        if (event.candidate) {
          this.socket.emit("signalling", { 
            type: "candidate", 
            candidate: event.candidate,
            to: this.otherUserId 
          });
        }
      };

      // Negotiation
      this.pc.onnegotiationneeded = async () => {
        try {
          const offer = await this.pc.createOffer();
          await this.pc.setLocalDescription(offer);
          this.socket.emit("signalling", { 
            type: "offer", 
            offer, 
            to: this.otherUserId 
          });
        } catch (error) {
          console.error("Error creating offer:", error);
        }
      };

      // Signalling events
      this.socket.on("signalling", async (data) => {
        try {
          if (data.type === "offer") {
            await this.pc.setRemoteDescription(new RTCSessionDescription(data.offer));
            const answer = await this.pc.createAnswer();
            await this.pc.setLocalDescription(answer);
            this.socket.emit("signalling", { 
              type: "answer", 
              answer, 
              to: this.otherUserId 
            });
          } else if (data.type === "answer") {
            await this.pc.setRemoteDescription(new RTCSessionDescription(data.answer));
          } else if (data.type === "candidate") {
            await this.pc.addIceCandidate(new RTCIceCandidate(data.candidate));
          }
        } catch (error) {
          console.error("Error handling signalling message:", error);
        }
      });

      this.socket.on("connect", () => {
        console.log("Socket connected to video namespace");
      });

      this.pc.onconnectionstatechange = () => {
        console.log("Connection state:", this.pc.connectionState);
      };

      this.pc.oniceconnectionstatechange = () => {
        console.log("ICE connection state:", this.pc.iceConnectionState);
      };

    } catch (error) {
      console.error("Error initializing video call:", error);
    }
  },
  methods: {
    toggleMute() {
      this.isMuted = !this.isMuted;
      this.localStream.getAudioTracks().forEach(track => track.enabled = !this.isMuted);
    },
    toggleVideo() {
      this.videoOff = !this.videoOff;
      this.localStream.getVideoTracks().forEach(track => track.enabled = !this.videoOff);
    }
  },
  unmounted() {
    if (this.localStream) {
      this.localStream.getTracks().forEach(track => track.stop());
    }
    if (this.pc) this.pc.close();
    if (this.socket) this.socket.disconnect();
  }
};
</script>

<style scoped>
.video-call {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
}

.video-container {
  display: flex;
  gap: 15px;
}

.video {
  width: 300px;
  height: 225px;
  border: 1px solid #ccc;
  border-radius: 8px;
}

.controls {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}

button {
  padding: 8px 12px;
  border: none;
  background-color: #1976d2;
  color: white;
  border-radius: 6px;
  cursor: pointer;
  transition: 0.3s;
}

button:hover {
  background-color: #125ca1;
}
</style>
