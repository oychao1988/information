function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}


$(function () {
    $(".pass_info").submit(function (e) {
        e.preventDefault();

        var old_password = $('[name=old_password]').val()
        var new_password_1 = $('[name=new_password_1]').val()
        var new_password_2 = $('[name=new_password_2]').val()

        // TODO 修改密码
        var params = {
            'old_password': old_password,
            'new_password_1': new_password_1,
            'new_password_2': new_password_2,
        }

        if(!old_password){
            alert('请输入旧密码')
        }
        if(!new_password_1){
            alert('请输入新密码')
        }
        if(!new_password_2){
            alert('请再次输入新密码')
        }

        if(new_password_1 != new_password_2){
            alert('两次输入的新密码不一致')
        }

        console.log(params)
        $.ajax({
            url: '/user/pass_info',
            type: 'post',
            data: JSON.stringify(params),
            contentType: 'application/json',
            dataType: 'json',
            headers: {'X-CSRFToken': getCookie('csrf_token')},
            success: function(resp){
                if(resp.errno==0){
                    $('.pass_info').children('input').val('')
                }else{
                    console.log(resp.errmsg)
                }
            }

        })
    })
})