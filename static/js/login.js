//로그아웃기능
function logout_out() {
    $.removeCookie('mytoken', {path: '/'});
    alert('로그아웃!')
    window.location.href = "/login"
}

function login(){
    window.location.href="/login"
}