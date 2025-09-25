<template>
  <div class="video-call">
    <h2>WebRTC Video Call (First 2 users only)</h2>
    <video ref="localVideo" autoplay playsinline muted class="video"></video>
    <video ref="remoteVideo" autoplay playsinline class="video"></video>
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
      localStream: null
    };
  },
  async mounted() {
    try {
      // Initialize socket first
      this.socket = io("http://localhost:8000", { 
        withCredentials: true,
        query: { type: "video" } 
      });

      // Get local media stream
      this.localStream = await navigator.mediaDevices.getUserMedia({ 
        video: true, 
        audio: true 
      });
      
      // Set local video source
      this.$refs.localVideo.srcObject = this.localStream;

      // Create peer connection with STUN/TURN servers
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

      // Add local tracks to peer connection
      this.localStream.getTracks().forEach(track => {
        this.pc.addTrack(track, this.localStream);
      });

      // Handle remote stream
      this.pc.ontrack = (event) => {
        console.log("Received remote stream");
        this.$refs.remoteVideo.srcObject = event.streams[0];
      };

      // Handle ICE candidates
      this.pc.onicecandidate = (event) => {
        if (event.candidate) {
          this.socket.emit("signalling", { 
            type: "candidate", 
            candidate: event.candidate,
            to: this.otherUserId 
          });
        }
      };

      // Create offer when negotiation is needed
      this.pc.onnegotiationneeded = async () => {
        try {
          const offer = await this.pc.createOffer();
          await this.pc.setLocalDescription(offer);
          this.socket.emit("signalling", { 
            type: "offer", 
            offer: offer,
            to: this.otherUserId 
          });
        } catch (error) {
          console.error("Error creating offer:", error);
        }
      };

      // Set up socket event listeners for signaling
      this.socket.on("signalling", async (data) => {
        try {
          if (data.type === "offer") {
            await this.pc.setRemoteDescription(new RTCSessionDescription(data.offer));
            const answer = await this.pc.createAnswer();
            await this.pc.setLocalDescription(answer);
            this.socket.emit("signalling", { 
              type: "answer", 
              answer: answer,
              to: this.otherUserId 
            });
          } 
          else if (data.type === "answer") {
            await this.pc.setRemoteDescription(new RTCSessionDescription(data.answer));
          } 
          else if (data.type === "candidate") {
            try {
              await this.pc.addIceCandidate(new RTCIceCandidate(data.candidate));
            } catch (e) {
              console.error("Error adding ICE candidate:", e);
            }
          }
        } catch (error) {
          console.error("Error handling signalling message:", error);
        }
      });

      // Handle socket connection
      this.socket.on("connect", () => {
        console.log("Socket connected to video namespace");
      });

      // Handle connection state changes for debugging
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
  unmounted() {
    // Cleanup
    if (this.localStream) {
      this.localStream.getTracks().forEach(track => track.stop());
    }
    if (this.pc) {
      this.pc.close();
    }
    if (this.socket) {
      this.socket.disconnect();
    }
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

.video {
  width: 300px;
  height: 225px;
  border: 1px solid #ccc;
  margin: 10px;
}
</style>