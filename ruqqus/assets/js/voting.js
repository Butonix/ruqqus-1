

function vote(post_id, direction) {
url="/api/vote/post/"+post_id+"/"+direction;

callback=function(){
thing = document.getElementById("post-"+post_id);
uparrow1=document.getElementById("post-"+post_id+"-up");
downarrow1=document.getElementById("post-"+post_id+"-down");
scoreup1=document.getElementById("post-"+post_id+"-score-up");
scorenone1=document.getElementById("post-"+post_id+"-score-none");
scoredown1=document.getElementById("post-"+post_id+"-score-down");

if (direction=="1") {
thing.classList.add("upvoted");
thing.classList.remove("downvoted");
uparrow1.onclick=function(){vote(post_id, 0)};
downarrow1.onclick=function(){vote(post_id, -1)};
scoreup1.classList.remove("noshow");
scorenone1.classList.add("noshow");
scoredown1.classList.add("noshow");
}
else if (direction=="-1"){
thing.classList.remove("upvoted");
thing.classList.add("downvoted");
uparrow1.onclick=function(){vote(post_id, 1)};
downarrow1.onclick=function(){vote(post_id, 0)};
scoreup1.classList.add("noshow");
scorenone1.classList.add("noshow");
scoredown1.classList.remove("noshow");
}
else if (direction=="0"){
thing.classList.remove("upvoted");
thing.classList.remove("downvoted");
uparrow1.onclick=function(){vote(post_id, 1)};
downarrow1.onclick=function(){vote(post_id, -1)};
scoreup1.classList.add("noshow");
scorenone1.classList.remove("noshow");
scoredown1.classList.add("noshow");
}
}

post(url, callback, "Unable to vote at this time. Please try again later.");
}


function vote_comment(comment_id, direction) {
url="/api/vote/comment/"+ comment_id +"/"+direction;

callback=function(){
thing = document.getElementById("comment-"+ comment_id+"-voting");
uparrow1=document.getElementById("comment-"+ comment_id +"-up");
downarrow1=document.getElementById("comment-"+ comment_id +"-down");
scoreup1=document.getElementById("comment-"+ comment_id +"-score-up");
scorenone1=document.getElementById("comment-"+ comment_id +"-score-none");
scoredown1=document.getElementById("comment-"+ comment_id +"-score-down");

if (direction=="1") {
thing.classList.add("upvoted");
thing.classList.remove("downvoted");
uparrow1.onclick=function(){vote_comment(comment_id, 0)};
downarrow1.onclick=function(){vote_comment(comment_id, -1)};
scoreup1.classList.remove("noshow");
scorenone1.classList.add("noshow");
scoredown1.classList.add("noshow");
}
else if (direction=="-1"){
thing.classList.remove("upvoted");
thing.classList.add("downvoted");
uparrow1.onclick=function(){vote_comment(comment_id, 1)};
downarrow1.onclick=function(){vote_comment(comment_id, 0)};
scoreup1.classList.add("noshow");
scorenone1.classList.add("noshow");
scoredown1.classList.remove("noshow");
}
else if (direction=="0"){
thing.classList.remove("upvoted");
thing.classList.remove("downvoted");
uparrow1.onclick=function(){vote_comment(comment_id, 1)};
downarrow1.onclick=function(){vote_comment(comment_id, -1)};
scoreup1.classList.add("noshow");
scorenone1.classList.remove("noshow");
scoredown1.classList.add("noshow");
}
}

post(url, callback, "Unable to vote at this time. Please try again later.");
}