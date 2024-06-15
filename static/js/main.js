function update_profile() {
    let file = $("#input-pic")[0].files[0];
    let username = $("#Username").val();
    let nama = $("#nama").val();
    let noHp = $("#noHp").val();
    let email = $("#email").val();
    let form_data = new FormData();
    form_data.append("file_give", file);
    form_data.append("username_give", username);
    form_data.append("nama_give", nama);
    form_data.append("noHp_give", noHp);
    form_data.append("email_give", email);
    console.log( file, username, nama, noHp,email, form_data);

    $.ajax({
        type: "POST",
        url: "/update_profile",
        data: form_data,
        cache: false,
        contentType: false,
        processData: false,
        success: function (response) {
            if (response["result"] === "success") {
                alert(response["msg"]);
                window.location.reload();
            }
        },
    });
}

function login() {
    let username = $("#username").val();
    let password = $("#password").val();
  
    if (username === "") {
      $("#help-id-login").text("Please input your id.");
      $("#username").focus();
      return;
    } else {
      $("#help-id-login").text("");
    }
  
    if (password === "") {
      $("#help-password-login").text("Please input your password.");
      $("#password").focus();
      return;
    } else {
      $("#help-password-login").text("");
    }
  
    $.ajax({
      type: "POST",
      url: "/login",
      data: {
        username_give: username,
        password_give: password,
      },
      success: function (response) {
        if (response.result === "success") {
            if(response.role === "user"){

                alert("Login succes");
                $.cookie("tokenuser", response["token"], { path: "/" });
                window.location.replace("/");
            }else if(response.role === "admin"){
                alert("Login succes to admin");
                $.cookie("mytoken", response["token"], { path: "/admin" });
                window.location.replace("/admin");
            }
        } 
      
        else {
          alert(response["msg"]);
        }
      },
    });
  }

  function sign_up() {
  let helpPassword = $("#help-password");
  let inputPassword = $("#input-password-sign-up");
  let helpPassword2 = $("#help-password2");
  let inputPassword2 = $("#input-password2");
  let inputUsername = $("#input-username-sign-up")
  let helpId = $("#help-id");

  let username = inputUsername.val();
  let password = inputPassword.val();
  let password2 = inputPassword2.val();

  if(username === ""){
    helpId
    .text("For your id, please enter 2-10 characters, numbers,or the following special characters (._-)")
    inputUsername.focus();
    return;
  }else{
    helpId.text("")
  }

  if (password === "") {
    helpPassword
      .text("Please enter your password")
      .removeClass("is-safe")
      .addClass("is-danger");
    inputPassword.focus();
    return;
  } else {
    helpPassword
      .text("")     
  }

  if (password2 === "") {
    helpPassword2
      .text("Please enter in your password again")
    inputPassword2.focus();
    return;
  }else{
    helpPassword2
      .text("")
  }
  $.ajax({
    type: "POST",
    url: "/signup",
    data: {
      username_give: username,
      password_give: password,
    },
    success: function (response) {
      alert("You are registered Nice!");
      window.location.replace("/login");
    },
  });
}