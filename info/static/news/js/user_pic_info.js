function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}


$(function () {
    $('#avatar')

    $(".pic_info").submit(function (e) {
        e.preventDefault()
        console.log($('#avatar'))
        //TODO 上传头像
        $(this).ajaxSubmit({
            url: '/user/pic_info',
            type: 'post',
            headers: {'X-CSRFToken': getCookie('csrf_token')},
            success: function(resp){
                if(resp.errno==0){
                    $('.now_user_pic').attr('src', resp.data.user_info.avatar_url)
                    $('.user_center_pic>img', parent.document).attr('src', resp.data.user_info.avatar_url)
                    $('.user_login>img', parent.document).attr('src', resp.data.user_info.avatar_url)
                }else{
                    console.log(resp.errmsg)
                }
            }
        })
    })
})