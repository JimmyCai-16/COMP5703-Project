const emailInput = document.querySelector("#id_email");
  //  const emailError = document.querySelector('#id_email_error');
  const firstNameInput = document.querySelector("#id_first_name");
  const lastNameInput = document.querySelector("#id_last_name");
  const companyInput = document.querySelector("#id_company");
  const password1Input = document.querySelector("#id_password1");
  const password2Input = document.querySelector("#id_password2");
  const registerButton = document.querySelector("#register-btn");
  const error = document.querySelector("#client-error");
  const emailCrossMarker = document.querySelector(".email-cross-marker");
  const fnameCrossMarker = document.querySelector(".fname-cross-marker");
  const lnameCrossMarker = document.querySelector(".lname-cross-marker");
  const companyCrossMarker = document.querySelector(".company-cross-marker");
  const password1CrossMarker = document.querySelector(
    ".password1-cross-marker"
  );
  const password2CrossMarker = document.querySelector(
    ".password2-cross-marker"
  );
  window.onload = function() {
    
    emailInput.value=""
    emailInput.blur()
    password1Input.value=""
    password1Input.focus()
    password1Input.blur()
    error.textContent=""
    if($("input[name='account_type']:checked").val() == "user"){
      $("#terms_conditions").css("display","none")
    }
    else{
      $("#terms_conditions").css("display","")
    }
  
    // $("#register-form").reset()
   
    $(".fa-times").hide()
    $(".fa-check").hide()
    
}

  emailInput.addEventListener("input", () => {
    checkServerError();
    emailCrossMarker.style.display = "inline";
    if (emailInput.value.trim() !== "") {
      if (emailInput.validity.typeMismatch) {
        error.textContent = "Please enter a valid email address.";
        emailInput.setCustomValidity("Please enter a valid email address.");
        emailCrossMarker.classList.replace("fa-check", "fa-times");
      } else {
        error.textContent = "";
        emailCrossMarker.classList.replace("fa-times", "fa-check");
        emailInput.setCustomValidity("");
      }
    } else {
      error.textContent = "Please enter a valid email address.";
      emailInput.setCustomValidity("Please enter a valid email address.");
      emailCrossMarker.classList.replace("fa-check", "fa-times");
    }
    checkInputs();
  });
  firstNameInput.addEventListener("input", () => {
    checkServerError();
    fnameCrossMarker.style.display = "inline";
    const firstName = firstNameInput.value.trim();

    if (firstName === "") {
      error.textContent = "First name is required.";
      firstNameInput.setCustomValidity("First name is required.");
      fnameCrossMarker.classList.replace("fa-check", "fa-times");
    } else {
      error.textContent = "";
      firstNameInput.setCustomValidity("");
      fnameCrossMarker.classList.replace("fa-times", "fa-check");
    }
    checkInputs();
  });
  lastNameInput.addEventListener("input", () => {
    checkServerError();
    const lastName = lastNameInput.value.trim();
    lnameCrossMarker.style.display = "inline";
    if (lastName === "") {
      error.textContent = "Last name is required.";
      lastNameInput.setCustomValidity("Last name is required.");

      lnameCrossMarker.classList.replace("fa-check", "fa-times");
    } else {
      error.textContent = "";
      lastNameInput.setCustomValidity("");
      lnameCrossMarker.classList.replace("fa-times", "fa-check");
    }
    checkInputs();
  });
  companyInput.addEventListener("input", () => {
    checkServerError();
    const company = companyInput.value.trim();
    companyCrossMarker.style.display = "inline";
    if (company === "") {
      error.textContent = "Company name is required.";
      companyInput.setCustomValidity("Comapny name is required.");

      companyCrossMarker.classList.replace("fa-check", "fa-times");
    } else {
      error.textContent = "";
      companyInput.setCustomValidity("");
      companyCrossMarker.classList.replace("fa-times", "fa-check");
    }
    checkInputs();
  });
  password1Input.addEventListener("input", () => {
    checkServerError();
    
    password1CrossMarker.style.display = "inline";
    error.textContent = "";
    let password = password1Input.value;
    let isValid = true;
    checkConfirmPassword();
    if (error.textContent.trim() !== "") {
      password2CrossMarker.classList.replace("fa-check", "fa-times");
    }
    if (password.length < 8 || password.length > 24) {
      $("#pass_length").fadeIn("fast")
      isValid = false;
    }
    else {
      $("#pass_length").fadeOut("fast")
    }

    if (!/[A-Z]/.test(password)) {
      $("#pass_upper").fadeIn("fast")
      isValid = false;
    }
    else {
      $("#pass_upper").fadeOut("fast")
    }

    if (!/\d/.test(password)) {
      $("#pass_number").fadeIn("fast")
      isValid = false;
    }
    else {
      $("#pass_number").fadeOut("fast")
    }

    if (!/\W/.test(password)) {
      $("#pass_special").fadeIn("fast")
      isValid = false;
    }
    else {
      $("#pass_special").fadeOut("fast")
    }

    if (isValid) {
      error.textContent = "";
      password1Input.setCustomValidity("");
      password1CrossMarker.classList.replace("fa-times", "fa-check");
    } else password1CrossMarker.classList.replace("fa-check", "fa-times");
    checkInputs();
  });

  password2Input.addEventListener("input", () => {
    checkConfirmPassword();
  });
  function checkInputs() {
    if (
      emailInput.value &&
      firstNameInput.value &&
      lastNameInput.value &&
      password1Input.value &&
      password2Input.value &&
      companyInput.value &&
      document.querySelector(".fa-times") === null
    ) {
      registerButton.disabled = false;
    } else registerButton.disabled = true;
  }
  function checkServerError() {
    if (document.getElementById("server-error") !== null) {
      document.getElementById("server-error").style.display = "none";
    }
  }
  function checkConfirmPassword() {
    checkServerError();
    password2CrossMarker.style.display = "inline";

    const confirmPassword = password2Input.value;
    const password = password1Input.value;

    if (confirmPassword.trim() === "" || confirmPassword !== password) {
      error.innerHTML = "Passwords do not match. <br>";
      password2Input.setCustomValidity("Passwords do not match.");
      password2CrossMarker.classList.replace("fa-check", "fa-times");
    } else {
      error.innerHTML = "";
      password2Input.setCustomValidity("");
      password2CrossMarker.classList.replace("fa-times", "fa-check");
    }
    checkInputs();
  }
  setTimeout(function () {
    if( document.getElementById("flash-message")){
    document.getElementById("flash-message").innerHTML="";
    document.getElementById("flash-message").style.display = "none";
    }
  }, 5000);

  document.getElementById("register-btn").addEventListener("click", function(event) {
    // Access properties of the event object
 
   let selectedAccountType = document.querySelector('input[name="account_type"]:checked').value
   const register_form = document.getElementById("register-form");
   if(selectedAccountType === "developer")
   {  
    event.preventDefault();
    let isTermsAccepted = $("#acceptTerms").prop("checked")
    if(isTermsAccepted){
      register_form.submit()

    }
    else
    {
      document.getElementById("flash-message").style.display=""
     document.getElementById("flash-message").innerHTML = ' <span class="alert alert-danger text-center px-2 py-2">  You have to accept terms of Orefox </span>';
     setTimeout(function () {
      document.getElementById("flash-message").innerHTML="";
      document.getElementById("flash-message").style.display = "none";
    }, 5000);
    }
     
  }
   else{
  
    register_form.submit()
   }
    // You can perform other actions based on the event object's properties

});
const userAccountType = document.getElementById("id_account_type_0")
const developerAccountType = document.getElementById("id_account_type_1")
//userAccountType.addEventListener('click', handleAccountTypeClick)
//developerAccountType.addEventListener('click', handleAccountTypeClick)
//developerAccountType.addEventListener('click', function(e){e.preventDefault();alert("Coming Soon");userAccountType.checked=true})
function handleAccountTypeClick (event){
 
  let terms = document.getElementById("terms_conditions")
  if(event.target.value == "user"){
 
   terms.style.display ="none"
  }
  else
  terms.style.display ="block"
}
$(document).ready(function () {
  $("#acceptTermsBtn").click(function () {
      $("#acceptTerms").prop("checked", true);
    
  });
  $("#cancelTermsBtn").click(function () {
     $("#acceptTerms").prop("checked", false);
   
});
  $("#termsModal").on("hidden.bs.modal", function () {
    
  });
});


$(document).ready(function () {
  
  $("#id_password1").on('focus', ()=>{
    $("#password_requirements").fadeIn("fast")
  })

  $("#id_password1").on('blur', ()=>{
    $("#password_requirements").fadeOut("fast")
  })

})