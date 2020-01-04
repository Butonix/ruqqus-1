function switch_css() {
  css = document.getElementById("css-link");
  dswitch = document.getElementById("dark-switch");

  if (css.href.endsWith("/assets/style/main.css")) {
    css.href="/assets/style/main_dark.css";
    post("/settings/dark_mode/1");
    dswitch.classList.remove("fa-toggle-off");
    dswitch.classList.add("fa-toggle-on");
  }
  else {
    css.href="/assets/style/main.css";
    post("/settings/dark_mode/0");
    dswitch.classList.remove("fa-toggle-on");
    dswitch.classList.add("fa-toggle-off");
  }
}

function switch_css_board(bname) {
  css = document.getElementById("css-link");
  dswitch = document.getElementById("dark-switch");

  if (css.href.endsWith("/+"+bname+"/main.css")) {
    css.href="/+"+bname+"/dark.css";
    post("/settings/dark_mode/1");
    dswitch.classList.remove("fa-toggle-off");
    dswitch.classList.add("fa-toggle-on");
  }
  else {
    css.href="/+"+bname+"/main.css";
    post("/settings/dark_mode/0");
    dswitch.classList.remove("fa-toggle-on");
    dswitch.classList.add("fa-toggle-off");
  }
}