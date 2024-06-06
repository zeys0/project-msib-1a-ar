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