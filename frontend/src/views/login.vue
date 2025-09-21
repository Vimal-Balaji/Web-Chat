<template>
  <div class="container">
    <div class="wrapper mt-4">
      <div class="title">Login Form</div>
      <form>
        <div class="field">
          <input type="text" v-model="phoneNo" required />
          <label>Phone No.</label>
        </div>
        <div class="field">
          <input type="password" v-model="password" required />
          <label>Password</label>
        </div>
        <div class="field">
          <button type="button" class="btn login-btn" @click="login">Login</button>
        </div>
        <div class="field mt-3">
          <button type="button" class="btn signup-btn" @click="$router.push('/signup')">
             Sign Up
          </button>
        </div>
      </form>
      <div class="text-center m-3">{{ message }}</div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      phoneNo: '',
      password: '',
      message: ''
    }
  },
  methods: {
    async login() {
      try {
        const response = await fetch('http://localhost:8000/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: "include",
          body: JSON.stringify({
            phoneNo: this.phoneNo,
            password: this.password
          })
        });
        const data = await response.json();
        if (response.ok) {
          this.message = "Login successful!!";
          console.log("Login successful:", data);
          localStorage.setItem('userId', data.userId);
         window.location.href = '/chat';
        } else {
          this.message = data.detail || "Login failed. Please try again.";
        }
      } catch (error) {
        console.error("Error during login:", error);
        this.message = "An error occurred. Please try again.";
      }
    }
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css?family=Poppins:400,500,600,700&display=swap');


html, body, #app {
  height: 100%;
  margin: 0;
}

.container {
  height: 100vh;
  width: 100vw;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f2f2f2;
}

.wrapper {
  width: 380px;
  background: #fff;
  border-radius: 15px;
  box-shadow: 0px 15px 20px rgba(0, 0, 0, 0.1);
}



.wrapper .title {
  font-size: 28px;
  font-weight: 600;
  text-align: center;
  padding: 20px;
  color: #fff;
  border-radius: 15px 15px 0 0;
  background: linear-gradient(-135deg, #2d292d, #737478);
}

.wrapper form {
  padding: 20px 30px 40px 30px;
}

.wrapper form .field {
  margin-top: 20px;
  position: relative;
}

.wrapper form .field input {
  height: 45px;
  width: 100%;
  outline: none;
  font-size: 16px;
  padding-left: 15px;
  border: 1px solid lightgrey;
  border-radius: 25px;
  transition: all 0.3s ease;
}

.wrapper form .field input:focus,
.wrapper form .field input:valid {
  border-color: #4158d0;
}

.wrapper form .field label {
  position: absolute;
  top: 50%;
  left: 20px;
  color: #999;
  font-size: 16px;
  pointer-events: none;
  transform: translateY(-50%);
  transition: all 0.3s ease;
}

.wrapper form .field input:focus ~ label,
.wrapper form .field input:valid ~ label {
  top: -8px;
  font-size: 14px;
  color: #4158d0;
  background: #fff;
  padding: 0 5px;
}

/* ✅ Fixed button sizes */
.btn {
  height: 45px;
  width: 100%;
  border: none;
  border-radius: 5px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.3s ease;
}

.login-btn {
  background: #222;
  color: #fff;
}

.login-btn:hover {
  background: #000;
}

.signup-btn {
  background: #737478;
  color: #fff;
}

.signup-btn:hover {
  background: #5c5d60;
}
</style>
