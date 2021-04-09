if (window.innerWidth>=992 || window.location.href.endsWith('/chat')) {

  var socket=io();
  var is_typing=false;

  $('#chatsend').click(function (event) {

    if (event.which != 1) {
      return
    }
    event.preventDefault();

    console.log('clicked')

    text = $('#input-text').val()
    guild=$('#guildname').val()

    socket.emit('speak', {text: text, guild: guild});
    $('#input-text').val('')
    is_typing=false

  });

  $('#input-text').on('input', function() {
    text=$('#input-text').val();
    guild=$('#guildname').val();
    if (text==''){
      if (is_typing==true) {
        is_typing=false;
        socket.emit('typing', {guild: guild, typing: false});
      }
    }
    else {
      if (is_typing==false) {
        is_typing=true;
        socket.emit('typing', {guild: guild, typing: true});
      }
    }
  });

  socket.on('typing', function (json){
    users=json['users']
    if (users.length==0){
      $('#typing-indicator').html('');
      $('#loading-indicator').addClass('d-none');
    }
    else if (users.length==1){
      $('#typing-indicator').html('<b>'+users[0]+"</b> is typing");
      $('#loading-indicator').removeClass('d-none');
    }
    else if (users.length==2){
      $('#typing-indicator').html('<b>'+users[0]+"</b> and <b>"+users[1]+"</b> are typing");
      $('#loading-indicator').removeClass('d-none');
    }
    else if (users.length==3){
      $('#typing-indicator').html('<b>'+users[0]+"</b>, <b>"+users[1]+"</b>, and <b>"+users[2]+"</b> are typing");
      $('#loading-indicator').removeClass('d-none');
    }
    else if (users.length>=4){
      more=users.length-3
      $('#typing-indicator').html('<b>'+users[0]+"</b>, <b>"+users[1]+"</b>, <b>"+users[2]+"</b> and "+more.toString()+" more are typing");
      $('#loading-indicator').removeClass('d-none');
    }
  }
  )

  var notifs=0;
  var titletoggle=true;
  var focused=true;
  var original_title=$('title').text()

  var flash = function(){

    guild=$('#guildname').val();

    if (notifs>=1 && focused==false){
      $('link[rel="shortcut icon"]').attr('href','/assets/images/logo/favicon_alert.png')
      if (titletoggle) {
        $('title').text('['+notifs.toString()+'] '+ original_title);
        titletoggle=false;
      }
      else {
        $('link[rel="shortcut icon"]').attr('href','/assets/images/logo/favicon.png')
        titletoggle=true;
      }
      setTimeout(flash, 500)
    }
    else {
      $('link[rel="shortcut icon"]').attr('href','/assets/images/logo/favicon.png')
      notifs=0
        $('title').text(original_title);
      titletoggle=true;
    }
  }

  on_blur = function(){
    focused=false
  };
  on_focus = function(){
    focused=true
    flash()
  };
  window.addEventListener('blur', on_blur);
  window.addEventListener('focus', on_focus);

  var scrolled_down=true;

  var box = document.getElementById('chat-text');

  var should_scroll = function() {
    scrolled_down= (box.scrollHeight - box.scrollTop <= window.innerHeight-109)
  }

  var scroll=function() {
    if (scrolled_down) {
      box.scrollTo(0,box.scrollHeight)
    }
  }

  var process_chat = function(json, template){
    console.log(json);
    username=json['username'];
    text=json['text'];
    ava=json['avatar']

    var my_name=$('#username').val()

    if (template=="#msg-in" || text.includes('href="/@'+my_name+'"')){
      $(template+'-template .chat-line').addClass('chat-mention');
      notifs=notifs+1;
      setTimeout(flash, 500);
    }
    else {
      $(template+' .chat-line').removeClass('chat-mention');
    };

    should_scroll()
    $(template+'-template img').attr('src', ava)
    $(template+'-template img').attr('data-original-title', json['time'])
    $(template+'-template a').attr('href','/@'+username)
    $(template+'-template a').text('@'+username)
    $(template+'-template .chat-message').html(text)
    $('#chat-text').append($(template+'-template .chat-line').clone())
    scroll()
  }

  socket.on('speak', function(json){process_chat(json, "#chat-line")});
  socket.on('bot',  function(json){process_chat(json, "#bot")});
  socket.on('wallop',  function(json){process_chat(json, "#wallop")});
  socket.on('gm',  function(json){process_chat(json, "#gm")});
  socket.on('admin',  function(json){process_chat(json, "#admin")});
  socket.on('motd',  function(json){process_chat(json, "#motd")});
  socket.on('msg-out',  function(json){process_chat(json, "#msg-out")});
  socket.on('msg-in',  function(json){process_chat(json, "#msg-in")});


  socket.on('message', function(msg){
    should_scroll()
    $('#system-template .message').text(msg)
    $('#chat-text').append($('#system-template .system-line').clone())
    scroll()
  }
  );

  socket.on('info', function(data){
    should_scroll()
    $('#system-info .message').text(data['msg'])
    $('#chat-text').append($('#system-info .system-line').clone())
    scroll()
  }
  );

  socket.on('me', function(data){
    should_scroll()
    $('#me-template .message').text(data['msg'])
    $('#chat-text').append($('#me-template .system-line').clone())
    scroll()
  }
  );


  socket.on('warning', function(data){
    should_scroll()
    $('#system-warning .message').text(data['msg'])
    $('#chat-text').append($('#system-warning .system-line').clone())
    scroll()
  }
  );

  socket.on('count', function(data){
    $('.board-chat-count').text(data['count'])
  }
  );

  socket.on('connect',
    function(event) {
      console.log('connected, joining room')
      name=$('#guildname').val();

      join=($('#autojoin').val()=="True")
      if (join){
        socket.emit('join room', {'guild': name });
      }
    }
    )

  document.getElementById('input-text').addEventListener("keyup", function(event) {
      // Number 13 is the "Enter" key on the keyboard
      if (event.keyCode === 13) {
        // Cancel the default action, if needed
        event.preventDefault();
        // Trigger the button element with a click
        document.getElementById("chatsend").click();
      }
    }
    )

  var upload_chat_image=function(){

    file=document.getElementById('chat-image-upload').files[0];
    fd=new FormData();
    fd.append("image", file);

    xhr= new XMLHttpRequest();
    xhr.open("post", "/chat_upload");
    xhr.withCredentials=true;
    xhr.onload=function(){
      guild=$('#guildname').val()
      url=JSON.parse(xhr.response)['url']
      text='![]('+url+')'
      socket.emit('speak', {text: text, guild: guild});
      document.getElementById('chat-image-upload').value=null;
      box.scrollTo(0,box.scrollHeight)
    }
    xhr.send(fd);
  }
}