
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

var flash = function(){

  guild=$('#guildname').val();

  if (notifs>=1 && focused==false){
    $('link[rel="shortcut icon"]').attr('href','/assets/images/logo/favicon_alert.png')
    if (titletoggle) {
      $('title').text('['+notifs.toString()+'] #'+guild+'- Ruqqus');
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
    $('title').text('#'+guild+'- Ruqqus');
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

var should_scroll = function() {
  scrolled_down= (window.scrollY+window.innerHeight >= document.body.scrollHeight)
}

var scroll=function() {
  if (scrolled_down) {
    window.scrollTo(0,document.body.scrollHeight)
  }
}

socket.on('speak', function(json){
  console.log(json);
  username=json['username'];
  text=json['text'];
  ava=json['avatar']

  var my_name=$('#username').val()

  if (text.includes('href="/@'+my_name+'"')){
    $('#chat-line-template .chat-line').addClass('chat-mention');
    notifs=notifs+1;
    setTimeout(flash, 500);
  }
  else {
    $('#chat-line-template .chat-line').removeClass('chat-mention');
  }

  should_scroll()
  $('#chat-line-template img').attr('src', ava)
  $('#chat-line-template a').attr('href','/@'+username)
  $('#chat-line-template a').text('@'+username)
  $('#chat-line-template .chat-message').html(text)
  $('#chat-text').append($('#chat-line-template .chat-line').clone())
  scroll()
}
);

  socket.on('bot', function(json){
  console.log(json);
  username=json['username'];
  text=json['text'];
  ava=json['avatar']

  should_scroll()
  $('#bot-template img').attr('src', ava)
  $('#bot-template a').attr('href','/@'+username)
  $('#bot-template a').text('@'+username)
  $('#bot-template .chat-message').html(text)
  $('#chat-text').append($('#bot-template .chat-line').clone())
  scroll()
}
);

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

socket.on('wallop', function(json){
  console.log(json);
  username=json['username'];
  text=json['text'];
  ava=json['avatar']

  should_scroll()
  $('#wallop-template img').attr('src', ava)
  $('#wallop-template a').attr('href','/@'+username)
  $('#wallop-template a').text('@'+username)
  $('#wallop-template .chat-message').html(text)
  $('#chat-text').append($('#wallop-template .chat-line').clone())
  scroll()
}
);

socket.on('gm', function(json){
  console.log(json);
  username=json['username'];
  text=json['text'];
  ava=json['avatar']

  var my_name=$('#username').val()

  if (text.includes('href="/@'+my_name+'"')){
    $('#gm-template .chat-line').addClass('chat-mention');
    notifs=notifs+1;
    setTimeout(flash, 500);
  }
  else {
    $('#gm-template .chat-line').removeClass('chat-mention');
  }

  should_scroll()
  $('#gm-template img').attr('src', ava)
  $('#gm-template a').attr('href','/@'+username)
  $('#gm-template a').text('@'+username)
  $('#gm-template .chat-message').html(text)
  $('#chat-text').append($('#gm-template .chat-line').clone())
  scroll()
}
);

socket.on('motd', function(json){
  console.log(json);
  username=json['username'];
  text=json['text'];
  ava=json['avatar']

  should_scroll=(window.scrollY+window.innerHeight >= document.body.scrollheight)

  should_scroll()
  $('#motd-template img').attr('src', ava)
  $('#motd-template a').attr('href','/+'+username)
  $('#motd-template a').text('+'+username)
  $('#motd-template .chat-message').html(text)
  $('#chat-text').append($('#motd-template .chat-line').clone())
  scroll()
}
);

socket.on('admin', function(json){
  console.log(json);
  username=json['username'];
  text=json['text'];
  ava=json['avatar']

  var my_name=$('#username').val()

  if (text.includes('href="/@'+my_name+'"')){
    $('#admin-template .chat-line').addClass('chat-mention');
    notifs=notifs+1;
    setTimeout(flash, 500);
  }
  else {
    $('#admin-template .chat-line').removeClass('chat-mention');
  }

  should_scroll()
  $('#admin-template img').attr('src', ava)
  $('#admin-template a').attr('href','/@'+username)
  $('#admin-template a').text('@'+username)
  $('#admin-template .chat-message').html(text)
  $('#chat-text').append($('#admin-template .chat-line').clone())
  scroll()
}
);

socket.on('count', function(data){
  $('#chat-count').text(data['count'])
}
);

socket.on('connect',
  function(event) {
    console.log('connected, joining room')
    name=$('#guildname').val();
    socket.emit('join room', {'guild': name });
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