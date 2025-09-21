<template>
  <div v-if="show" class="modal-backdrop">
    <div class="modal-box">
      <div class="modal-header">
        <h5>Enter OTP</h5>
        <button class="btn-close" @click="$emit('close')">&times;</button>
      </div>
      <div class="modal-body">
        <input
          type="text"
          v-model="otp"
          placeholder="Enter OTP"
          class="form-control"
        />
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" @click="$emit('close')">Cancel</button>
        <button class="btn btn-dark" @click="verifyOtp">Verify</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue"

const props = defineProps({
  show: Boolean
})
const emit = defineEmits(["close", "verify"])

const otp = ref("")

function verifyOtp() {
  emit("verify", otp.value)
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal-box {
  background: white;
  border-radius: 10px;
  width: 350px;
  padding: 20px;
  box-shadow: 0 5px 20px rgba(0,0,0,0.3);
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.modal-footer {
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
.btn-close {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
}
</style>
