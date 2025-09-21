<template>
  <div class="wrapper">
    <div class="title"><span>Signup Form</span></div>
    <form @submit.prevent="handleSignup">
      <div class="row">
        <i class="fas fa-user"></i>
        <input type="text" v-model="name" placeholder="Name" required />
      </div>
      <div class="row">
        <i class="fas fa-phone"></i>
        <input type="text" v-model="phoneNo" placeholder="Phone number" required />
      </div>
      <div class="row">
        <i class="fas fa-lock"></i>
        <input type="password" v-model="password" placeholder="Password" required />
      </div>
      <div class="row">
        <i class="fas fa-lock"></i>
        <input type="password" v-model="confirmPassword" placeholder="Confirm Password" required />
      </div>
      <div class="row button">
        <button class="btn btn-dark" @click="signup"> Sign Up</button>
      </div>
      <div class="signup-link" >Already have an account? <router-link to="/login">Login now</router-link></div>
      <p class="text-center mt-3">{{ message }}</p>
    </form>
    <OtpModal 
        :show="showOtpModal"
        @close="showOtpModal = false"
        @verify="verifyOtp"
     />   
</div>
</template>
<script>
import OtpModal from '../modals/OtpModal.vue';  
export default{
    components:{
        OtpModal
    },
    data(){
        return{
            name:'',
            phoneNo:'',
            password:'',
            confirmPassword:'',
            message:'',
            showOtpModal:false
        }
    },
    methods:{
        async signup(){
            if(this.password !== this.confirmPassword){
                alert("Passwords do not match");
                return;
            }

            console.log("Signing up with", this.name, this.email, this.password);
            this.showOtpModal = true;
            
        },
        async verifyOtp(otp){
            console.log("Verifying OTP:", otp);
            const response = await fetch('http://localhost:8000/signup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: this.name,
                    phoneNo: this.phoneNo,  
                    password: this.password,
                    otp: otp
                })
            });
            const data = await response.json();
            if(response.status !== 201){
                this.message = data.detail || "Signup failed";
            }
            else{
                this.message="OTP verified successfully! Account created.";
                setTimeout(() => {
                    this.$router.push('/login');
                }, 2000);
            }
            
            this.showOtpModal = false;
        }
    }
}
</script>
<style scoped>
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.6.0/css/all.min.css');

.wrapper {
  width: 380px;
  background: #fff;
  padding: 40px 30px;
  border-radius: 10px;
  box-shadow: 0 15px 25px rgba(0, 0, 0, 0.2);
  margin: 100px auto;
}

.wrapper .title {
  font-size: 24px;
  font-weight: 600;
  text-align: center;
  margin-bottom: 25px;
  color: #333;
}

.wrapper .row {
  position: relative;
  height: 45px;
  margin-bottom: 25px;
}

.wrapper .row i {
  position: absolute;
  width: 47px;
  height: 100%;
  background: #333;
  color: #fff;
  font-size: 18px;
  text-align: center;
  line-height: 45px;
  border-radius: 5px 0 0 5px;
}

.wrapper .row input {
  width: 100%;
  height: 100%;
  padding-left: 55px;
  border: none;
  outline: none;
  background: #f0f0f0;
  border-radius: 5px;
  font-size: 16px;
}

.wrapper .row.button input {
  background: #333;
  color: #fff;
  font-weight: 500;
  cursor: pointer;
  transition: 0.3s;
}

.wrapper .row.button input:hover {
  background: #444;
}

.signup-link {
  text-align: center;
  font-size: 14px;
  margin-top: 20px;
}

.signup-link a {
  color: #007bff;
  text-decoration: none;
}
.signup-link a:hover {
  text-decoration: underline;
}
</style>