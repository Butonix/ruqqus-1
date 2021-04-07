
  var socket=io();

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

  });

  socket.on('speak', function(json){
    console.log(json);
    username=json['username'];
    text=json['text'];
    ava=json['avatar']

    $('#chat-line-template img').attr('src', ava)
    $('#chat-line-template a').attr('href','/@'+username)
    $('#chat-line-template a').text('@'+username)
    $('#chat-line-template .chat-message').html(text)
    $('#chat-text').append($('#chat-line-template .chat-line').clone())
    window.scrollTo(0,document.body.scrollHeight)
  }
  );

    socket.on('bot', function(json){
    console.log(json);
    username=json['username'];
    text=json['text'];
    ava=json['avatar']

    $('#bot-template img').attr('src', ava)
    $('#bot-template a').attr('href','/@'+username)
    $('#bot-template a').text('@'+username)
    $('#bot-template .chat-message').html(text)
    $('#chat-text').append($('#bot-template .chat-line').clone())
    window.scrollTo(0,document.body.scrollHeight)
  }
  );

  socket.on('message', function(msg){
    $('#system-template .message').text(msg)
    $('#chat-text').append($('#system-template .system-line').clone())
    window.scrollTo(0,document.body.scrollHeight)
  }
  );

  socket.on('info', function(data){
    $('#system-info .message').text(data['msg'])
    $('#chat-text').append($('#system-info .system-line').clone())
    window.scrollTo(0,document.body.scrollHeight)
  }
  );

  socket.on('me', function(data){
    $('#me-template .message').text(data['msg'])
    $('#chat-text').append($('#me-template .system-line').clone())
    window.scrollTo(0,document.body.scrollHeight)
  }
  );


  socket.on('warning', function(data){
    $('#system-warning .message').text(data['msg'])
    $('#chat-text').append($('#system-warning .system-line').clone())
    window.scrollTo(0,document.body.scrollHeight)
  }
  );

  socket.on('wallop', function(json){
    console.log(json);
    username=json['username'];
    text=json['text'];
    ava=json['avatar']

    $('#wallop-template img').attr('src', ava)
    $('#wallop-template a').attr('href','/@'+username)
    $('#wallop-template a').text('@'+username)
    $('#wallop-template .chat-message').html(text)
    $('#chat-text').append($('#wallop-template .chat-line').clone())
    window.scrollTo(0,document.body.scrollHeight)
  }
  );

  socket.on('gm', function(json){
    console.log(json);
    username=json['username'];
    text=json['text'];
    ava=json['avatar']

    $('#gm-template img').attr('src', ava)
    $('#gm-template a').attr('href','/@'+username)
    $('#gm-template a').text('@'+username)
    $('#gm-template .chat-message').html(text)
    $('#chat-text').append($('#gm-template .chat-line').clone())
    window.scrollTo(0,document.body.scrollHeight)
  }
  );

  socket.on('motd', function(json){
    console.log(json);
    username=json['username'];
    text=json['text'];
    ava=json['avatar']

    $('#motd-template img').attr('src', ava)
    $('#motd-template a').attr('href','/+'+username)
    $('#motd-template a').text('+'+username)
    $('#motd-template .chat-message').html(text)
    $('#chat-text').append($('#motd-template .chat-line').clone())
    window.scrollTo(0,document.body.scrollHeight)
  }
  );

  socket.on('admin', function(json){
    console.log(json);
    username=json['username'];
    text=json['text'];
    ava=json['avatar']

    $('#admin-template img').attr('src', ava)
    $('#admin-template a').attr('href','/@'+username)
    $('#admin-template a').text('@'+username)
    $('#admin-template .chat-message').html(text)
    $('#chat-text').append($('#admin-template .chat-line').clone())
    window.scrollTo(0,document.body.scrollHeight)
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