//로그아웃기능
function logout_out() {
    $.removeCookie('mytoken', {path: '/'});
    alert('로그아웃!')
    window.location.href = "/login"
}

function login(){
    window.location.href="/login"
}

function home(){
    window.location.href="/"
}

function writeReview() {
    //TODO 로그인 되어있는지 체크
    //if(로그인 되어있으면){
    window.location.href = "/review/insert"
    // }else{
    //      if(confirm('로그인하시면 리뷰를 쓸수 있습니다.\n 로그인 하시겠습니까?'){
    //          login()
    //      }
    // }
}