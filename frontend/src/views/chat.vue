<template>
  <div class="d-flex vh-100 bg-light">
    <!-- Sidebar -->
    <div class="border-end bg-white" style="width: 30%; min-width: 250px;">
      <div class="p-3 border-bottom fw-bold">Chats</div>
      <button @click="logout">logout</button>
      <div class="overflow-auto" style="height: calc(100% - 56px);">
        <div
          v-for="(chat, index) in chats"
          :key="index"
          class="p-3 border-bottom chat-item"
        >
          <button
            class="btn p-0 fw-semibold text-dark text-decoration-none w-100 text-start"
            @click="selectChat(chat)"
          >
            {{ chat.name }}

            <!-- Last message -->
            <div v-if="chat.senderId == userId" class="text-muted small">
              <b>You:</b> {{ chat.message }}
            </div>
            <div v-else class="text-muted small">
              {{ chat.message }}
            </div>

            <!-- Unread Indicator -->
            <div
              v-if="unreadDict[chat.otherId]"
              class="text-danger small fw-bold"
            >
              New message arrived
            </div>
          </button>
        </div>
      </div>
    </div>

    <!-- Chat Window -->
    <div class="flex-grow-1 d-flex flex-column">
      <div class="p-3 border-bottom fw-bold d-flex align-items-center">
        <!-- Default user icon -->
        <i class="bi bi-person-circle fs-3 me-2"></i>
        {{ senderName }}
        <button @click="toggleBlock" class="btn btn-sm btn-outline-danger ms-3">
          {{ blockedUser[senderId] ? "Unblock" : "Block" }}
        </button>
      </div>

      <!-- Messages -->
      <div class="flex-grow-1 overflow-auto p-3 bg-light">
        <div
          v-for="(msg, i) in messages"
          :key="i"
          class="d-flex mb-2"
          :class="msg.from == 'me' ? 'justify-content-end' : 'justify-content-start'"
        >
          <div
            class="p-2 rounded"
            :class="msg.from == 'me' ? 'bg-dark text-white' : 'bg-white border'"
            style="max-width: 60%;"
          >
            {{ msg.text }}
          </div>
        </div>
      </div>

      <!-- Input Box -->
      <div class="p-3 border-top d-flex">
        <input
          type="text"
          v-model="input"
          class="form-control me-2"
          placeholder="Type a message"
          @keyup.enter="sendMessage"
          :disabled="blockedUser[senderId]"
        />
        <button
          class="btn btn-dark"
          @click="sendMessage"
          :disabled="blockedUser[senderId]"
        >
          Send
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { io } from "socket.io-client";

export default {
  name: "chat",
  data() {
    return {
      socket: null,
      chats: [],
      senderId: "",
      senderName: "",
      userId: localStorage.getItem("userId"),
      messages: [],
      messageDict: {},
      unreadDict: {}, // store unread status
      input: "",
      blockedUser: {}, // store block status per user
    };
  },
  async created() {
    this.checkAuth();
    this.getNames();
  },
  async mounted() {
    this.socket = io("http://localhost:8000", { withCredentials: true });

    this.socket.on("connect", () => {
      console.log("Connected to server");
    });

    this.socket.on("new_message", (data) => {
      if (data.senderId == this.senderId) {
        // Current chat is open → push message directly
        this.messages.push({ from: "other", text: data.message });
        this.messageDict[this.senderId] = this.messages;
      } else {
        // Chat is not open → mark as unread
        this.unreadDict[data.otherId] = true;
      }

      // Reorder chats so latest is on top
      const chatIndex = this.chats.findIndex(
        (chat) => chat.otherId == data.otherId
      );
      if (chatIndex != -1) {
        const [chat] = this.chats.splice(chatIndex, 1);
      }
      this.chats.unshift({
        otherId: data.otherId,
        name: data.name,
        message: data.message,
        senderId: data.senderId,
      });
    });
  },
  methods: {
    // --------------------------functions of create cycle---------------------------
    async getNames() {
      const response = await fetch("http://localhost:8000/lastMessage", {
        method: "GET",
        credentials: "include",
      });
      this.chats = await response.json();
      console.log(this.chats);
    },
    async checkAuth() {
      try {
        const response = await fetch("http://localhost:8000/check-auth", {
          method: "GET",
          credentials: "include",
        });

        if (!response.ok) {
          this.$router.push("/");
          return;
        }

        const data = await response.json();
        this.isAuthenticated = data.authenticated;

        if (!this.isAuthenticated) {
          this.$router.push("/");
        }
      } catch (error) {
        console.error("Auth check failed:", error);
        this.$router.push("/");
      }
    },

    //----------------------end of create cycle functions-------------------------

    async logout() {
      const response = await fetch("http://localhost:8000/logout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
      });
      if (response.ok) {
        if (this.socket) {
          this.socket.disconnect();
        }
        console.log("Logout successful");
        this.$router.push("/");
      } else {
        console.error("Logout failed");
      }
    },
    async selectChat(chat) {
      this.senderId = chat.otherId;
      this.senderName = chat.name;

      // Clear unread flag when chat is opened
      if (this.unreadDict[this.senderId]) {
        delete this.unreadDict[this.senderId];
      }

      if (this.senderId in this.messageDict) {
        this.messages = this.messageDict[this.senderId];
        return;
      }
      try {
        const response = await fetch(
          `http://localhost:8000/message/${this.senderId}`,
          {
            method: "GET",
            credentials: "include",
          }
        );
        if (response.ok) {
          const data = await response.json();
          const dat = data.messages;

          // Save block status
          this.blockedUser[this.senderId] = data.isBlocked;

          this.messages = dat.map((msg) => ({
            from: msg.senderId == this.userId ? "me" : "other",
            text: msg.message,
          }));
          this.messageDict[this.senderId] = this.messages;
        } else {
          console.error("Failed to fetch messages");
        }
      } catch (error) {
        console.error("Error fetching messages:", error);
      }
    },
    async sendMessage() {
      if (!this.input.trim() || !this.senderId) {
        return;
      }
      const message = this.input.trim();
      this.input = "";
      this.messages.push({ from: "me", text: message });
      this.messageDict[this.senderId] = this.messages;

      const chatIndex = this.chats.findIndex(
        (chat) => chat.otherId == this.senderId
      );
      if (chatIndex != -1) {
        const [chat] = this.chats.splice(chatIndex, 1);
      }
      this.chats.unshift({
        otherId: this.senderId,
        name: this.senderName,
        message: message,
        senderId: this.userId,
      });

      this.socket.emit("private_message", {
        receiverId: this.senderId,
        message: message,
      });
    },
    async toggleBlock() {
      if (!this.senderId) {
        return;
      }
      try {
        if (this.blockedUser[this.senderId]) {
          
          const response = await fetch(
            `http://localhost:8000/unblock/${this.senderId}`,
            { credentials: "include" }
          );
          if (response.ok) {
            this.blockedUser[this.senderId] = false;
            alert("User unblocked successfully");
          } else {
            console.error("Failed to unblock user");
          }
        } else {
     
          const response = await fetch(
            `http://localhost:8000/block/${this.senderId}`,
            { credentials: "include" }
          );
          if (response.ok) {
            this.blockedUser[this.senderId] = true;
            alert("User blocked successfully");
          } else {
            console.error("Failed to block user");
          }
        }
      } catch (error) {
        console.error("Error blocking/unblocking user:", error);
      }
    },
  },
};
</script>

<style>
.chat-item:hover {
  background-color: #f8f9fa;
  cursor: pointer;
}
</style>
