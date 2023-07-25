document.getElementById('login-form').addEventListener('submit', function (e) {
    e.preventDefault();

    var email = document.getElementById('login-email').value;
    var password = document.getElementById('login-password').value;

    firebase.auth().signInWithEmailAndPassword(email, password)
        .then((userCredential) => {
            // ログイン成功
            var user = userCredential.user;
            alert("ログイン成功");
        })
        .catch((error) => {
            // ログイン失敗
            var errorCode = error.code;
            var errorMessage = error.message;
            alert("ログイン失敗: " + errorMessage);
        });
});
